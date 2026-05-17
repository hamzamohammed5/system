"""
ui/tabs/design/designs/_size_card.py
======================================
بطاقة مقاس واحد — تصميم Modern/Flat محسّن.

التحسينات:
  - layout أوضح: thumbnail كبير + معلومات منظّمة
  - شريط حالة ملوّن أسفل كل بطاقة
  - أزرار مرتّبة بـ hierarchy واضح
  - ألوان وحدود خفيفة بدل الثقيلة
"""

import os
import subprocess

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
    QFrame, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal
from PyQt5.QtGui  import QPixmap, QColor

from db.designs.designs_sizes_repo import (
    update_design_size_path,
    fetch_canvas_size,
    fetch_canvas_dpi,
)
from ._xcf_thumbnail import get_xcf_thumbnail, get_watcher

# ── ألوان النظام الجديد ──
_BG         = "#ffffff"
_BG_SUBTLE  = "#f8fafc"
_BORDER     = "#e2e8f0"
_BORDER_MED = "#cbd5e1"
_TEXT       = "#0f172a"
_TEXT_MED   = "#475569"
_TEXT_MUTED = "#94a3b8"
_BLUE       = "#3b82f6"
_BLUE_LT    = "#eff6ff"
_BLUE_MED   = "#bfdbfe"
_GREEN      = "#16a34a"
_GREEN_LT   = "#f0fdf4"
_GREEN_MED  = "#bbf7d0"
_ORANGE     = "#ea580c"
_ORANGE_LT  = "#fff7ed"
_ORANGE_MED = "#fed7aa"
_RED        = "#dc2626"
_RED_LT     = "#fef2f2"
_PURPLE     = "#7c3aed"
_PURPLE_LT  = "#f5f3ff"

_DEFAULT_DPI  = 300.0
_THUMB_SIZE   = 80


# ── دوال مساعدة للـ stylesheet ──

def _btn(bg, fg, border, hover_bg):
    return (
        f"QPushButton {{"
        f"  background:{bg}; color:{fg}; border:1px solid {border};"
        f"  border-radius:6px; padding:4px 12px; font-size:11px; font-weight:500;"
        f"}}"
        f"QPushButton:hover {{ background:{hover_bg}; }}"
        f"QPushButton:pressed {{ opacity:0.85; }}"
    )


# ════════════════════════════════════════════════════════
# Worker — استخراج الـ thumbnail
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
# وحدات GIMP
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
    if u in ("inch","in","انش","بوصة"): return max(1, int(round(value * dpi)))
    return max(1, int(round(value)))


def _prepare_native_dims(w, h, unit, dpi=300.0):
    u = unit.strip().lower()
    if u == "m":
        w, h, u = w * 1000, h * 1000, "mm"
    gimp_uid = _GIMP_UNIT_MAP.get(u, 0)
    return _to_px(w, u, dpi), _to_px(h, u, dpi), gimp_uid, dpi


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
            w_px = _to_px(width_val,  unit, actual_dpi)
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
# Widget الـ Thumbnail — مربع أكبر وأوضح
# ════════════════════════════════════════════════════════

