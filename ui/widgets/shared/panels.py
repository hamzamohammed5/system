"""
ui/widgets/shared/panels.py
============================
مكونات UI مشتركة — نقطة الاستيراد الوحيدة لكل الـ shared components.

الاستيرادات المتوفرة:
  - DetailHeader    : هيدر موحد لصفحات التفاصيل
  - StatCard        : بطاقة إحصائية
  - SectionHeader   : رأس قسم مع accent bar وأزرار
  - EmptyState      : حالة فارغة مع أيقونة وزر اختياري
  - CollapsibleCard : بطاقة قابلة للطي
  - ActionToolbar   : شريط أزرار (fixed size)
  - BadgeLabel      : label بشكل badge ملون
  - InfoRow         : صف معلومات ثانوية
  - _make_btn       : دالة إنشاء زر بحجم ثابت
  - StatusChip      : شريحة حالة ملونة (للـ dashboards)
  - CardGrid        : شبكة بطاقات إحصائية متجاوبة
  - make_stat_card  : دالة سريعة لبناء بطاقة إحصائية بسيطة
  - make_status_chip: دالة سريعة لبناء شريحة حالة
"""

from .panles_helper.detail_header    import DetailHeader
from .panles_helper.stat_card        import StatCard
from .panles_helper.section_header   import SectionHeader
from .panles_helper.empty_state      import EmptyState
from .panles_helper.collapsible_card import CollapsibleCard
from .panles_helper.action_toolbar   import ActionToolbar
from .panles_helper.badge_label      import BadgeLabel
from .panles_helper.info_row         import InfoRow
from .panles_helper.make_btn         import _make_btn
from .panles_helper.status_chip      import StatusChip, make_stat_card_simple, make_status_chip
from .panles_helper.card_grid        import CardGrid

__all__ = [
    "DetailHeader",
    "StatCard",
    "SectionHeader",
    "EmptyState",
    "CollapsibleCard",
    "ActionToolbar",
    "BadgeLabel",
    "InfoRow",
    "_make_btn",
    "StatusChip",
    "CardGrid",
    "make_stat_card_simple",
    "make_status_chip",
]