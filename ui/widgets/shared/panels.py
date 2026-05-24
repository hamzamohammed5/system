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

  --- إضافات لتسهيل الاستيراد ---
  FormGroup, labeled_widget, spin_field, ResultBadge, ModeBadge,
  build_inner_scroll, CrudButtonsBar,
  LiveConnMixin,
  BaseDialog,
  wrap_in_scroll, ScrollableFormWidget,
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

# ── connection ────────────────────────────────────────────
from .connection_mixin import LiveConnMixin                     # noqa: F401

# ── dialog ───────────────────────────────────────────────
from .dialog_base import BaseDialog                             # noqa: F401

# ── scroll ───────────────────────────────────────────────
from .scrollable_form import wrap_in_scroll, ScrollableFormWidget  # noqa: F401

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
    # connection
    "LiveConnMixin",
    # dialog
    "BaseDialog",
    # scroll
    "wrap_in_scroll", "ScrollableFormWidget",
]
