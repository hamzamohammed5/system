"""
ui/tabs/orders/dashboard/_status_grid.py
"""
from ui.widgets.panels.layout_widgets import CardGrid
from ui.widgets.components.status_chip import make_status_chip
from ui.constants import CARD_GRID_DEFAULT_COLS, CARD_GRID_DEFAULT_SPACING
from ._config import get_status_config


def build_status_grid(dashboard) -> CardGrid:
    """
    يبني شبكة شرائح الحالات ويحفظ references في dashboard._status_chips.
    يرجع CardGrid جاهز للإضافة.
    """
    dashboard._status_chips = {}
    grid = CardGrid(cols=CARD_GRID_DEFAULT_COLS, spacing=CARD_GRID_DEFAULT_SPACING)

    for status, (icon, label, color, bg, border) in get_status_config().items():
        chip = make_status_chip(icon, label, 0, color)
        grid.add_widget(chip)
        dashboard._status_chips[status] = chip

    return grid
