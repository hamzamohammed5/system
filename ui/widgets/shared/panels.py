"""
ui/widgets/shared/panels.py
============================
مكونات UI مشتركة — re-export من refactored_widgets.

[v11 - REFACTORED]:
  كل الـ imports بقت من refactored_widgets بدل الملفات القديمة.
  هذا الملف بقى مجرد compatibility layer.
"""

# ══════════════════════════════════════════════════════════
# Core
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.core.settings import get_base, get_font_size, fs, _C  # noqa: F401
from ui.refactored_widgets.core.colors   import STATUS_COLORS                     # noqa: F401
from ui.refactored_widgets.core.conn     import (                                 # noqa: F401
    LiveConnMixin, SafeConnMixin, DualConnMixin,
)
from ui.refactored_widgets.core.events   import (                                 # noqa: F401
    get_active_company_id, emit_company_data_changed, is_same_company,
)

# ══════════════════════════════════════════════════════════
# Theme
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.theme.builders import (                                # noqa: F401
    h_divider as make_divider,
    v_divider as make_vline_sep,
)
from ui.refactored_widgets.theme.styles import (                                  # noqa: F401
    input_style        as get_input_style,
    search_input_style as get_search_input_style,
    card_style         as get_card_style,
    status_card_style  as get_status_card_style,
    group_box_style    as get_group_box_style,
    filter_bar_style   as get_filter_bar_style,
    toolbar_style      as get_toolbar_style,
    scroll_style       as get_scroll_style,
    splitter_style     as get_splitter_style,
    icon_btn_style     as get_icon_btn_style,
    link_btn_style     as get_link_btn_style,
    tab_style          as get_tab_style,
    tree_style         as get_tree_style,
    list_style         as get_list_style,
    status_label_style as get_status_label_style,
    muted_label_style  as get_muted_label_style,
    section_title_style as get_section_title_style,
    table_style        as get_table_header_style,
)

# ══════════════════════════════════════════════════════════
# Components
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.components.button        import make_btn as _make_btn, calc_btn_width as _calc_btn_width  # noqa: F401
from ui.refactored_widgets.components.badge         import BadgeLabel, StatusChip                 # noqa: F401
from ui.refactored_widgets.components.card          import StatCard                               # noqa: F401
from ui.refactored_widgets.components.label         import (                                      # noqa: F401
    InfoRow, ModeLabel, AmountLabel,
    format_amount, amount_color, dr_cr_color,
)
from ui.refactored_widgets.components.notification  import NotificationBar                        # noqa: F401
from ui.refactored_widgets.components.spinner       import (                                      # noqa: F401
    LoadingSpinner, LoadingOverlay, LoadingButton,
)
from ui.refactored_widgets.components.action_toolbar import ActionToolbar                         # noqa: F401
from ui.refactored_widgets.components.stat_row       import (                                     # noqa: F401
    StatItem, StatRow, make_stat_row, stat_card_pair,
)
from ui.refactored_widgets.components.headers        import (                                     # noqa: F401
    SearchBar, StatusBar as ListStatusBar,
    SectionHeader, ListHeader, PageHeader, DetailHeader,
    make_list_header,
)

# ══════════════════════════════════════════════════════════
# Panels
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.panels.cards      import (                             # noqa: F401
    make_stat_card_simple, make_status_chip,
)
from ui.refactored_widgets.panels.display    import (                             # noqa: F401
    DebitCreditDisplay, BalanceDisplay,
    ProgressBar, MultiProgressBar,
)
from ui.refactored_widgets.panels.notify     import BaseWarningBar                # noqa: F401
from ui.refactored_widgets.panels.state      import (                             # noqa: F401
    EmptyState, EmptyPanelState,
    set_table_empty_state, clear_table_empty_state,
)
from ui.refactored_widgets.panels.filter     import FilterToolbar                 # noqa: F401
from ui.refactored_widgets.panels.form_parts import (                             # noqa: F401
    form_label, required_label, hint_label,
    section_title as form_section_title,
    separator_line, field_row, labeled_row,
    make_form_layout, make_preview_label,
    spin_field, int_spin_field, labeled_widget,
    FormGroup, ResultBadge, ModeBadge, InlinePreview, CrudButtonsBar,
)

# ══════════════════════════════════════════════════════════
# Tables
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.tables.styles   import (                               # noqa: F401
    ROW_HEIGHT_NORMAL, ROW_HEIGHT_COMPACT, ROW_HEIGHT_LARGE,
)
from ui.refactored_widgets.tables.items    import (                               # noqa: F401
    make_table_item, bold_table_item, colored_table_item,
    center_table_item, set_row_background, color_item,
    insert_row, auto_fit_columns, calc_width as calc_table_width,
)
from ui.refactored_widgets.tables.builders import (                               # noqa: F401
    make_table      as make_detail_table,
    make_compact_table, make_list_table, make_fixed_table,
    make_splitter_table, make_splitter_table_guarded,
    fit_splitter_table,
)
from ui.refactored_widgets.tables.flexible import (                               # noqa: F401
    WrapDelegate, AutoTooltipDelegate, FlexItem,
    set_flexible_columns, make_flexible_table,
    FlexibleTreeWidget, refresh_tooltips, apply_tooltip_to_all,
)

