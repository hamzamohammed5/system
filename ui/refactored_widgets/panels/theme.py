"""
ui/refactored_widgets/panels/theme.py
======================================
re-export من theme/styles.py + builders.py للتوافق مع الكود القديم.
"""

# ── styles ────────────────────────────────────────────────
from ..theme.styles import (                          # noqa: F401
    input_style      as get_input_style,
    search_input_style as get_search_input_style,
    card_style       as get_card_style,
    status_card_style as get_status_card_style,
    table_style      as get_table_header_style,
    group_box_style  as get_group_box_style,
    filter_bar_style as get_filter_bar_style,
    toolbar_style    as get_toolbar_style,
    scroll_style     as get_scroll_style,
    splitter_style   as get_splitter_style,
    icon_btn_style   as get_icon_btn_style,
    link_btn_style   as get_link_btn_style,
    tab_style        as get_tab_style,
    tree_style       as get_tree_style,
    list_style       as get_list_style,
    status_label_style as get_status_label_style,
    muted_label_style  as get_muted_label_style,
    section_title_style as get_section_title_style,
)

# ── colors ────────────────────────────────────────────────
from ..core.colors import STATUS_COLORS                # noqa: F401

# ── dividers ──────────────────────────────────────────────
from ..theme.builders import (                         # noqa: F401
    h_divider  as make_divider,
    v_divider  as make_vline_sep,
    h_divider,
    v_divider,
)