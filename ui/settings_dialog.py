"""
ui/settings_dialog.py
=====================
نافذة الإعدادات — حجم الخط + مسار GIMP + إدارة وحدات القياس.
"""

import os
from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QDialogButtonBox,
    QLineEdit, QFileDialog, QGroupBox,
    QListWidget, QListWidgetItem, QMessageBox,
    QInputDialog,
)

from ui.app_settings import get_font_size, set_font_size, apply_font
from db.shared.connection import get_connection
from db.shared.settings_repo import get_setting, set_setting
from ui.widgets.shared.unit_combo import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _DEFAULT_UNITS,
)


class SettingsDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app           = app
        self._original_size = get_font_size()

        self.setWindowTitle("⚙️  إعدادات")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._build()
        self._slider.setValue(self._original_size)
        self._load_settings()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(14)
        root.setContentsMargins(20, 20, 20, 20)

        # ══ قسم الخط ══════════════════════════════════════
        font_group = QGroupBox("حجم الخط")
        font_lay   = QVBoxLayout(font_group)

        row = QHBoxLayout()
        row.setSpacing(8)

        lbl_small = QLabel("أ")
        lbl_small.setStyleSheet("font-size: 9pt;")

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(8, 20)
        self._slider.setTickInterval(1)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.valueChanged.connect(self._on_font_change)

        lbl_big = QLabel("أ")
        lbl_big.setStyleSheet("font-size: 15pt; font-weight: bold;")

        self._lbl_val = QLabel("11 pt")
        self._lbl_val.setMinimumWidth(44)
        self._lbl_val.setAlignment(Qt.AlignCenter)

        row.addWidget(lbl_small)
        row.addWidget(self._slider, stretch=1)
        row.addWidget(lbl_big)
        row.addSpacing(8)
        row.addWidget(self._lbl_val)
        font_lay.addLayout(row)

        self._preview = QLabel("معاينة النص — Preview 123")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setStyleSheet(
            "border: 1px solid #ccc; border-radius: 6px; padding: 12px;"
        )
        font_lay.addWidget(self._preview)
        root.addWidget(font_group)

        # ══ قسم GIMP ══════════════════════════════════════
        gimp_group = QGroupBox("مسار برنامج GIMP")
        gimp_lay   = QVBoxLayout(gimp_group)
        gimp_lay.setSpacing(6)

        gimp_row = QHBoxLayout()
        gimp_row.setSpacing(6)

        self._inp_gimp = QLineEdit()
        self._inp_gimp.setPlaceholderText(
            r"مثال: C:\Program Files\GIMP 2\bin\gimp-2.10.exe"
        )
        self._inp_gimp.setMinimumHeight(34)

        btn_browse = QPushButton("📂  تصفح")
        btn_browse.setMinimumHeight(34)
        btn_browse.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                border: none; border-radius: 6px;
                padding: 4px 14px; font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_browse.clicked.connect(self._browse_gimp)

        btn_clear = QPushButton("✖")
        btn_clear.setFixedSize(34, 34)
        btn_clear.setToolTip("مسح المسار")
        btn_clear.setStyleSheet("""
            QPushButton {
                background: #fdecea; color: #c62828;
                border: 1px solid #ef9a9a; border-radius: 6px;
            }
            QPushButton:hover { background: #ffcdd2; }
        """)
        btn_clear.clicked.connect(lambda: self._inp_gimp.clear())

        gimp_row.addWidget(self._inp_gimp, stretch=1)
        gimp_row.addWidget(btn_browse)
        gimp_row.addWidget(btn_clear)
        gimp_lay.addLayout(gimp_row)

        lbl_hint = QLabel("💡  اتركه فارغاً للبحث التلقائي في المسارات الشائعة")
        lbl_hint.setStyleSheet(
            "color: #888; font-size: 10px; background: transparent;"
        )
        gimp_lay.addWidget(lbl_hint)
        root.addWidget(gimp_group)

        # ══ قسم وحدات القياس ══════════════════════════════
        units_group = QGroupBox("وحدات القياس")
        units_lay   = QVBoxLayout(units_group)
        units_lay.setSpacing(6)

        lbl_units_hint = QLabel(
            "💡  هذه الوحدات تظهر في كل dropdown اختيار الوحدة في التطبيق.\n"
            "الوحدات الافتراضية (px, mm, cm, m, inch) لا يمكن حذفها."
        )
        lbl_units_hint.setStyleSheet(
            "color: #555; font-size: 10px; background: #fff8e1;"
            "border: 1px solid #ffe082; border-radius: 4px; padding: 6px 8px;"
        )
        lbl_units_hint.setWordWrap(True)
        units_lay.addWidget(lbl_units_hint)

        # قائمة الوحدات
        self._units_list = QListWidget()
        self._units_list.setMaximumHeight(130)
        self._units_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #c5cae9;
                border-radius: 4px;
                font-size: 11px;
            }
            QListWidget::item { padding: 4px 8px; }
            QListWidget::item:selected {
                background: #e8f0fe;
                color: #1565c0;
            }
        """)
        units_lay.addWidget(self._units_list)

        # أزرار إدارة الوحدات
        units_btn_row = QHBoxLayout()
        units_btn_row.setSpacing(6)

        btn_add_unit = QPushButton("➕  إضافة وحدة")
        btn_add_unit.setMinimumHeight(30)
        btn_add_unit.setStyleSheet("""
            QPushButton {
                background: #e8f5e9; color: #2e7d32;
                border: 1px solid #a5d6a7; border-radius: 4px;
                padding: 3px 10px; font-size: 11px;
            }
            QPushButton:hover { background: #c8e6c9; }
        """)
        btn_add_unit.clicked.connect(self._add_unit)

        btn_del_unit = QPushButton("🗑️  حذف المحدد")
        btn_del_unit.setMinimumHeight(30)
        btn_del_unit.setStyleSheet("""
            QPushButton {
                background: #fdecea; color: #c62828;
                border: 1px solid #ef9a9a; border-radius: 4px;
                padding: 3px 10px; font-size: 11px;
            }
            QPushButton:hover { background: #ffcdd2; }
        """)
        btn_del_unit.clicked.connect(self._del_unit)

        btn_reset_units = QPushButton("↺  استعادة الافتراضية")
        btn_reset_units.setMinimumHeight(30)
        btn_reset_units.setStyleSheet("""
            QPushButton {
                background: #e8eaf6; color: #3949ab;
                border: 1px solid #c5cae9; border-radius: 4px;
                padding: 3px 10px; font-size: 11px;
            }
            QPushButton:hover { background: #c5cae9; }
        """)
        btn_reset_units.clicked.connect(self._reset_units)

        units_btn_row.addWidget(btn_add_unit)
        units_btn_row.addWidget(btn_del_unit)
        units_btn_row.addStretch()
        units_btn_row.addWidget(btn_reset_units)
        units_lay.addLayout(units_btn_row)

        root.addWidget(units_group)

        # ══ أزرار ══════════════════════════════════════════
        btns       = QDialogButtonBox()
        btn_ok     = btns.addButton("✅  حفظ",    QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton("✖  إلغاء",  QDialogButtonBox.RejectRole)
        btn_ok.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_ok.clicked.connect(self._save)
        btn_cancel.clicked.connect(self._cancel)
        root.addWidget(btns)

    # ── تحميل الإعدادات ──────────────────────────────────

    def _load_settings(self):
        try:
            conn = get_connection()
            path = get_setting(conn, "gimp_path", "")
            conn.close()
            self._inp_gimp.setText(path)
        except Exception:
            pass
        self._reload_units_list()

    def _reload_units_list(self):
        """يعيد تحميل قائمة الوحدات."""
        self._units_list.clear()
        try:
            conn = get_connection()
            units = load_units(conn)
            conn.close()
        except Exception:
            # ← إزالة الـ local import — _DEFAULT_UNITS متعرّف في الأعلى
            units = list(_DEFAULT_UNITS)

        default_vals = {u[0] for u in _DEFAULT_UNITS}

        for val, label in units:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, val)
            if val in default_vals:
                item.setForeground(Qt.gray)
                item.setToolTip("وحدة افتراضية — لا يمكن حذفها")
            self._units_list.addItem(item)

    # ── إدارة الوحدات ────────────────────────────────────

    def _add_unit(self):
        """يفتح input صغير لإضافة وحدة جديدة."""
        val, ok = QInputDialog.getText(
            self, "إضافة وحدة",
            "اكتب رمز الوحدة (مثال: ft, yd, pt):",
        )
        if not ok or not val.strip():
            return

        val = val.strip().lower()

        label, ok2 = QInputDialog.getText(
            self, "إضافة وحدة",
            f"اكتب التسمية الكاملة للوحدة «{val}» (مثال: ft — قدم):",
            text=val,
        )
        if not ok2 or not label.strip():
            return

        try:
            conn = get_connection()
            result = add_unit(conn, val, label.strip())
            conn.close()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return

        if result:
            self._reload_units_list()
        else:
            QMessageBox.information(
                self, "تنبيه",
                f"الوحدة «{val}» موجودة بالفعل."
            )

    def _del_unit(self):
        """يحذف الوحدة المحددة."""
        item = self._units_list.currentItem()
        if not item:
            QMessageBox.information(self, "تنبيه", "اختر وحدة أولاً")
            return

        val = item.data(Qt.UserRole)
        default_vals = {u[0] for u in _DEFAULT_UNITS}

        if val in default_vals:
            QMessageBox.warning(
                self, "تنبيه",
                f"لا يمكن حذف الوحدة الافتراضية «{val}»."
            )
            return

        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف الوحدة «{item.text()}»؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                conn = get_connection()
                remove_unit(conn, val)
                conn.close()
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            self._reload_units_list()

    def _reset_units(self):
        """يعيد الوحدات للافتراضية."""
        if QMessageBox.question(
            self, "استعادة الافتراضية",
            "حذف كل الوحدات المضافة والرجوع للقائمة الافتراضية؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                conn = get_connection()
                reset_units_to_default(conn)
                conn.close()
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            self._reload_units_list()

    # ── تصفح لملف GIMP ───────────────────────────────────

    def _browse_gimp(self):
        start = self._inp_gimp.text().strip()
        if start and os.path.exists(os.path.dirname(start)):
            start_dir = os.path.dirname(start)
        else:
            start_dir = r"C:\Program Files"

        path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف GIMP التنفيذي",
            start_dir,
            "GIMP (gimp*.exe);;Executable Files (*.exe);;All Files (*)"
        )
        if path:
            self._inp_gimp.setText(path)

    # ── معاينة حجم الخط ──────────────────────────────────

    def _on_font_change(self, val: int):
        self._lbl_val.setText(f"{val} pt")
        apply_font(self._app, val)
        self._preview.setStyleSheet(
            f"font-size: {val}pt; border: 1px solid #ccc; "
            "border-radius: 6px; padding: 12px;"
        )

    # ── حفظ ───────────────────────────────────────────────

    def _save(self):
        size = self._slider.value()
        set_font_size(size)
        apply_font(self._app, size)

        try:
            conn = get_connection()
            set_setting(conn, "gimp_path", self._inp_gimp.text().strip())
            conn.close()
        except Exception:
            pass

        self.accept()

    def _cancel(self):
        apply_font(self._app, self._original_size)
        self.reject()