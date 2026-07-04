"""
ui/tabs/design/designs/_xcf_thumbnail.py  — v5
===============================================
استخراج thumbnail من XCF + مراقبة تلقائية للتغييرات.

الأولويات:
  1. Wand (ImageMagick) ← الأسرع والأدق مع XCF
  2. magick subprocess ← fallback لو Wand مش لاقي ImageMagick
  3. GIMP cache
  4. XCF native (v1-v9 فقط)
  5. Placeholder جميل (fallback دائم)

XcfWatcher: singleton يراقب الملفات ويطلق signal عند التغيير.
"""

from __future__ import annotations

import hashlib
import os
import struct
import tempfile
import subprocess

from PyQt5.QtGui  import QPixmap, QImage, QPainter, QColor
from PyQt5.QtCore import Qt, QRect, QObject, pyqtSignal, QTimer, QFileSystemWatcher

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.constants import XCF_WATCHER_DEBOUNCE_MS, XCF_THUMB_MIN_SIZE

# ── Cache: xcf_path → (mtime, QPixmap) ─────────────────
_CACHE: dict[str, tuple[float, QPixmap]] = {}

_XCF_MAGIC      = b"gimp xcf "
_PROP_END       = 0
_PROP_THUMBNAIL = 1028
_MAX_PROPS      = 300

# مسار ImageMagick الثابت — يُحدَّث مرة واحدة عند أول استخدام
_MAGICK_EXE: str | None = "UNSET"


# ════════════════════════════════════════════════════════
# XcfWatcher — singleton
# ════════════════════════════════════════════════════════

class XcfWatcher(QObject):
    """
    يراقب ملفات XCF ويطلق file_changed(path) بعد debounce.
    GIMP يكتب الملف على مراحل (atomic save) → debounce 1.5 ث.
    """

    file_changed = pyqtSignal(str)
    _DEBOUNCE_MS = XCF_WATCHER_DEBOUNCE_MS

    def __init__(self, parent=None):
        super().__init__(parent)
        self._fs   = QFileSystemWatcher(self)
        self._fs.fileChanged.connect(self._on_raw)
        self._timers: dict[str, QTimer] = {}
        self._watched: set[str] = set()

    def watch(self, path: str):
        if not path or not os.path.exists(path):
            return
        path = os.path.normpath(path)
        if path not in self._watched:
            self._fs.addPath(path)
            self._watched.add(path)

    def unwatch(self, path: str):
        if not path:
            return
        path = os.path.normpath(path)
        if path in self._watched:
            self._fs.removePath(path)
            self._watched.discard(path)
        t = self._timers.pop(path, None)
        if t:
            t.stop()
            t.deleteLater()

    def _on_raw(self, path: str):
        path = os.path.normpath(path)
        # atomic save: GIMP حذف الملف وأعاد كتابته
        if os.path.exists(path) and path not in self._fs.files():
            self._fs.addPath(path)

        if path in self._timers:
            self._timers[path].stop()
        else:
            t = QTimer(self)
            t.setSingleShot(True)
            t.timeout.connect(lambda p=path: self._emit(p))
            self._timers[path] = t
        self._timers[path].start(self._DEBOUNCE_MS)

    def _emit(self, path: str):
        if not os.path.exists(path):
            return
        clear_cache(path)
        t = self._timers.pop(path, None)
        if t:
            t.deleteLater()
        self.file_changed.emit(path)


_watcher_instance: XcfWatcher | None = None


def get_watcher() -> XcfWatcher:
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = XcfWatcher()
    return _watcher_instance


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
        _try_wand(xcf_path)
        or _try_magick_subprocess(xcf_path)
        or _try_gimp_cache(xcf_path)
        or _try_xcf_native(xcf_path)
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
# مساعد: إيجاد magick.exe
# ════════════════════════════════════════════════════════

def _find_magick() -> str | None:
    global _MAGICK_EXE
    if _MAGICK_EXE != "UNSET":
        return _MAGICK_EXE

    import glob
    import shutil

    # 1. المسار الثابت المعروف
    for pattern in [
        r"C:\Program Files\ImageMagick*\magick.exe",
        r"C:\Program Files (x86)\ImageMagick*\magick.exe",
    ]:
        matches = glob.glob(pattern)
        if matches:
            _MAGICK_EXE = sorted(matches)[-1]
            return _MAGICK_EXE

    # 2. PATH
    found = shutil.which("magick")
    if found:
        _MAGICK_EXE = found
        return _MAGICK_EXE

    # 3. convert.exe لكن مش Windows system32
    found = shutil.which("convert")
    if found and "system32" not in found.lower():
        _MAGICK_EXE = found
        return _MAGICK_EXE

    _MAGICK_EXE = None
    return None


