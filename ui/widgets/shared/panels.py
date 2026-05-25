"""
ui/widgets/shared/panels.py
============================
مكونات UI مشتركة — re-export من panles_helper وملفات أخرى.

[تحديث v10]:
  - AccountTypeFilter انتقل لـ ui/tabs/accounting/accounts_combo_widget.py
  - ScenarioComparisonWidget انتقل لـ ui/tabs/costing/scenario_comparison_widget.py
"""

from .panles_helper.detail_header    import DetailHeader        # noqa: F401
from .panles_helper.stat_card        import StatCard            # noqa: F401
from .panles_helper.section_header   import SectionHeader       # noqa: F401
from .panles_helper.empty_state      import EmptyState          # noqa: F401
from .panles_helper.collapsible_card import CollapsibleCard     # noqa: F401
from .panles_helper.action_toolbar   import ActionToolbar       # noqa: F401
from .panles_helper.badge_label      import BadgeLabel          # noqa: F401
from .panles_helper.info_row         import InfoRow             # noqa: F401
from .panles_helper.make_btn         import _make_btn, _calc_btn_width  # noqa: F401
from .panles_helper.card_grid        import CardGrid            # noqa: F401
from .panles_helper.status_chip      import (                   # noqa: F401
    StatusChip,
    make_stat_card_simple,
    make_status_chip,
)
from .panles_helper.notification_bar import NotificationBar     # noqa: F401
from .panles_helper.page_header      import PageHeader          # noqa: F401

# ── theme ──────────────────────────────────────────────────
from .panles_helper.theme import (                              # noqa: F401
    STATUS_COLORS,
    get_input_style,
    get_search_input_style,
    get_card_style,
    get_status_card_style,
    get_table_header_style,
    get_group_box_style,
    get_filter_bar_style,
    get_toolbar_style,
    get_scroll_style,
    get_splitter_style,
    get_icon_btn_style,
    get_link_btn_style,
    get_tab_style,
    get_tree_style,
    get_list_style,
    get_status_label_style,
    get_muted_label_style,
    get_section_title_style,
)

# ── list_header ────────────────────────────────────────────
from .panles_helper.list_header import (                        # noqa: F401
    ListHeader,
    SearchBar,
    StatusBar as ListStatusBar,
    make_list_header,
)

# ── form_row ───────────────────────────────────────────────
from .panles_helper.form_row import (                           # noqa: F401
    form_label,
    required_label,
    hint_label,
    section_title as form_section_title,
    separator_line,
    field_row,
    labeled_row,
    make_form_layout,
    make_preview_label,
)

# ── mode_label ─────────────────────────────────────────────
from .panles_helper.mode_label import ModeLabel                 # noqa: F401

# ── amount_display ─────────────────────────────────────────
from .panles_helper.amount_display import (                     # noqa: F401
    AmountLabel,
    DebitCreditDisplay,
    BalanceDisplay,
    format_amount,
    amount_color,
    dr_cr_color,
)

# ── stat_row ───────────────────────────────────────────────
from .stat_row import (                                         # noqa: F401
    StatRow,
    StatItem,
    make_stat_row,
    stat_card_pair,
)

# ── tab_builder ────────────────────────────────────────────
from .tab_builder import (                                      # noqa: F401
    make_tabs,
    make_inner_tabs,
    make_financial_tabs,
)

# ── form_utils ─────────────────────────────────────────────
from .form_utils import (                                       # noqa: F401
    FormGroup,
    labeled_widget,
    spin_field,
    int_spin_field,
    ResultBadge,
    ModeBadge,
    build_inner_scroll,
    CrudButtonsBar,
    InlinePreview,
)

# ── base forms & panels ────────────────────────────────────
from .base_crud_form    import BaseCrudForm                     # noqa: F401
from .base_list_panel   import BaseListPanel                    # noqa: F401
from .base_detail_panel import BaseDetailPanel                  # noqa: F401
from .base_section      import BaseSection                      # noqa: F401
from .tab_section_base  import TabSectionBase                   # noqa: F401

# ── CrudSection ────────────────────────────────────────────
from .panles_helper.crud_section import CrudSection             # noqa: F401

# ── FilterToolbar ──────────────────────────────────────────
from .panles_helper.filter_toolbar import FilterToolbar         # noqa: F401

# ── DetailSection ──────────────────────────────────────────
from .panles_helper.detail_section import (                     # noqa: F401
    DetailSection,
    TwoColDetails,
    make_detail_row,
)

