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
        import glob
        matches = glob.glob(pattern)
        if matches:
            return sorted(matches)[-1]

    return None

def _open_gimp(xcf_path: str = None,
               width_px: float = None, height_px: float = None,
               unit: str = "px"):
    gimp_exe = _find_gimp()
    if not gimp_exe:
        QMessageBox.warning(
            None, "GIMP غير موجود",
            "لم يتم العثور على GIMP.\n"
            "حدد مساره من ⚙️ الإعدادات."
        )
        return False

    try:
        if xcf_path and os.path.exists(xcf_path):
            subprocess.Popen([gimp_exe, xcf_path])
            return True

        if width_px and height_px:
            import tempfile
            from PIL import Image

            # تحويل الوحدات إلى px
            DPI = 96
            MM_TO_PX = DPI / 25.4

            unit_lower = (unit or "px").lower().strip()

            if unit_lower in ("mm", "مم"):
                w = int(round(width_px  * MM_TO_PX))
                h = int(round(height_px * MM_TO_PX))
            elif unit_lower in ("cm", "سم"):
                w = int(round(width_px  * MM_TO_PX * 10))
                h = int(round(height_px * MM_TO_PX * 10))
            elif unit_lower in ("in", "inch", "انش"):
                w = int(round(width_px  * DPI))
                h = int(round(height_px * DPI))
            else:
                # px — بدون تحويل
                w = int(round(width_px))
                h = int(round(height_px))

            # طبقة شفافة
            tmp = tempfile.NamedTemporaryFile(
                suffix=".png",
                delete=False
            )
            tmp.close()

            img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            img.save(tmp.name)

            subprocess.Popen([gimp_exe, tmp.name])
            return True

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
        has_file  = bool(self._data["xcf_path"])
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

        # اسم المقاس + المجموعة
        inst_name = self._data["instance_name"] or f"مقاس #{self._data['instance_id']}"
        set_name  = self._data["set_name"]
        lbl_name  = QLabel(f"<b>{inst_name}</b>  <span style='color:{_TEXT_MUTED}'>({set_name})</span>")
        lbl_name.setStyleSheet(f"font-size: 13px; color: {_TEXT}; background: transparent; border: none;")

        # أبعاد الكانفاس
        w, h = fetch_canvas_size(self.conn, self._size_id)
        if w is not None and h is not None:
            dims_txt = f"📐  {w:g} × {h:g}"
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

        # الزر الرئيسي: "فتح" لو الملف موجود، "إنشاء" لو مش موجود
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

        # الزر الثانوي: "ربط ملف موجود" لو مفيش ملف، أو "فتح / ربط" لو الملف مش موجود
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

    def _open_in_gimp(self):
        """فتح ملف .xcf موجود في GIMP."""
        xcf = self._data["xcf_path"]
        if xcf and os.path.exists(xcf):
            _open_gimp(xcf_path=xcf)
        else:
            # الملف كان محفوظاً لكن اتحذف أو اتنقل
            QMessageBox.warning(
                self, "الملف غير موجود",
                f"الملف غير موجود في المسار المحفوظ:\n{xcf}\n\n"
                "استخدم زر «ربط ملف موجود» لتحديد المسار الجديد،\n"
                "أو احذف المسار وأنشئ ملفاً جديداً."
            )

    def _create_in_gimp(self):
        w, h = fetch_canvas_size(self.conn, self._size_id)

        inst_name  = (self._data["instance_name"] or "design").replace(" ", "_")
        default_name = f"{inst_name}.xcf"

        start_dir = os.path.expanduser("~")
        if self._data["xcf_path"]:
            parent = os.path.dirname(self._data["xcf_path"])
            if os.path.isdir(parent):
                start_dir = parent

        # ── اختر مكان الحفظ أولاً ──
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

        # ── احفظ المسار في الـ DB ──
        update_design_size_path(self.conn, self._size_id, save_path)
        self._data = dict(self._data)
        self._data["xcf_path"] = save_path

        # ── افتح GIMP مع رسالة توضيحية ──
        if w and h:
            msg = (
                f"سيفتح GIMP الآن.\n\n"
                f"1️⃣  من القائمة: File → New\n"
                f"2️⃣  حدد الأبعاد:\n"
                f"      العرض : {int(round(w))} px\n"
                f"      الطول : {int(round(h))} px\n\n"
                f"3️⃣  بعد الانتهاء احفظ الملف في:\n"
                f"      {save_path}"
            )
            QMessageBox.information(self, "📐  تعليمات GIMP", msg)
            _open_gimp(width_px=w, height_px=h)
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

