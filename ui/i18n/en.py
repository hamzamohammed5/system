"""
ui/i18n/en/__init__.py
==============================
يجمّع كل ملفات الدومين في EN_STRINGS واحد — نفس واجهة الاستيراد القديمة.
"""

from ui.i18n.en_data.en_general import EN_STRINGS_GENERAL
from ui.i18n.en_data.en_accounting import EN_STRINGS_ACCOUNTING
from ui.i18n.en_data.en_costing import EN_STRINGS_COSTING
from ui.i18n.en_data.en_design import EN_STRINGS_DESIGN
from ui.i18n.en_data.en_inventory import EN_STRINGS_INVENTORY
from ui.i18n.en_data.en_orders import EN_STRINGS_ORDERS
from ui.i18n.en_data.en_pricing import EN_STRINGS_PRICING
from ui.i18n.en_data.en_companies import EN_STRINGS_COMPANIES
from ui.i18n.en_data.en_shared_items import EN_STRINGS_SHARED_ITEMS

EN_STRINGS: dict[str, str] = {}
EN_STRINGS.update(EN_STRINGS_GENERAL)
EN_STRINGS.update(EN_STRINGS_ACCOUNTING)
EN_STRINGS.update(EN_STRINGS_COSTING)
EN_STRINGS.update(EN_STRINGS_DESIGN)
EN_STRINGS.update(EN_STRINGS_INVENTORY)
EN_STRINGS.update(EN_STRINGS_ORDERS)
EN_STRINGS.update(EN_STRINGS_PRICING)
EN_STRINGS.update(EN_STRINGS_COMPANIES)
EN_STRINGS.update(EN_STRINGS_SHARED_ITEMS)

__all__ = ["EN_STRINGS"]
