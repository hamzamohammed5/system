"""
ui/widgets/shared/panels.py
============================
مكونات UI مشتركة — re-export من panles_helper.

كل الملفات التانية تستورد من هنا مباشرة — مش من panles_helper.

المتوفر:
  DetailHeader, StatCard, SectionHeader, EmptyState,
  CollapsibleCard, ActionToolbar, BadgeLabel, InfoRow,
  _make_btn, make_stat_card_simple, make_status_chip, CardGrid
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

__all__ = [
    "DetailHeader", "StatCard", "SectionHeader", "EmptyState",
    "CollapsibleCard", "ActionToolbar", "BadgeLabel", "InfoRow",
    "_make_btn", "CardGrid", "StatusChip",
    "make_stat_card_simple", "make_status_chip",
]