"""
ui/widgets/shared/panels.py
============================
مكونات UI مشتركة قابلة لإعادة الاستخدام في كل الأقسام.

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
]