# ── connection ─────────────────────────────────────────────
from .connection_mixin import LiveConnMixin                     # noqa: F401
from .safe_conn_mixin  import DualConnMixin, SafeConnMixin      # noqa: F401

# ── company utils ─────────────────────────────────────────
from .company_utils import (                                    # noqa: F401
    get_active_company_id,
    emit_company_data_changed,
    is_same_company,
)

# ── dialog ────────────────────────────────────────────────
from .dialog_base      import BaseDialog                        # noqa: F401

# ── confirm_dialog ─────────────────────────────────────────
from .confirm_dialog   import (                                 # noqa: F401
    confirm_delete,
    confirm_action,
    confirm_save,
)

# ── scroll ────────────────────────────────────────────────
from .scrollable_form import wrap_in_scroll, ScrollableFormWidget  # noqa: F401

# ── flexible text ─────────────────────────────────────────
from .flexible_text import (                                    # noqa: F401
    WrapDelegate,
    AutoTooltipDelegate,
    set_flexible_columns,
    make_flexible_table,
    FlexibleTreeWidget,
    FlexItem,
    refresh_tooltips,
    apply_tooltip_to_all,
)

# ── no-wheel ──────────────────────────────────────────────
from .no_wheel import (                                         # noqa: F401
    NoWheelCombo,
    NoWheelSpin,
    NoWheelDouble,
    NoWheelDate,
    NoWheelSlider,
    install_no_wheel_filter,
)

# ── وحدات ─────────────────────────────────────────────────
from .unit_combo import UnitCombo, make_unit_combo              # noqa: F401

# ── layout ────────────────────────────────────────────────
from .flow_layout import FlowLayout                             # noqa: F401

# ── color picker ──────────────────────────────────────────
from .color_picker_widget import ColorPickerWidget              # noqa: F401

# ── date range filter ─────────────────────────────────────
from .date_range_filter import DateRangeFilter                  # noqa: F401

# ── loading ───────────────────────────────────────────────
from .loading_spinner import (                                  # noqa: F401
    LoadingSpinner,
    LoadingOverlay,
    LoadingButton,
)

# ── empty state helpers ───────────────────────────────────
from .empty_state_helpers import (                              # noqa: F401
    set_table_empty_state,
    clear_table_empty_state,
    EmptyPanelState,
)

# ── warning bar ───────────────────────────────────────────
from .base_warning_bar import BaseWarningBar                    # noqa: F401

# ── tooltip helpers ───────────────────────────────────────
from .tooltip_helper import (                                   # noqa: F401
    apply_table_tooltips,
    apply_tree_tooltips,
)

# ── shared ops mixin ──────────────────────────────────────
from .shared_ops_mixin import SharedOpsMixin                    # noqa: F401

# ── rebuild mixin ──────────────────────────────────────────
from .rebuild_mixin import RebuildMixin                         # noqa: F401

# ── table utils shortcuts ─────────────────────────────────
from .table_utils import (                                      # noqa: F401
    make_detail_table,
    make_compact_table,
    make_list_table,
    make_fixed_table,
    make_splitter_table,
    make_splitter_table_guarded,
    bold_table_item,
    colored_table_item,
    center_table_item,
    set_row_background,
    make_table_item,
    insert_row,
    auto_fit_columns,
    fit_splitter_table,
    fit_splitter_to_table,
    ROW_HEIGHT_NORMAL,
    ROW_HEIGHT_COMPACT,
    ROW_HEIGHT_LARGE,
    calc_table_width,
)

# ── shared UI mixins ──────────────────────────────────────
from .shared_ui_mixins import (                                 # noqa: F401
    RefreshableMixin,
    BusConnectedMixin,
    SelectionMixin,
    FormValidationMixin,
)

# ── input widgets ─────────────────────────────────────────
from .input_widgets import (                                    # noqa: F401
    SearchLineEdit,
    AmountSpinBox,
    DateField,
    LabeledInput,
    RequiredLineEdit,
    StyledComboBox,
    NotesLineEdit,
)

from .panles_helper.progress_bar import (                       # noqa: F401
    ProgressBar,
    MultiProgressBar,
)

# ── data_table_widget ──────────────────────────────────────
from .panles_helper.data_table_widget import DataTableWidget    # noqa: F401