# ════════════════════════════════════════════════════════
# طريقة 1 — Wand
# ════════════════════════════════════════════════════════

def _try_wand(xcf_path: str) -> "QPixmap | None":
    try:
        # إضافة مسار ImageMagick لـ PATH قبل import Wand
        magick = _find_magick()
        if magick:
            magick_dir = os.path.dirname(magick)
            if magick_dir not in os.environ.get("PATH", ""):
                os.environ["PATH"] = magick_dir + os.pathsep + os.environ.get("PATH", "")
            # Wand على Windows يحتاج MAGICK_HOME
            os.environ.setdefault("MAGICK_HOME", magick_dir)

        from wand.image import Image as WandImage

        with WandImage(filename=xcf_path) as img:
            img.merge_layers("flatten")
            img.thumbnail(256, 256)
            img.format = "png"
            blob = img.make_blob()

        if not blob:
            return None

        qimg = QImage()
        qimg.loadFromData(blob, "PNG")
        if not qimg.isNull():
            return QPixmap.fromImage(qimg)

    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════
# طريقة 2 — magick subprocess (fallback لو Wand فشل)
# ════════════════════════════════════════════════════════

def _try_magick_subprocess(xcf_path: str) -> "QPixmap | None":
    magick = _find_magick()
    if not magick:
        return None

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp_path = tmp.name

        # xcf_path[0] = أول layer/frame
        r = subprocess.run(
            [magick, xcf_path + "[0]", "-thumbnail", "256x256",
             "-background", "white", "-flatten", tmp_path],
            capture_output=True,
            timeout=20,
        )

        if (r.returncode == 0
                and os.path.exists(tmp_path)
                and os.path.getsize(tmp_path) > 100):
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
# طريقة 3 — GIMP Cache
# ════════════════════════════════════════════════════════

def _try_gimp_cache(xcf_path: str) -> "QPixmap | None":
    home     = os.path.expanduser("~")
    appdata  = os.environ.get("APPDATA", "")
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
# طريقة 4 — XCF Native (v1–v9)
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
# طريقة 5 — Placeholder جميل
# ════════════════════════════════════════════════════════

def _make_placeholder(xcf_path: str, size: int = 80) -> QPixmap:
    s    = max(size, XCF_THUMB_MIN_SIZE)
    name = os.path.splitext(os.path.basename(xcf_path))[0]
    if len(name) > 10:
        name = name[:9] + "…"

    px = QPixmap(s, s)
    px.fill(QColor(_C["design_thumb_bg_end"]))
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing)

    from PyQt5.QtGui import QLinearGradient
    grad = QLinearGradient(0, 0, 0, s)
    grad.setColorAt(0, QColor(_C["design_thumb_bg_start"]))
    grad.setColorAt(1, QColor(_C["design_thumb_bg_end"]))
    painter.fillRect(0, 0, s, s, grad)

    painter.setPen(QColor(_C["design_thumb_border"]))
    painter.drawRoundedRect(1, 1, s-2, s-2, 6, 6)

    font = painter.font()
    font.setPointSize(s // 3)
    painter.setFont(font)
    painter.setPen(QColor(_C["design_thumb_icon"]))
    painter.drawText(QRect(0, s//8, s, s//2), Qt.AlignCenter, tr("design_card_thumb_placeholder_icon"))

    font.setPointSize(max(6, s // 10))
    painter.setFont(font)
    painter.setPen(QColor(_C["design_thumb_text"]))
    painter.drawText(QRect(2, s*6//8, s-4, s//5), Qt.AlignCenter, name)

    painter.end()
    return px


# ════════════════════════════════════════════════════════
# مساعدات
# ════════════════════════════════════════════════════════

def _scale(pixmap: QPixmap, size: int) -> QPixmap:
    return pixmap.scaled(
        size, size,
        Qt.KeepAspectRatio,
        Qt.SmoothTransformation,
    )