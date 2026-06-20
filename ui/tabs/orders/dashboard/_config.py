"""
ui/tabs/orders/dashboard/_config.py
"""
from ui.theme import _C
from ui.widgets.core.i18n import tr


def get_status_config() -> dict:
    """يرجع إعدادات الحالات مع الألوان من _C."""
    return {
        "pending":     ("⏳", tr("status_pending"),     _C['warning'],  _C['warning_bg'],  _C['warning_border']),
        "confirmed":   ("✅", tr("status_confirmed"),   _C['accent'],   _C['accent_light'],_C['accent_mid']),
        "in_progress": ("🔧", tr("status_in_progress"), _C['purple'],   _C['purple_bg'],   _C['purple_border']),
        "ready":       ("📦", tr("status_ready"),       _C['success'],  _C['success_bg'],  _C['success_border']),
        "delivered":   ("🚚", tr("status_delivered"),   _C['text_sec'], _C['bg_surface_2'],_C['border']),
        "cancelled":   ("❌", tr("status_cancelled"),   _C['danger'],   _C['danger_bg'],   _C['danger_border']),
        "on_hold":     ("⏸", tr("status_on_hold"),     _C['orange'],   _C['orange_bg'],   _C['orange_border']),
    }


def get_status_map() -> dict:
    return {
        "pending":     f"⏳ {tr('status_pending')}",
        "confirmed":   f"✅ {tr('status_confirmed')}",
        "in_progress": f"🔧 {tr('status_in_progress')}",
        "ready":       f"📦 {tr('status_ready')}",
        "delivered":   f"🚚 {tr('status_delivered')}",
        "cancelled":   f"❌ {tr('status_cancelled')}",
        "on_hold":     f"⏸ {tr('status_on_hold')}",
    }


def get_status_color() -> dict:
    return {
        "pending":     _C['warning'],
        "confirmed":   _C['accent'],
        "in_progress": _C['purple'],
        "ready":       _C['success'],
        "delivered":   _C['text_sec'],
        "cancelled":   _C['danger'],
        "on_hold":     _C['orange'],
    }


def get_type_map() -> dict:
    return {
        "new":     tr("order_type_new"),
        "reorder": tr("order_type_reorder"),
        "custom":  tr("order_type_custom"),
    }


def get_priority_map() -> dict:
    return {
        "low":    tr("priority_low"),
        "normal": tr("priority_normal"),
        "high":   tr("priority_high"),
        "urgent": tr("priority_urgent"),
    }


def get_table_cols() -> list:
    return [tr(k) for k in [
        "order_col_number", "order_col_customer", "order_type_label",
        "order_col_status", "order_col_priority", "order_header_total", "order_col_date",
    ]]


COL_WIDTHS    = {0: 130, 1: 160, 2: 80, 3: 100, 4: 75, 5: 100, 6: 90}
TABLE_TOTAL_W = sum(COL_WIDTHS.values()) + 4  # +4 للـ border
