"""
ui/widgets/shared/panels.py
============================
مكونات UI مشتركة — re-export من panles_helper وملفات أخرى.

كل الملفات التانية تستورد من هنا مباشرة — مش من panles_helper.

المتوفر:
  DetailHeader, StatCard, SectionHeader, EmptyState,
  CollapsibleCard, ActionToolbar, BadgeLabel, InfoRow,
  _make_btn, make_stat_card_simple, make_status_chip, CardGrid,
  StatusChip,

  --- form_utils ---
  FormGroup, labeled_widget, spin_field, int_spin_field,
  ResultBadge, ModeBadge, build_inner_scroll, CrudButtonsBar, InlinePreview,

  --- base forms & panels ---
  BaseCrudForm,
  BaseListPanel,
  BaseDetailPanel,
  BaseSection,
  TabSectionBase,

  --- connection ---
  LiveConnMixin,

  --- dialog ---
  BaseDialog,

  --- scroll ---
  wrap_in_scroll, ScrollableFormWidget,

  --- جدول مرن ---
  WrapDelegate, AutoTooltipDelegate,
  set_flexible_columns, make_flexible_table,
  FlexibleTreeWidget, FlexItem, refresh_tooltips,
  apply_tooltip_to_all,

  --- no-wheel ---
  NoWheelCombo, NoWheelSpin, NoWheelDouble,
  NoWheelDate, NoWheelSlider, install_no_wheel_filter,

  --- وحدات ---
  UnitCombo, make_unit_combo,

  --- layout ---
  FlowLayout,

  --- مقارنة سيناريوهات ---
  ScenarioComparisonWidget,
"""

from .panles_helper.detail_header    import DetailHeader        # noqa: F401
from .panles_helper.stat_card        import StatCard            # noqa: F401
from .panles_helper.section_header   import SectionHeader       # noqa: F401
from .panles_helper.empty_state      import EmptyState          # noqa: F401
from .panles_helper.collapsible_card import CollapsibleCard     # noqa: F401
from .panles_helper.action_toolbar   import ActionToolbar       # noqa: F401
from .panles_helper.badge_label      import BadgeLabel          # noqa: F401
from .panles_helper.info_row         import InfoRow             # noqa: F401
from .panles_helper.make_btn         import _make_btn           # noqa: F401
from .panles_helper.card_grid        import CardGrid            # noqa: F401
from .panles_helper.status_chip      import (                   # noqa: F401
    StatusChip,
    make_stat_card_simple,
    make_status_chip,
)

# ── form_utils ────────────────────────────────────────────
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

# ── base forms & panels ───────────────────────────────────
from .base_crud_form   import BaseCrudForm                      # noqa: F401
from .base_list_panel  import BaseListPanel                     # noqa: F401
from .base_detail_panel import BaseDetailPanel                  # noqa: F401
from .base_section     import BaseSection                       # noqa: F401
from .tab_section_base import TabSectionBase                    # noqa: F401

# ── connection ────────────────────────────────────────────
from .connection_mixin import LiveConnMixin                     # noqa: F401

# ── dialog ───────────────────────────────────────────────
from .dialog_base import BaseDialog                             # noqa: F401

# ── scroll ───────────────────────────────────────────────
from .scrollable_form import wrap_in_scroll, ScrollableFormWidget  # noqa: F401

# ── جدول مرن (flexible_text) ─────────────────────────────
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

# ── no-wheel ─────────────────────────────────────────────
from .no_wheel import (                                         # noqa: F401
    NoWheelCombo,
    NoWheelSpin,
    NoWheelDouble,
    NoWheelDate,
    NoWheelSlider,
    install_no_wheel_filter,
)

# ── وحدات ────────────────────────────────────────────────
from .unit_combo import UnitCombo, make_unit_combo              # noqa: F401

# ── layout ───────────────────────────────────────────────
from .flow_layout import FlowLayout                             # noqa: F401

# ── مقارنة سيناريوهات ────────────────────────────────────
from .scenario_comparison_widget import ScenarioComparisonWidget  # noqa: F401


__all__ = [
    # panles_helper
    "DetailHeader", "StatCard", "SectionHeader", "EmptyState",
    "CollapsibleCard", "ActionToolbar", "BadgeLabel", "InfoRow",
    "_make_btn", "CardGrid", "StatusChip",
    "make_stat_card_simple", "make_status_chip",
    # form_utils
    "FormGroup", "labeled_widget", "spin_field", "int_spin_field",
    "ResultBadge", "ModeBadge", "build_inner_scroll",
    "CrudButtonsBar", "InlinePreview",
    # base forms & panels
    "BaseCrudForm",
    "BaseListPanel",
    "BaseDetailPanel",
    "BaseSection",
    "TabSectionBase",
    # connection
    "LiveConnMixin",
    # dialog
    "BaseDialog",
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
    # scenario_comparison
    "ScenarioComparisonWidget",
]