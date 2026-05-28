"""
ui/settings_dialog.py
=====================
نافذة الإعدادات — حجم الخط + مسار GIMP + إدارة وحدات القياس.

[تحسين 48]:
  - _get_settings_conn() أصبحت تستخدم company_state.get_erp_conn()
    بدل فتح sqlite3.connect() جديد منفصل.
  - لو الشركة مش جاهزة ترجع None (نفس السلوك القديم).
  - دوال الحفظ تستخدم _get_settings_conn_for_write() لو احتاجت
    transaction منفصلة (حالياً WAL يكفي).
  - الـ conn من company_state لا تُغلق — هي shared connection.
"""

import os
from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QDialogButtonBox,
    QLineEdit, QFileDialog, QGroupBox,
    QListWidget, QListWidgetItem,
    QInputDialog, QScrollArea, QWidget,
)

from ui.app_settings import get_font_size, set_font_size, apply_font, _C, fs

from ui.widgets.combo.unit import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _DEFAULT_UNITS,
)
from ui.widgets.dialogs.message  import msg_info, msg_warning
from ui.widgets.dialogs.confirm  import confirm_action
from ui.widgets.components.button import make_btn


def _get_settings_conn():
    """
    [تحسين 48] يرجع الـ shared ERP connection من company_state.

    القديم: كان يفتح sqlite3.connect() جديد منفصل لكل استدعاء.
    الجديد: يستخدم company_state.get_erp_conn() مباشرة — لا connection مكرر،
    ولا حاجة لإغلاقه (هو shared).

    يرجع None لو الشركة مش جاهزة — نفس السلوك القديم.
    """
    try:
        from db.companies.company_state import company_state
        if not company_state.is_ready:
            return None
        return company_state.get_erp_conn()
    except Exception:
        return None


