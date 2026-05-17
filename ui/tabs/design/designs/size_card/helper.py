"""
ui/tabs/design/designs/size_card/helper.py  — v3
==========================================
بطاقة مقاس واحد — تصميم محسّن.

التحسينات:
  - Layout أوضح وأكثر تنظيماً
  - أزرار أصغر وأنظف
  - Status bar أجمل
  - Thumbnail مع rounded corners
  - ألوان Palette موحدة
"""

import os
import subprocess

from PyQt5.QtWidgets import (
    QLabel, QMessageBox,

)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal



from .._xcf_thumbnail import get_xcf_thumbnail

# ── Palette ──────────────────────────────────────────────
_BG_SURFACE  = "#F8F9FB"
_BORDER_MED  = "#CDD3E0"
_TEXT_MUT    = "#9BA5BE"

_ACCENT_BDR  = "#C7D2FE"

_RADIUS_SM   = "6px"

_DEFAULT_DPI = 300.0
_THUMB_SIZE  = 72


def _btn_ss(bg, fg, bdr, hover_bg, height=28, radius=_RADIUS_SM):
    return (
        f"QPushButton{{"
        f"  background:{bg}; color:{fg};"
        f"  border:1px solid {bdr}; border-radius:{radius};"
        f"  padding:0 10px; font-size:11px; min-height:{height}px;"
        f"}}"
        f"QPushButton:hover{{background:{hover_bg};}}"
        f"QPushButton:pressed{{opacity:0.85;}}"
    )


# ════════════════════════════════════════════════════════
# Thumbnail Worker
# ════════════════════════════════════════════════════════

class _ThumbWorker(QThread):
    done = Signal(object)

    def __init__(self, xcf_path: str, size: int = _THUMB_SIZE):
        super().__init__()
        self._path = xcf_path
        self._size = size

    def run(self):
        px = get_xcf_thumbnail(self._path, self._size)
        self.done.emit(px)


# ════════════════════════════════════════════════════════
# GIMP Utilities
# ════════════════════════════════════════════════════════

_GIMP_UNIT_MAP = {
    "px": 0, "mm": 2, "cm": 3, "inch": 4, "in": 4, "pt": 5, "m": 2,
}


def _to_px(value: float, unit: str, dpi: float = 300.0) -> int:
    u = unit.strip().lower()
    if u == "px":    return max(1, int(round(value)))
    if u == "mm":    return max(1, int(round(value / 25.4 * dpi)))
    if u == "cm":    return max(1, int(round(value / 2.54  * dpi)))
    if u in ("m", "متر"): return max(1, int(round(value / 0.0254 * dpi)))
    if u in ("inch", "in", "انش", "بوصة"): return max(1, int(round(value * dpi)))
    return max(1, int(round(value)))


def _unit_for_set(conn, set_id: int) -> str:
    try:
        row = conn.execute(
            "SELECT default_unit FROM dimension_sets WHERE id=?", (set_id,)
        ).fetchone()
        return row["default_unit"] if row and row["default_unit"] else "px"
    except Exception:
        return "px"


def _find_gimp() -> str | None:
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
    for pattern in [r"C:\Program Files\GIMP *\bin\gimp-*.exe",
                    r"C:\Program Files (x86)\GIMP *\bin\gimp-*.exe"]:
        matches = glob.glob(pattern)
        if matches:
            return sorted(matches)[-1]
    return None


def _open_gimp(xcf_path=None, width_val=None, height_val=None,
               unit="px", dpi=_DEFAULT_DPI):
    gimp_exe = _find_gimp()
    if not gimp_exe:
        QMessageBox.warning(
            None, "GIMP غير موجود",
            "لم يتم العثور على GIMP.\nحدد مساره من ⚙️ الإعدادات."
        )
        return False
    try:
        if xcf_path and os.path.exists(xcf_path):
            subprocess.Popen([gimp_exe, xcf_path])
            return True
        if width_val and height_val:
            import tempfile
            from PIL import Image
            u = unit.strip().lower()
            actual_dpi = 96.0 if u == "px" else float(dpi)
            w_px = _to_px(width_val, unit, actual_dpi)
            h_px = _to_px(height_val, unit, actual_dpi)
            tmp  = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            img = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
            img.save(tmp.name, dpi=(actual_dpi, actual_dpi))
            subprocess.Popen([gimp_exe, tmp.name])
            return True
        subprocess.Popen([gimp_exe])
        return True
    except ImportError:
        QMessageBox.warning(None, "مكتبة ناقصة",
                            "تحتاج تثبيت Pillow:\n\npip install Pillow")
        return False
    except Exception as e:
        QMessageBox.critical(None, "خطأ", f"فشل فتح GIMP:\n{e}")
        return False


# ════════════════════════════════════════════════════════
# Thumbnail Widget
# ════════════════════════════════════════════════════════

class _ThumbnailWidget(QLabel):
    def __init__(self, xcf_path: str, size: int = _THUMB_SIZE, parent=None):
        super().__init__(parent)
        self._size     = size
        self._xcf_path = xcf_path
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self._show_placeholder()

        if xcf_path and os.path.exists(xcf_path):
            self._load_async(xcf_path)

    def _show_placeholder(self):
        self.setText("🎨")
        self.setStyleSheet(f"""
            QLabel {{
                background: #1E1B4B;
                border-radius: {_RADIUS_SM};
                font-size: 20px;
            }}
        """)

    def _load_async(self, path: str):
        self._worker = _ThumbWorker(path, self._size)
        self._worker.done.connect(self._on_thumb_ready)
        self._worker.start()

    def _on_thumb_ready(self, pixmap):
        if pixmap and not pixmap.isNull():
            self.setText("")
            scaled = pixmap.scaled(
                self._size, self._size,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self.setPixmap(scaled)
            self.setStyleSheet(f"""
                QLabel {{
                    background: #0F0E17;
                    border-radius: {_RADIUS_SM};
                    border: 1px solid {_ACCENT_BDR};
                }}
            """)
        else:
            self.setText("📄")
            self.setStyleSheet(f"""
                QLabel {{
                    background: {_BG_SURFACE};
                    border: 1px dashed {_BORDER_MED};
                    border-radius: {_RADIUS_SM};
                    font-size: 22px;
                    color: {_TEXT_MUT};
                }}
            """)

    def refresh(self, xcf_path: str = None):
        from .._xcf_thumbnail import clear_cache
        if xcf_path:
            self._xcf_path = xcf_path
        path = self._xcf_path
        if path:
            clear_cache(path)
        self._show_placeholder()
        if path and os.path.exists(path):
            self._load_async(path)

