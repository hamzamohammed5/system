# دليل تحديث الاستدعاءات المباشرة
# الملفات اللي هتتمسح والبديل المباشر لكل import

==============================================================
1. ui/widgets/components/headers.py  →  يتمسح
==============================================================

الملفات اللي هتتغير فيها:

── ui/widgets/base/list_panel.py ──
القديم:  from ..components.headers_list import ListHeader, StatusBar
الجديد:  from ..components.headers_list import ListHeader, StatusBar

── ui/widgets/base/detail_panel.py ──
القديم:  from ..components.headers import DetailHeader
الجديد:  from ..components.headers_page import DetailHeader

── ui/widgets/panels/filter.py ──
القديم:  from ..components.headers import SearchBar
الجديد:  from ..components.headers_list import SearchBar

── ui/widgets/panels/data_table.py ──
القديم:  from ..components.headers_list import ListHeader, StatusBar
الجديد:  from ..components.headers_list import ListHeader, StatusBar

── ui/widgets/components/headers_page.py ──  (الملف الجديد نفسه)
القديم:  from .stat_row import BadgeLabel, StatCard
الجديد:  from .badge import BadgeLabel
         from .stat_card import StatCard

القديم:  from .label import InfoRow
الجديد:  from .label import InfoRow   (← نفسه، مش بيتغير)

القديم:  from ..theme.styles import h_divider, v_divider
الجديد:  from ..theme.builders import h_divider, v_divider


==============================================================
2. ui/widgets/components/stat_row.py  →  يتمسح
==============================================================

الملفات اللي هتتغير فيها:

── ui/widgets/components/headers_page.py ──
القديم:  from .stat_row import BadgeLabel, StatCard
الجديد:  from .badge import BadgeLabel
         from .stat_card import StatCard

ملاحظة: أي كود تاني بيستورد من stat_row يستبدل:
  BadgeLabel       → from .badge import BadgeLabel
  StatItem         → from .stat_card import StatItem
  StatCard         → from .stat_card import StatCard
  _StatCard        → from .stat_card import _StatCard
  StatRow          → from .stat_card import StatRow
  make_stat_row    → from .stat_card import make_stat_row
  stat_card_pair   → from .stat_card import stat_card_pair
  make_stat_card_simple → from .stat_card import make_stat_card_simple
  StatusChip       → from .status_chip import StatusChip
  StatusCard       → from .status_chip import StatusCard
  make_status_chip → from .status_chip import make_status_chip


==============================================================
3. ui/widgets/mixins/data_mixins.py  →  يتمسح
==============================================================

أي كود بيستورد منه:
  RefreshableMixin → from ..mixins.refresh_mixin import RefreshableMixin
  RebuildMixin     → from ..mixins.rebuild_mixin import RebuildMixin
  SelectionMixin   → from ..mixins.selection_mixin import SelectionMixin

(مفيش ملفات في الـ docs الحالية بتستورد منه)


==============================================================
4. ui/widgets/panels/form_parts.py  →  يتمسح
==============================================================

الملفات اللي هتتغير فيها:

── ui/widgets/base/crud_form.py ──
القديم:  from ui.widgets.panels.form_parts import FormGroup
الجديد:  from ui.widgets.panels.form_group import FormGroup

القديم:  from ui.widgets.theme.styles import wrap_in_scroll
الجديد:  from ui.widgets.theme.builders import wrap_in_scroll

أي كود تاني بيستورد من form_parts يستبدل:
  form_label       → from ..panels.form_labels import form_label
  required_label   → from ..panels.form_labels import required_label
  hint_label       → from ..panels.form_labels import hint_label
  section_title    → from ..panels.form_labels import section_title
  separator_line   → from ..panels.form_labels import separator_line
  spin_field       → from ..panels.form_fields import spin_field
  int_spin_field   → from ..panels.form_fields import int_spin_field
  labeled_widget   → from ..panels.form_fields import labeled_widget
  field_row        → from ..panels.form_fields import field_row
  labeled_row      → from ..panels.form_fields import labeled_row
  make_form_layout → from ..panels.form_fields import make_form_layout
  FormGroup        → from ..panels.form_group import FormGroup
  ResultBadge      → from ..panels.form_badges import ResultBadge
  ModeBadge        → from ..panels.form_badges import ModeBadge
  InlinePreview    → from ..panels.form_badges import InlinePreview
  make_preview_label → from ..panels.form_badges import make_preview_label
  CrudButtonsBar   → from ..panels.form_buttons import CrudButtonsBar


==============================================================
5. ui/widgets/panels/crud_section.py  →  يتمسح
==============================================================

أي كود بيستورد منه:
  CrudSection → from ui.widgets.base.section import BaseSection as CrudSection
  أو:          from ui.widgets.base.section import BaseSection
               # واستخدم BaseSection بدل CrudSection

(مفيش ملفات في الـ docs الحالية بتستورد منه)


==============================================================
6. ui/widgets/theme/styles.py  →  يتمسح
==============================================================

الملفات اللي هتتغير فيها:

── ui/widgets/utils/splitter.py ──
القديم:  from ..theme.table_styles import splitter_style
الجديد:  from ..theme.table_styles import splitter_style

── ui/widgets/components/action_toolbar.py ──
القديم:  from ..theme.styles import v_divider
الجديد:  from ..theme.builders import v_divider

── ui/widgets/combo/category.py ──  (tree_style)
القديم:  from ..theme.styles import tree_style
الجديد:  from ..theme.layout_styles import tree_style

