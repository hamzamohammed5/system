"""
ui/i18n/ar/__init__.py
==============================
يجمّع كل ملفات الدومين في AR_STRINGS واحد — نفس واجهة الاستيراد القديمة.
"""

from ui.i18n.ar_data.ar_general import AR_STRINGS_GENERAL
from ui.i18n.ar_data.ar_accounting import AR_STRINGS_ACCOUNTING
from ui.i18n.ar_data.ar_costing import AR_STRINGS_COSTING
from ui.i18n.ar_data.ar_design import AR_STRINGS_DESIGN
from ui.i18n.ar_data.ar_inventory import AR_STRINGS_INVENTORY
from ui.i18n.ar_data.ar_orders import AR_STRINGS_ORDERS
from ui.i18n.ar_data.ar_pricing import AR_STRINGS_PRICING
from ui.i18n.ar_data.ar_companies import AR_STRINGS_COMPANIES
from ui.i18n.ar_data.ar_shared_items import AR_STRINGS_SHARED_ITEMS

AR_STRINGS: dict[str, str] = {}
AR_STRINGS.update(AR_STRINGS_GENERAL)
AR_STRINGS.update(AR_STRINGS_ACCOUNTING)
AR_STRINGS.update(AR_STRINGS_COSTING)
AR_STRINGS.update(AR_STRINGS_DESIGN)
AR_STRINGS.update(AR_STRINGS_INVENTORY)
AR_STRINGS.update(AR_STRINGS_ORDERS)
AR_STRINGS.update(AR_STRINGS_PRICING)
AR_STRINGS.update(AR_STRINGS_COMPANIES)
AR_STRINGS.update(AR_STRINGS_SHARED_ITEMS)

__all__ = ["AR_STRINGS"]
