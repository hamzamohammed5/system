"""
ui/tabs/orders/order_detail/_status_config.py
"""
from ui.theme import _C
from ui.widgets.core.i18n import tr


def get_status_labels() -> dict:
    return {
        "pending":     (f"⏳ {tr('status_pending')}",     _C['warning'],  _C['warning_bg'],  _C['warning_border']),
        "confirmed":   (f"✅ {tr('status_confirmed')}",   _C['accent'],   _C['accent_light'],_C['accent_mid']),
        "in_progress": (f"🔧 {tr('status_in_progress')}", _C['purple'],   _C['purple_bg'],   _C['purple_border']),
        "ready":       (f"📦 {tr('status_ready')}",       _C['success'],  _C['success_bg'],  _C['success_border']),
        "delivered":   (f"🚚 {tr('status_delivered')}",   _C['text_sec'], _C['bg_surface_2'],_C['border']),
        "cancelled":   (f"❌ {tr('status_cancelled')}",   _C['danger'],   _C['danger_bg'],   _C['danger_border']),
        "on_hold":     (f"⏸ {tr('status_on_hold')}",     _C['orange'],   _C['orange_bg'],   _C['orange_border']),
    }


def get_status_transitions() -> dict:
    return {
        "pending":     ["confirmed", "cancelled", "on_hold"],
        "confirmed":   ["in_progress", "cancelled", "on_hold"],
        "in_progress": ["ready", "cancelled", "on_hold"],
        "ready":       ["delivered", "cancelled"],
        "on_hold":     ["pending", "confirmed", "cancelled"],
        "delivered":   [],
        "cancelled":   ["pending"],
    }


# للتوافق مع الكود القديم الذي يستورد STATUS_TRANSITIONS كثابت مباشر
STATUS_TRANSITIONS = get_status_transitions()


def get_priority_labels() -> dict:
    return {
        "low":    (tr("priority_low"),    _C['text_disabled']),
        "normal": (tr("priority_normal"), _C['text_muted']),
        "high":   (tr("priority_high"),   _C['warning']),
        "urgent": (tr("priority_urgent"), _C['danger']),
    }


def get_type_labels() -> dict:
    return {
        "new":     tr("order_type_new"),
        "reorder": tr("order_type_reorder"),
        "custom":  tr("order_type_custom"),
    }


def get_status_labels_short() -> dict:
    return {k: v[0] for k, v in get_status_labels().items()}


def get_status_colors() -> dict:
    return {k: v[1:] for k, v in get_status_labels().items()}