def _should_close_conn(conn) -> bool:
    """
    [تحسين 48] يتحقق لو الـ conn ملك هذا الكود أو shared.
    الـ shared connections لا تُغلق من هنا.
    """
    if conn is None:
        return False
    try:
        from db.companies.company_state import company_state
        return conn is not company_state.get_erp_conn()
    except Exception:
        return False


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
        base = get_font_size()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 12)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background:{_C['bg_surface_2']}; width: 8px; border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background:{_C['border_med']}; border-radius: 4px; min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{ background:{_C['border_strong']}; }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0px; }}
        """)

        content = QWidget()
        content_lay = QVBoxLayout(content)
        content_lay.setSpacing(14)
        content_lay.setContentsMargins(20, 20, 20, 10)

        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

        # ── شريط الأزرار ──
        btn_bar = QWidget()
        btn_bar.setStyleSheet(f"background:{_C['bg_surface']}; border-top:1px solid {_C['border']};")
        btn_bar_lay = QHBoxLayout(btn_bar)
        btn_bar_lay.setContentsMargins(20, 8, 20, 0)

        btns       = QDialogButtonBox()
        btn_ok     = btns.addButton("✅  حفظ",   QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton("✖  إلغاء", QDialogButtonBox.RejectRole)
        btn_ok.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_ok.clicked.connect(self._save)
        btn_cancel.clicked.connect(self._cancel)
        btn_bar_lay.addWidget(btns)
        outer.addWidget(btn_bar)

        # ══ قسم الخط ══
        font_group = QGroupBox("حجم الخط")
        font_lay   = QVBoxLayout(font_group)

        row = QHBoxLayout()
        row.setSpacing(8)

        lbl_small = QLabel("أ")
        lbl_small.setStyleSheet(f"font-size: {fs(base, -2)}pt;")

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(8, 20)
        self._slider.setTickInterval(1)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.valueChanged.connect(self._on_font_change)

        lbl_big = QLabel("أ")
        lbl_big.setStyleSheet(f"font-size: {fs(base, +4)}pt; font-weight: bold;")

        self._lbl_val = QLabel("11 pt")
        self._lbl_val.setMinimumWidth(44)
        self._lbl_val.setAlignment(Qt.AlignCenter)

        row.addWidget(lbl_small)
        row.addWidget(self._slider, stretch=1)
        row.addWidget(lbl_big)
        row.addSpacing(8)
        row.addWidget(self._lbl_val)
        font_lay.addLayout(row)

        self._preview = QLabel(
            "معاينة النص — Preview 123\n"
            "أبجد هوز حطي كلمن — The quick brown fox\n"
            "١٢٣٤٥٦٧٨٩٠ — ABCDEFG abcdefg"
        )
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setWordWrap(True)
        self._preview.setStyleSheet(
            f"font-size: {self._original_size}pt;"
            f"border: 1px solid {_C['border']}; border-radius: 6px;"
            f"padding: 12px; background:{_C['bg_surface']}; color:{_C['text_primary']};"
        )
        font_lay.addWidget(self._preview)

        lbl_hint_font = QLabel(
            "💡  المعاينة أعلاه تعرض شكل النص بالحجم المختار — "
            "اضغط حفظ لتطبيقه على كامل الواجهة"
        )
        lbl_hint_font.setWordWrap(True)
        lbl_hint_font.setStyleSheet(
            f"color:{_C['text_muted']}; font-size: {fs(base, -2)}pt; background: transparent;"
        )
        font_lay.addWidget(lbl_hint_font)
        content_lay.addWidget(font_group)

        # ══ قسم GIMP ══
        gimp_group = QGroupBox("مسار برنامج GIMP")
        gimp_lay   = QVBoxLayout(gimp_group)
        gimp_lay.setSpacing(6)

        gimp_row = QHBoxLayout()
        gimp_row.setSpacing(6)

        self._inp_gimp = QLineEdit()
        self._inp_gimp.setPlaceholderText(r"مثال: C:\Program Files\GIMP 2\bin\gimp-2.10.exe")
        self._inp_gimp.setMinimumHeight(34)

        btn_browse = make_btn("📂  تصفح", "primary", fixed_size=False)
        btn_browse.setMinimumHeight(34)
        btn_browse.clicked.connect(self._browse_gimp)

        btn_clear = make_btn("✖", "danger", fixed_size=True)
        btn_clear.setFixedSize(34, 34)
        btn_clear.setToolTip("مسح المسار")
        btn_clear.clicked.connect(lambda: self._inp_gimp.clear())

        gimp_row.addWidget(self._inp_gimp, stretch=1)
        gimp_row.addWidget(btn_browse)
        gimp_row.addWidget(btn_clear)
        gimp_lay.addLayout(gimp_row)

        lbl_hint_gimp = QLabel("💡  اتركه فارغاً للبحث التلقائي في المسارات الشائعة")
        lbl_hint_gimp.setStyleSheet(
            f"color:{_C['text_muted']}; font-size: {fs(base, -2)}pt; background: transparent;"
        )
        gimp_lay.addWidget(lbl_hint_gimp)
        content_lay.addWidget(gimp_group)

        # ══ قسم وحدات القياس ══
        units_group = QGroupBox("وحدات القياس")
        units_lay   = QVBoxLayout(units_group)
        units_lay.setSpacing(6)

        from ui.widgets.core.colors import status_colors
        hint_s = status_colors("warning")
        lbl_units_hint = QLabel(
            "💡  هذه الوحدات تظهر في كل dropdown اختيار الوحدة في التطبيق.\n"
            "الوحدات الافتراضية (px, mm, cm, m, inch) لا يمكن حذفها."
        )
        lbl_units_hint.setStyleSheet(
            f"color:{hint_s['fg']}; font-size: {fs(base, -2)}pt;"
            f"background:{hint_s['bg']}; border:1px solid {hint_s['border']};"
            "border-radius: 4px; padding: 6px 8px;"
        )
        lbl_units_hint.setWordWrap(True)
        units_lay.addWidget(lbl_units_hint)

        self._units_list = QListWidget()
        self._units_list.setMaximumHeight(130)
        self._units_list.setStyleSheet(f"""
            QListWidget {{
                border:1px solid {_C['border_med']}; border-radius:4px;
                font-size: {fs(base, -1)}pt;
            }}
            QListWidget::item {{ padding: 4px 8px; }}
            QListWidget::item:selected {{
                background:{_C['accent_light']}; color:{_C['accent_text']};
            }}
        """)
        units_lay.addWidget(self._units_list)

        units_btn_row = QHBoxLayout()
        units_btn_row.setSpacing(6)

        btn_add_unit    = make_btn("➕  إضافة وحدة",       "success")
        btn_del_unit    = make_btn("🗑️  حذف المحدد",       "danger")
        btn_reset_units = make_btn("↺  استعادة الافتراضية", "ghost")

        btn_add_unit.clicked.connect(self._add_unit)
        btn_del_unit.clicked.connect(self._del_unit)
        btn_reset_units.clicked.connect(self._reset_units)

        units_btn_row.addWidget(btn_add_unit)
        units_btn_row.addWidget(btn_del_unit)
        units_btn_row.addStretch()
        units_btn_row.addWidget(btn_reset_units)
        units_lay.addLayout(units_btn_row)
        content_lay.addWidget(units_group)

        content_lay.addStretch()

    # ── تحميل الإعدادات ──

    def _load_settings(self):
        # [تحسين 48] استخدام shared connection — لا إغلاق هنا
        conn = _get_settings_conn()
        if conn:
            try:
                from db.shared.settings_repo import get_setting
                path = get_setting(conn, "gimp_path", "")
                self._inp_gimp.setText(path)
            except Exception:
                pass
            # لا conn.close() — هو shared من company_state
        self._reload_units_list()

    def _reload_units_list(self):
        self._units_list.clear()
        # [تحسين 48] shared connection — لا إغلاق
        conn = _get_settings_conn()
        if conn:
            try:
                units = load_units(conn)
            except Exception:
                units = list(_DEFAULT_UNITS)
        else:
            units = list(_DEFAULT_UNITS)

        default_vals = {u[0] for u in _DEFAULT_UNITS}
        for val, label in units:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, val)
            if val in default_vals:
                from PyQt5.QtGui import QColor
                item.setForeground(QColor(_C['text_muted']))
                item.setToolTip("وحدة افتراضية — لا يمكن حذفها")
            self._units_list.addItem(item)

    # ── إدارة الوحدات ──

    def _add_unit(self):
        val, ok = QInputDialog.getText(
            self, "إضافة وحدة", "اكتب رمز الوحدة (مثال: ft, yd, pt):",
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

        # [تحسين 48] shared connection — لا إغلاق
        conn = _get_settings_conn()
        if not conn:
            msg_warning(self, "تنبيه", "لا توجد شركة نشطة")
            return
        try:
            result = add_unit(conn, val, label.strip())
        except Exception as e:
            msg_warning(self, "خطأ", str(e))
            return

        if result:
            self._reload_units_list()
        else:
            msg_info(self, "تنبيه", f"الوحدة «{val}» موجودة بالفعل.")

    def _del_unit(self):
        item = self._units_list.currentItem()
        if not item:
            msg_info(self, "تنبيه", "اختر وحدة أولاً")
            return
        val = item.data(Qt.UserRole)
        default_vals = {u[0] for u in _DEFAULT_UNITS}
        if val in default_vals:
            msg_warning(self, "تنبيه", f"لا يمكن حذف الوحدة الافتراضية «{val}».")
            return
        if confirm_action(self, "تأكيد الحذف", f"حذف الوحدة «{item.text()}»؟",
                          icon="🗑️", confirm_text="حذف", danger=True):
            # [تحسين 48] shared connection — لا إغلاق
            conn = _get_settings_conn()
            if not conn:
                return
            try:
                remove_unit(conn, val)
            except Exception as e:
                msg_warning(self, "خطأ", str(e))
                return
            self._reload_units_list()

    def _reset_units(self):
        if confirm_action(self, "استعادة الافتراضية",
                          "حذف كل الوحدات المضافة والرجوع للقائمة الافتراضية؟",
                          icon="↺", confirm_text="استعادة"):
            # [تحسين 48] shared connection — لا إغلاق
            conn = _get_settings_conn()
            if not conn:
                return
            try:
                reset_units_to_default(conn)
            except Exception as e:
                msg_warning(self, "خطأ", str(e))
                return
            self._reload_units_list()

    # ── تصفح لملف GIMP ──

    def _browse_gimp(self):
        start = self._inp_gimp.text().strip()
        if start and os.path.exists(os.path.dirname(start)):
            start_dir = os.path.dirname(start)
        else:
            start_dir = r"C:\Program Files"
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف GIMP التنفيذي", start_dir,
            "GIMP (gimp*.exe);;Executable Files (*.exe);;All Files (*)"
        )
        if path:
            self._inp_gimp.setText(path)

    # ── معاينة حجم الخط ──

    def _on_font_change(self, val: int):
        self._lbl_val.setText(f"{val} pt")
        self._preview.setStyleSheet(
            f"font-size: {val}pt;"
            f"border: 1px solid {_C['border']}; border-radius: 6px;"
            f"padding: 12px; background:{_C['bg_surface']}; color:{_C['text_primary']};"
        )

    # ── حفظ ──

    def _save(self):
        size = self._slider.value()
        set_font_size(size)
        apply_font(self._app, size)

        # [تحسين 48] shared connection — لا إغلاق
        conn = _get_settings_conn()
        if conn:
            try:
                from db.shared.settings_repo import set_setting
                set_setting(conn, "gimp_path", self._inp_gimp.text().strip())
            except Exception:
                pass
        self.accept()

    def _cancel(self):
        self.reject()