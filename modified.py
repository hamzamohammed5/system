from ui.widgets.panels.form_fields import (labeled_widget, spin_field)
from ui.widgets.panels.form_badges import ResultBadge
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.theme.builders import wrap_in_scroll
from ui.widgets.tables.tables     import make_item, colored_item
from ui.widgets.managers.category import CategoryManager
from ui.widgets.combo.category import CategoryCombo
from ui.widgets.components.stat_card import stat_card_pair
from ui.widgets.core.events import bus
from ui.widgets.panels.filter import FilterToolbar # بدل FilterBar
from ui.widgets.dialogs.confirm      import confirm_delete
from ui.widgets.panels.form_labels   import section_title # بدل section_label
from ui.widgets.components.button    import make_btn
from ui.widgets.tables.tables        import auto_fit_columns
from ui.widgets.combo.unit import UnitCombo
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_list import ListHeader, StatusBar # ListStatusBar
from ui.widgets.theme.layout_styles      import tree_style # get_tree_style
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.amount_label  import BalanceDisplay
from ui.widgets.components.stat_card import StatRow, StatItem
from db.accounting.accounting_repo import get_account_balance
from db.accounting.accounting_accounts_repo import _get_group_descendants

# sep
from ui.widgets.theme.builders import v_divider
sep = v_divider()

#
from ui.widgets.theme.input_styles import input_style
self._style_combo(self.cmb_move_type)

# setup_table_columns
from ui.widgets.tables.tables       import auto_fit_columns
auto_fit_columns(
        self.table,
        fixed_cols=[0, 2, 3, 4, 5, 6],
        stretch_col=1,
        min_width=40,
        max_width=150,
    )

# danger_button
from ui.widgets.core.i18n import tr

from ui.widgets.components.button   import make_btn
make_btn("🗑️  " + tr("delete"), style="danger")

from ui.theme import _C
from ui.font import fs, get_font_size

from ui.widgets.tables.tables       import make_table
from ui.widgets.components.button   import make_btn
from ui.widgets.panels.filter       import FilterToolbar
from ui.widgets.core.events         import bus, emit_company_data_changed
"""
# bus.data_changed.emit -> emit_company_data_changed
ال
# if self._company_id is not None:
#                 bus.company_data_changed.emit(self._company_id)
#             else:
#                 bus.data_changed.emit()
هيبقى
emit_company_data_changed()
"""
# bus.data_changed.connect -> bus.company_data_changed

from PyQt5.QtWidgets import QHBoxLayout

def buttons_row(*buttons) -> QHBoxLayout:
    """صف أزرار أفقي."""
    row = QHBoxLayout()
    row.setSpacing(6)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row