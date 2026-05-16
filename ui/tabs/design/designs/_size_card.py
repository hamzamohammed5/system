"""
ui/tabs/design/designs/_size_card.py
======================================
بطاقة مقاس واحد — مع عرض thumbnail من ملف XCF.
"""

import os
import subprocess

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
    QFrame, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal
from PyQt5.QtGui  import QPixmap

from db.designs.designs_sizes_repo import (
    update_design_size_path,
    fetch_canvas_size,
    fetch_canvas_dpi,
)

# ── ألوان ──
_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GREEN      = "#2e7d32"
_ORANGE     = "#e65100"
_RED_LT     = "#fdecea"
_BORDER     = "#e0e7f3"
_TEXT       = "#1a2340"
_TEXT_MUTED = "#7a869a"

_DEFAULT_DPI  = 300.0
_THUMB_SIZE   = 72      # حجم الـ thumbnail في البطاقة (px)


# ════════════════════════════════════════════════════════
# Worker — استخراج الـ thumbnail في thread منفصل
# ════════════════════════════════════════════════════════

class _ThumbWorker(QThread):
    """يستخرج الـ thumbnail في الخلفية ويُطلق signal بالنتيجة."""
    done = Signal(object)   # QPixmap أو None

    def __init__(self, xcf_path: str, size: int = _THUMB_SIZE):
        super().__init__()
        self._path = xcf_path
        self._size = size

    def run(self):
        from ._xcf_thumbnail import get_xcf_thumbnail
        pixmap = get_xcf_thumbnail(self._path, self._size)
        self.done.emit(pixmap)


# ════════════════════════════════════════════════════════
# وحدات GIMP الداخلية
# ════════════════════════════════════════════════════════

_GIMP_UNIT_MAP = {
    "px": 0, "mm": 2, "cm": 3, "inch": 4, "in": 4, "pt": 5, "m": 2,
}


def _to_px(value: float, unit: str, dpi: float = 300.0) -> int:
    u = unit.strip().lower()
    if u == "px":    return max(1, int(round(value)))
    if u == "mm":    return max(1, int(round(value / 25.4 * dpi)))
    if u == "cm":    return max(1, int(round(value / 2.54  * dpi)))
    if u in ("m", "متر"):    return max(1, int(round(value / 0.0254 * dpi)))
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


# ════════════════════════════════════════════════════════
# GIMP launcher
# ════════════════════════════════════════════════════════

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
# Widget الـ Thumbnail
# ════════════════════════════════════════════════════════

