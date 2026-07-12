"""
ui/widgets/dialogs/settings_dialog.py
======================================
نافذة الإعدادات — حجم الخط + مسار GIMP + وحدات القياس + الثيم + اللغة.

[إصلاح] الاستيراد من unit_service مباشرة — المصدر الأصلي للدوال.
  قبل: from ui.widgets.combo.unit import load_units, add_unit, ...
  بعد: from ui.widgets.combo.unit_service import load_units, add_unit, ...

[دمج events] المصدر الوحيد للـ bus هو ui.widgets.core.events.
  الجديد: from ui.widgets.core.events import bus

[إصلاح ثيم] SettingsDialog كان بيبني كل الـ stylesheets (تبويبات: خط/
  ثيم/لغة/وحدات/GIMP) مرة واحدة بس وقت الإنشاء بقيم _C و get_font_size.
  بما إنها QDialog مودال طويلة العمر نسبياً، الستايل كان بيتجمد لو
  المستخدم غيّر الثيم من نافذة تانية والنافذة دي لسه مفتوحة. الحل:
  WidgetMixin (theme=True, font=True) + فصل بناء كل widget (مرة واحدة
  جوه _build_*_tab) عن تطبيق الستايل (_refresh_style مركزية).
  ملاحظة: bus.font_changed.emit و bus.language_changed.emit في _save()
  هي عملية نشر (publish) مش اشتراك (subscribe) — فضلت زي ما هي.
"""

import os
from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QSlider, QDialogButtonBox,
    QFileDialog, QGroupBox,
    QListWidget, QListWidgetItem,
    QInputDialog, QScrollArea, QWidget,
    QTabWidget, QButtonGroup, QRadioButton,
    QPushButton, QFrame,
)
from ui.widgets.panels.themed_inputs import ThemedLineEdit

from ui.font  import get_font_size, set_font_size, apply_font, fs
from ui.theme import _C
from ui.constants import (
    DIALOG_BTN_MIN_H, MIN_FONT_SIZE, MAX_FONT_SIZE, BTN_MIN_HEIGHT,
    SETTINGS_DLG_MIN_W, SETTINGS_DLG_MIN_H, SETTINGS_SWATCH_SIZE,
    SETTINGS_GIMP_DEFAULT_DIR, SETTINGS_TAB_MARGINS, SETTINGS_CARD_MARGINS,
    SETTINGS_BTN_BAR_MARGINS, DIALOG_HDR_COL_SPACING,
    SETTINGS_UNITS_LIST_MIN_H, SETTINGS_VAL_LBL_MIN_W, SETTINGS_CLEAR_BTN_W,
    SETTINGS_PREVIEW_RADIUS, SETTINGS_PREVIEW_PAD, SETTINGS_CARD_RADIUS,
    SETTINGS_SWATCH_RADIUS, SETTINGS_CARD_INNER_PAD, SETTINGS_GIMP_INPUT_RADIUS,
    SETTINGS_GIMP_INPUT_PAD_H, SETTINGS_NOTICE_RADIUS, SETTINGS_NOTICE_PAD_V,
    SETTINGS_NOTICE_PAD_H, SETTINGS_TAB_PAD_V, SETTINGS_TAB_PAD_H, SETTINGS_TAB_MIN_W,
    SPACING_ZERO, SPACING_SM, SPACING_MD, SPACING_MD_LG, SPACING_LG,
    MARGIN_ZERO,
)

from services.shared.unit_service import (
    load_units, add_unit, remove_unit,
    reset_units_to_default, _default_units, _DEFAULT_UNIT_KEYS,
)
from services.shared.settings_service import SettingsService
from services.companies.company_service import CompanyService
from ui.widgets.dialogs.message  import msg_info, msg_warning
from ui.widgets.dialogs.confirm  import confirm_action
from ui.widgets.components.button import make_btn
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr


def _get_settings_conn_and_status() -> "tuple":
    """
    [A-05] يرجع (conn, has_active_company) في استدعاء واحد.
    """
    try:
        if not CompanyService.is_company_ready():
            return None, False
        conn = CompanyService.get_active_erp_conn()
        return conn, conn is not None
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


