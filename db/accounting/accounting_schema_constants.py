"""
db/accounting/accounting_schema_constants.py
===================================
ثوابت أنواع الحسابات المستخدمة في كل أنحاء التطبيق.
"""

TYPE_AR = {
    "asset":     "أصول",
    "liability": "خصوم",
    "capital":   "رأس المال",
    "revenue":   "إيرادات",
    "expense":   "مصروفات",
    "drawings":  "مسحوبات",
}

# الأنواع التي تنتمي لحقوق الملكية
EQUITY_TYPES = {"capital", "drawings", "revenue", "expense"}

# تجميع كل نوع تحت مجموعته الكبرى
TYPE_GROUP = {
    "asset":     "asset",
    "liability": "liability",
    "capital":   "equity",
    "drawings":  "equity",
    "revenue":   "equity",
    "expense":   "equity",
}

# عنوان المجموعة الكبرى
GROUP_AR = {
    "asset":     "الأصول",
    "liability":  "الخصوم",
    "equity":    "حقوق الملكية",
}

NORMAL_BALANCE = {
    "asset":     "dr",
    "expense":   "dr",
    "drawings":  "dr",
    "liability": "cr",
    "capital":   "cr",
    "revenue":   "cr",
}

_VALID_TYPES = "('asset','liability','capital','revenue','expense','drawings')"