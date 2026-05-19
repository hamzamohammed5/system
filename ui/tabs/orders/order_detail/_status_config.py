"""
ui/tabs/orders/order_detail/_status_config.py
"""

STATUS_LABELS = {
    "pending":     ("⏳ انتظار",   "#b45309", "#fffbeb", "#fde68a"),
    "confirmed":   ("✅ مؤكد",     "#1d4ed8", "#eff6ff", "#bfdbfe"),
    "in_progress": ("🔧 تنفيذ",   "#6d28d9", "#f5f3ff", "#ddd6fe"),
    "ready":       ("📦 جاهز",    "#065f46", "#ecfdf5", "#a7f3d0"),
    "delivered":   ("🚚 مُسلَّم",  "#374151", "#f9fafb", "#e5e7eb"),
    "cancelled":   ("❌ ملغي",    "#991b1b", "#fef2f2", "#fecaca"),
    "on_hold":     ("⏸ معلق",    "#9a3412", "#fff7ed", "#fed7aa"),
}

STATUS_TRANSITIONS = {
    "pending":     ["confirmed", "cancelled", "on_hold"],
    "confirmed":   ["in_progress", "cancelled", "on_hold"],
    "in_progress": ["ready", "cancelled", "on_hold"],
    "ready":       ["delivered", "cancelled"],
    "on_hold":     ["pending", "confirmed", "cancelled"],
    "delivered":   [],
    "cancelled":   ["pending"],
}

PRIORITY_LABELS = {
    "low":    ("⬇ منخفض", "#9ca3af"),
    "normal": ("➡ عادي",  "#6b7280"),
    "high":   ("⬆ عالي",  "#f59e0b"),
    "urgent": ("🔴 عاجل", "#ef4444"),
}

TYPE_LABELS = {
    "new":     "🆕 جديد",
    "reorder": "🔄 إعادة طلب",
    "custom":  "⚙️ مخصص",
}

STATUS_LABELS_SHORT = {k: v[0] for k, v in STATUS_LABELS.items()}
STATUS_COLORS       = {k: v[1:] for k, v in STATUS_LABELS.items()}