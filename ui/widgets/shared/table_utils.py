"""
ui/widgets/shared/table_utils.py
================================
أدوات موحدة لإنشاء وإدارة الجداول في كل أقسام التطبيق.

[v3]: يستورد من sub-modules لتجنب تكرار الكود.
  - table_utils/table_styles.py   → ستايلات الجداول
  - table_utils/table_builders.py → دوال بناء الجداول
  - table_utils/table_helpers.py  → أدوات الخلايا والقياس
"""

# ── ستايلات ──────────────────────────────────────────────
from .table_utils_helper.table_styles import (           # noqa: F401
    ROW_HEIGHT_NORMAL,
    ROW_HEIGHT_COMPACT,
    ROW_HEIGHT_LARGE,
    _table_stylesheet,
    _splitter_stylesheet,
)

# ── بناء الجداول ──────────────────────────────────────────
from .table_utils_helper.table_builders import (         # noqa: F401
    make_detail_table,
    make_compact_table,
    make_list_table,
    make_fixed_table,
    make_splitter_table,
    make_splitter_table_guarded,
)

# ── أدوات الخلايا والقياس ─────────────────────────────────
from .table_utils_helper.table_helpers import (          # noqa: F401
    make_table_item,
    bold_table_item,
    colored_table_item,
    center_table_item,
    set_row_background,
    insert_row,
    auto_fit_columns,
    calc_table_width,
    fit_table_width,
    fit_splitter_table,
    fit_splitter_to_table,
    color_item,
    bold_item,
    muted_item,
    apply_row_height,
)