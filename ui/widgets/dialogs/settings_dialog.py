"""
ui/widgets/dialogs/settings_dialog.py
======================================
نافذة الإعدادات — حجم الخط + مسار GIMP + وحدات القياس + الثيم + اللغة.

[إصلاح] الاستيراد من unit_service مباشرة — المصدر الأصلي للدوال.
  قبل: from ui.widgets.combo.unit import load_units, add_unit, ...
  بعد: from ui.widgets.combo.unit_service import load_units, add_unit, ...
"""

import os
from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QDialogButtonBox,
    QLineEdit, QFileDialog, QGroupBox,
    QListWidget, QListWidgetItem,
    QInputDialog, QScrollArea, QWidget,
    QTabWidget, QButtonGroup, QRadioButton,
    QPushButton, QFrame,
)

from ui.font  import get_font_size, set_font_size, apply_font, fs
from ui.theme import _C

from ui.widgets.combo.unit_service import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _DEFAULT_UNITS,
)
from ui.widgets.dialogs.message  import msg_info, msg_warning
from ui.widgets.dialogs.confirm  import confirm_action
from ui.widgets.components.button import make_btn


def _get_settings_conn_and_status() -> "tuple":
    """
    [A-05] يرجع (conn, has_active_company) في استدعاء واحد.
    """
    try:
        from db.companies.company_state import company_state
        if not company_state.is_ready:
            return None, False
        conn = company_state.get_erp_conn()
        return conn, True
    except Exception:
        return None, False


def _get_settings_conn():
    """[للتوافق مع الكود القديم] يرجع الـ connection فقط."""
    conn, _ = _get_settings_conn_and_status()
    return conn


def _has_active_company() -> bool:
    """[للتوافق مع الكود القديم] يتحقق بسرعة من وجود شركة نشطة."""
    _, has_company = _get_settings_conn_and_status()
    return has_company


class SettingsDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app           = app
        self._original_size = get_font_size()

        self.setWindowTitle("⚙️  إعدادات")
        self.setMinimumWidth(560)
        self.setMinimumHeight(480)
        self.setModal(True)
        self._build()
        self._slider.setValue(self._original_size)
        self._load_settings()

    def _build(self):
        base = get_font_size()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: none;
                background: {_C['bg_page']};
            }}
            QTabBar::tab {{
                font-size: {fs(base, 0)}pt;
                color: {_C['text_muted']};
                background: {_C['bg_surface_2']};
                border: none;
                border-bottom: 2px solid transparent;
                padding: 8px 18px; min-width: 80px;
            }}
            QTabBar::tab:selected {{
                color: {_C['accent']};
                border-bottom: 2px solid {_C['accent']};
                font-weight: 700;
                background: {_C['bg_surface']};
            }}
            QTabBar::tab:hover:!selected {{
                color: {_C['text_primary']};
                background: {_C['bg_hover']};
            }}
        """)

        self._tabs.addTab(self._build_font_tab(),    "🔤  الخط")
        self._tabs.addTab(self._build_theme_tab(),   "🎨  المظهر")
        self._tabs.addTab(self._build_lang_tab(),    "🌐  اللغة")
        self._tabs.addTab(self._build_units_tab(),   "📏  الوحدات")
        self._tabs.addTab(self._build_gimp_tab(),    "🖼️  GIMP")
        outer.addWidget(self._tabs, stretch=1)

        btn_bar = QWidget()
        btn_bar.setStyleSheet(
            f"background:{_C['bg_surface']}; border-top:1px solid {_C['border']};"
        )
        btn_bar_lay = QHBoxLayout(btn_bar)
        btn_bar_lay.setContentsMargins(20, 8, 20, 8)

        btns       = QDialogButtonBox()
        btn_ok     = btns.addButton("✅  حفظ",   QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton("✖  إلغاء", QDialogButtonBox.RejectRole)
        btn_ok.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_ok.clicked.connect(self._save)
        btn_cancel.clicked.connect(self._cancel)
        btn_bar_lay.addWidget(btns)
        outer.addWidget(btn_bar)

    # ══════════════════════════════════════════════════════
    # تبويب الخط
    # ══════════════════════════════════════════════════════

    def _build_font_tab(self) -> QWidget:
        base   = get_font_size()
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        grp = QGroupBox("حجم الخط")
        grp_lay = QVBoxLayout(grp)

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

        self._lbl_val = QLabel(f"{base} pt")
        self._lbl_val.setMinimumWidth(44)
        self._lbl_val.setAlignment(Qt.AlignCenter)

        row.addWidget(lbl_small)
        row.addWidget(self._slider, stretch=1)
        row.addWidget(lbl_big)
        row.addSpacing(8)
        row.addWidget(self._lbl_val)
        grp_lay.addLayout(row)

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
        grp_lay.addWidget(self._preview)

        lbl_hint = QLabel(
            "💡  اضغط حفظ لتطبيق حجم الخط الجديد على كامل الواجهة"
        )
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet(
            f"color:{_C['text_muted']}; font-size: {fs(base, -2)}pt; background: transparent;"
        )
        grp_lay.addWidget(lbl_hint)
        lay.addWidget(grp)
        lay.addStretch()
        return widget

    # ══════════════════════════════════════════════════════
    # تبويب الثيم
    # ══════════════════════════════════════════════════════

    def _build_theme_tab(self) -> QWidget:
        base   = get_font_size()
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        grp     = QGroupBox("اختر مظهر التطبيق")
        grp_lay = QVBoxLayout(grp)
        grp_lay.setSpacing(10)

        from ui.theme_manager import theme_manager, THEMES, THEME_DISPLAY_NAMES

        self._theme_btn_group = QButtonGroup(self)
        self._theme_radios    = {}
        current = theme_manager.current_theme

        themes_info = {
            "light": ("☀️", "فاتح",  "خلفية بيضاء دافئة مريحة للعين"),
            "dark":  ("🌙", "داكن",  "خلفية داكنة للاستخدام الليلي"),
        }

        for key, (icon, name, desc) in themes_info.items():
            card = self._make_theme_card(icon, name, desc, key == current)
            radio = card.findChild(QRadioButton)
            if radio:
                self._theme_btn_group.addButton(radio)
                self._theme_radios[key] = radio
            grp_lay.addWidget(card)

        lay.addWidget(grp)

        preview_grp     = QGroupBox("معاينة الألوان")
        preview_grp_lay = QHBoxLayout(preview_grp)
        preview_grp_lay.setSpacing(6)

        color_samples = [
            (_C['accent'],       "accent"),
            (_C['success'],      "success"),
            (_C['warning'],      "warning"),
            (_C['danger'],       "danger"),
            (_C['bg_surface'],   "surface"),
            (_C['text_primary'], "text"),
        ]
        for color, label in color_samples:
            swatch = QFrame()
            swatch.setFixedSize(36, 36)
            swatch.setStyleSheet(
                f"background:{color}; border-radius:6px; "
                f"border:1px solid {_C['border']};"
            )
            swatch.setToolTip(f"{label}: {color}")
            preview_grp_lay.addWidget(swatch)

        preview_grp_lay.addStretch()
        lay.addWidget(preview_grp)
        lay.addStretch()
        return widget

    def _make_theme_card(self, icon: str, name: str,
                          desc: str, is_selected: bool) -> QWidget:
        base  = get_font_size()
        card  = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{_C['bg_surface_2']}; border-radius:8px;"
            f"border:1px solid {_C['border']}; padding:4px; }}"
        )
        lay   = QHBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(12)

        radio = QRadioButton()
        radio.setChecked(is_selected)
        lay.addWidget(radio)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet(f"font-size:{fs(base, +4)}pt; background:transparent;")
        lay.addWidget(lbl_icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(
            f"font-weight:700; font-size:{fs(base, +1)}pt; background:transparent;"
        )
        lbl_desc = QLabel(desc)
        lbl_desc.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt; background:transparent;"
        )
        text_col.addWidget(lbl_name)
        text_col.addWidget(lbl_desc)
        lay.addLayout(text_col)
        lay.addStretch()
        return card

    def _get_selected_theme(self) -> str:
        for key, radio in self._theme_radios.items():
            if radio.isChecked():
                return key
        return "light"

    # ══════════════════════════════════════════════════════
    # تبويب اللغة
    # ══════════════════════════════════════════════════════

    def _build_lang_tab(self) -> QWidget:
        base   = get_font_size()
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        grp     = QGroupBox("اختر لغة الواجهة")
        grp_lay = QVBoxLayout(grp)
        grp_lay.setSpacing(10)

        try:
            from ui.widgets.core.i18n import i18n_manager
            current_lang = i18n_manager.language
        except Exception:
            current_lang = "ar"

        self._lang_btn_group = QButtonGroup(self)
        self._lang_radios    = {}

        langs_info = {
            "ar": ("🇸🇦", "العربية",  "واجهة باللغة العربية (RTL)"),
            "en": ("🇬🇧", "English", "Interface in English (LTR)"),
        }

        for key, (flag, name, desc) in langs_info.items():
            card  = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background:{_C['bg_surface_2']}; border-radius:8px;"
                f"border:1px solid {_C['border']}; padding:4px; }}"
            )
            cLay  = QHBoxLayout(card)
            cLay.setContentsMargins(12, 8, 12, 8)
            cLay.setSpacing(12)

            radio = QRadioButton()
            radio.setChecked(key == current_lang)
            self._lang_btn_group.addButton(radio)
            self._lang_radios[key] = radio
            cLay.addWidget(radio)

            lbl_flag = QLabel(flag)
            lbl_flag.setStyleSheet(
                f"font-size:{fs(base, +4)}pt; background:transparent;"
            )
            cLay.addWidget(lbl_flag)

            text_col = QVBoxLayout()
            text_col.setSpacing(2)
            lbl_name = QLabel(name)
            lbl_name.setStyleSheet(
                f"font-weight:700; font-size:{fs(base, +1)}pt; background:transparent;"
            )
            lbl_desc = QLabel(desc)
            lbl_desc.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt; background:transparent;"
            )
            text_col.addWidget(lbl_name)
            text_col.addWidget(lbl_desc)
            cLay.addLayout(text_col)
            cLay.addStretch()

            grp_lay.addWidget(card)

        lay.addWidget(grp)

        hint = QLabel("💡  تغيير اللغة يُطبَّق فوراً بعد الحفظ")
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt; background:transparent;"
        )
        lay.addWidget(hint)
        lay.addStretch()
        return widget

    def _get_selected_lang(self) -> str:
        for key, radio in self._lang_radios.items():
            if radio.isChecked():
                return key
        return "ar"

    # ══════════════════════════════════════════════════════
    # تبويب الوحدات
    # ══════════════════════════════════════════════════════

    def _build_units_tab(self) -> QWidget:
        base   = get_font_size()
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        grp     = QGroupBox("وحدات القياس المتاحة")
        grp_lay = QVBoxLayout(grp)

        self._units_list = QListWidget()
        self._units_list.setAlternatingRowColors(True)
        self._units_list.setMinimumHeight(140)
        grp_lay.addWidget(self._units_list)

        btn_row = QHBoxLayout()
        btn_add   = make_btn("➕  إضافة وحدة",        "primary")
        btn_del   = make_btn("🗑️  حذف المحددة",       "danger")
        btn_reset = make_btn("↺  استعادة الافتراضية", "ghost")
        btn_add.clicked.connect(self._add_unit)
        btn_del.clicked.connect(self._del_unit)
        btn_reset.clicked.connect(self._reset_units)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        grp_lay.addLayout(btn_row)

        hint = QLabel("💡  الوحدات الافتراضية (باللون الرمادي) لا يمكن حذفها")
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -2)}pt; background:transparent;"
        )
        grp_lay.addWidget(hint)
        lay.addWidget(grp)
        lay.addStretch()
        return widget

    # ══════════════════════════════════════════════════════
    # تبويب GIMP
    # ══════════════════════════════════════════════════════

    def _build_gimp_tab(self) -> QWidget:
        base   = get_font_size()
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(20, 16, 20, 16)
        lay.setSpacing(12)

        grp     = QGroupBox("مسار برنامج GIMP")
        grp_lay = QVBoxLayout(grp)

        self._inp_gimp = QLineEdit()
        self._inp_gimp.setMinimumHeight(30)
        self._inp_gimp.setPlaceholderText(r"مثال: C:\Program Files\GIMP 2\bin\gimp-2.10.exe")
        self._inp_gimp.setStyleSheet(
            f"font-size:{fs(base, -1)}pt; color:{_C['text_primary']};"
            f"background:{_C['bg_input']}; border:1px solid {_C['border_med']};"
            "border-radius:4px; padding:4px 8px;"
        )

        gimp_row = QHBoxLayout()
        btn_browse = make_btn("📂  تصفح", "normal")
        btn_clear  = make_btn("✖",        "ghost")
        btn_clear.setFixedWidth(28)
        btn_browse.clicked.connect(self._browse_gimp)
        btn_clear.clicked.connect(lambda: self._inp_gimp.clear())

        gimp_row.addWidget(self._inp_gimp, stretch=1)
        gimp_row.addWidget(btn_browse)
        gimp_row.addWidget(btn_clear)
        grp_lay.addLayout(gimp_row)

        lbl_hint = QLabel("💡  اتركه فارغاً للبحث التلقائي في المسارات الشائعة")
        lbl_hint.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -2)}pt; background: transparent;"
        )
        grp_lay.addWidget(lbl_hint)
        lay.addWidget(grp)
        lay.addStretch()
        return widget

    # ══════════════════════════════════════════════════════
    # تحميل الإعدادات
    # ══════════════════════════════════════════════════════

    def _load_settings(self):
        conn, has_company = _get_settings_conn_and_status()

        if not has_company or conn is None:
            if not has_company:
                self._show_no_company_notice()
        else:
            try:
                from db.shared.settings_repo import get_setting
                path = get_setting(conn, "gimp_path", "")
                self._inp_gimp.setText(path)
            except Exception:
                pass

        self._reload_units_list()

    def _show_no_company_notice(self):
        base = get_font_size()
        from ui.widgets.core.colors import status_colors
        s = status_colors("warning")

        notice_style = (
            f"color: {s['fg']}; font-size: {fs(base, -1)}pt;"
            f"background: {s['bg']}; border: 1px solid {s['border']};"
            "border-radius: 6px; padding: 6px 10px;"
        )
        notice_text = "⚠️  اختر شركة نشطة لعرض وحدات القياس ومسار GIMP"

        units_tab = self._tabs.widget(3)
        if units_tab:
            lbl = QLabel(notice_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(notice_style)
            lay = units_tab.layout()
            if lay:
                lay.insertWidget(0, lbl)

        gimp_tab = self._tabs.widget(4)
        if gimp_tab:
            lbl2 = QLabel(notice_text)
            lbl2.setWordWrap(True)
            lbl2.setStyleSheet(notice_style)
            lay2 = gimp_tab.layout()
            if lay2:
                lay2.insertWidget(0, lbl2)

    def _reload_units_list(self):
        self._units_list.clear()
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

    # ══════════════════════════════════════════════════════
    # إدارة الوحدات
    # ══════════════════════════════════════════════════════

    def _add_unit(self):
        conn = _get_settings_conn()
        if not conn:
            msg_warning(self, "تنبيه", "اختر شركة نشطة أولاً لإضافة وحدات قياس")
            return

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

        conn = _get_settings_conn()
        if not conn:
            msg_warning(self, "تنبيه", "اختر شركة نشطة أولاً لحذف وحدات القياس")
            return

        if confirm_action(self, "تأكيد الحذف", f"حذف الوحدة «{item.text()}»؟",
                          icon="🗑️", confirm_text="حذف", danger=True):
            try:
                remove_unit(conn, val)
            except Exception as e:
                msg_warning(self, "خطأ", str(e))
                return
            self._reload_units_list()

    def _reset_units(self):
        conn = _get_settings_conn()
        if not conn:
            msg_warning(self, "تنبيه", "اختر شركة نشطة أولاً لاستعادة الوحدات الافتراضية")
            return

        if confirm_action(self, "استعادة الافتراضية",
                          "حذف كل الوحدات المضافة والرجوع للقائمة الافتراضية؟",
                          icon="↺", confirm_text="استعادة"):
            try:
                reset_units_to_default(conn)
            except Exception as e:
                msg_warning(self, "خطأ", str(e))
                return
            self._reload_units_list()

    # ══════════════════════════════════════════════════════
    # GIMP
    # ══════════════════════════════════════════════════════

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

    # ══════════════════════════════════════════════════════
    # معاينة الخط
    # ══════════════════════════════════════════════════════

    def _on_font_change(self, val: int):
        self._lbl_val.setText(f"{val} pt")
        self._preview.setStyleSheet(
            f"font-size: {val}pt;"
            f"border: 1px solid {_C['border']}; border-radius: 6px;"
            f"padding: 12px; background:{_C['bg_surface']}; color:{_C['text_primary']};"
        )

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def _save(self):
        from ui.events import bus

        size = self._slider.value()
        set_font_size(size)
        apply_font(self._app, size)
        bus.font_changed.emit(size)

        selected_theme = self._get_selected_theme()
        from ui.theme_manager import theme_manager
        if selected_theme != theme_manager.current_theme:
            theme_manager.set_theme(selected_theme, save=True)

        selected_lang = self._get_selected_lang()
        from ui.widgets.core.i18n import i18n_manager
        if selected_lang != i18n_manager.language:
            i18n_manager.set_language(selected_lang, save=True)
            self._app.setLayoutDirection(i18n_manager.qt_direction)
            bus.language_changed.emit(selected_lang)

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