── ui/widgets/base/section.py ──
القديم:  from ..theme.table_styles import splitter_style
الجديد:  from ..theme.table_styles import splitter_style

── ui/widgets/base/crud_form.py ──
القديم:  from ui.widgets.theme.styles import wrap_in_scroll
الجديد:  from ui.widgets.theme.builders import wrap_in_scroll

── ui/widgets/base/tab_section.py ──
القديم:  from ..theme.styles import tab_style
الجديد:  from ..theme.layout_styles import tab_style

── ui/widgets/managers/category.py ──
القديم:  from ..theme.styles import tree_style
الجديد:  from ..theme.layout_styles import tree_style

── ui/widgets/base/list_panel.py ──
القديم:  from ..theme.styles import (...)
تفاصيل الـ imports الموجودة في list_panel:
  → ROW_HEIGHT_LARGE          : from ..theme.table_styles import ROW_HEIGHT_LARGE
  → (make_splitter_table_guarded, fit_splitter_table, auto_fit_columns من tables.py مش styles)

── ui/widgets/components/label.py ──
القديم:  from ..theme.styles import (...)
تفاصيل:
  → (label.py بتستورد من ..core.colors مش styles مباشرة)

── ui/widgets/base/detail_panel.py ──
القديم:  from ..theme.styles import scroll_style
الجديد:  from ..theme.layout_styles import scroll_style

── ui/widgets/panels/layout_widgets.py ──
القديم:  from ..theme.styles import h_divider, card_style
الجديد:  from ..theme.builders import h_divider
         from ..theme.card_styles import card_style

── ui/widgets/components/headers_page.py ──  (الملف الجديد)
القديم:  from ..theme.styles import h_divider, v_divider
الجديد:  from ..theme.builders import h_divider, v_divider

── ui/widgets/panels/data_table.py ──
القديم:  from ..theme.styles import (...)
تفاصيل:
  → (data_table بتستورد من ..tables.tables و ..components.headers)

── ui/widgets/panels/form_group.py ──
القديم:  (spinbox_style via form_parts أو styles)
الجديد:  from ..theme.input_styles import spinbox_style

── ui/widgets/panels/form_fields.py ──
القديم:  from ..theme.styles import spinbox_style
الجديد:  from ..theme.input_styles import spinbox_style


==============================================================
ملخص جدول التحويل السريع
==============================================================

| القديم                        | الجديد                                    |
|-------------------------------|-------------------------------------------|
| ..theme.styles → splitter_style  | ..theme.table_styles                   |
| ..theme.styles → table_style     | ..theme.table_styles                   |
| ..theme.styles → ROW_HEIGHT_*    | ..theme.table_styles                   |
| ..theme.styles → input_style     | ..theme.input_styles                   |
| ..theme.styles → spinbox_style   | ..theme.input_styles                   |
| ..theme.styles → search_input_style | ..theme.input_styles               |
| ..theme.styles → card_style      | ..theme.card_styles                    |
| ..theme.styles → status_card_style | ..theme.card_styles                  |
| ..theme.styles → group_box_style | ..theme.card_styles                    |
| ..theme.styles → status_label_style | ..theme.label_styles               |
| ..theme.styles → muted_label_style  | ..theme.label_styles               |
| ..theme.styles → section_title_style | ..theme.label_styles              |
| ..theme.styles → icon_btn_style  | ..theme.label_styles                   |
| ..theme.styles → link_btn_style  | ..theme.label_styles                   |
| ..theme.styles → tab_style       | ..theme.layout_styles                  |
| ..theme.styles → scroll_style    | ..theme.layout_styles                  |
| ..theme.styles → filter_bar_style | ..theme.layout_styles                 |
| ..theme.styles → toolbar_style   | ..theme.layout_styles                  |
| ..theme.styles → tree_style      | ..theme.layout_styles                  |
| ..theme.styles → list_style      | ..theme.layout_styles                  |
| ..theme.styles → h_divider       | ..theme.builders                       |
| ..theme.styles → v_divider       | ..theme.builders                       |
| ..theme.styles → wrap_in_scroll  | ..theme.builders                       |
| ..components.headers → ListHeader   | ..components.headers_list           |
| ..components.headers → StatusBar    | ..components.headers_list           |
| ..components.headers → SearchBar    | ..components.headers_list           |
| ..components.headers → SectionHeader | ..components.headers_page          |
| ..components.headers → PageHeader   | ..components.headers_page           |
| ..components.headers → DetailHeader | ..components.headers_page           |
| ..components.stat_row → BadgeLabel  | ..components.badge                  |
| ..components.stat_row → Stat*       | ..components.stat_card              |
| ..components.stat_row → Status*     | ..components.status_chip            |
| ..panels.form_parts → FormGroup     | ..panels.form_group                 |
| ..panels.form_parts → form_label    | ..panels.form_labels                |
| ..panels.form_parts → spin_field    | ..panels.form_fields                |
| ..panels.form_parts → ResultBadge   | ..panels.form_badges                |
| ..panels.form_parts → CrudButtonsBar | ..panels.form_buttons              |
| ..mixins.data_mixins → Refreshable* | ..mixins.refresh_mixin             |
| ..mixins.data_mixins → Rebuild*     | ..mixins.rebuild_mixin              |
| ..mixins.data_mixins → Selection*   | ..mixins.selection_mixin            |
| ..panels.crud_section → CrudSection | ui.widgets.base.section → BaseSection |