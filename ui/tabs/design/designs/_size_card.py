"""
ui/tabs/design/designs/_size_card.py
==============================
"""

import os
import subprocess

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
    QFrame, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer


from db.designs.designs_sizes_repo import (
    update_design_size_path,
    fetch_canvas_size
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


# ══════════════════════════════════════════════════════════
# تحويل الوحدات إلى بكسل
# ══════════════════════════════════════════════════════════

# DPI المرجعي لـ GIMP الافتراضي
_GIMP_DPI = 96.0


def _to_px(value: float, unit: str) -> int:
    """
    يحوّل قيمة من الوحدة المحددة إلى بكسل صحيح.

    الوحدات المدعومة:
        px   → بدون تحويل
        mm   → value / 25.4 * DPI
        cm   → value / 2.54  * DPI
        m    → value / 0.0254 * DPI
        inch → value * DPI
    """
    unit_lower = (unit or "px").strip().lower()

    if unit_lower == "px":
        return int(round(value))
    elif unit_lower == "mm":
        return int(round(value / 25.4 * _GIMP_DPI))
    elif unit_lower == "cm":
        return int(round(value / 2.54  * _GIMP_DPI))
    elif unit_lower in ("m", "متر"):
        return int(round(value / 0.0254 * _GIMP_DPI))
    elif unit_lower in ("inch", "in", "انش", "بوصة"):
        return int(round(value * _GIMP_DPI))
    else:
        # وحدة غير معروفة → نعاملها كـ px
        return int(round(value))


def _unit_for_set(conn, set_id: int) -> str:
    """يجلب الوحدة الافتراضية لمجموعة المقاسات."""
    try:
        row = conn.execute(
            "SELECT default_unit FROM dimension_sets WHERE id=?", (set_id,)
        ).fetchone()
        return row["default_unit"] if row and row["default_unit"] else "px"
    except Exception:
        return "px"


# ══════════════════════════════════════════════════════════
# مساعد فتح GIMP
# ══════════════════════════════════════════════════════════

def _find_gimp() -> str | None:
    """يجلب مسار GIMP: من الإعدادات أولاً، ثم البحث التلقائي."""
    import shutil, glob

    # أولاً: المسار المحفوظ في الإعدادات
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

    # ثانياً: بحث تلقائي
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


def _open_gimp(xcf_path: str = None,
               width_val: float = None, height_val: float = None,
               unit: str = "px"):
    """
    يفتح GIMP مع ملف موجود أو يُنشئ صورة شفافة بالأبعاد المحددة.

    width_val / height_val : القيم بالوحدة المحددة (unit)
    unit                   : الوحدة (px / mm / cm / m / inch)
    """
    gimp_exe = _find_gimp()
    if not gimp_exe:
        QMessageBox.warning(
            None, "GIMP غير موجود",
            "لم يتم العثور على GIMP.\n"
            "حدد مساره من ⚙️ الإعدادات."
        )
        return False

    try:
        # ── فتح ملف موجود ──
        if xcf_path and os.path.exists(xcf_path):
            subprocess.Popen([gimp_exe, xcf_path])
            return True

        # ── إنشاء صورة شفافة بالأبعاد المحولة ──
        if width_val and height_val:
            import tempfile
            from PIL import Image

            # تحويل الأبعاد إلى بكسل
            w_px = _to_px(width_val,  unit)
            h_px = _to_px(height_val, unit)

            # تأكد من حد أدنى معقول
            w_px = max(1, w_px)
            h_px = max(1, h_px)

            # ── صورة شفافة (RGBA مع alpha=0) ──
            tmp = tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False
            )
            tmp.close()

            img = Image.new("RGBA", (w_px, h_px), (0, 0, 0, 0))
            img.save(tmp.name)

            subprocess.Popen([gimp_exe, tmp.name])
            return True

        # ── فتح GIMP بدون ملف ──
        subprocess.Popen([gimp_exe])
        return True

    except ImportError:
        QMessageBox.warning(
            None, "مكتبة ناقصة",
            "تحتاج تثبيت Pillow:\n\npip install Pillow"
        )
        return False

    except Exception as e:
        QMessageBox.critical(None, "خطأ", f"فشل فتح GIMP:\n{e}")
        return False


# ══════════════════════════════════════════════════════════
# بطاقة مقاس واحد
# ══════════════════════════════════════════════════════════