__all__ = [
    # panles_helper
    "DetailHeader", "StatCard", "SectionHeader", "EmptyState",
    "CollapsibleCard", "ActionToolbar", "BadgeLabel", "InfoRow",
    "_make_btn", "_calc_btn_width", "CardGrid", "StatusChip",
    "make_stat_card_simple", "make_status_chip",
    "NotificationBar", "PageHeader",

    # theme
    "STATUS_COLORS",
    "get_input_style", "get_search_input_style",
    "get_card_style", "get_status_card_style",
    "get_table_header_style", "get_group_box_style",
    "get_filter_bar_style", "get_toolbar_style",
    "get_scroll_style", "get_splitter_style",
    "get_icon_btn_style", "get_link_btn_style",
    "get_tab_style", "get_tree_style", "get_list_style",
    "get_status_label_style", "get_muted_label_style",
    "get_section_title_style",

    # list_header
    "ListHeader", "SearchBar", "ListStatusBar", "make_list_header",

    # form_row
    "form_label", "required_label", "hint_label",
    "form_section_title", "separator_line",
    "field_row", "labeled_row", "make_form_layout", "make_preview_label",

    # mode_label
    "ModeLabel",

    # amount_display
    "AmountLabel", "DebitCreditDisplay", "BalanceDisplay",
    "format_amount", "amount_color", "dr_cr_color",

    # stat_row
    "StatRow", "StatItem", "make_stat_row", "stat_card_pair",

    # tab_builder
    "make_tabs", "make_inner_tabs", "make_financial_tabs",

    # form_utils
    "FormGroup", "labeled_widget", "spin_field", "int_spin_field",
    "ResultBadge", "ModeBadge", "build_inner_scroll",
    "CrudButtonsBar", "InlinePreview",

    # base forms & panels
    "BaseCrudForm", "BaseListPanel", "BaseDetailPanel",
    "BaseSection", "TabSectionBase",

    # CrudSection
    "CrudSection",

    # FilterToolbar
    "FilterToolbar",

    # DetailSection
    "DetailSection", "TwoColDetails", "make_detail_row",

    # connection
    "LiveConnMixin", "DualConnMixin", "SafeConnMixin",

    # company utils
    "get_active_company_id", "emit_company_data_changed", "is_same_company",

    # dialog
    "BaseDialog",

    # confirm_dialog
    "confirm_delete", "confirm_action", "confirm_save",

    # scroll
    "wrap_in_scroll", "ScrollableFormWidget",

    # flexible_text
    "WrapDelegate", "AutoTooltipDelegate",
    "set_flexible_columns", "make_flexible_table",
    "FlexibleTreeWidget", "FlexItem",
    "refresh_tooltips", "apply_tooltip_to_all",

    # no_wheel
    "NoWheelCombo", "NoWheelSpin", "NoWheelDouble",
    "NoWheelDate", "NoWheelSlider", "install_no_wheel_filter",

    # unit_combo
    "UnitCombo", "make_unit_combo",

    # flow_layout
    "FlowLayout",

    # color_picker
    "ColorPickerWidget",

    # date_range_filter
    "DateRangeFilter",

    # loading
    "LoadingSpinner", "LoadingOverlay", "LoadingButton",

    # empty_state_helpers
    "set_table_empty_state", "clear_table_empty_state", "EmptyPanelState",

    # warning_bar
    "BaseWarningBar",

    # tooltip_helper
    "apply_table_tooltips", "apply_tree_tooltips",

    # shared_ops_mixin
    "SharedOpsMixin",

    # rebuild_mixin
    "RebuildMixin",

    # table_utils
    "make_detail_table", "make_compact_table", "make_list_table",
    "make_fixed_table",
    "make_splitter_table", "make_splitter_table_guarded",
    "bold_table_item", "colored_table_item", "center_table_item",
    "set_row_background", "make_table_item", "insert_row",
    "auto_fit_columns",
    "fit_splitter_table", "fit_splitter_to_table",
    "ROW_HEIGHT_NORMAL", "ROW_HEIGHT_COMPACT", "ROW_HEIGHT_LARGE",
    "calc_table_width",

    # shared_ui_mixins
    "RefreshableMixin", "BusConnectedMixin",
    "SelectionMixin", "FormValidationMixin",

    # input_widgets
    "SearchLineEdit", "AmountSpinBox", "DateField",
    "LabeledInput", "RequiredLineEdit", "StyledComboBox", "NotesLineEdit",

    # progress_bar
    "ProgressBar", "MultiProgressBar",

    # data_table_widget
    "DataTableWidget",
]