class _ThumbnailWidget(QLabel):
    """
    Label يعرض thumbnail من XCF أو placeholder.
    يحمّل الصورة في thread منفصل لتجنب تجميد الواجهة.
    """

    # placeholder SVG-based colors
    _PLACEHOLDER_BG = "#f0f4ff"
    _PLACEHOLDER_FG = "#c5cae9"

    def __init__(self, xcf_path: str, size: int = _THUMB_SIZE, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet(f"""
            QLabel {{
                background: {self._PLACEHOLDER_BG};
                border: 1.5px solid {self._PLACEHOLDER_FG};
                border-radius: 6px;
            }}
        """)
        self._show_placeholder()

        if xcf_path and os.path.exists(xcf_path):
            self._load_async(xcf_path)

    def _show_placeholder(self):
        self.setText("🖼")
        font = self.font()
        font.setPointSize(self._size // 4)
        self.setFont(font)

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
                    background: #1a1a2e;
                    border: 1.5px solid {_BLUE_MID};
                    border-radius: 6px;
                }}
            """)
        else:
            self._show_no_preview()

    def _show_no_preview(self):
        self.setText("📄")
        font = self.font()
        font.setPointSize(self._size // 4)
        self.setFont(font)
        self.setStyleSheet(f"""
            QLabel {{
                background: #fafafa;
                border: 1.5px dashed {self._PLACEHOLDER_FG};
                border-radius: 6px;
                color: {_TEXT_MUTED};
            }}
        """)

    def refresh(self, xcf_path: str):
        """يعيد تحميل الـ thumbnail بعد تغيير المسار."""
        from ._xcf_thumbnail import clear_cache
        clear_cache(xcf_path)
        self._show_placeholder()
        if xcf_path and os.path.exists(xcf_path):
            self._load_async(xcf_path)
        else:
            self._show_no_preview()


# ════════════════════════════════════════════════════════
# بطاقة مقاس واحد
# ════════════════════════════════════════════════════════

class _SizeCard(QFrame):
    """بطاقة تعرض مقاساً واحداً مع thumbnail + أزرار."""

    edit_requested   = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    path_changed     = pyqtSignal()

    def __init__(self, conn, size_data, parent=None):
        super().__init__(parent)
        self.conn     = conn
        # تحويل sqlite3.Row لـ dict لدعم .get() والتعديل لاحقاً
        self._data    = dict(size_data)
        self._size_id = self._data["id"]
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1.5px solid {_BORDER};
                border-radius: 10px;
            }}
        """)
        self.setMinimumHeight(96)

        root = QHBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(10)

        # ── Thumbnail ──────────────────────────────────
        xcf_path = self._data.get("xcf_path") or ""
        self._thumb = _ThumbnailWidget(xcf_path, size=_THUMB_SIZE)
        root.addWidget(self._thumb)

        # ── أيقونة الحالة ──
        has_file    = bool(xcf_path)
        file_exists = has_file and os.path.exists(xcf_path)

        if file_exists:
            icon_txt, icon_color = "✅", _GREEN
        elif has_file:
            icon_txt, icon_color = "⚠️", _ORANGE
        else:
            icon_txt, icon_color = "📄", _TEXT_MUTED

        lbl_icon = QLabel(icon_txt)
        lbl_icon.setStyleSheet(
            f"font-size:18px; color:{icon_color}; background:transparent; border:none;"
        )
        lbl_icon.setFixedWidth(24)
        lbl_icon.setAlignment(Qt.AlignCenter)

        # ── معلومات المقاس ──
        info = QVBoxLayout()
        info.setSpacing(3)

        inst_name = self._data["instance_name"] or f"مقاس #{self._data['instance_id']}"
        set_name  = self._data["set_name"]
        lbl_name  = QLabel(
            f"<b>{inst_name}</b>  "
            f"<span style='color:{_TEXT_MUTED}'>({set_name})</span>"
        )
        lbl_name.setStyleSheet(
            f"font-size:13px; color:{_TEXT}; background:transparent; border:none;"
        )

        # أبعاد الكانفاس
        w, h = fetch_canvas_size(self.conn, self._size_id)
        unit = _unit_for_set(self.conn, self._data["set_id"])
        dpi  = fetch_canvas_dpi(self.conn, self._size_id)

        if w is not None and h is not None:
            if dpi:
                w_px = _to_px(w, unit, dpi)
                h_px = _to_px(h, unit, dpi)
                dims_txt = (
                    f"📐  {w:g} × {h:g} {unit}  →  "
                    f"{w_px} × {h_px} px  @  {dpi:g} DPI"
                )
            else:
                dims_txt = (
                    f"📐  {w:g} × {h:g} {unit}  "
                    f"(بدون DPI — الافتراضي {int(_DEFAULT_DPI)})"
                )
        else:
            dims_txt = "📐  الأبعاد غير محددة"

        lbl_dims = QLabel(dims_txt)
        lbl_dims.setStyleSheet(
            f"font-size:11px; color:{_TEXT_MUTED}; background:transparent; border:none;"
        )

        # مسار الملف
        if has_file:
            path_display = xcf_path
            if len(path_display) > 52:
                path_display = "..." + path_display[-49:]
            lbl_path = QLabel(f"📁  {path_display}")
            color = _GREEN if file_exists else _ORANGE
        else:
            lbl_path = QLabel("📁  لا يوجد ملف — سيُفتح GIMP بكانفاس جديد")
            color = _TEXT_MUTED
        lbl_path.setStyleSheet(
            f"font-size:10px; color:{color}; background:transparent; border:none;"
        )

        info.addWidget(lbl_name)
        info.addWidget(lbl_dims)
        info.addWidget(lbl_path)

        # ── أزرار ──
        btns = QVBoxLayout()
        btns.setSpacing(6)

        if file_exists:
            btn_main = QPushButton("🎨  فتح في GIMP")
            btn_main.setStyleSheet(f"""
                QPushButton {{
                    background:{_BLUE}; color:white; border:none;
                    border-radius:6px; font-weight:bold; font-size:11px; padding:4px 10px;
                }}
                QPushButton:hover {{ background:#0d47a1; }}
            """)
            btn_main.clicked.connect(self._open_in_gimp)
        else:
            btn_main = QPushButton("✨  إنشاء في GIMP")
            btn_main.setStyleSheet(f"""
                QPushButton {{
                    background:{_GREEN}; color:white; border:none;
                    border-radius:6px; font-weight:bold; font-size:11px; padding:4px 10px;
                }}
                QPushButton:hover {{ background:#1b5e20; }}
            """)
            btn_main.clicked.connect(self._create_in_gimp)

        btn_main.setMinimumHeight(30)
        btn_main.setMinimumWidth(120)

        if not file_exists:
            btn_link = QPushButton("📂  ربط ملف موجود")
            btn_link.setMinimumHeight(28)
            btn_link.setStyleSheet(f"""
                QPushButton {{
                    background:white; color:{_BLUE};
                    border:1.5px solid {_BLUE_MID}; border-radius:6px;
                    font-size:11px; padding:3px 8px;
                }}
                QPushButton:hover {{ background:{_BLUE_LIGHT}; }}
            """)
            btn_link.clicked.connect(self._set_path)
            btns.addWidget(btn_link)

        btn_row2 = QHBoxLayout()
        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(28, 28)
        btn_edit.setToolTip("تعديل")
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background:{_BLUE_LIGHT}; border:none; border-radius:6px; font-size:13px;
            }}
            QPushButton:hover {{ background:{_BLUE_MID}; }}
        """)
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self._size_id))

        btn_del = QPushButton("🗑️")
        btn_del.setFixedSize(28, 28)
        btn_del.setToolTip("حذف")
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background:{_RED_LT}; border:none; border-radius:6px; font-size:13px;
            }}
            QPushButton:hover {{ background:#ffcdd2; }}
        """)
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self._size_id))

        btn_row2.addWidget(btn_edit)
        btn_row2.addWidget(btn_del)
        btn_row2.addStretch()

        btns.addWidget(btn_main)
        btns.addLayout(btn_row2)

        root.addWidget(lbl_icon)
        root.addLayout(info, stretch=1)
        root.addLayout(btns)

    # ── فتح GIMP ──────────────────────────────────────

    def _open_in_gimp(self):
        xcf = self._data["xcf_path"]
        if xcf and os.path.exists(xcf):
            _open_gimp(xcf_path=xcf)
        else:
            QMessageBox.warning(
                self, "الملف غير موجود",
                f"الملف غير موجود:\n{xcf}\n\n"
                "استخدم «ربط ملف موجود» لتحديث المسار."
            )

    def _create_in_gimp(self):
        w, h  = fetch_canvas_size(self.conn, self._size_id)
        unit  = _unit_for_set(self.conn, self._data["set_id"])
        dpi   = fetch_canvas_dpi(self.conn, self._size_id) or _DEFAULT_DPI

        inst_name    = (self._data["instance_name"] or "design").replace(" ", "_")
        default_name = f"{inst_name}.xcf"
        start_dir    = os.path.expanduser("~")
        if self._data["xcf_path"]:
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

        if w and h:
            u = unit.strip().lower()
            actual_dpi = 96.0 if u == "px" else float(dpi)
            w_px, h_px, _, _ = _prepare_native_dims(w, h, unit, actual_dpi)
            dims_display = f"{w:g} × {h:g} {unit}"
            QMessageBox.information(
                self, "📐  إنشاء كانفاس في GIMP",
                f"📐  الأبعاد: {dims_display}\n"
                f"📌  بالبكسل: {w_px} × {h_px} px  @  {int(actual_dpi)} DPI\n\n"
                f"📁  الملف:\n      {save_path}"
            )
            _open_gimp(xcf_path=save_path, width_val=w, height_val=h,
                       unit=unit, dpi=actual_dpi)
        else:
            QMessageBox.information(
                self, "📐  تعليمات GIMP",
                f"سيفتح GIMP — حدد الأبعاد من File → New\n\n📁  احفظ في:\n{save_path}"
            )
            _open_gimp()

        self._thumb.refresh(save_path)
        self.path_changed.emit()

    def _set_path(self):
        start_dir = os.path.expanduser("~")
        if self._data["xcf_path"]:
            parent = os.path.dirname(self._data["xcf_path"])
            if os.path.isdir(parent):
                start_dir = parent

        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف GIMP موجود",
            start_dir, "GIMP Files (*.xcf);;All Files (*)"
        )
        if path:
            update_design_size_path(self.conn, self._size_id, path)
            self._data = dict(self._data)
            self._data["xcf_path"] = path
            self._thumb.refresh(path)
            self.path_changed.emit()