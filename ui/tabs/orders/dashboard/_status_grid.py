"""
ui/tabs/orders/dashboard/_status_grid.py
"""
from ui.widgets.panels.layout_widgets import CardGrid
from ui.widgets.components.status_chip import make_status_chip
from ._config import get_status_config


def build_status_grid(dashboard) -> CardGrid:
    """
    يبني شبكة شرائح الحالات ويحفظ references في dashboard._status_chips.
    يرجع CardGrid جاهز للإضافة.
    """
    dashboard._status_chips = {}
    grid = CardGrid(cols=4, spacing=10)

    for status, (icon, label, color, bg, border) in get_status_config().items():
        chip, cnt_lbl = make_status_chip(icon, label, 0, color, bg, border)
        grid.add_widget(chip)
        dashboard._status_chips[status] = cnt_lbl

    return grid
