"""
ui/widgets/tables/styles.py
============================
ثوابت ارتفاع الصفوف + re-export لـ table_style و splitter_style
من المصدر الوحيد: theme/styles.py
"""
from ..theme.styles import table_style, splitter_style  # noqa: F401

ROW_HEIGHT_COMPACT = 34
ROW_HEIGHT_NORMAL  = 40
ROW_HEIGHT_LARGE   = 48