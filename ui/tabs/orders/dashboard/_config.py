"""
ui/tabs/orders/dashboard/_config.py
=====================================
ثوابت لوحة المتابعة — الحالات والأعمدة.
"""

# ── ثوابت الحالة: (icon, label, color, bg, border) ──
STATUS_CONFIG = {
    "pending":     ("⏳", "انتظار",   "#f59e0b", "#fffbeb", "#fde68a"),
    "confirmed":   ("✅", "مؤكد",     "#3b82f6", "#eff6ff", "#bfdbfe"),
    "in_progress": ("🔧", "تنفيذ",   "#8b5cf6", "#f5f3ff", "#ddd6fe"),
    "ready":       ("📦", "جاهز",    "#10b981", "#ecfdf5", "#a7f3d0"),
    "delivered":   ("🚚", "مُسلَّم",  "#6b7280", "#f9fafb", "#e5e7eb"),
    "cancelled":   ("❌", "ملغي",    "#ef4444", "#fef2f2", "#fecaca"),
    "on_hold":     ("⏸", "معلق",    "#f97316", "#fff7ed", "#fed7aa"),
}

STATUS_MAP = {
    "pending":     "⏳ انتظار",
    "confirmed":   "✅ مؤكد",
    "in_progress": "🔧 تنفيذ",
    "ready":       "📦 جاهز",
    "delivered":   "🚚 مُسلَّم",
    "cancelled":   "❌ ملغي",
    "on_hold":     "⏸ معلق",
}

STATUS_COLOR = {
    "pending":     "#f59e0b",
    "confirmed":   "#3b82f6",
    "in_progress": "#8b5cf6",
    "ready":       "#10b981",
    "delivered":   "#6b7280",
    "cancelled":   "#ef4444",
    "on_hold":     "#f97316",
}

TYPE_MAP = {
    "new":     "جديد",
    "reorder": "إعادة طلب",
    "custom":  "مخصص",
}

PRIORITY_MAP = {
    "low":    "⬇ منخفض",
    "normal": "➡ عادي",
    "high":   "⬆ عالي",
    "urgent": "🔴 عاجل",
}

# ── أعمدة الجدول وعرضها ──
TABLE_COLS   = ["رقم الطلب", "العميل", "النوع", "الحالة", "الأولوية", "الإجمالي", "التاريخ"]
COL_WIDTHS   = {0: 130, 1: 160, 2: 80, 3: 100, 4: 75, 5: 100, 6: 90}
TABLE_TOTAL_W = sum(COL_WIDTHS.values()) + 4  # +4 للـ border