# fit_splitter_to_table — helper إضافي
from ui.refactored_widgets.utils.splitter import fit_list_panel as fit_splitter_to_table  # noqa: F401

# ══════════════════════════════════════════════════════════
# Dialogs
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.dialogs.shell   import DialogShell as _DialogShell    # noqa: F401
from ui.refactored_widgets.dialogs.base    import BaseDialog                     # noqa: F401
from ui.refactored_widgets.dialogs.confirm import (                              # noqa: F401
    confirm_delete, confirm_action, confirm_save,
)
from ui.refactored_widgets.dialogs.message import (                              # noqa: F401
    msg_question, msg_info, msg_warning, msg_critical,
)

# ══════════════════════════════════════════════════════════
# Combo
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.combo.category import CategoryCombo                   # noqa: F401
from ui.refactored_widgets.combo.unit     import UnitCombo, make_unit_combo      # noqa: F401

# ══════════════════════════════════════════════════════════
# Forms / Inputs
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.forms.inputs import (                                 # noqa: F401
    SearchLineEdit, AmountSpinBox, DateField,
    StyledComboBox, LabeledInput, RequiredLineEdit, NotesLineEdit,
)

# ══════════════════════════════════════════════════════════
# Helpers
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.helpers.color_picker import ColorPickerWidget         # noqa: F401
from ui.refactored_widgets.utils.flow_layout    import FlowLayout                # noqa: F401
from ui.refactored_widgets.utils.date_range     import DateRangeFilter           # noqa: F401
from ui.refactored_widgets.utils.no_wheel       import (                         # noqa: F401
    NoWheelCombo, NoWheelSpin, NoWheelDouble,
    NoWheelDate, NoWheelSlider, install_no_wheel_filter,
)
from ui.refactored_widgets.utils.scroll         import (                         # noqa: F401
    wrap_in_scroll, ScrollableFormWidget,
)
from ui.refactored_widgets.utils.scrollable_form import build_inner_scroll       # noqa: F401
from ui.refactored_widgets.utils.tooltip         import (                        # noqa: F401
    apply_table_tooltips, apply_tree_tooltips,
)
from ui.refactored_widgets.utils.searchable_combo import (                       # noqa: F401
    SearchableCombo as _SearchableCombo,
    build_grouped_items as _build_grouped_items,
)

# ══════════════════════════════════════════════════════════
# Mixins
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.mixins.bus        import BusConnectedMixin            # noqa: F401
from ui.refactored_widgets.mixins.edit       import EditModeMixin                # noqa: F401  (via helpers.py)
from ui.refactored_widgets.mixins.validate   import FormValidationMixin          # noqa: F401
from ui.refactored_widgets.mixins.select     import SelectionMixin               # noqa: F401
from ui.refactored_widgets.mixins.refresh    import RefreshableMixin             # noqa: F401
from ui.refactored_widgets.mixins.rebuild    import RebuildMixin                 # noqa: F401
from ui.refactored_widgets.mixins.shared_ops import SharedOpsMixin               # noqa: F401

# ══════════════════════════════════════════════════════════
# Base Panels
# ══════════════════════════════════════════════════════════
from ui.refactored_widgets.base.list_panel   import BaseListPanel                # noqa: F401
from ui.refactored_widgets.base.detail_panel import BaseDetailPanel              # noqa: F401
from ui.refactored_widgets.base.crud_form    import BaseCrudForm                 # noqa: F401
from ui.refactored_widgets.base.section      import BaseSection                  # noqa: F401

# ══════════════════════════════════════════════════════════
# Tab utilities
# ══════════════════════════════════════════════════════════

def make_tabs(*tab_defs, accent: str = "#1565c0", style: str = "main"):
    from PyQt5.QtWidgets import QTabWidget
    from ui.refactored_widgets.theme.styles import tab_style
    tabs = QTabWidget()
    if style == "inner":
        tabs.setStyleSheet(tab_style(accent=accent, size="small"))
    elif style in ("financial", "minimal"):
        tabs.setStyleSheet(
            f"QTabBar::tab:selected {{ color:{accent}; border-top:2px solid {accent}; }}"
        )
    else:
        tabs.setStyleSheet(tab_style(accent=accent, size="normal"))
    for label, widget in tab_defs:
        tabs.addTab(widget, label)
    return tabs


def make_inner_tabs(*tab_defs, accent: str = "#1565c0"):
    return make_tabs(*tab_defs, accent=accent, style="inner")


def make_financial_tabs(*tab_defs, accent: str = "#1565c0"):
    return make_tabs(*tab_defs, accent=accent, style="financial")