class _SizeCard(QFrame):
    """بطاقة تعرض مقاساً واحداً مع أزرار الفتح والتعديل."""

    edit_requested   = pyqtSignal(int)   # size_id
    delete_requested = pyqtSignal(int)   # size_id
    path_changed     = pyqtSignal()

    def __init__(self, conn, size_data, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._data     = size_data
        self._size_id  = size_data["id"]
        self._build()

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1.5px solid {_BORDER};
                border-radius: 10px;
            }}
        """)
        self.setMinimumHeight(88)

        root = QHBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(12)

        # ── أيقونة الحالة ──
        has_file    = bool(self._data["xcf_path"])
        file_exists = has_file and os.path.exists(self._data["xcf_path"])

        if file_exists:
            icon_txt   = "✅"
            icon_color = _GREEN
        elif has_file:
            icon_txt   = "⚠️"
            icon_color = _ORANGE
        else:
            icon_txt   = "📄"
            icon_color = _TEXT_MUTED

        lbl_icon = QLabel(icon_txt)
        lbl_icon.setStyleSheet(
            f"font-size: 22px; color: {icon_color}; background: transparent; border: none;"
        )
        lbl_icon.setFixedWidth(30)
        lbl_icon.setAlignment(Qt.AlignCenter)

        # ── معلومات المقاس ──
        info = QVBoxLayout()
        info.setSpacing(3)

        inst_name = self._data["instance_name"] or f"مقاس #{self._data['instance_id']}"
        set_name  = self._data["set_name"]
        lbl_name  = QLabel(f"<b>{inst_name}</b>  <span style='color:{_TEXT_MUTED}'>({set_name})</span>")
        lbl_name.setStyleSheet(f"font-size: 13px; color: {_TEXT}; background: transparent; border: none;")

        # ── أبعاد الكانفاس مع الوحدة ──
        w, h = fetch_canvas_size(self.conn, self._size_id)
        unit  = _unit_for_set(self.conn, self._data["set_id"])

        if w is not None and h is not None:
            # عرض القيمة الأصلية + الوحدة + البكسل المحول
            w_px = _to_px(w, unit)
            h_px = _to_px(h, unit)
            dims_txt = f"📐  {w:g} × {h:g} {unit}"
            if unit != "px":
                dims_txt += f"  ({w_px} × {h_px} px)"
            if self._data["width_label"]:
                dims_txt += f"  ({self._data['width_label']} × {self._data['height_label']})"
        else:
            dims_txt = "📐  الأبعاد غير محددة"

        lbl_dims = QLabel(dims_txt)
        lbl_dims.setStyleSheet(
            f"font-size: 11px; color: {_TEXT_MUTED}; background: transparent; border: none;"
        )

        # مسار الملف
        if has_file:
            path_display = self._data["xcf_path"]
            if len(path_display) > 55:
                path_display = "..." + path_display[-52:]
            lbl_path = QLabel(f"📁  {path_display}")
            color = _GREEN if file_exists else _ORANGE
            lbl_path.setStyleSheet(
                f"font-size: 10px; color: {color}; background: transparent; border: none;"
            )
        else:
            lbl_path = QLabel("📁  لا يوجد ملف محفوظ — سيُفتح GIMP بكانفاس جديد")
            lbl_path.setStyleSheet(
                f"font-size: 10px; color: {_TEXT_MUTED}; background: transparent; border: none;"
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
                    background: {_BLUE}; color: white; border: none;
                    border-radius: 6px; font-weight: bold; font-size: 11px;
                    padding: 4px 10px;
                }}
                QPushButton:hover {{ background: #0d47a1; }}
            """)
            btn_main.clicked.connect(self._open_in_gimp)
        else:
            btn_main = QPushButton("✨  إنشاء في GIMP")
            btn_main.setStyleSheet(f"""
                QPushButton {{
                    background: {_GREEN}; color: white; border: none;
                    border-radius: 6px; font-weight: bold; font-size: 11px;
                    padding: 4px 10px;
                }}
                QPushButton:hover {{ background: #1b5e20; }}
            """)
            btn_main.clicked.connect(self._create_in_gimp)

        btn_main.setMinimumHeight(30)
        btn_main.setMinimumWidth(120)

        if not file_exists:
            btn_link = QPushButton("📂  ربط ملف موجود")
            btn_link.setMinimumHeight(28)
            btn_link.setStyleSheet(f"""
                QPushButton {{
                    background: white; color: {_BLUE};
                    border: 1.5px solid {_BLUE_MID}; border-radius: 6px;
                    font-size: 11px; padding: 3px 8px;
                }}
                QPushButton:hover {{ background: {_BLUE_LIGHT}; }}
            """)
            btn_link.clicked.connect(self._set_path)
            btns.addWidget(btn_link)

        btn_row2 = QHBoxLayout()
        btn_edit = QPushButton("✏️")
        btn_edit.setFixedSize(28, 28)
        btn_edit.setToolTip("تعديل")
        btn_edit.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE_LIGHT}; border: none; border-radius: 6px; font-size: 13px;
            }}
            QPushButton:hover {{ background: {_BLUE_MID}; }}
        """)
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self._size_id))

        btn_del = QPushButton("🗑️")
        btn_del.setFixedSize(28, 28)
        btn_del.setToolTip("حذف")
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background: {_RED_LT}; border: none; border-radius: 6px; font-size: 13px;
            }}
            QPushButton:hover {{ background: #ffcdd2; }}
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

    # ──────────────────────────────────────────────────────
    # فتح GIMP
    # ──────────────────────────────────────────────────────

    def _open_in_gimp(self):
        """فتح ملف .xcf موجود في GIMP."""
        xcf = self._data["xcf_path"]
        if xcf and os.path.exists(xcf):
            _open_gimp(xcf_path=xcf)
        else:
            QMessageBox.warning(
                self, "الملف غير موجود",
                f"الملف غير موجود في المسار المحفوظ:\n{xcf}\n\n"
                "استخدم زر «ربط ملف موجود» لتحديد المسار الجديد،\n"
                "أو احذف المسار وأنشئ ملفاً جديداً."
            )

    def _create_in_gimp(self):
        w, h = fetch_canvas_size(self.conn, self._size_id)
        unit  = _unit_for_set(self.conn, self._data["set_id"])

        inst_name    = (self._data["instance_name"] or "design").replace(" ", "_")
        default_name = f"{inst_name}.xcf"

        start_dir = os.path.expanduser("~")
        if self._data["xcf_path"]:
            parent = os.path.dirname(self._data["xcf_path"])
            if os.path.isdir(parent):
                start_dir = parent

        # ── اختر مكان الحفظ ──
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "اختر مكان حفظ ملف GIMP",
            os.path.join(start_dir, default_name),
            "GIMP Files (*.xcf)"
        )
        if not save_path:
            return

        if not save_path.lower().endswith(".xcf"):
            save_path += ".xcf"

        # احفظ المسار في الـ DB
        update_design_size_path(self.conn, self._size_id, save_path)
        self._data = dict(self._data)
        self._data["xcf_path"] = save_path

        # ── افتح GIMP مع رسالة توضيحية ──
        if w and h:
            w_px = _to_px(w, unit)
            h_px = _to_px(h, unit)

            # رسالة توضيحية تُظهر الوحدة الأصلية والبكسل المحول
            if unit == "px":
                dims_display = f"{w_px} × {h_px} px"
            else:
                dims_display = f"{w:g} × {h:g} {unit}  →  {w_px} × {h_px} px"

            msg = (
                f"سيفتح GIMP الآن مع صورة شفافة.\n\n"
                f"📐  الأبعاد: {dims_display}\n\n"
                f"3️⃣  بعد الانتهاء احفظ الملف في:\n"
                f"      {save_path}"
            )
            QMessageBox.information(self, "📐  تعليمات GIMP", msg)
            _open_gimp(width_val=w, height_val=h, unit=unit)
        else:
            msg = (
                f"سيفتح GIMP الآن.\n\n"
                f"1️⃣  من القائمة: File → New\n"
                f"2️⃣  حدد الأبعاد المطلوبة\n\n"
                f"3️⃣  بعد الانتهاء احفظ الملف في:\n"
                f"      {save_path}"
            )
            QMessageBox.information(self, "📐  تعليمات GIMP", msg)
            _open_gimp()

        self.path_changed.emit()

    def _set_path(self):
        """ربط ملف .xcf موجود بهذا المقاس."""
        start_dir = os.path.expanduser("~")
        if self._data["xcf_path"]:
            parent = os.path.dirname(self._data["xcf_path"])
            if os.path.isdir(parent):
                start_dir = parent

        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف GIMP موجود",
            start_dir,
            "GIMP Files (*.xcf);;All Files (*)"
        )
        if path:
            update_design_size_path(self.conn, self._size_id, path)
            self._data = dict(self._data)
            self._data["xcf_path"] = path
            self.path_changed.emit()