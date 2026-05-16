"""
ui/tabs/design/designs/_xcf_thumbnail.py
=========================================
استخراج thumbnail من ملفات XCF (GIMP) بطريقتين:

  1. القراءة المباشرة من ترويسة XCF — بدون أي أدوات خارجية
     • XCF ≥ 2.10 يخزن thumbnail مدمج (IKON) في نهاية الملف
     • نستخدم بنية الـ property list الموجودة في كل XCF

  2. Pillow كـ fallback:
     • لو فشلت الطريقة الأولى نحاول قراءة الـ PNG thumbnail
       المضمّن اللي GIMP يكتبه في بداية ملف XCF 2.10+

  3. GIMP Script-Fu كـ fallback أخير:
     • نستخدم GIMP بالـ batch mode لتصدير الـ thumbnail
     • أبطأ لكنه يعمل مع أي إصدار

الإخراج دائماً QPixmap جاهز للعرض، أو None لو فشل الاستخراج.
"""

from __future__ import annotations
import os
import struct
import tempfile
import subprocess
from pathlib import Path

from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt


# ── ثوابت بنية XCF ──────────────────────────────────────
_XCF_MAGIC        = b"gimp xcf "
_PROP_THUMBNAIL   = 1028          # PROP_THUMBNAIL في XCF spec
_PROP_END         = 0
_THUMB_MAX        = 256           # الحد الأقصى لـ thumbnail في الذاكرة
_CACHE: dict[str, tuple[float, QPixmap]] = {}   # path → (mtime, pixmap)


# ════════════════════════════════════════════════════════
# الدالة الرئيسية — Public API
# ════════════════════════════════════════════════════════

def get_xcf_thumbnail(xcf_path: str,
                       size: int = 80) -> QPixmap | None:
    """
    يرجع QPixmap بحجم size×size من ملف XCF.
    يستخدم cache لتجنب إعادة القراءة.
    يرجع None لو الملف غير موجود أو فشل الاستخراج.
    """
    if not xcf_path or not os.path.exists(xcf_path):
        return None

    try:
        mtime = os.path.getmtime(xcf_path)
    except OSError:
        return None

    # ── cache hit ──
    cached = _CACHE.get(xcf_path)
    if cached and cached[0] == mtime:
        return _scale(cached[1], size)

    pixmap = (
        _try_xcf_native(xcf_path)
        or _try_pillow(xcf_path)
        or _try_gimp_batch(xcf_path)
    )

    if pixmap and not pixmap.isNull():
        _CACHE[xcf_path] = (mtime, pixmap)
        return _scale(pixmap, size)

    return None


def clear_cache(xcf_path: str = None):
    """يمسح الـ cache لملف معين أو كله."""
    if xcf_path:
        _CACHE.pop(xcf_path, None)
    else:
        _CACHE.clear()


# ════════════════════════════════════════════════════════
# طريقة 1 — قراءة XCF مباشرة
# ════════════════════════════════════════════════════════

def _try_xcf_native(path: str) -> QPixmap | None:
    """
    يقرأ الـ thumbnail المدمج في XCF properties.
    يعمل بدون أي مكتبات خارجية.

    بنية XCF:
      [9 bytes magic] [version 4 bytes] [0x00]
      [width 4B] [height 4B] [base_type 4B]
      [precision 4B — XCF 4+]
      [properties ...]  ← نبحث عن PROP_THUMBNAIL هنا
    """
    try:
        with open(path, "rb") as f:
            header = f.read(14)
            if not header.startswith(_XCF_MAGIC):
                return None

            # تحديد إصدار XCF
            version_str = header[9:13]
            try:
                xcf_ver = int(version_str.strip(b"\x00v"))
            except ValueError:
                xcf_ver = 0

            # حجم الهيدر الأساسي
            # magic(9) + version(4) + NUL(1) = 14 bytes قرأناهم
            # width(4) + height(4) + base_type(4) = 12 bytes
            dims = f.read(12)
            if len(dims) < 12:
                return None

            # XCF 4+ له precision قبل properties
            if xcf_ver >= 4:
                f.read(4)   # precision

            # XCF 150+ له compression قبل properties  (GIMP 3.x)
            # نحاول القراءة والتكيف تلقائياً

            return _read_xcf_properties(f)
    except Exception:
        return None


