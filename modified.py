from ui.widgets.panels.form_fields import (labeled_widget, spin_field)
from ui.widgets.panels.form_badges import ResultBadge
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.theme.builders import wrap_in_scroll
from ui.widgets.tables.tables     import make_item, colored_item

from ui.widgets.core.events import bus
from ui.theme import _C
from ui.font import fs, get_font_size

from ui.widgets.tables.tables       import make_table
from ui.widgets.components.button   import make_btn
from ui.widgets.panels.form_labels  import section_title
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