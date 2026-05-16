"""
ui/tabs/design/designs/_xcf_thumbnail.py
=========================================
استخراج thumbnail من ملفات XCF — نسخة مُصلَحة ومتينة.

الأولويات:
  1. GIMP thumbnail cache (freedesktop standard PNG) — أسرع وأضمن
  2. قراءة PROP_THUMBNAIL من XCF مباشرة — بدون أدوات خارجية
  3. GIMP batch export — fallback أخير

Cache داخلي بالـ mtime لتجنب إعادة القراءة.
"""

from __future__ import annotations

import hashlib
import os
import struct
import tempfile
import subprocess

from PyQt5.QtGui  import QPixmap, QImage
from PyQt5.QtCore import Qt

# ── Cache: xcf_path → (mtime, QPixmap) ─────────────────
_CACHE: dict[str, tuple[float, QPixmap]] = {}

# ── XCF constants ───────────────────────────────────────
_XCF_MAGIC      = b"gimp xcf "
_PROP_END       = 0
_PROP_THUMBNAIL = 1028
_MAX_PROPS      = 300


# ════════════════════════════════════════════════════════
# Public API
# ════════════════════════════════════════════════════════

def get_xcf_thumbnail(xcf_path: str, size: int = 80) -> "QPixmap | None":
    if not xcf_path or not os.path.exists(xcf_path):
        return None

    try:
        mtime = os.path.getmtime(xcf_path)
    except OSError:
        return None

    cached = _CACHE.get(xcf_path)
    if cached and cached[0] == mtime:
        return _scale(cached[1], size)

    pixmap = (
        _try_gimp_cache(xcf_path)
        or _try_xcf_native(xcf_path)
        or _try_gimp_batch(xcf_path)
    )

    if pixmap and not pixmap.isNull():
        _CACHE[xcf_path] = (mtime, pixmap)
        return _scale(pixmap, size)

    return None


def clear_cache(xcf_path: str = None):
    if xcf_path:
        _CACHE.pop(xcf_path, None)
    else:
        _CACHE.clear()


# ════════════════════════════════════════════════════════
# طريقة 1 — GIMP thumbnail cache (freedesktop standard)
# ════════════════════════════════════════════════════════

def _xcf_uri(path: str) -> str:
    """يبني URI صحيح من مسار الملف (Windows + Linux)."""
    p = path.replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        # Windows: C:/path → file:///C:/path
        return "file:///" + p
    elif p.startswith("/"):
        return "file://" + p
    return "file:///" + p


def _gimp_cache_paths(xcf_path: str) -> list:
    """يبني قائمة بكل المسارات المحتملة لـ GIMP thumbnail cache."""
    uris = [
        _xcf_uri(xcf_path),
        # بعض إصدارات GIMP على Windows تستخدم forward slash بدون encoding
        "file:///" + xcf_path.replace("\\", "/").lstrip("/"),
    ]

    candidates = []
    home = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", "")

    for uri in dict.fromkeys(uris):
        md5 = hashlib.md5(uri.encode("utf-8")).hexdigest()

        for size_dir in ("large", "normal", "x-large"):
            # Freedesktop standard (Linux/Mac/GIMP on Windows)
            candidates.append(
                os.path.join(home, ".cache", "thumbnails", size_dir, md5 + ".png")
            )
            candidates.append(
                os.path.join(home, ".thumbnails", size_dir, md5 + ".png")
            )
            # GIMP Windows cache
            if appdata:
                for ver in ("3.0", "2.99", "2.10", "2.8"):
                    candidates.append(
                        os.path.join(
                            appdata, "GIMP", ver, "thumbnails",
                            size_dir, md5 + ".png"
                        )
                    )

    return candidates


def _try_gimp_cache(xcf_path: str) -> "QPixmap | None":
    for path in _gimp_cache_paths(xcf_path):
        if os.path.exists(path):
            px = QPixmap(path)
            if not px.isNull():
                return px
    return None


# ════════════════════════════════════════════════════════
# طريقة 2 — قراءة XCF مباشرة (PROP_THUMBNAIL)
# ════════════════════════════════════════════════════════

def _try_xcf_native(xcf_path: str) -> "QPixmap | None":
    """
    يقرأ PROP_THUMBNAIL من XCF properties مباشرة.

    بنية PROP_THUMBNAIL (من GIMP source xcf.c):
      prop_type    uint32 = 1028
      payload_len  uint32
      [3 int32s: format/bpp, width, height — ترتيبهم يختلف بالإصدار]
      data         raw bytes (RGB أو RGBA)

    نحسب bpp من payload_len تلقائياً لتجنب الاعتماد على الترتيب.
    """
    try:
        with open(xcf_path, "rb") as f:
            if f.read(9) != _XCF_MAGIC:
                return None

            ver_raw = f.read(4)
            f.read(1)   # NUL

            try:
                xcf_ver = int(ver_raw.strip(b"\x00v"))
            except (ValueError, TypeError):
                xcf_ver = 0

            # width, height, base_type
            f.read(12)

            # precision — XCF v4+ (GIMP 2.10+)
            if xcf_ver >= 4:
                f.read(4)

            return _scan_for_thumbnail(f)

    except Exception:
        return None


def _scan_for_thumbnail(f) -> "QPixmap | None":
    for _ in range(_MAX_PROPS):
        try:
            ptype_b = f.read(4)
            if len(ptype_b) < 4:
                break
            ptype = struct.unpack(">I", ptype_b)[0]
            plen  = struct.unpack(">I", f.read(4))[0]
        except struct.error:
            break

        if ptype == _PROP_END:
            break

        if ptype == _PROP_THUMBNAIL:
            return _decode_thumbnail(f, plen)

        try:
            f.seek(plen, 1)
        except Exception:
            break

    return None


def _decode_thumbnail(f, payload_len: int) -> "QPixmap | None":
    """
    يحلل payload الـ PROP_THUMBNAIL بطريقة مرنة.

    يقرأ أول 3 int32 (12 bytes) ثم يحسب bpp من الحجم المتبقي.
    يجرب كل التفسيرات الممكنة لـ (a, b, c).
    """
    try:
        if payload_len < 12:
            return None

        a = struct.unpack(">i", f.read(4))[0]
        b = struct.unpack(">i", f.read(4))[0]
        c = struct.unpack(">i", f.read(4))[0]

        data_len = payload_len - 12

        if data_len <= 0 or data_len > 16 * 1024 * 1024:
            if data_len > 0:
                f.seek(min(data_len, 16 * 1024 * 1024), 1)
            return None

        raw = f.read(data_len)
        if len(raw) < data_len:
            return None

        # نجرب كل التفسيرات الممكنة لـ (a, b, c)
        # الهدف: نجد width و height يقسّمان data_len بـ 3 أو 4
        for width, height in [(b, c), (a, b), (c, b), (a, c)]:
            if not (1 <= width <= 4096 and 1 <= height <= 4096):
                continue
            total = width * height
            if total == 0 or data_len % total != 0:
                continue
            bpp = data_len // total
            if bpp not in (3, 4):
                continue

            fmt = QImage.Format_RGB888 if bpp == 3 else QImage.Format_RGBA8888
            img = QImage(bytes(raw), width, height, width * bpp, fmt)
            if not img.isNull():
                return QPixmap.fromImage(img)

        return None

    except Exception:
        return None


# ════════════════════════════════════════════════════════
# طريقة 3 — GIMP Batch Script-Fu
# ════════════════════════════════════════════════════════

def _try_gimp_batch(xcf_path: str) -> "QPixmap | None":
    """
    يشغّل GIMP في batch mode لتصدير thumbnail.
    أبطأ لكن يعمل مع أي إصدار.
    """
    gimp_exe = _find_gimp()
    if not gimp_exe:
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        xcf_fwd  = xcf_path.replace("\\", "/")
        tmp_fwd  = tmp_path.replace("\\", "/")
        basename = os.path.basename(xcf_path)

        # Script-Fu: تحميل الصورة، تصغيرها، حفظها PNG
        script = (
            f'(let* ('
            f'  (image (car (gimp-file-load RUN-NONINTERACTIVE "{xcf_fwd}" "{basename}")))'
            f'  (drawable (car (gimp-image-get-active-drawable image)))'
            f'  (scaled (car (gimp-image-duplicate image)))'
            f') '
            f'  (gimp-image-scale-full scaled 256 256 INTERPOLATION-LINEAR)'
            f'  (file-png-save RUN-NONINTERACTIVE scaled'
            f'    (car (gimp-image-get-active-drawable scaled))'
            f'    "{tmp_fwd}" "t" 0 9 1 1 1 1 1)'
            f')'
        )

        subprocess.run(
            [gimp_exe, "-i", "-b", script, "-b", "(gimp-quit 0)"],
            timeout=20,
            capture_output=True,
        )

        if tmp_path and os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 100:
            px = QPixmap(tmp_path)
            if not px.isNull():
                return px

    except Exception:
        pass
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    return None


# ════════════════════════════════════════════════════════
# مساعدات
# ════════════════════════════════════════════════════════

def _find_gimp() -> "str | None":
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
    for pattern in [
        r"C:\Program Files\GIMP *\bin\gimp-*.exe",
        r"C:\Program Files (x86)\GIMP *\bin\gimp-*.exe",
    ]:
        matches = glob.glob(pattern)
        if matches:
            return sorted(matches)[-1]
    return None


def _scale(pixmap: QPixmap, size: int) -> QPixmap:
    return pixmap.scaled(
        size, size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )