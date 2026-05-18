"""
ui/tabs/orders/dashboard/_status_grid.py
==========================================
بناء شبكة شرائح الحالات في لوحة المتابعة.
"""

from ui.widgets.shared.panels import make_status_chip, CardGrid
from ._config import STATUS_CONFIG


def build_status_grid(dashboard) -> CardGrid:
    """
    يبني شبكة شرائح الحالات ويحفظ references في dashboard._status_chips.
    يرجع CardGrid جاهز للإضافة.
    """
    dashboard._status_chips = {}
    grid = CardGrid(cols=4, spacing=10)

    for status, (icon, label, color, bg, border) in STATUS_CONFIG.items():
        chip, cnt_lbl = make_status_chip(icon, label, 0, color, bg, border)
        grid.add_widget(chip)
        dashboard._status_chips[status] = cnt_lbl

    return grid