class _ThumbnailWidget(QLabel):
    def __init__(self, xcf_path: str, size: int = _THUMB_SIZE, parent=None):
        super().__init__(parent)
        self._size     = size
        self._xcf_path = xcf_path
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self._show_loading()

        if xcf_path and os.path.exists(xcf_path):
            self._load_async(xcf_path)
        else:
            self._show_no_preview()

    def _show_loading(self):
        self.setText("⏳")
        self.setStyleSheet(f"""
            QLabel {{
                background: {_BG_SUBTLE};
                border: 1px solid {_BORDER};
                border-radius: 8px;
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
            self.setPixmap(pixmap)
            self.setStyleSheet(f"""
                QLabel {{
                    background: #1e1b4b;
                    border: 1px solid {_BLUE_MED};
                    border-radius: 8px;
                }}
            """)
        else:
            self._show_no_preview()

    def _show_no_preview(self):
        self.setText("📄")
        self.setStyleSheet(f"""
            QLabel {{
                background: {_BG_SUBTLE};
                border: 1px dashed {_BORDER_MED};
                border-radius: 8px;
                font-size: 24px;
                color: {_TEXT_MUTED};
            }}
        """)

    def refresh(self, xcf_path: str = None):
        from ._xcf_thumbnail import clear_cache
        if xcf_path:
            self._xcf_path = xcf_path
        path = self._xcf_path
        if path:
            clear_cache(path)
        self._show_loading()
        if path and os.path.exists(path):
            self._load_async(path)
        else:
            self._show_no_preview()


# ════════════════════════════════════════════════════════
# بطاقة مقاس واحد — تصميم Modern/Flat
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

    def hideEvent(self, event):
        self._stop_watching()
        super().hideEvent(event)

    def closeEvent(self, event):
        self._stop_watching()
        super().closeEvent(event)

    def _stop_watching(self):
        xcf = self._data.get("xcf_path") or ""
        if xcf:
            try:
                get_watcher().file_changed.disconnect(self._on_xcf_changed)
            except Exception:
                pass

    def _build(self):
        # ── حالة الملف ──
        xcf_path    = self._data.get("xcf_path") or ""
        has_file    = bool(xcf_path)
        file_exists = has_file and os.path.exists(xcf_path)

        # ── Frame الرئيسي ──
        self.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border: 1px solid {_BORDER};
                border-radius: 10px;
            }}
        """)
        self.setMinimumHeight(100)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══ الجزء العلوي: thumbnail + معلومات + أزرار ══
        top = QFrame()
        top.setStyleSheet("QFrame { background: transparent; border: none; }")
        top_lay = QHBoxLayout(top)
        top_lay.setContentsMargins(14, 12, 14, 12)
        top_lay.setSpacing(14)

        # ── Thumbnail ──
        self._thumb = _ThumbnailWidget(xcf_path, size=_THUMB_SIZE)
        top_lay.addWidget(self._thumb)

        # ── المعلومات ──
        info = QVBoxLayout()
        info.setSpacing(4)
        info.setContentsMargins(0, 2, 0, 2)

        # اسم المقاس
        inst_name = self._data.get("instance_name") or f"مقاس #{self._data.get('instance_id', '')}"
        set_name  = self._data.get("set_name", "")
        lbl_name  = QLabel(f"{inst_name}  <span style='color:{_TEXT_MUTED}; font-weight:400'>({set_name})</span>")
        lbl_name.setStyleSheet(f"color:{_TEXT}; font-size:13px; font-weight:600; background:transparent;")
        lbl_name.setTextFormat(Qt.RichText)

        # الأبعاد
        w, h = fetch_canvas_size(self.conn, self._size_id)
        unit = _unit_for_set(self.conn, self._data.get("set_id", 0))
        dpi  = fetch_canvas_dpi(self.conn, self._size_id)

        if w is not None and h is not None:
            if dpi:
                w_px = _to_px(w, unit, dpi)
                h_px = _to_px(h, unit, dpi)
                dims_txt = f"📐  {w:g} × {h:g} {unit}  →  {w_px:,} × {h_px:,} px  @  {int(dpi)} DPI"
            else:
                dims_txt = f"📐  {w:g} × {h:g} {unit}"
        else:
            dims_txt = "📐  الأبعاد غير محددة"

        lbl_dims = QLabel(dims_txt)
        lbl_dims.setStyleSheet(f"color:{_TEXT_MED}; font-size:11px; background:transparent;")

        # مسار الملف
        if has_file:
            path_display = xcf_path
            if len(path_display) > 55:
                path_display = "…" + path_display[-52:]
            path_color = _GREEN if file_exists else _ORANGE
            path_icon  = "📁" if file_exists else "⚠️"
            lbl_path = QLabel(f"{path_icon}  {path_display}")
        else:
            path_color = _TEXT_MUTED
            lbl_path = QLabel("📁  لا يوجد ملف — سيُفتح GIMP بكانفاس جديد")

        lbl_path.setStyleSheet(f"color:{path_color}; font-size:10px; background:transparent;")

        info.addWidget(lbl_name)
        info.addWidget(lbl_dims)
        info.addWidget(lbl_path)
        info.addStretch()

        top_lay.addLayout(info, stretch=1)

        # ── الأزرار ──
        btns = QVBoxLayout()
        btns.setSpacing(6)
        btns.setContentsMargins(0, 0, 0, 0)

        # زر GIMP الرئيسي
        if file_exists:
            btn_main = QPushButton("🎨  فتح في GIMP")
            btn_main.setStyleSheet(_btn(_BLUE, "#fff", _BLUE, "#2563eb"))
        else:
            btn_main = QPushButton("✨  إنشاء في GIMP")
            btn_main.setStyleSheet(_btn(_GREEN, "#fff", _GREEN, "#15803d"))

        btn_main.setMinimumHeight(32)
        btn_main.setMinimumWidth(130)
        btn_main.clicked.connect(
            self._open_in_gimp if file_exists else self._create_in_gimp
        )

        # صف أزرار الإجراءات
        act_row = QHBoxLayout()
        act_row.setSpacing(4)

        if not file_exists:
            btn_link = QPushButton("📂  ربط")
            btn_link.setMinimumHeight(28)
            btn_link.setStyleSheet(_btn(_BG, _BLUE, _BLUE_MED, _BLUE_LT))
            btn_link.clicked.connect(self._set_path)
            act_row.addWidget(btn_link)

        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(30, 30)
        btn_edit.setToolTip("تعديل")
        btn_edit.setStyleSheet(_btn(_BG_SUBTLE, _TEXT_MED, _BORDER, _BG))
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self._size_id))

        btn_del = QPushButton("🗑️")
        btn_del.setFixedSize(30, 30)
        btn_del.setToolTip("حذف")
        btn_del.setStyleSheet(_btn(_RED_LT, _RED, "#fca5a5", "#fee2e2"))
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self._size_id))

        act_row.addStretch()
        act_row.addWidget(btn_edit)
        act_row.addWidget(btn_del)

        btns.addWidget(btn_main)
        btns.addLayout(act_row)
        btns.addStretch()

        top_lay.addLayout(btns)
        root.addWidget(top)

        # ══ شريط الحالة الملوّن ══
        self._build_status_bar(root, file_exists, has_file, unit, dpi)

    def _build_status_bar(self, root, file_exists, has_file, unit, dpi):
        """شريط أسفل البطاقة يعرض حالة الملف بشكل ملوّن."""
        bar = QFrame()

        if file_exists:
            bar_bg     = _GREEN_LT
            bar_border = _GREEN_MED
            status_txt = "✓  الملف موجود"
            status_col = _GREEN
        elif has_file:
            bar_bg     = _ORANGE_LT
            bar_border = _ORANGE_MED
            status_txt = "⚠  الملف غير موجود"
            status_col = _ORANGE
        else:
            bar_bg     = _BG_SUBTLE
            bar_border = _BORDER
            status_txt = "—  لا يوجد ملف"
            status_col = _TEXT_MUTED

        bar.setStyleSheet(f"""
            QFrame {{
                background: {bar_bg};
                border-top: 1px solid {bar_border};
                border-bottom-left-radius: 10px;
                border-bottom-right-radius: 10px;
            }}
        """)

        bar_lay = QHBoxLayout(bar)
        bar_lay.setContentsMargins(14, 6, 14, 6)
        bar_lay.setSpacing(10)

        lbl_status = QLabel(status_txt)
        lbl_status.setStyleSheet(
            f"color:{status_col}; font-size:11px; font-weight:500; background:transparent;"
        )

        # وحدة + DPI كـ chips
        chips_row = QHBoxLayout()
        chips_row.setSpacing(6)

        for txt in [unit, (f"{int(dpi)} DPI" if dpi else "بدون DPI")]:
            chip = QLabel(txt)
            chip.setStyleSheet(f"""
                QLabel {{
                    background: {_BG};
                    color: {_TEXT_MED};
                    border: 1px solid {_BORDER_MED};
                    border-radius: 4px;
                    padding: 1px 8px;
                    font-size: 10px;
                }}
            """)
            chips_row.addWidget(chip)

        bar_lay.addWidget(lbl_status)
        bar_lay.addStretch()
        bar_lay.addLayout(chips_row)

        root.addWidget(bar)

    # ── فتح GIMP ──────────────────────────────────────

    def _open_in_gimp(self):
        xcf = self._data["xcf_path"]
        if xcf and os.path.exists(xcf):
            get_watcher().watch(xcf)
            _open_gimp(xcf_path=xcf)
        else:
            QMessageBox.warning(
                self, "الملف غير موجود",
                f"الملف غير موجود:\n{xcf}\n\nاستخدم «ربط ملف موجود» لتحديث المسار."
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
        self._data = dict(self._data)
        self._data["xcf_path"] = save_path
        get_watcher().watch(save_path)

        if w and h:
            u = unit.strip().lower()
            actual_dpi = 96.0 if u == "px" else float(dpi)
            w_px, h_px, _, _ = _prepare_native_dims(w, h, unit, actual_dpi)
            QMessageBox.information(
                self, "📐  إنشاء كانفاس في GIMP",
                f"📐  الأبعاد: {w:g} × {h:g} {unit}\n"
                f"📌  بالبكسل: {w_px:,} × {h_px:,} px  @  {int(actual_dpi)} DPI\n\n"
                f"📁  الملف:\n      {save_path}"
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
            old_path = self._data.get("xcf_path") or ""
            if old_path:
                get_watcher().unwatch(old_path)

            update_design_size_path(self.conn, self._size_id, path)
            self._data = dict(self._data)
            self._data["xcf_path"] = path
            get_watcher().watch(path)
            self._thumb.refresh(path)
            self.path_changed.emit()