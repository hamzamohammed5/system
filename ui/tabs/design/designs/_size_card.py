"""
ui/tabs/design/designs/_size_card.py  — v3
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
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
    QFrame, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal
from PyQt5.QtGui  import QPixmap, QFont

from db.designs.designs_sizes_repo import (
    update_design_size_path,
    fetch_canvas_size,
    fetch_canvas_dpi,
)
from ._xcf_thumbnail import get_xcf_thumbnail, get_watcher

# ── Palette ──────────────────────────────────────────────
_BG          = "#FFFFFF"
_BG_SURFACE  = "#F8F9FB"
_BORDER      = "#E5E9F0"
_BORDER_MED  = "#CDD3E0"
_TEXT_PRI    = "#1A2035"
_TEXT_SEC    = "#5A6680"
_TEXT_MUT    = "#9BA5BE"

_ACCENT      = "#4F6EF7"
_ACCENT_LT   = "#EEF2FF"
_ACCENT_BDR  = "#C7D2FE"
_ACCENT_DARK = "#3D5BEF"

_SUCCESS     = "#16A34A"
_SUCCESS_LT  = "#F0FDF4"
_SUCCESS_BDR = "#BBF7D0"

_WARNING     = "#D97706"
_WARNING_LT  = "#FFFBEB"
_WARNING_BDR = "#FDE68A"

_DANGER      = "#DC2626"
_DANGER_LT   = "#FEF2F2"
_DANGER_BDR  = "#FECACA"

_RADIUS      = "10px"
_RADIUS_SM   = "6px"
_RADIUS_XS   = "4px"

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
        from ._xcf_thumbnail import clear_cache
        if xcf_path:
            self._xcf_path = xcf_path
        path = self._xcf_path
        if path:
            clear_cache(path)
        self._show_placeholder()
        if path and os.path.exists(path):
            self._load_async(path)


# ════════════════════════════════════════════════════════
# بطاقة مقاس — v3
# ════════════════════════════════════════════════════════

class _SizeCard(QFrame):
    edit_requested   = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    path_changed     = pyqtSignal()

    def __init__(self, conn, size_data, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self._data    = dict(size_data)
        self._size_id = self._data["id"]
        self._build()

        xcf = self._data.get("xcf_path") or ""
        if xcf and os.path.exists(xcf):
            get_watcher().watch(xcf)
            get_watcher().file_changed.connect(self._on_xcf_changed)

    def _on_xcf_changed(self, path: str):
        xcf = os.path.normpath(self._data.get("xcf_path") or "")
        if os.path.normpath(path) == xcf:
            self._thumb.refresh(path)

    def closeEvent(self, event):
        self._stop_watching()
        super().closeEvent(event)

    def hideEvent(self, event):
        self._stop_watching()
        super().hideEvent(event)

    def _stop_watching(self):
        xcf = self._data.get("xcf_path") or ""
        if xcf:
            try:
                get_watcher().file_changed.disconnect(self._on_xcf_changed)
            except Exception:
                pass

    def _build(self):
        xcf_path    = self._data.get("xcf_path") or ""
        has_file    = bool(xcf_path)
        file_exists = has_file and os.path.exists(xcf_path)

        self.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border: 1px solid {_BORDER};
                border-radius: {_RADIUS};
            }}
        """)
        self.setMinimumHeight(90)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── الجزء الرئيسي ──────────────────────────
        main = QFrame()
        main.setStyleSheet("QFrame{background:transparent;border:none;}")
        m_lay = QHBoxLayout(main)
        m_lay.setContentsMargins(12, 12, 12, 12)
        m_lay.setSpacing(12)

        # Thumbnail
        self._thumb = _ThumbnailWidget(xcf_path, size=_THUMB_SIZE)
        m_lay.addWidget(self._thumb)

        # معلومات
        info = QVBoxLayout()
        info.setSpacing(3)
        info.setContentsMargins(0, 0, 0, 0)

        # اسم المقاس + مجموعته
        inst_name = (self._data.get("instance_name") or
                     f"مقاس #{self._data.get('instance_id', '')}")
        set_name  = self._data.get("set_name", "")

        lbl_name = QLabel(inst_name)
        font_n = QFont()
        font_n.setPointSize(11)
        font_n.setWeight(QFont.Medium)
        lbl_name.setFont(font_n)
        lbl_name.setStyleSheet(f"color:{_TEXT_PRI}; background:transparent;")

        lbl_set = QLabel(set_name)
        lbl_set.setStyleSheet(f"color:{_TEXT_MUT}; font-size:10px; background:transparent;")

        # الأبعاد
        w, h = fetch_canvas_size(self.conn, self._size_id)
        unit = _unit_for_set(self.conn, self._data.get("set_id", 0))
        dpi  = fetch_canvas_dpi(self.conn, self._size_id)

        if w is not None and h is not None:
            if dpi:
                w_px = _to_px(w, unit, dpi)
                h_px = _to_px(h, unit, dpi)
                dims = f"{w:g} × {h:g} {unit}  →  {w_px:,} × {h_px:,} px"
            else:
                dims = f"{w:g} × {h:g} {unit}"
        else:
            dims = "الأبعاد غير محددة"

        lbl_dims = QLabel(dims)
        lbl_dims.setStyleSheet(f"color:{_TEXT_SEC}; font-size:10px; background:transparent;")

        info.addWidget(lbl_name)
        info.addWidget(lbl_set)
        info.addWidget(lbl_dims)
        info.addStretch()

        m_lay.addLayout(info, stretch=1)

        # أزرار
        btns = QVBoxLayout()
        btns.setSpacing(5)
        btns.setContentsMargins(0, 0, 0, 0)

        # الزر الرئيسي (GIMP)
        if file_exists:
            btn_main = QPushButton("فتح في GIMP")
            btn_main.setStyleSheet(
                _btn_ss(_ACCENT, "#fff", _ACCENT, _ACCENT_DARK, height=30)
            )
            btn_main.clicked.connect(self._open_in_gimp)
        else:
            btn_main = QPushButton("إنشاء في GIMP")
            btn_main.setStyleSheet(
                _btn_ss(_SUCCESS_LT, _SUCCESS, _SUCCESS_BDR, "#DCFCE7", height=30)
            )
            btn_main.clicked.connect(self._create_in_gimp)

        btn_main.setMinimumWidth(120)
        btns.addWidget(btn_main)

        # صف أزرار الإجراءات
        act = QHBoxLayout()
        act.setSpacing(4)

        if not file_exists:
            btn_link = QPushButton("ربط ملف")
            btn_link.setStyleSheet(
                _btn_ss(_BG_SURFACE, _TEXT_SEC, _BORDER, _BG, height=26)
            )
            btn_link.clicked.connect(self._set_path)
            act.addWidget(btn_link)

        btn_edit = QPushButton("✏")
        btn_edit.setFixedSize(28, 26)
        btn_edit.setToolTip("تعديل")
        btn_edit.setStyleSheet(
            _btn_ss(_BG_SURFACE, _TEXT_SEC, _BORDER, _BG, height=26, radius=_RADIUS_XS)
        )
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self._size_id))

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(28, 26)
        btn_del.setToolTip("حذف")
        btn_del.setStyleSheet(
            _btn_ss(_DANGER_LT, _DANGER, _DANGER_BDR, "#FEE2E2", height=26, radius=_RADIUS_XS)
        )
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self._size_id))

        act.addStretch()
        act.addWidget(btn_edit)
        act.addWidget(btn_del)

        btns.addLayout(act)
        btns.addStretch()

        m_lay.addLayout(btns)
        root.addWidget(main)

        # ── شريط الحالة ────────────────────────────
        self._build_status_bar(root, file_exists, has_file, unit, dpi)

    def _build_status_bar(self, root, file_exists, has_file, unit, dpi):
        bar = QFrame()

        if file_exists:
            bg     = _SUCCESS_LT
            border = _SUCCESS_BDR
            txt    = "الملف موجود"
            col    = _SUCCESS
        elif has_file:
            bg     = _WARNING_LT
            border = _WARNING_BDR
            txt    = "الملف غير موجود"
            col    = _WARNING
        else:
            bg     = _BG_SURFACE
            border = _BORDER
            txt    = "لا يوجد ملف"
            col    = _TEXT_MUT

        bar.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-top: 1px solid {border};
                border-bottom-left-radius: {_RADIUS};
                border-bottom-right-radius: {_RADIUS};
            }}
        """)

        bl = QHBoxLayout(bar)
        bl.setContentsMargins(12, 5, 12, 5)
        bl.setSpacing(8)

        lbl_s = QLabel(txt)
        lbl_s.setStyleSheet(
            f"color:{col}; font-size:10px; font-weight:600; background:transparent;"
        )

        chips = QHBoxLayout()
        chips.setSpacing(4)
        for chip_txt in [unit, (f"{int(dpi)} DPI" if dpi else "—")]:
            chip = QLabel(chip_txt)
            chip.setStyleSheet(f"""
                QLabel {{
                    background: {_BG};
                    color: {_TEXT_SEC};
                    border: 1px solid {_BORDER_MED};
                    border-radius: 3px;
                    padding: 1px 6px;
                    font-size: 9px;
                }}
            """)
            chips.addWidget(chip)

        bl.addWidget(lbl_s)
        bl.addStretch()
        bl.addLayout(chips)

        root.addWidget(bar)

    # ── GIMP Actions ───────────────────────────────────────

    def _open_in_gimp(self):
        xcf = self._data["xcf_path"]
        if xcf and os.path.exists(xcf):
            get_watcher().watch(xcf)
            _open_gimp(xcf_path=xcf)
        else:
            QMessageBox.warning(
                self, "الملف غير موجود",
                f"الملف:\n{xcf}\n\nاستخدم «ربط ملف» لتحديث المسار."
            )

    def _create_in_gimp(self):
        w, h  = fetch_canvas_size(self.conn, self._size_id)
        unit  = _unit_for_set(self.conn, self._data["set_id"])
        dpi   = fetch_canvas_dpi(self.conn, self._size_id) or _DEFAULT_DPI

        inst_name    = (self._data.get("instance_name") or "design").replace(" ", "_")
        default_name = f"{inst_name}.xcf"
        start_dir    = os.path.expanduser("~")

        if self._data.get("xcf_path"):
            parent = os.path.dirname(self._data["xcf_path"])
            if os.path.isdir(parent):
                start_dir = parent

        save_path, _ = QFileDialog.getSaveFileName(
            self, "اختر مكان حفظ ملف GIMP",
            os.path.join(start_dir, default_name),
            "GIMP Files (*.xcf)"
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".xcf"):
            save_path += ".xcf"

        update_design_size_path(self.conn, self._size_id, save_path)
        self._data["xcf_path"] = save_path
        get_watcher().watch(save_path)

        if w and h:
            u = unit.strip().lower()
            actual_dpi = 96.0 if u == "px" else float(dpi)
            w_px = _to_px(w, unit, actual_dpi)
            h_px = _to_px(h, unit, actual_dpi)
            QMessageBox.information(
                self, "إنشاء كانفاس",
                f"الأبعاد: {w:g} × {h:g} {unit}\n"
                f"البكسل: {w_px:,} × {h_px:,} px  @  {int(actual_dpi)} DPI\n"
                f"الملف: {save_path}"
            )
            _open_gimp(xcf_path=save_path, width_val=w, height_val=h,
                       unit=unit, dpi=actual_dpi)
        else:
            _open_gimp()

        self._thumb.refresh(save_path)
        self.path_changed.emit()

    def _set_path(self):
        start_dir = os.path.expanduser("~")
        if self._data.get("xcf_path"):
            parent = os.path.dirname(self._data["xcf_path"])
            if os.path.isdir(parent):
                start_dir = parent

        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف GIMP موجود",
            start_dir, "GIMP Files (*.xcf);;All Files (*)"
        )
        if path:
            old = self._data.get("xcf_path") or ""
            if old:
                get_watcher().unwatch(old)
            update_design_size_path(self.conn, self._size_id, path)
            self._data["xcf_path"] = path
            get_watcher().watch(path)
            self._thumb.refresh(path)
            self.path_changed.emit()