class SettingsDialog(QDialog, WidgetMixin):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app           = app
        self._original_size = get_font_size()
        self._notice_labels = []  # لافتات "اختر شركة نشطة" — تتبنى ديناميكياً

        self.setWindowTitle(tr("settings_title"))
        self.setMinimumWidth(SETTINGS_DLG_MIN_W)
        self.setMinimumHeight(SETTINGS_DLG_MIN_H)
        self.setModal(True)
        self._build()
        self._slider.setValue(self._original_size)
        self._init_widget_mixin(theme=True, font=True, lang=True)
        self._refresh_style()
        self._refresh_lang()
        self._load_settings()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(*MARGIN_ZERO)
        outer.setSpacing(SPACING_ZERO)

        self._tabs = QTabWidget()

        self._tabs.addTab(self._build_font_tab(),    tr("settings_tab_font"))
        self._tabs.addTab(self._build_theme_tab(),   tr("settings_tab_theme"))
        self._tabs.addTab(self._build_lang_tab(),    tr("settings_tab_lang"))
        self._tabs.addTab(self._build_units_tab(),   tr("settings_tab_units"))
        self._tabs.addTab(self._build_gimp_tab(),    tr("settings_tab_gimp"))
        outer.addWidget(self._tabs, stretch=1)

        self._btn_bar = QWidget()
        btn_bar_lay = QHBoxLayout(self._btn_bar)
        btn_bar_lay.setContentsMargins(*SETTINGS_BTN_BAR_MARGINS)

        btns       = QDialogButtonBox()
        self._btn_ok_bar     = btns.addButton(tr("settings_btn_save"),   QDialogButtonBox.AcceptRole)
        self._btn_cancel_bar = btns.addButton(tr("settings_btn_cancel"), QDialogButtonBox.RejectRole)
        btn_ok     = self._btn_ok_bar
        btn_cancel = self._btn_cancel_bar
        btn_ok.setMinimumHeight(DIALOG_BTN_MIN_H)
        btn_cancel.setMinimumHeight(DIALOG_BTN_MIN_H)
        btn_ok.clicked.connect(self._save)
        btn_cancel.clicked.connect(self._cancel)
        btn_bar_lay.addWidget(btns)
        outer.addWidget(self._btn_bar)

    def _refresh_style(self, *_):
        base = get_font_size()

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
                padding: {SETTINGS_TAB_PAD_V}px {SETTINGS_TAB_PAD_H}px; min-width: {SETTINGS_TAB_MIN_W}px;
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

        self._btn_bar.setStyleSheet(
            f"background:{_C['bg_surface']}; border-top:1px solid {_C['border']};"
        )

        self._refresh_font_tab_style()
        self._refresh_theme_tab_style()
        self._refresh_lang_tab_style()
        self._refresh_units_tab_style()
        self._refresh_gimp_tab_style()
        self._refresh_notice_labels_style()

    # ══════════════════════════════════════════════════════
    # تبويب الخط
    # ══════════════════════════════════════════════════════

    def _build_font_tab(self) -> QWidget:
        base   = get_font_size()
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(*SETTINGS_TAB_MARGINS)
        lay.setSpacing(SPACING_LG)

        grp = QGroupBox(tr("settings_grp_font"))
        grp_lay = QVBoxLayout(grp)

        row = QHBoxLayout()
        row.setSpacing(SPACING_MD)

        self._lbl_small = QLabel(tr("settings_font_sample_small"))

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(MIN_FONT_SIZE, MAX_FONT_SIZE)
        self._slider.setTickInterval(1)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.valueChanged.connect(self._on_font_change)

        self._lbl_big = QLabel(tr("settings_font_sample_big"))

        self._lbl_val = QLabel(tr("font_pt_suffix", size=base))
        self._lbl_val.setMinimumWidth(SETTINGS_VAL_LBL_MIN_W)
        self._lbl_val.setAlignment(Qt.AlignCenter)

        row.addWidget(self._lbl_small)
        row.addWidget(self._slider, stretch=1)
        row.addWidget(self._lbl_big)
        row.addSpacing(SPACING_MD)
        row.addWidget(self._lbl_val)
        grp_lay.addLayout(row)

        self._preview = QLabel(tr("settings_font_preview"))
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setWordWrap(True)
        grp_lay.addWidget(self._preview)

        self._lbl_font_hint = QLabel(tr("settings_font_hint"))
        self._lbl_font_hint.setWordWrap(True)
        grp_lay.addWidget(self._lbl_font_hint)
        lay.addWidget(grp)
        lay.addStretch()
        return widget

    def _refresh_font_tab_style(self):
        base = get_font_size()
        self._lbl_small.setStyleSheet(f"font-size: {fs(base, -2)}pt;")
        self._lbl_big.setStyleSheet(f"font-size: {fs(base, +4)}pt; font-weight: bold;")
        # المعاينة بتعكس قيمة الـ slider الحالية (قد تكون مختلفة عن
        # get_font_size() لو المستخدم بيجرب قيم لسه ما حفظهاش)
        preview_size = self._slider.value() if hasattr(self, "_slider") else base
        self._preview.setStyleSheet(
            f"font-size: {preview_size}pt;"
            f"border: 1px solid {_C['border']}; border-radius: {SETTINGS_PREVIEW_RADIUS}px;"
            f"padding: {SETTINGS_PREVIEW_PAD}px; background:{_C['bg_surface']}; color:{_C['text_primary']};"
        )
        self._lbl_font_hint.setStyleSheet(
            f"color:{_C['text_muted']}; font-size: {fs(base, -2)}pt; background: transparent;"
        )

    # ══════════════════════════════════════════════════════
    # تبويب الثيم
    # ══════════════════════════════════════════════════════

    def _build_theme_tab(self) -> QWidget:
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(*SETTINGS_TAB_MARGINS)
        lay.setSpacing(SPACING_LG)

        grp     = QGroupBox(tr("settings_grp_theme"))
        grp_lay = QVBoxLayout(grp)
        grp_lay.setSpacing(SPACING_MD_LG)

        from ui.theme_manager import theme_manager, THEMES

        self._theme_btn_group = QButtonGroup(self)
        self._theme_radios    = {}
        self._theme_cards     = []
        current = theme_manager.current_theme

        themes_info = {
            "light": (tr("icon_theme_light"), tr("settings_theme_light_name"), tr("settings_theme_light_desc")),
            "dark":  (tr("icon_theme_dark"),  tr("settings_theme_dark_name"),  tr("settings_theme_dark_desc")),
        }

        for key, (icon, name, desc) in themes_info.items():
            card = self._make_theme_card(icon, name, desc, key == current)
            radio = card.findChild(QRadioButton)
            if radio:
                self._theme_btn_group.addButton(radio)
                self._theme_radios[key] = radio
            grp_lay.addWidget(card)

        lay.addWidget(grp)

        preview_grp     = QGroupBox(tr("settings_grp_theme_preview"))
        preview_grp_lay = QHBoxLayout(preview_grp)
        preview_grp_lay.setSpacing(SPACING_SM)

        self._color_swatches = []
        swatch_info = [
            ("accent",       tr("swatch_label_accent")),
            ("success",      tr("swatch_label_success")),
            ("warning",      tr("swatch_label_warning")),
            ("danger",       tr("swatch_label_danger")),
            ("bg_surface",   tr("swatch_label_surface")),
            ("text_primary", tr("swatch_label_text")),
        ]
        for key, display_label in swatch_info:
            swatch = QFrame()
            swatch.setFixedSize(SETTINGS_SWATCH_SIZE, SETTINGS_SWATCH_SIZE)
            self._color_swatches.append((swatch, key, display_label))
            preview_grp_lay.addWidget(swatch)

        preview_grp_lay.addStretch()
        lay.addWidget(preview_grp)
        lay.addStretch()
        return widget

    def _make_theme_card(self, icon: str, name: str,
                          desc: str, is_selected: bool) -> QWidget:
        card  = QFrame()
        lay   = QHBoxLayout(card)
        lay.setContentsMargins(*SETTINGS_CARD_MARGINS)
        lay.setSpacing(SPACING_LG)

        radio = QRadioButton()
        radio.setChecked(is_selected)
        lay.addWidget(radio)

        lbl_icon = QLabel(icon)
        lay.addWidget(lbl_icon)

        text_col = QVBoxLayout()
        text_col.setSpacing(DIALOG_HDR_COL_SPACING)
        lbl_name = QLabel(name)
        lbl_desc = QLabel(desc)
        text_col.addWidget(lbl_name)
        text_col.addWidget(lbl_desc)
        lay.addLayout(text_col)
        lay.addStretch()

        self._theme_cards.append((card, lbl_icon, lbl_name, lbl_desc))
        return card

    def _refresh_theme_tab_style(self):
        base = get_font_size()
        for card, lbl_icon, lbl_name, lbl_desc in self._theme_cards:
            card.setStyleSheet(
                f"QFrame {{ background:{_C['bg_surface_2']}; border-radius:{SETTINGS_CARD_RADIUS}px;"
                f"border:1px solid {_C["border"]}; padding:{SETTINGS_CARD_INNER_PAD}px; }}"
            )
            lbl_icon.setStyleSheet(f"font-size:{fs(base, +4)}pt; background:transparent;")
            lbl_name.setStyleSheet(
                f"font-weight:700; font-size:{fs(base, +1)}pt; background:transparent;"
            )
            lbl_desc.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt; background:transparent;"
            )

        for swatch, key, display_label in self._color_swatches:
            color = _C[key]
            swatch.setStyleSheet(
                f"background:{color}; border-radius:{SETTINGS_SWATCH_RADIUS}px; "
                f"border:1px solid {_C['border']};"
            )
            swatch.setToolTip(f"{display_label}: {color}")

    def _get_selected_theme(self) -> str:
        for key, radio in self._theme_radios.items():
            if radio.isChecked():
                return key
        return "light"

    # ══════════════════════════════════════════════════════
    # تبويب اللغة
    # ══════════════════════════════════════════════════════

    def _build_lang_tab(self) -> QWidget:
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(*SETTINGS_TAB_MARGINS)
        lay.setSpacing(SPACING_LG)

        grp     = QGroupBox(tr("settings_grp_lang"))
        grp_lay = QVBoxLayout(grp)
        grp_lay.setSpacing(SPACING_MD_LG)

        try:
            from ui.widgets.core.i18n import i18n_manager
            current_lang = i18n_manager.language
        except Exception:
            current_lang = "ar"

        self._lang_btn_group = QButtonGroup(self)
        self._lang_radios    = {}
        self._lang_cards     = []

        langs_info = {
            "ar": (tr("icon_flag_ar"), tr("settings_lang_ar_name"), tr("settings_lang_ar_desc")),
            "en": (tr("icon_flag_en"), tr("settings_lang_en_name"), tr("settings_lang_en_desc")),
        }

        for key, (flag, name, desc) in langs_info.items():
            card  = QFrame()
            cLay  = QHBoxLayout(card)
            cLay.setContentsMargins(*SETTINGS_CARD_MARGINS)
            cLay.setSpacing(SPACING_LG)

            radio = QRadioButton()
            radio.setChecked(key == current_lang)
            self._lang_btn_group.addButton(radio)
            self._lang_radios[key] = radio
            cLay.addWidget(radio)

            lbl_flag = QLabel(flag)
            cLay.addWidget(lbl_flag)

            text_col = QVBoxLayout()
            text_col.setSpacing(DIALOG_HDR_COL_SPACING)
            lbl_name = QLabel(name)
            lbl_desc = QLabel(desc)
            text_col.addWidget(lbl_name)
            text_col.addWidget(lbl_desc)
            cLay.addLayout(text_col)
            cLay.addStretch()

            self._lang_cards.append((card, lbl_flag, lbl_name, lbl_desc))
            grp_lay.addWidget(card)

        lay.addWidget(grp)

        self._lbl_lang_hint = QLabel(tr("settings_lang_hint"))
        self._lbl_lang_hint.setWordWrap(True)
        lay.addWidget(self._lbl_lang_hint)
        lay.addStretch()
        return widget

    def _refresh_lang_tab_style(self):
        base = get_font_size()
        for card, lbl_flag, lbl_name, lbl_desc in self._lang_cards:
            card.setStyleSheet(
                f"QFrame {{ background:{_C['bg_surface_2']}; border-radius:{SETTINGS_CARD_RADIUS}px;"
                f"border:1px solid {_C["border"]}; padding:{SETTINGS_CARD_INNER_PAD}px; }}"
            )
            lbl_flag.setStyleSheet(
                f"font-size:{fs(base, +4)}pt; background:transparent;"
            )
            lbl_name.setStyleSheet(
                f"font-weight:700; font-size:{fs(base, +1)}pt; background:transparent;"
            )
            lbl_desc.setStyleSheet(
                f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt; background:transparent;"
            )
        self._lbl_lang_hint.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -1)}pt; background:transparent;"
        )

    def _get_selected_lang(self) -> str:
        for key, radio in self._lang_radios.items():
            if radio.isChecked():
                return key
        return "ar"

    # ══════════════════════════════════════════════════════
    # تبويب الوحدات
    # ══════════════════════════════════════════════════════

    def _build_units_tab(self) -> QWidget:
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(*SETTINGS_TAB_MARGINS)
        lay.setSpacing(SPACING_LG)

        grp     = QGroupBox(tr("settings_grp_units"))
        grp_lay = QVBoxLayout(grp)

        self._units_list = QListWidget()
        self._units_list.setAlternatingRowColors(True)
        self._units_list.setMinimumHeight(SETTINGS_UNITS_LIST_MIN_H)
        grp_lay.addWidget(self._units_list)

        btn_row = QHBoxLayout()
        btn_add   = make_btn(tr("settings_btn_add_unit"),   "primary")
        btn_del   = make_btn(tr("settings_btn_del_unit"),   "danger")
        btn_reset = make_btn(tr("settings_btn_reset_units"), "ghost")
        btn_add.clicked.connect(self._add_unit)
        btn_del.clicked.connect(self._del_unit)
        btn_reset.clicked.connect(self._reset_units)
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_del)
        btn_row.addWidget(btn_reset)
        btn_row.addStretch()
        grp_lay.addLayout(btn_row)

        self._lbl_units_hint = QLabel(tr("settings_units_hint"))
        self._lbl_units_hint.setWordWrap(True)
        grp_lay.addWidget(self._lbl_units_hint)
        lay.addWidget(grp)
        lay.addStretch()
        return widget

    def _refresh_units_tab_style(self):
        base = get_font_size()
        # [إصلاح ثيم] self._units_list كانت من غير setStyleSheet خالص —
        # كانت بتاخد default Qt palette، وبما إنها setAlternatingRowColors(True)
        # كان بيطلع نمط zebra عشوائي (صف أبيض/صف داكن) مهما كان الثيم الحالي.
        from ..theme.layout_styles import list_style
        self._units_list.setStyleSheet(list_style())
        self._lbl_units_hint.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -2)}pt; background:transparent;"
        )

    # ══════════════════════════════════════════════════════
    # تبويب GIMP
    # ══════════════════════════════════════════════════════

    def _build_gimp_tab(self) -> QWidget:
        widget = QWidget()
        lay    = QVBoxLayout(widget)
        lay.setContentsMargins(*SETTINGS_TAB_MARGINS)
        lay.setSpacing(SPACING_LG)

        grp     = QGroupBox(tr("settings_grp_gimp"))
        grp_lay = QVBoxLayout(grp)

        self._inp_gimp = ThemedLineEdit()
        self._inp_gimp.setMinimumHeight(BTN_MIN_HEIGHT)
        self._inp_gimp.setPlaceholderText(tr("settings_gimp_placeholder"))

        gimp_row = QHBoxLayout()
        btn_browse = make_btn(tr("settings_btn_browse"), "normal")
        btn_clear  = make_btn(tr("clear"),               "ghost")
        btn_clear.setFixedWidth(SETTINGS_CLEAR_BTN_W)
        btn_browse.clicked.connect(self._browse_gimp)
        btn_clear.clicked.connect(lambda: self._inp_gimp.clear())

        gimp_row.addWidget(self._inp_gimp, stretch=1)
        gimp_row.addWidget(btn_browse)
        gimp_row.addWidget(btn_clear)
        grp_lay.addLayout(gimp_row)

        self._lbl_gimp_hint = QLabel(tr("settings_gimp_hint"))
        self._lbl_gimp_hint.setWordWrap(True)
        grp_lay.addWidget(self._lbl_gimp_hint)
        lay.addWidget(grp)
        lay.addStretch()
        return widget

    def _refresh_gimp_tab_style(self):
        base = get_font_size()
        self._lbl_gimp_hint.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base, -2)}pt; background:transparent;"
        )
        self._inp_gimp.setStyleSheet(
            f"font-size:{fs(base, -1)}pt; color:{_C['text_primary']};"
            f"background:{_C['bg_input']}; border:1px solid {_C['border_med']};"
            f"border-radius:{SETTINGS_GIMP_INPUT_RADIUS}px; padding:{SETTINGS_GIMP_INPUT_RADIUS}px {SETTINGS_GIMP_INPUT_PAD_H}px;"
        )

    def _refresh_notice_labels_style(self):
        if not self._notice_labels:
            return
        base = get_font_size()
        from ui.widgets.core.colors import status_colors
        s = status_colors("warning")
        notice_style = (
            f"color: {s['fg']}; font-size: {fs(base, -1)}pt;"
            f"background: {s['bg']}; border: 1px solid {s['border']};"
            f"border-radius: {SETTINGS_NOTICE_RADIUS}px; padding: {SETTINGS_NOTICE_PAD_V}px {SETTINGS_NOTICE_PAD_H}px;"
        )
        for lbl in self._notice_labels:
            lbl.setStyleSheet(notice_style)
    # ══════════════════════════════════════════════════════

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
                path = SettingsService.get("gimp_path", "")
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
            f"border-radius: {SETTINGS_NOTICE_RADIUS}px; padding: {SETTINGS_NOTICE_PAD_V}px {SETTINGS_NOTICE_PAD_H}px;"
        )
        notice_text = tr("settings_no_company_notice")

        units_tab = self._tabs.widget(3)
        if units_tab:
            lbl = QLabel(notice_text)
            lbl.setWordWrap(True)
            lbl.setStyleSheet(notice_style)
            lay = units_tab.layout()
            if lay:
                lay.insertWidget(0, lbl)
            self._notice_labels.append(lbl)

        gimp_tab = self._tabs.widget(4)
        if gimp_tab:
            lbl2 = QLabel(notice_text)
            lbl2.setWordWrap(True)
            lbl2.setStyleSheet(notice_style)
            lay2 = gimp_tab.layout()
            if lay2:
                lay2.insertWidget(0, lbl2)
            self._notice_labels.append(lbl2)

    def _reload_units_list(self):
        self._units_list.clear()
        conn = _get_settings_conn()
        if conn:
            try:
                units = load_units(conn)
            except Exception:
                units = _default_units()
        else:
            units = _default_units()

        default_vals = set(_DEFAULT_UNIT_KEYS)
        for val, label in units:
            item = QListWidgetItem(label)
            item.setData(Qt.UserRole, val)
            if val in default_vals:
                from PyQt5.QtGui import QColor
                item.setForeground(QColor(_C['text_muted']))
                item.setToolTip(tr("settings_unit_default_tip"))
            self._units_list.addItem(item)

    # ══════════════════════════════════════════════════════
    # إدارة الوحدات
    # ══════════════════════════════════════════════════════

    def _add_unit(self):
        conn = _get_settings_conn()
        if not conn:
            msg_warning(self, tr("settings_warning_title"), tr("settings_no_company_units"))
            return

        val, ok = QInputDialog.getText(
            self, tr("settings_add_unit_title"), tr("settings_add_unit_prompt"),
        )
        if not ok or not val.strip():
            return
        val = val.strip().lower()
        label, ok2 = QInputDialog.getText(
            self, tr("settings_add_unit_title"),
            tr("settings_add_unit_label", val=val),
            text=val,
        )
        if not ok2 or not label.strip():
            return
        try:
            result = add_unit(conn, val, label.strip())
        except Exception as e:
            msg_warning(self, tr("settings_error_title"), str(e))
            return
        if result:
            self._reload_units_list()
        else:
            msg_info(self, tr("settings_warning_title"), tr("settings_unit_exists", val=val))

    def _del_unit(self):
        item = self._units_list.currentItem()
        if not item:
            msg_info(self, tr("settings_warning_title"), tr("settings_select_unit"))
            return
        val = item.data(Qt.UserRole)
        default_vals = set(_DEFAULT_UNIT_KEYS)
        if val in default_vals:
            msg_warning(self, tr("settings_warning_title"), tr("settings_no_del_default", val=val))
            return

        conn = _get_settings_conn()
        if not conn:
            msg_warning(self, tr("settings_warning_title"), tr("settings_no_company_del"))
            return

        if confirm_action(self, tr("settings_del_unit_title"),
                          tr("settings_del_unit_msg", label=item.text()),
                          icon=tr("icon_delete_trash"), confirm_text=tr("settings_del_unit_btn"), danger=True):
            try:
                remove_unit(conn, val)
            except Exception as e:
                msg_warning(self, tr("settings_error_title"), str(e))
                return
            self._reload_units_list()

    def _reset_units(self):
        conn = _get_settings_conn()
        if not conn:
            msg_warning(self, tr("settings_warning_title"), tr("settings_no_company_reset"))
            return

        if confirm_action(self, tr("settings_reset_units_title"),
                          tr("settings_reset_units_msg"),
                          icon=tr("icon_reset"), confirm_text=tr("settings_reset_units_btn")):
            try:
                reset_units_to_default(conn)
            except Exception as e:
                msg_warning(self, tr("settings_error_title"), str(e))
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
            start_dir = SETTINGS_GIMP_DEFAULT_DIR
        path, _ = QFileDialog.getOpenFileName(
            self, tr("settings_browse_gimp"), start_dir,
            tr("settings_gimp_filter")
        )
        if path:
            self._inp_gimp.setText(path)

    # ══════════════════════════════════════════════════════
    # معاينة الخط
    # ══════════════════════════════════════════════════════

    def _on_font_change(self, val: int):
        self._lbl_val.setText(tr("font_pt_suffix", size=val))
        self._preview.setStyleSheet(
            f"font-size: {val}pt;"
            f"border: 1px solid {_C['border']}; border-radius: {SETTINGS_PREVIEW_RADIUS}px;"
            f"padding: {SETTINGS_PREVIEW_PAD}px; background:{_C['bg_surface']}; color:{_C['text_primary']};"
        )

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def _save(self):
        from ui.widgets.core.events import bus

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

        if CompanyService.is_company_ready():
            try:
                SettingsService.set("gimp_path", self._inp_gimp.text().strip())
            except Exception:
                pass

        self.accept()

    def _cancel(self):
        self.reject()

    def _refresh_lang(self, *_):
        self.setWindowTitle(tr("settings_title"))
        self._tabs.setTabText(0, tr("settings_tab_font"))
        self._tabs.setTabText(1, tr("settings_tab_theme"))
        self._tabs.setTabText(2, tr("settings_tab_lang"))
        self._tabs.setTabText(3, tr("settings_tab_units"))
        self._tabs.setTabText(4, tr("settings_tab_gimp"))
        self._btn_ok_bar.setText(tr("settings_btn_save"))
        self._btn_cancel_bar.setText(tr("settings_btn_cancel"))
        self._lbl_font_hint.setText(tr("settings_font_hint"))
        self._lbl_small.setText(tr("settings_font_sample_small"))
        self._lbl_big.setText(tr("settings_font_sample_big"))
        self._lbl_lang_hint.setText(tr("settings_lang_hint"))
        self._lbl_units_hint.setText(tr("settings_units_hint"))
        self._lbl_gimp_hint.setText(tr("settings_gimp_hint"))
        self._inp_gimp.setPlaceholderText(tr("settings_gimp_placeholder"))