# ══════════════════════════════════════════════════════════
# CrudSection (لا يزال في panles_helper — سيُنقل لاحقاً)
# ══════════════════════════════════════════════════════════
from .panles_helper.crud_section   import CrudSection                # noqa: F401
from .panles_helper.detail_section import (                          # noqa: F401
    DetailSection, TwoColDetails, make_detail_row,
)
from .panles_helper.card_grid      import CardGrid                   # noqa: F401
from .panles_helper.collapsible_card import CollapsibleCard          # noqa: F401
from .panles_helper.status_chip    import make_stat_card_simple as _msc  # noqa: F401 compat
from .panles_helper.page_header    import PageHeader as _PageHeader_old  # noqa: F401 compat

# ══════════════════════════════════════════════════════════
# __all__
# ══════════════════════════════════════════════════════════
__all__ = [
    # core
    "get_active_company_id", "emit_company_data_changed", "is_same_company",
    "LiveConnMixin", "SafeConnMixin", "DualConnMixin",
    "STATUS_COLORS",

    # theme
    "get_input_style", "get_search_input_style", "get_card_style",
    "get_status_card_style", "get_table_header_style", "get_group_box_style",
    "get_filter_bar_style", "get_toolbar_style", "get_scroll_style",
    "get_splitter_style", "get_icon_btn_style", "get_link_btn_style",
    "get_tab_style", "get_tree_style", "get_list_style",
    "get_status_label_style", "get_muted_label_style", "get_section_title_style",

    # components
    "_make_btn", "_calc_btn_width",
    "BadgeLabel", "StatusChip", "StatCard",
    "InfoRow", "ModeLabel", "AmountLabel",
    "format_amount", "amount_color", "dr_cr_color",
    "NotificationBar", "LoadingSpinner", "LoadingOverlay", "LoadingButton",
    "ActionToolbar", "StatItem", "StatRow", "make_stat_row", "stat_card_pair",
    "SearchBar", "ListStatusBar", "SectionHeader", "ListHeader",
    "PageHeader", "DetailHeader", "make_list_header",

    # panels
    "make_stat_card_simple", "make_status_chip",
    "DebitCreditDisplay", "BalanceDisplay", "ProgressBar", "MultiProgressBar",
    "BaseWarningBar", "EmptyState", "EmptyPanelState",
    "set_table_empty_state", "clear_table_empty_state",
    "FilterToolbar",
    "form_label", "required_label", "hint_label", "form_section_title",
    "separator_line", "field_row", "labeled_row",
    "make_form_layout", "make_preview_label",
    "spin_field", "int_spin_field", "labeled_widget",
    "FormGroup", "ResultBadge", "ModeBadge", "InlinePreview", "CrudButtonsBar",

    # tables
    "ROW_HEIGHT_NORMAL", "ROW_HEIGHT_COMPACT", "ROW_HEIGHT_LARGE",
    "make_table_item", "bold_table_item", "colored_table_item",
    "center_table_item", "set_row_background", "color_item",
    "insert_row", "auto_fit_columns", "calc_table_width",
    "make_detail_table", "make_compact_table", "make_list_table",
    "make_fixed_table", "make_splitter_table", "make_splitter_table_guarded",
    "fit_splitter_table", "fit_splitter_to_table",
    "WrapDelegate", "AutoTooltipDelegate", "FlexItem",
    "set_flexible_columns", "make_flexible_table",
    "FlexibleTreeWidget", "refresh_tooltips", "apply_tooltip_to_all",

    # dialogs
    "_DialogShell", "BaseDialog",
    "confirm_delete", "confirm_action", "confirm_save",
    "msg_question", "msg_info", "msg_warning", "msg_critical",

    # combo
    "CategoryCombo", "UnitCombo", "make_unit_combo",

    # inputs
    "SearchLineEdit", "AmountSpinBox", "DateField",
    "StyledComboBox", "LabeledInput", "RequiredLineEdit", "NotesLineEdit",

    # helpers
    "ColorPickerWidget", "FlowLayout", "DateRangeFilter",
    "NoWheelCombo", "NoWheelSpin", "NoWheelDouble",
    "NoWheelDate", "NoWheelSlider", "install_no_wheel_filter",
    "wrap_in_scroll", "ScrollableFormWidget", "build_inner_scroll",
    "apply_table_tooltips", "apply_tree_tooltips",

    # mixins
    "BusConnectedMixin", "EditModeMixin", "FormValidationMixin",
    "SelectionMixin", "RefreshableMixin", "RebuildMixin", "SharedOpsMixin",

    # base panels
    "BaseListPanel", "BaseDetailPanel", "BaseCrudForm", "BaseSection",

    # tabs
    "make_tabs", "make_inner_tabs", "make_financial_tabs",

    # panles_helper (لا تزال قيد الانتقال)
    "CrudSection", "DetailSection", "TwoColDetails", "make_detail_row",
    "CardGrid", "CollapsibleCard",
]