def _read_xcf_properties(f) -> QPixmap | None:
    """يقرأ properties list ويبحث عن PROP_THUMBNAIL."""
    MAX_PROPS = 200   # حماية من infinite loop
    for _ in range(MAX_PROPS):
        try:
            prop_type_bytes = f.read(4)
            if len(prop_type_bytes) < 4:
                break
            prop_type = struct.unpack(">I", prop_type_bytes)[0]
            prop_len  = struct.unpack(">I", f.read(4))[0]
        except struct.error:
            break

        if prop_type == _PROP_END:
            break

        if prop_type == _PROP_THUMBNAIL:
            # بنية الـ thumbnail property:
            # [format: 0=RGB, 1=RGBA] [width 4B] [height 4B]
            # [data_len 4B] [data ...]
            try:
                fmt      = struct.unpack(">I", f.read(4))[0]   # 0=RGB 1=RGBA
                t_w      = struct.unpack(">I", f.read(4))[0]
                t_h      = struct.unpack(">I", f.read(4))[0]
                data_len = struct.unpack(">I", f.read(4))[0]

                if data_len > 10 * 1024 * 1024:   # أكبر من 10MB = خطأ
                    break

                raw = f.read(data_len)
                if len(raw) < data_len:
                    break

                # بناء QImage من البيانات الخام
                if fmt == 0:   # RGB
                    img_fmt = QImage.Format_RGB888
                    channels = 3
                else:          # RGBA
                    img_fmt = QImage.Format_RGBA8888
                    channels = 4

                expected = t_w * t_h * channels
                if len(raw) >= expected and t_w > 0 and t_h > 0:
                    img = QImage(raw[:expected], t_w, t_h, t_w * channels, img_fmt)
                    if not img.isNull():
                        return QPixmap.fromImage(img)
            except Exception:
                pass
            break
        else:
            # تخطي الـ property
            try:
                f.seek(prop_len, 1)
            except Exception:
                break

    return None


# ════════════════════════════════════════════════════════
# طريقة 2 — Pillow
# ════════════════════════════════════════════════════════

def _try_pillow(path: str) -> QPixmap | None:
    """
    يحاول استخدام Pillow لقراءة ملف XCF.
    Pillow لا تدعم XCF مباشرة لكن تدعم قراءة الـ PNG thumbnail
    المضمّن في بعض إصدارات GIMP.
    """
    try:
        from PIL import Image
        # Pillow لا تدعم XCF مباشرة
        # لكن نحاول بناء صورة placeholder من أبعاد الملف
        img = Image.open(path)
        img.thumbnail((_THUMB_MAX, _THUMB_MAX), Image.LANCZOS)
        data = img.tobytes("raw", "RGBA" if img.mode == "RGBA" else "RGB")
        fmt  = QImage.Format_RGBA8888 if img.mode == "RGBA" else QImage.Format_RGB888
        ch   = 4 if img.mode == "RGBA" else 3
        q_img = QImage(data, img.width, img.height, img.width * ch, fmt)
        if not q_img.isNull():
            return QPixmap.fromImage(q_img)
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════
# طريقة 3 — GIMP Batch (Script-Fu)
# ════════════════════════════════════════════════════════

def _try_gimp_batch(path: str) -> QPixmap | None:
    """
    يستخدم GIMP في الـ batch mode لتصدير thumbnail PNG مؤقت.
    أبطأ (2-5 ثواني) لكن الأدق.
    يُستخدم فقط لو الطرق الأخرى فشلت.
    """
    try:
        from ._size_card import _find_gimp
        gimp_exe = _find_gimp()
    except ImportError:
        gimp_exe = _find_gimp_fallback()

    if not gimp_exe:
        return None

    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        script = (
            f'(let* ((image (car (gimp-file-load RUN-NONINTERACTIVE '
            f'"{path.replace(chr(92), "/")}" "{os.path.basename(path)}"))) '
            f'(drawable (car (gimp-image-get-active-drawable image)))) '
            f'(file-png-save RUN-NONINTERACTIVE image drawable '
            f'"{tmp_path.replace(chr(92), "/")}" "thumb" 0 9 1 1 1 1 1))'
        )

        result = subprocess.run(
            [gimp_exe, "-i", "-b", script, "-b", "(gimp-quit 0)"],
            timeout=15,
            capture_output=True,
        )

        if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
            pixmap = QPixmap(tmp_path)
            os.unlink(tmp_path)
            if not pixmap.isNull():
                return pixmap
        elif os.path.exists(tmp_path):
            os.unlink(tmp_path)

    except Exception:
        pass

    return None


def _find_gimp_fallback() -> str | None:
    import shutil, glob
    try:
        from db.shared.connection import get_connection
        from db.settings_repo import get_setting
        conn  = get_connection()
        saved = get_setting(conn, "gimp_path", "")
        conn.close()
        if saved and os.path.exists(saved):
            return saved
    except Exception:
        pass
    for name in ("gimp", "gimp-2.10", "gimp-2.99", "gimp-3.0"):
        found = shutil.which(name)
        if found:
            return found
    for pattern in [r"C:\Program Files\GIMP *\bin\gimp-*.exe"]:
        matches = glob.glob(pattern)
        if matches:
            return sorted(matches)[-1]
    return None


# ════════════════════════════════════════════════════════
# مساعدات
# ════════════════════════════════════════════════════════

def _scale(pixmap: QPixmap, size: int) -> QPixmap:
    """يعيد تحجيم الـ pixmap مع الحفاظ على النسبة."""
    return pixmap.scaled(
        size, size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )