"""
ui/tabs/design/designs/_xcf_thumbnail.py  — v3
===============================================
استخراج thumbnail من XCF + مراقبة تلقائية للتغييرات.

الجديد في v3:
  - XcfWatcher: singleton يراقب ملفات XCF بـ QFileSystemWatcher
  - debounce 1.5 ثانية عشان GIMP بيكتب الملف على مراحل
  - signal file_changed(path) لما يتحدث الملف فعلاً
  - clear_cache تلقائي عند كل تغيير

الاستخدام في _size_card.py:
    from ._xcf_thumbnail import get_xcf_thumbnail, get_watcher

    # اشترك في التغييرات
    get_watcher().file_changed.connect(self._on_xcf_changed)

    # ابدأ المراقبة
    get_watcher().watch(xcf_path)

    def _on_xcf_changed(self, path):
        if path == self._data.get("xcf_path"):
            self._thumb.refresh(path)
"""

from __future__ import annotations

import hashlib
import os
import struct
import tempfile
import subprocess

from PyQt5.QtGui     import QPixmap, QImage, QPainter, QColor
from PyQt5.QtCore    import Qt, QRect, QObject, pyqtSignal, QTimer, QFileSystemWatcher
from PyQt5.QtWidgets import QApplication

# ── Cache: xcf_path → (mtime, QPixmap) ─────────────────
_CACHE: dict[str, tuple[float, QPixmap]] = {}

# ── XCF constants ───────────────────────────────────────
_XCF_MAGIC      = b"gimp xcf "
_PROP_END       = 0
_PROP_THUMBNAIL = 1028
_MAX_PROPS      = 300


# ════════════════════════════════════════════════════════
# XcfWatcher — singleton لمراقبة ملفات XCF
# ════════════════════════════════════════════════════════

class XcfWatcher(QObject):
    """
    يراقب ملفات XCF ويطلق signal عند تغييرها.
    Debounce 1.5 ثانية لأن GIMP يكتب الملف على مراحل.

    الاستخدام:
        watcher = get_watcher()
        watcher.watch("/path/to/file.xcf")
        watcher.file_changed.connect(my_slot)
        watcher.unwatch("/path/to/file.xcf")   # عند إزالة البطاقة
    """

    file_changed = pyqtSignal(str)   # path الكامل للملف المتغير

    _DEBOUNCE_MS = 1500   # انتظر 1.5 ثانية بعد آخر تغيير قبل الإشعار

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fs_watcher = QFileSystemWatcher(self)
        self._fs_watcher.fileChanged.connect(self._on_raw_change)

        # debounce: path → QTimer
        self._timers: dict[str, QTimer] = {}

        # مسارات نراقبها حالياً
        self._watched: set[str] = set()

    # ── API ──────────────────────────────────────────────

    def watch(self, path: str):
        """يضيف ملف للمراقبة."""
        if not path or not os.path.exists(path):
            return
        path = os.path.normpath(path)
        if path not in self._watched:
            self._fs_watcher.addPath(path)
            self._watched.add(path)

    def unwatch(self, path: str):
        """يوقف مراقبة ملف."""
        if not path:
            return
        path = os.path.normpath(path)
        if path in self._watched:
            self._fs_watcher.removePath(path)
            self._watched.discard(path)
        # إلغاء الـ timer لو موجود
        timer = self._timers.pop(path, None)
        if timer:
            timer.stop()
            timer.deleteLater()

    def unwatch_all(self):
        """يوقف مراقبة كل الملفات."""
        for path in list(self._watched):
            self.unwatch(path)

    # ── Handler داخلي ────────────────────────────────────

    def _on_raw_change(self, path: str):
        """
        يُستدعى مباشرة من QFileSystemWatcher.
        GIMP بيحذف الملف ويعيد كتابته (atomic save)،
        فلازم نعيد إضافته للـ watcher بعد التغيير.
        """
        path = os.path.normpath(path)

        # GIMP atomic save: الملف اتحذف مؤقتاً → أعد إضافته
        if os.path.exists(path) and path not in self._fs_watcher.files():
            self._fs_watcher.addPath(path)

        # debounce — ريست الـ timer
        if path in self._timers:
            self._timers[path].stop()
        else:
            timer = QTimer(self)
            timer.setSingleShot(True)
            timer.timeout.connect(lambda p=path: self._emit_change(p))
            self._timers[path] = timer

        self._timers[path].start(self._DEBOUNCE_MS)

    def _emit_change(self, path: str):
        """يُطلق الـ signal بعد انتهاء الـ debounce."""
        # تأكد إن الملف موجود فعلاً
        if not os.path.exists(path):
            return

        # مسح الـ cache عشان يُعاد التحميل
        clear_cache(path)

        # تنظيف الـ timer
        timer = self._timers.pop(path, None)
        if timer:
            timer.deleteLater()

        self.file_changed.emit(path)


# ── Singleton ────────────────────────────────────────────
_watcher_instance: XcfWatcher | None = None


def get_watcher() -> XcfWatcher:
    """يرجع الـ singleton — يُنشئه أول مرة."""
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = XcfWatcher()
    return _watcher_instance


# ════════════════════════════════════════════════════════
# Public API — Thumbnail
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
        or _try_pillow(xcf_path)
        or _try_gimp_batch(xcf_path)
        or _make_placeholder(xcf_path, size)
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
# طريقة 1 — GIMP Cache
# ════════════════════════════════════════════════════════

def _xcf_uri(path: str) -> str:
    p = path.replace("\\", "/")
    if len(p) >= 2 and p[1] == ":":
        return "file:///" + p
    elif p.startswith("/"):
        return "file://" + p
    return "file:///" + p


def _try_gimp_cache(xcf_path: str) -> "QPixmap | None":
    home    = os.path.expanduser("~")
    appdata = os.environ.get("APPDATA", "")

    path_fwd = xcf_path.replace("\\", "/")
    uris = set()
    for p in [path_fwd, path_fwd[0].lower() + path_fwd[1:]]:
        uris.add("file:///" + p.lstrip("/"))

    for uri in uris:
        md5 = hashlib.md5(uri.encode("utf-8")).hexdigest()
        for size_dir in ("large", "normal", "x-large", "xx-large"):
            candidates = [
                os.path.join(home, ".cache", "thumbnails", size_dir, md5 + ".png"),
                os.path.join(home, ".thumbnails", size_dir, md5 + ".png"),
            ]
            if appdata:
                for ver in ("3.0", "2.99", "2.10", "2.8"):
                    candidates.append(
                        os.path.join(appdata, "GIMP", ver, "thumbnails",
                                     size_dir, md5 + ".png")
                    )
            for p in candidates:
                if os.path.exists(p):
                    px = QPixmap(p)
                    if not px.isNull():
                        return px
    return None


# ════════════════════════════════════════════════════════
# طريقة 2 — XCF Native (v1–v9)
# ════════════════════════════════════════════════════════

def _try_xcf_native(xcf_path: str) -> "QPixmap | None":
    try:
        with open(xcf_path, "rb") as f:
            if f.read(9) != _XCF_MAGIC:
                return None
            ver_raw = f.read(4)
            f.read(1)
            try:
                xcf_ver = int(ver_raw.strip(b"\x00v"))
            except (ValueError, TypeError):
                xcf_ver = 0
            f.read(12)
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
# طريقة 3 — Pillow
# ════════════════════════════════════════════════════════

def _try_pillow(xcf_path: str) -> "QPixmap | None":
    try:
        from PIL import Image
        img = Image.open(xcf_path)
        img.thumbnail((256, 256), Image.LANCZOS)
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGBA")
        bpp  = 4 if img.mode == "RGBA" else 3
        fmt  = QImage.Format_RGBA8888 if img.mode == "RGBA" else QImage.Format_RGB888
        data = img.tobytes("raw", img.mode)
        qimg = QImage(data, img.width, img.height, img.width * bpp, fmt)
        if not qimg.isNull():
            return QPixmap.fromImage(qimg)
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════
# طريقة 4 — GIMP Batch
# ════════════════════════════════════════════════════════

def _try_gimp_batch(xcf_path: str) -> "QPixmap | None":
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

        script = (
            f'(let* ('
            f'  (image (car (gimp-file-load RUN-NONINTERACTIVE "{xcf_fwd}" "{basename}")))'
            f') '
            f'  (gimp-image-scale image 256 256)'
            f'  (file-png-save RUN-NONINTERACTIVE image'
            f'    (car (gimp-image-get-active-drawable image))'
            f'    "{tmp_fwd}" "thumb" 0 9 1 1 1 1 1)'
            f'  (gimp-image-delete image)'
            f')'
        )
        subprocess.run(
            [gimp_exe, "-i", "-b", script, "-b", "(gimp-quit 0)"],
            timeout=25, capture_output=True,
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
# طريقة 5 — Placeholder جميل (fallback دائم)
# ════════════════════════════════════════════════════════

def _make_placeholder(xcf_path: str, size: int = 80) -> QPixmap:
    s    = max(size, 64)
    name = os.path.splitext(os.path.basename(xcf_path))[0]
    if len(name) > 10:
        name = name[:9] + "…"

    px = QPixmap(s, s)
    px.fill(QColor("#1a1a2e"))

    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing)

    from PyQt5.QtGui import QLinearGradient
    grad = QLinearGradient(0, 0, 0, s)
    grad.setColorAt(0, QColor("#2d2d5e"))
    grad.setColorAt(1, QColor("#1a1a2e"))
    painter.fillRect(0, 0, s, s, grad)

    painter.setPen(QColor("#5c6bc0"))
    painter.drawRoundedRect(1, 1, s-2, s-2, 6, 6)

    font = painter.font()
    font.setPointSize(s // 3)
    painter.setFont(font)
    painter.setPen(QColor("#7986cb"))
    painter.drawText(QRect(0, s//8, s, s//2), Qt.AlignCenter, "🎨")

    font.setPointSize(max(6, s // 10))
    painter.setFont(font)
    painter.setPen(QColor("#9fa8da"))
    painter.drawText(QRect(2, s*6//8, s-4, s//5), Qt.AlignCenter, name)

    painter.end()
    return px


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