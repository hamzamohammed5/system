# خطة إعادة هيكلة قسم المحاسبة — نسخة نهائية قابلة للتطبيق المباشر

> تاريخ الإعداد: 2026-06-05
> المبدأ: كل استدعاء مباشر لمصدره الأصلي — لا re-exports — لا shims — لا hardcoded

---

## صفر: ما يُحذف قبل البدء

| الملف | السبب |
|---|---|
| `ui/tabs/accounting/investors/_helpers.py` | كان re-export بحت لـ spin_field و stat_card_pair |
| أي ملف `ui/widgets/shared/panels.py` | wrapper وهمي — لا وجود له فعلاً في البنية |
| أي ملف `ui/widgets/shared/stat_row.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/tab_builder.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/safe_conn_mixin.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/company_utils.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/date_range_filter.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/input_widgets.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/empty_state_helpers.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/form_utils.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/color_picker_widget.py` | wrapper وهمي |
| أي ملف `ui/widgets/shared/panles_helper/` | مجلد wrapper وهمي بالكامل |
| أي ملف `ui/widgets/theme/styles.py` | wrapper وهمي لـ table_styles + layout_styles |
| أي ملف `ui/helpers.py` | wrapper وهمي — وظائفه موزعة على الـ widgets الفعلية |
| أي ملف `ui/font_utils.py` | wrapper وهمي لـ ui.font |
| أي ملف `ui/events.py` | wrapper وهمي — استخدم ui.widgets.core.events مباشرة |
| أي ملف `ui/app_settings.py` | wrapper وهمي — استخدم ui.theme و ui.font مباشرة |

---

## أولاً: خريطة الـ imports النهائية (المصدر الحقيقي لكل شيء)

### Mixins و Connections
```
SafeConnMixin, DualConnMixin, LiveConnMixin   →  ui.widgets.core.conn
```

### Events و Bus
```
bus, emit_company_data_changed, get_active_company_id  →  ui.widgets.core.events
```

### Theme و Font
```
_C                →  ui.theme
fs, get_font_size →  ui.font
```

### Components
```
PageHeader, SectionHeader          →  ui.widgets.components.headers_page
ListHeader, StatusBar              →  ui.widgets.components.headers_list
StatRow, StatItem, stat_card_pair  →  ui.widgets.components.stat_card
BalanceDisplay, AmountLabel        →  ui.widgets.components.amount_label
NotificationBar                    →  ui.widgets.components.notification
ModeLabel                          →  ui.widgets.components.label
make_btn                           →  ui.widgets.components.button
ColorPickerWidget                  →  ui.widgets.helpers.color_picker
```

### Tables
```
make_table, make_list_table, bold_item, colored_item,
center_item, set_row_bg, auto_fit_columns,
ROW_HEIGHT_NORMAL, ROW_HEIGHT_LARGE              →  ui.widgets.tables.tables
```

### Panels / Forms
```
FormGroup         →  ui.widgets.panels.form_group
spin_field, make_form_layout  →  ui.widgets.panels.form_fields
form_label, required_label    →  ui.widgets.panels.form_labels
EmptyState (بدل EmptyPanelState)  →  ui.widgets.panels.state
FilterToolbar     →  ui.widgets.panels.filter
```

### Inputs
```
NotesLineEdit, DateField, AmountSpinBox  →  ui.widgets.forms.inputs
```

### Dialogs
```
confirm_delete, confirm_action  →  ui.widgets.dialogs.confirm
msg_warning, msg_info           →  ui.widgets.dialogs.message
```

### Theme Styles
```
table_style, splitter_style, ROW_HEIGHT_NORMAL  →  ui.widgets.theme.table_styles
tree_style, tab_style, scroll_style             →  ui.widgets.theme.layout_styles
```

### Mixins
```
EditModeMixin, FormValidationMixin  →  ui.widgets.mixins.form_mixins
```

### Widgets Utils
```
DateRangeFilter  →  ui.widgets.utils.date_range
```

---

## ثانياً: إضافة alias واحد فقط في `ui/widgets/core/conn.py`

أضف داخل `SafeConnMixin`:

```python
def _on_company_event_safe(self, company_id: int) -> bool:
    """Alias لـ _should_respond_to_company — للتوافق مع الكود الموجود."""
    return self._should_respond_to_company(company_id)
```

---

## ثالثاً: ألوان جديدة في `ui/theme_manager.py`

أضف في **كلا** `_LIGHT_THEME` و `_DARK_THEME`:

### في `_LIGHT_THEME`:
```python
# ── Accounting Journal ────────────────────────────────────
"journal_dr_bg":          "#f4f8ff",
"journal_dr_border":      "#c5d8f7",
"journal_dr_accent":      "#1565c0",
"journal_cr_bg":          "#fff4f4",
"journal_cr_border":      "#f7c5c5",
"journal_cr_accent":      "#c62828",
"journal_neutral_bg":     "#fafbff",
"journal_neutral_border": "#dde3f0",
"journal_header_bg":      "#f0f4ff",
"journal_header_border":  "#c5cae9",
# ── Investor ─────────────────────────────────────────────
"investor_capital_bg":    "#f1f8e9",
"investor_capital_text":  "#2e7d32",
"investor_drawings_bg":   "#fdecea",
"investor_drawings_text": "#c62828",
"investor_link_bg":       "#fff8e1",
"investor_link_border":   "#ffe082",
"investor_link_text":     "#f57f17",
# ── Audit Log ────────────────────────────────────────────
"audit_delete_fg":        "#C0392B",
"audit_delete_bg":        "#FDF0EF",
"audit_update_fg":        "#7A5C00",
"audit_update_bg":        "#FDF8E7",
"audit_create_fg":        "#2E7D52",
"audit_create_bg":        "#EDF7F2",
# ── T-Account ────────────────────────────────────────────
"t_account_dr_bg":        "#e3f2fd",
"t_account_cr_bg":        "#fdecea",
"t_account_frame":        "#c5cae9",
# ── Badge ────────────────────────────────────────────────
"badge_dr_bg":            "#e3f2fd",
"badge_dr_text":          "#1565c0",
"badge_cr_bg":            "#fdecea",
"badge_cr_text":          "#c62828",
```

### في `_DARK_THEME`:
```python
# ── Accounting Journal ────────────────────────────────────
"journal_dr_bg":          "#1a2a3a",
"journal_dr_border":      "#2a4a6a",
"journal_dr_accent":      "#5B8DB8",
"journal_cr_bg":          "#2a1010",
"journal_cr_border":      "#5a2020",
"journal_cr_accent":      "#E57373",
"journal_neutral_bg":     "#1A1A1A",
"journal_neutral_border": "#2E2E2E",
"journal_header_bg":      "#1a2030",
"journal_header_border":  "#2a3050",
# ── Investor ─────────────────────────────────────────────
"investor_capital_bg":    "#0a2018",
"investor_capital_text":  "#66BB8A",
"investor_drawings_bg":   "#2a1010",
"investor_drawings_text": "#E57373",
"investor_link_bg":       "#282000",
"investor_link_border":   "#4a3800",
"investor_link_text":     "#FFD54F",
# ── Audit Log ────────────────────────────────────────────
"audit_delete_fg":        "#E57373",
"audit_delete_bg":        "#2a1010",
"audit_update_fg":        "#FFD54F",
"audit_update_bg":        "#2a2000",
"audit_create_fg":        "#66BB8A",
"audit_create_bg":        "#0a2018",
# ── T-Account ────────────────────────────────────────────
"t_account_dr_bg":        "#1a2a3a",
"t_account_cr_bg":        "#2a1010",
"t_account_frame":        "#2a3050",
# ── Badge ────────────────────────────────────────────────
"badge_dr_bg":            "#1a2a3a",
"badge_dr_text":          "#5B8DB8",
"badge_cr_bg":            "#2a1010",
"badge_cr_text":          "#E57373",
```

---

## رابعاً: مفاتيح ترجمة جديدة

### يُضاف في `ui/i18n/ar.py` داخل `AR_STRINGS`:
```python
# ══════════════════════════════════════════════
# دفتر الأستاذ
# ══════════════════════════════════════════════
"ledger":                  "دفتر الأستاذ",
"t_account":               "حساب T",
"normal_balance_dr":       "طبيعة مدينة (DR↑)",
"normal_balance_cr":       "طبيعة دائنة (CR↑)",

# ══════════════════════════════════════════════
# فورم القيد
# ══════════════════════════════════════════════
"journal_balanced":        "✅ متوازن — يمكن الحفظ",
"journal_unbalanced":      "⚠️ غير متوازن",
"add_journal_line":        "➕  إضافة صف",
"journal_lines_title":     "📋  صفوف القيد",
"journal_increase":        "زيادة ✚",
"journal_decrease":        "نقص ✖",
"entry_type_manual":       "📝 يدوي",
"entry_type_opening":      "🟢 افتتاحي",
"entry_type_closing":      "🔴 ختامي",
"entry_type_transfer":     "🔄 ترحيل",
"select_account":          "— اختر الحساب —",
"select_journal_first":    "اختر قيداً أولاً",
"journal_saved_success":   "✅ تم حفظ القيد بنجاح",
"no_dr_line":              "لا يوجد أي صف مدين (DR)",
"no_cr_line":              "لا يوجد أي صف دائن (CR)",
"entry_description_placeholder": "وصف القيد الإجمالي...",
"line_description_placeholder":  "بيان...",
"balance_bar_diff":        "الفرق:",
"balance_bar_add_rows":    "○ أضف صفوف",
"entry_save_btn":          "💾  حفظ القيد",
"entry_clear_btn":         "✖  مسح",
"new_journal_entry":       "── قيد يومية جديد ──",

# ══════════════════════════════════════════════
# Audit Log
# ══════════════════════════════════════════════
"audit_log_delete":        "🗑️ حذف",
"audit_log_update":        "✏️ تعديل",
"audit_log_create":        "➕ إضافة",
"audit_detail_title":      "تفاصيل العملية",
"old_data":                "البيانات القديمة",
"changed_by":              "بواسطة",
"no_audit_records":        "لا توجد سجلات",
"no_audit_yet":            "لم يُسجَّل أي عملية حتى الآن",
"audit_all_tables":        "— كل الجداول —",
"audit_all_types":         "— كل الأنواع —",

# ══════════════════════════════════════════════
# المستثمرون
# ══════════════════════════════════════════════
"investor_capital_badge":  "💰 رأس مال",
"investor_drawings_badge": "💸 مسحوبات",
"initial_capital":         "رأس المال الأولي",
"capital_account":         "حساب رأس المال",
"deposit_account":         "حساب الإيداع",
"payment_account":         "حساب الصرف",
"link_investor_to_entry":  "🔗  ربط بقيد محاسبي",
"link_success":            "✅ تم ربط القيد بالمستثمر بنجاح",
"investor_join_date":      "تاريخ الانضمام",
"investor_new":            "مستثمر جديد",
"select_investor":         "اختر المستثمر",
"investor_movements":      "─── الحركات المالية ───",
"delete_movement_title":   "تأكيد حذف الحركة",
"delete_movement_msg":     "حذف {type} (قيد {ref})؟\n\n⚠️ سيتم حذف الحركة من سجل المستثمر وحذف القيد من الحسابات.",
"investor_list_title":     "─── المستثمرون ───",
"add_capital_title":       "💰  إضافة رأس مال",
"add_drawings_title":      "💸  تسجيل مسحوبات",
"expected_entry":          "القيد المتوقع:",
"link_entry_info":         "🔗  ربط قيد محاسبي موجود بمستثمر\nاستخدم هذا لو أضفت القيد يدوياً في تبويب القيود وتريد نسبته لمستثمر.",
"entry_ref_placeholder":   "مثال: JE-00012",
"link_entry_btn":          "🔗  ربط",

# ══════════════════════════════════════════════
# Pagination
# ══════════════════════════════════════════════
"load_more":               "تحميل {count} إضافي  ▼",
"show_all_records":        "عرض الكل",
"showing_records":         "يعرض {shown:,} من {total:,}",
"showing_all_records":     "يعرض كل {shown:,} سجل",

# ══════════════════════════════════════════════
# شريط الحالة والفلاتر
# ══════════════════════════════════════════════
"group_filter":            "🏷 التصنيف:",
"balance_status_filter":   "الحالة:",
"all_groups":              "— كل التصنيفات —",
"balanced_filter":         "✅ متوازن",
"unbalanced_filter":       "⚠️ غير متوازن",
"move_type_all":           "كل الحركات",
"move_type_dr":            "مدين فقط",
"move_type_cr":            "دائن فقط",
"clear_filters":           "↺ مسح الفلاتر",
"entry_date_label":        "التاريخ:",
"entry_type_label":        "النوع:",
"entry_desc_label":        "الوصف:",
```

### يُضاف في `ui/i18n/en.py` داخل `EN_STRINGS`:
```python
# ══════════════════════════════════════════════
# Ledger
# ══════════════════════════════════════════════
"ledger":                  "Ledger",
"t_account":               "T-Account",
"normal_balance_dr":       "Debit Nature (DR↑)",
"normal_balance_cr":       "Credit Nature (CR↑)",

# ══════════════════════════════════════════════
# Journal Form
# ══════════════════════════════════════════════
"journal_balanced":        "✅ Balanced — can save",
"journal_unbalanced":      "⚠️ Unbalanced",
"add_journal_line":        "➕  Add Row",
"journal_lines_title":     "📋  Journal Lines",
"journal_increase":        "Increase ✚",
"journal_decrease":        "Decrease ✖",
"entry_type_manual":       "📝 Manual",
"entry_type_opening":      "🟢 Opening",
"entry_type_closing":      "🔴 Closing",
"entry_type_transfer":     "🔄 Transfer",
"select_account":          "— Select Account —",
"select_journal_first":    "Select an entry first",
"journal_saved_success":   "✅ Entry saved successfully",
"no_dr_line":              "No debit (DR) line found",
"no_cr_line":              "No credit (CR) line found",
"entry_description_placeholder": "Entry description...",
"line_description_placeholder":  "Description...",
"balance_bar_diff":        "Diff:",
"balance_bar_add_rows":    "○ Add rows",
"entry_save_btn":          "💾  Save Entry",
"entry_clear_btn":         "✖  Clear",
"new_journal_entry":       "── New Journal Entry ──",

# ══════════════════════════════════════════════
# Audit Log
# ══════════════════════════════════════════════
"audit_log_delete":        "🗑️ Delete",
"audit_log_update":        "✏️ Update",
"audit_log_create":        "➕ Create",
"audit_detail_title":      "Operation Details",
"old_data":                "Old Data",
"changed_by":              "Changed By",
"no_audit_records":        "No records found",
"no_audit_yet":            "No operations logged yet",
"audit_all_tables":        "— All Tables —",
"audit_all_types":         "— All Types —",

# ══════════════════════════════════════════════
# Investors
# ══════════════════════════════════════════════
"investor_capital_badge":  "💰 Capital",
"investor_drawings_badge": "💸 Drawings",
"initial_capital":         "Initial Capital",
"capital_account":         "Capital Account",
"deposit_account":         "Deposit Account",
"payment_account":         "Payment Account",
"link_investor_to_entry":  "🔗  Link to Accounting Entry",
"link_success":            "✅ Entry linked to investor successfully",
"investor_join_date":      "Join Date",
"investor_new":            "New Investor",
"select_investor":         "Select Investor",
"investor_movements":      "─── Financial Movements ───",
"delete_movement_title":   "Confirm Delete Movement",
"delete_movement_msg":     "Delete {type} (entry {ref})?\n\n⚠️ This will delete the movement and its accounting entry.",
"investor_list_title":     "─── Investors ───",
"add_capital_title":       "💰  Add Capital",
"add_drawings_title":      "💸  Record Drawings",
"expected_entry":          "Expected Entry:",
"link_entry_info":         "🔗  Link an existing accounting entry to an investor\nUse this if you added the entry manually in the journal tab.",
"entry_ref_placeholder":   "e.g. JE-00012",
"link_entry_btn":          "🔗  Link",

# ══════════════════════════════════════════════
# Pagination
# ══════════════════════════════════════════════
"load_more":               "Load {count} More  ▼",
"show_all_records":        "Show All",
"showing_records":         "Showing {shown:,} of {total:,}",
"showing_all_records":     "Showing all {shown:,} records",

# ══════════════════════════════════════════════
# Filters
# ══════════════════════════════════════════════
"group_filter":            "🏷 Group:",
"balance_status_filter":   "Status:",
"all_groups":              "— All Groups —",
"balanced_filter":         "✅ Balanced",
"unbalanced_filter":       "⚠️ Unbalanced",
"move_type_all":           "All Movements",
"move_type_dr":            "Debit Only",
"move_type_cr":            "Credit Only",
"clear_filters":           "↺ Clear Filters",
"entry_date_label":        "Date:",
"entry_type_label":        "Type:",
"entry_desc_label":        "Description:",
```

---

## خامساً: التعديلات الكاملة — ملف بملف

---

### 1. `ui/widgets/core/conn.py` — إضافة alias

أضف داخل كلاس `SafeConnMixin` (بعد `_should_respond_to_company` مباشرةً):

```python
def _on_company_event_safe(self, company_id: int) -> bool:
    """Alias لـ _should_respond_to_company — للتوافق مع الكود الموجود."""
    return self._should_respond_to_company(company_id)
```

---

### 2. `ui/tabs/accounting/helpers.py` — تعديل كامل

```python
"""
ui/tabs/accounting/helpers.py
==============================
أدوات مساعدة صغيرة مشتركة بين تبويبات الحسابات.
"""
from db.accounting.accounting_schema import TYPE_AR, NORMAL_BALANCE
from ui.widgets.components.stat_card import stat_card_pair
from ui.widgets.panels.form_fields import spin_field


TYPE_COLORS = {
    "asset":    "#1565c0",
    "liability":"#c62828",
    "capital":  "#2e7d32",
    "revenue":  "#6a1b9a",
    "expense":  "#e65100",
    "drawings": "#4e342e",
}


def _spin(max_=999_999_999, dec=2, min_height: int = 30):
    """QDoubleSpinBox موحد — wrapper للتوافق مع الكود القديم في هذا المجلد."""
    return spin_field(max_=float(max_), dec=dec, min_height=min_height)


def _money(val: float) -> str:
    """تنسيق مبلغ مالي."""
    return f"{val:,.2f}  ج"


def _stat_card(label: str, color: str = "#1565c0"):
    """بطاقة إحصائية — يرجع (QFrame, QLabel_value)."""
    return stat_card_pair(label=label, color=color)
```

---

### 3. `ui/tabs/accounting/accounts_combo_widget.py` — تعديل import فقط

استبدل السطر:
```python
from ui.app_settings import _C
```
بـ:
```python
from ui.theme import _C
```

---

### 4. `ui/tabs/accounting/account_combo.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.font_utils import badge_style, badge_width
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.theme import _C
```

ثم احذف كل استخدام لـ `badge_style` و `badge_width` واستبدلها بدوال محلية صغيرة في نفس الملف:

```python
def _badge_style(side: str = "") -> str:
    if side == "dr":
        return (f"font-size:10px; font-weight:bold; color:{_C['badge_dr_text']};"
                f"background:{_C['badge_dr_bg']}; border-radius:3px; padding:2px 4px;")
    if side == "cr":
        return (f"font-size:10px; font-weight:bold; color:{_C['badge_cr_text']};"
                f"background:{_C['badge_cr_bg']}; border-radius:3px; padding:2px 4px;")
    return "font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px;"

_BADGE_WIDTH = 44
```

ثم استبدل كل `badge_style(...)` بـ `_badge_style(...)` وكل `badge_width()` بـ `_BADGE_WIDTH`.

---

### 5. `ui/tabs/accounting/accounts_tree.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.panels import (
    SectionHeader, _make_btn, get_splitter_style,
    get_tree_style, confirm_delete,
)
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_page import SectionHeader
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.theme.table_styles import splitter_style as get_splitter_style
from ui.widgets.theme.layout_styles import tree_style as get_tree_style
from ui.widgets.dialogs.confirm import confirm_delete
```

---

### 6. `ui/tabs/accounting/group_manager.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.color_picker_widget import ColorPickerWidget
from ui.widgets.shared.panels import (
    SectionHeader, _make_btn, get_tree_style, confirm_delete, ListStatusBar,
)
from ui.widgets.shared.form_utils import FormGroup
from ui.widgets.shared.panles_helper.mode_label import ModeLabel
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.helpers.color_picker import ColorPickerWidget
from ui.widgets.components.headers_page import SectionHeader
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.components.headers_list import StatusBar as ListStatusBar
from ui.widgets.theme.layout_styles import tree_style as get_tree_style
from ui.widgets.dialogs.confirm import confirm_delete
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.components.label import ModeLabel
```

---

### 7. `ui/tabs/accounting/accounting_tabs_builder.py` — تعديل كامل

```python
"""
ui/tabs/accounting/accounting_tabs_builder.py
==============================================
_AccountingTabsBuilder — دوال بناء التبويبات الفرعية للقسم المحاسبي.
"""
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSplitter, QTabWidget
from PyQt5.QtCore import Qt

from .accounts_tree import AccountsTreePanel
from .group_manager import _GroupManagerPanel
from .financial.trial_balance_tab    import TrialBalanceTab
from .financial.income_statement_tab import IncomeStatementTab
from .financial.owners_equity_tab    import OwnersEquityTab
from .financial.balance_sheet_tab    import BalanceSheetTab
from ui.widgets.theme.layout_styles import tab_style
from ui.widgets.theme.table_styles import splitter_style


# للتوافق مع accounting_section.py الذي يستورد _INNER_TAB_STYLE
_INNER_TAB_STYLE = tab_style(size="inner")


def _make_tab_widget(size: str = "inner") -> QTabWidget:
    """مساعد داخلي لإنشاء QTabWidget بستايل موحد."""
    tabs = QTabWidget()
    tabs.setLayoutDirection(Qt.RightToLeft)
    tabs.setStyleSheet(tab_style(size=size))
    return tabs


def build_accounts_tabs(acc):
    """يبني تبويبات قسم الحسابات."""
    # الأصول
    assets_inner = _make_tab_widget()
    assets_inner.addTab(AccountsTreePanel(acc, ["asset"], "الأصول"), "📊 الحسابات")
    assets_inner.addTab(_GroupManagerPanel(acc, "asset"), "🏷️ التصنيفات")

    # الخصوم
    liab_inner = _make_tab_widget()
    liab_inner.addTab(AccountsTreePanel(acc, ["liability"], "الخصوم"), "📊 الحسابات")
    liab_inner.addTab(_GroupManagerPanel(acc, "liability"), "🏷️ التصنيفات")

    # الرئيسية
    outer = _make_tab_widget()
    outer.addTab(assets_inner,          "🏦  الأصول")
    outer.addTab(liab_inner,            "📋  الخصوم")
    outer.addTab(build_equity_tab(acc), "👑  حقوق الملكية")
    return outer


def build_equity_tab(acc) -> QWidget:
    """يبني تبويب حقوق الملكية."""
    widget   = QWidget()
    root     = QVBoxLayout(widget)
    root.setContentsMargins(0, 0, 0, 0)
    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(5)
    splitter.setStyleSheet(splitter_style())

    tree_panel = AccountsTreePanel(
        acc,
        ["capital", "drawings", "revenue", "expense"],
        "حقوق الملكية"
    )
    splitter.addWidget(tree_panel)

    cat_tabs = _make_tab_widget()
    cat_tabs.addTab(_GroupManagerPanel(acc, "capital"),   "👑 رأس المال")
    cat_tabs.addTab(_GroupManagerPanel(acc, "drawings"),  "💸 المسحوبات")
    cat_tabs.addTab(_GroupManagerPanel(acc, "revenue"),   "💹 الإيرادات")
    cat_tabs.addTab(_GroupManagerPanel(acc, "expense"),   "📤 المصروفات")
    splitter.addWidget(cat_tabs)
    splitter.setSizes([600, 300])

    root.addWidget(splitter)
    return widget


def build_financial_tab(acc):
    """يبني تبويبات القوائم المالية."""
    tabs = _make_tab_widget(size="small")
    tabs.addTab(IncomeStatementTab(acc),  "📊 قائمة الدخل")
    tabs.addTab(OwnersEquityTab(acc),     "👑 حقوق الملكية")
    tabs.addTab(BalanceSheetTab(acc),     "🏛️ الميزانية العمومية")
    tabs.addTab(TrialBalanceTab(acc),     "⚖️ ميزان المراجعة")
    return tabs
```

---

### 8. `ui/tabs/accounting/audit_log_tab.py` — تعديل imports

استبدل:
```python
from ui.app_settings import _C, fs, get_font_size
from ui.widgets.theme.styles import (
    table_style, scroll_style, splitter_style, ROW_HEIGHT_NORMAL,
)
from ui.widgets.components.headers import ListHeader, StatusBar
from ui.widgets.components.button import make_btn
from ui.widgets.panels.state import EmptyState
from ui.widgets.core.conn import LiveConnMixin
```
بـ:
```python
from ui.theme import _C
from ui.font import fs, get_font_size
from ui.widgets.theme.table_styles import table_style, ROW_HEIGHT_NORMAL
from ui.widgets.components.headers_list import ListHeader, StatusBar
from ui.widgets.components.button import make_btn
from ui.widgets.panels.state import EmptyState
from ui.widgets.core.conn import LiveConnMixin
from ui.widgets.core.i18n import tr
```

**ثم استبدل كل النصوص الـ hardcoded في الملف:**

```python
# بدل النصوص الـ hardcoded في _ACTION_COLORS و _ACTION_ICONS و _TABLE_LABELS
# عدّل الـ _fill_table لتقرأ من _C:

_ACTION_COLORS = {
    "delete": lambda: (_C["audit_delete_fg"], _C["audit_delete_bg"]),
    "update": lambda: (_C["audit_update_fg"], _C["audit_update_bg"]),
    "create": lambda: (_C["audit_create_fg"], _C["audit_create_bg"]),
}

# بدل الـ hardcoded في _build_header:
# lbl.setStyleSheet(f"font-weight:bold; ...")
# استبدل بـ _C مباشرة في كل style

# بدل في _build_pagination:
# self._btn_load_more.setText(f"تحميل {_PAGE_SIZE} إضافي  ▼")
# استبدل بـ:
# self._btn_load_more.setText(tr("load_more", count=_PAGE_SIZE))

# بدل "لا توجد سجلات" و "لم يُسجَّل أي عملية حتى الآن":
# استبدل بـ tr("no_audit_records") و tr("no_audit_yet")

# بدل "— كل الجداول —" و "— كل الأنواع —":
# استبدل بـ tr("audit_all_tables") و tr("audit_all_types")
```

---

### 9. `ui/tabs/accounting/_state_widgets.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.empty_state_helpers import EmptyPanelState
```
بـ:
```python
from ui.widgets.panels.state import EmptyState
```

ثم غيّر كل `EmptyPanelState` في الملف إلى `EmptyState` مع إضافة `expandable=True`:

```python
def make_empty_state(icon: str = "📋",
                     title: str = "لا توجد بيانات",
                     subtitle: str = "",
                     action_text: str = "") -> EmptyState:
    return EmptyState(
        icon=icon,
        title=title,
        subtitle=subtitle,
        action_text=action_text,
        expandable=True,
    )
```

---

### 10. `ui/tabs/accounting/financial_statements.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.panels import make_financial_tabs
```
بـ:
```python
from ui.widgets.core.conn import SafeConnMixin
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtCore import Qt
from ui.widgets.theme.layout_styles import tab_style
```

ثم استبدل كل استدعاء `make_financial_tabs(...)` بـ:

```python
def _build(self):
    conn = self._get_safe_conn()
    self._tabs = QTabWidget()
    self._tabs.setLayoutDirection(Qt.RightToLeft)
    self._tabs.setStyleSheet(tab_style(size="small"))
    self._tabs.addTab(IncomeStatementTab(conn),  "📊 قائمة الدخل")
    self._tabs.addTab(OwnersEquityTab(conn),     "👑 حقوق الملكية")
    self._tabs.addTab(BalanceSheetTab(conn),     "🏛️ الميزانية العمومية")
    self._tabs.addTab(TrialBalanceTab(conn),     "⚖️ ميزان المراجعة")
    self._root_layout.addWidget(self._tabs)
```

---

### 11. `ui/tabs/accounting/ledger_tab.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.events import bus
```
بـ:
```python
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.events import bus
```

---

### 12. `ui/tabs/accounting/investors_tab.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
```
بـ:
```python
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.events import bus
```

احذف `from ui.events import bus` لو موجودة.

---

### 13. `ui/tabs/accounting/financial/trial_balance_tab.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.panels import (
    PageHeader, make_list_table, bold_table_item, colored_table_item,
)
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.tables.tables import (
    make_list_table,
    bold_item as bold_table_item,
    colored_item as colored_table_item,
)
from ui.widgets.core.i18n import tr
```

---

### 14. `ui/tabs/accounting/financial/balance_sheet_tab.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.helpers import make_table, section_label
from ui.widgets.shared.panels import PageHeader, StatRow, StatItem, NotificationBar
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.tables.tables import make_table
```

**واستبدل كل استخدام `section_label("نص")` بـ:**
```python
from PyQt5.QtWidgets import QLabel
# بدل: section_label("🏦 الأصول")
lbl = QLabel("🏦 الأصول")
lbl.setStyleSheet(
    f"font-weight:bold; color:{_C['accent']}; font-size:11px;"
    "background:transparent; border:none;"
)
```

أضف في أعلى الملف:
```python
from ui.theme import _C
```

---

### 15. `ui/tabs/accounting/financial/income_statement_tab.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.helpers import make_table, section_label
from ui.widgets.shared.panels import PageHeader, StatRow, StatItem
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.tables.tables import make_table
from ui.theme import _C
```

واستبدل كل `section_label("نص")` بـ:
```python
lbl = QLabel("نص")
lbl.setStyleSheet(
    f"font-weight:bold; color:{_C['accent']}; font-size:11px;"
    "background:transparent; border:none;"
)
```

---

### 16. `ui/tabs/accounting/financial/owners_equity_tab.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.helpers import make_table, section_label
from ui.widgets.shared.panels import PageHeader, StatRow, StatItem
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.tables.tables import make_table
from ui.theme import _C
```

واستبدل كل `section_label("نص")` بـ `QLabel` مع style من `_C` كما سبق.

---

### 17. `ui/tabs/accounting/ledger/ledger_accounts_panel.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.panels import ListHeader, ListStatusBar, get_tree_style
```
بـ:
```python
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_list import ListHeader, StatusBar as ListStatusBar
from ui.widgets.theme.layout_styles import tree_style as get_tree_style
```

احذف `from ui.events import bus` ← مش بتستخدمه مباشرة هنا.

---

### 18. `ui/tabs/accounting/ledger/ledger_filter_bar.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.panles_helper.filter_toolbar import FilterToolbar
```
بـ:
```python
from ui.widgets.panels.filter import FilterToolbar
```

**هام:** أضف في `_add_move_type_filter` استخدام `tr()` بدل النصوص الـ hardcoded:

```python
from ui.widgets.core.i18n import tr
# ...
self.cmb_move_type.addItem(tr("move_type_all"), None)
self.cmb_move_type.addItem(tr("move_type_dr"),  "dr")
self.cmb_move_type.addItem(tr("move_type_cr"),  "cr")
```

---

### 19. `ui/tabs/accounting/ledger/ledger_t_account.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.panels import PageHeader, BalanceDisplay
```
بـ:
```python
from ui.widgets.components.headers_page import PageHeader
from ui.widgets.components.amount_label import BalanceDisplay
from ui.theme import _C
```

**استبدل الألوان الـ hardcoded في `_make_t_table` و `_build` بـ `_C`:**

```python
# بدل: "background: white; border: 2px solid #c5cae9;"
f"background:{_C['bg_surface']}; border:2px solid {_C['t_account_frame']};"

# بدل: "background: #e3f2fd;"  في dr_hdr
f"background:{_C['t_account_dr_bg']};"

# بدل: "background: #fdecea;" في cr_hdr
f"background:{_C['t_account_cr_bg']};"

# بدل: "background: #1565c0; color: #1565c0;"
f"color:{_C['journal_dr_accent']};"

# بدل: "color: #c62828;"
f"color:{_C['journal_cr_accent']};"
```

---

### 20. `ui/tabs/accounting/ledger/ledger_stat_cards.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.stat_row import StatRow, StatItem
```
بـ:
```python
from ui.widgets.components.stat_card import StatRow, StatItem
```

---

### 21. `ui/tabs/accounting/tree/_group_filter.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
```
بـ:
```python
from ui.widgets.core.conn import SafeConnMixin
```

---

### 22. `ui/tabs/accounting/tree/_account_form.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
```

**احذف الدالة `_emit_data_changed` المحلية** واستبدل كل استخدامها بـ:
```python
from ui.widgets.core.events import emit_company_data_changed
# بدل _emit_data_changed():
emit_company_data_changed()
```

**احذف الدالة `_get_current_company_id` المحلية** — مش محتاجها بعد استخدام `emit_company_data_changed`.

---

### 23. `ui/tabs/accounting/journal/journal_filter.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.date_range_filter import DateRangeFilter
from ui.widgets.shared.company_utils import get_active_company_id
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.utils.date_range import DateRangeFilter
from ui.widgets.core.events import get_active_company_id
from ui.widgets.core.i18n import tr
```

**استبدل النصوص الـ hardcoded في `_build`:**
```python
# بدل: "— كل الأنواع —"
tr("all_groups")
# بدل: "✅ متوازن"
tr("balanced_filter")
# بدل: "⚠️ غير متوازن"
tr("unbalanced_filter")
# بدل: "↺ مسح الفلاتر"
tr("clear_filters")
# بدل: "🏷 التصنيف:"
tr("group_filter")
# بدل: "الحالة:"
tr("balance_status_filter")
```

---

### 24. `ui/tabs/accounting/journal/journal_tree_table.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.company_utils import get_active_company_id
from ui.widgets.shared.panels import (
    ListHeader, ListStatusBar, confirm_delete, _make_btn,
    bold_table_item, colored_table_item, center_table_item, set_row_background,
)
```
بـ:
```python
from ui.widgets.core.events import bus, get_active_company_id, emit_company_data_changed
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.components.headers_list import ListHeader, StatusBar as ListStatusBar
from ui.widgets.dialogs.confirm import confirm_delete
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.tables.tables import (
    bold_item as bold_table_item,
    colored_item as colored_table_item,
    center_item as center_table_item,
    set_row_bg as set_row_background,
)
```

**احذف الـ import الداخلي `from ui.widgets.shared.company_utils import emit_company_data_changed`** داخل `_delete_selected` واستخدم الـ import العلوي بدلاً منه.

---

### 25. `ui/tabs/accounting/journal/journal_tab_widget.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.events import bus
```
بـ:
```python
from ui.widgets.core.conn import SafeConnMixin
from ui.widgets.core.events import bus
```

**في `_get_erp_conn`:** استبدل `company_state._get_conn("erp")` بـ `company_state.get_erp_conn()` (public API):

```python
def _get_erp_conn(self):
    try:
        if self._erp_conn is not None:
            self._erp_conn.execute("SELECT 1")
            return self._erp_conn
    except Exception:
        pass
    try:
        from db.companies.company_state import company_state
        new = company_state.get_erp_conn()   # ← public API
        self._erp_conn = new
        return new
    except Exception:
        return self._erp_conn
```

---

### 26. `ui/tabs/accounting/journal/journal_form.py` — تعديل imports

استبدل:
```python
from ui.helpers import buttons_row
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.company_utils import emit_company_data_changed
```
بـ:
```python
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
```

**استبدل كل `buttons_row(btn1, btn2)` بـ layout inline:**
```python
btn_row = QHBoxLayout()
btn_row.setSpacing(8)
btn_row.addWidget(self.btn_save)
btn_row.addWidget(self.btn_cancel)
btn_row.addStretch()
root.addLayout(btn_row)
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل: "💾  حفظ القيد"
tr("entry_save_btn")
# بدل: "✖  مسح"
tr("entry_clear_btn")
# بدل: "── قيد يومية جديد ──"
tr("new_journal_entry")
# بدل: QMessageBox.warning(self, "تنبيه", "أدخل وصف القيد")
from ui.widgets.dialogs.message import msg_warning
msg_warning(self, tr("warning"), tr("enter_field", label=tr("description")))
# بدل: QMessageBox.warning(self, "تنبيه", "لا يوجد أي صف مدين (DR)")
msg_warning(self, tr("warning"), tr("no_dr_line"))
# بدل: QMessageBox.warning(self, "تنبيه", "لا يوجد أي صف دائن (CR)")
msg_warning(self, tr("warning"), tr("no_cr_line"))
# بدل: QMessageBox.information(self, "تم", "✅ تم حفظ القيد بنجاح")
from ui.widgets.dialogs.message import msg_info
msg_info(self, tr("done"), tr("journal_saved_success"))
```

**استبدل الألوان الـ hardcoded في `_build`:**
```python
from ui.theme import _C
# بدل "background:#1565c0; color:white;"
f"background:{_C['accent']}; color:{_C['accent_text']};"
# بدل "background:#b0bec5; color:#eceff1;"
f"background:{_C['text_disabled']}; color:{_C['bg_surface_2']};"
# بدل "background:#f5f5f5; color:#555;"
f"background:{_C['bg_surface_2']}; color:{_C['text_sec']};"
```

---

### 27. `ui/tabs/accounting/journal/account_picker/_account_picker_button.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
```
بـ:
```python
from ui.widgets.core.conn import SafeConnMixin
from ui.theme import _C
```

**استبدل الألوان الـ hardcoded في `_build` و `_update_nb_label`:**
```python
# بدل "background:#e3f2fd;" → f"background:{_C['badge_dr_bg']};"
# بدل "color:#1565c0;"      → f"color:{_C['badge_dr_text']};"
# بدل "background:#fdecea;" → f"background:{_C['badge_cr_bg']};"
# بدل "color:#c62828;"      → f"color:{_C['badge_cr_text']};"
```

---

### 28. `ui/tabs/accounting/journal/lines/_smart_line.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.company_utils import get_active_company_id
```
بـ:
```python
from ui.widgets.core.events import bus, get_active_company_id
from ui.widgets.core.conn import DualConnMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
```

**استبدل الألوان الـ hardcoded في `_update_side_style`:**
```python
# بدل "background: #f4f8ff; border: 1px solid #c5d8f7; border-right: 3px solid #1565c0;"
f"background:{_C['journal_dr_bg']}; border:1px solid {_C['journal_dr_border']}; border-right:3px solid {_C['journal_dr_accent']};"

# بدل "background: #fff4f4; border: 1px solid #f7c5c5; border-right: 3px solid #c62828;"
f"background:{_C['journal_cr_bg']}; border:1px solid {_C['journal_cr_border']}; border-right:3px solid {_C['journal_cr_accent']};"

# بدل "background: #fafbff; border: 1px solid #dde3f0;"
f"background:{_C['journal_neutral_bg']}; border:1px solid {_C['journal_neutral_border']};"
```

**استبدل الألوان الـ hardcoded في `_build` (الـ investor_row):**
```python
# بدل "background:#fff8e1; border:1px solid #ffe082;"
f"background:{_C['investor_link_bg']}; border:1px solid {_C['investor_link_border']};"

# بدل "color:#f57f17;"
f"color:{_C['investor_link_text']};"
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل "زيادة ✚"
tr("journal_increase")
# بدل "نقص ✖"
tr("journal_decrease")
# بدل "بيان..."
tr("line_description_placeholder")
# بدل "👤  ربط بمستثمر:"
tr("link_investor_to_entry")  # أو نص مناسب
# بدل "— لا يوجد ربط —"
tr("filter_all")
```

---

### 29. `ui/tabs/accounting/journal/lines/_lines_panel.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
```
بـ:
```python
from ui.widgets.core.conn import DualConnMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
```

**استبدل الألوان الـ hardcoded في `_build`:**
```python
# بدل "background: white; border: 1px solid #e0e0e0;"
f"background:{_C['bg_surface']}; border:1px solid {_C['border']};"

# بدل "background:#f0f4ff; border-radius:7px 7px 0 0;"
f"background:{_C['journal_header_bg']}; border-radius:7px 7px 0 0;"

# بدل "background:#e3f2fd;"
f"background:{_C['badge_dr_bg']};"

# بدل "background:#fdecea;"
f"background:{_C['badge_cr_bg']};"

# بدل "background:#f0f4ff; color:#1565c0;"
f"background:{_C['journal_header_bg']}; color:{_C['accent']};"
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل "📋  صفوف القيد"
tr("journal_lines_title")
# بدل "➕  إضافة صف"
tr("add_journal_line")
# بدل "لازم يكون في صف واحد على الأقل"
from ui.widgets.dialogs.message import msg_info
msg_info(None, tr("warning"), tr("min_one_row_required"))
```

---

### 30. `ui/tabs/accounting/journal/group_combo/_tree_group_combo.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import SafeConnMixin
from ui.widgets.shared.company_utils import get_active_company_id
```
بـ:
```python
from ui.widgets.core.events import bus, get_active_company_id
from ui.widgets.core.conn import SafeConnMixin
from ui.theme import _C
```

**استبدل الألوان الـ hardcoded في `_populate` و `_add_group_items`:**
```python
# بدل "background: white; border: 1px solid #c5cae9;"
f"background:{_C['bg_input']}; border:1px solid {_C['border_med']};"

# بدل "background: #e3f2fd; color: #1565c0;"
f"background:{_C['accent_light']}; color:{_C['accent_text']};"

# بدل "background: #f5f5f5;"
f"background:{_C['bg_hover']};"

# بدل "#f1f8e9"
_C["success_bg"]

# بدل "#f0f4ff"
_C["info_bg"]
```

---

### 31. `ui/tabs/accounting/journal/form/_balance_bar.py` — تعديل كامل (إضافة _C)

أضف في أعلى الملف:
```python
from ui.theme import _C
from ui.widgets.core.i18n import tr
```

**استبدل كل الألوان الـ hardcoded:**
```python
# في _build:
# بدل "background: #f0f4ff; border: 1px solid #c5cae9;"
f"background:{_C['journal_header_bg']}; border:1px solid {_C['journal_header_border']};"

# بدل "color:#c5cae9;"
f"color:{_C['border_med']};"

# بدل "color:#1565c0;" في lbl_dr_t
f"color:{_C['journal_dr_accent']};"

# بدل "background:#e3f2fd;" في lbl_sum_dr
f"background:{_C['badge_dr_bg']};"

# بدل "color:#c62828;" في lbl_cr_t
f"color:{_C['journal_cr_accent']};"

# بدل "background:#fdecea;" في lbl_sum_cr
f"background:{_C['badge_cr_bg']};"
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل "إجمالي DR:"
tr("total_debit") + ":"
# بدل "إجمالي CR:"
tr("total_credit") + ":"
# بدل "الفرق:"
tr("balance_bar_diff")
# بدل "○ أضف صفوف"
tr("balance_bar_add_rows")
# بدل "✅  متوازن — يمكن الحفظ"
tr("journal_balanced")
```

---

### 32. `ui/tabs/accounting/journal/form/_journal_header.py` — تعديل (إضافة tr)

أضف:
```python
from ui.widgets.core.i18n import tr
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل "وصف القيد الإجمالي..."
tr("entry_description_placeholder")
# بدل "التاريخ:"
tr("entry_date_label")
# بدل "النوع:"
tr("entry_type_label")
# بدل "الوصف:"
tr("entry_desc_label")
```

**بدل الـ _ENTRY_TYPES الـ hardcoded استخدم tr():**
```python
from ui.widgets.core.i18n import tr

def _get_entry_types():
    return [
        ("manual",   tr("entry_type_manual")),
        ("opening",  tr("entry_type_opening")),
        ("closing",  tr("entry_type_closing")),
        ("transfer", tr("entry_type_transfer")),
    ]
```

وفي `_build`:
```python
for key, label in _get_entry_types():
    self.cmb_type.addItem(label, key)
```

---

### 33. `ui/tabs/accounting/journal/form/_entry_meta.py` — تعديل (إضافة _C)

أضف:
```python
from ui.theme import _C
```

**بدل الـ `_TYPE_COLORS` الـ hardcoded** ابنيها من `_C` وأنواع الحسابات:
```python
def _get_type_colors(entry_type: str) -> tuple:
    """يرجع (fg, bg, border) من _C حسب نوع القيد."""
    mapping = {
        "manual":   (_C["accent"],      _C["accent_light"],    _C["accent_mid"]),
        "opening":  (_C["success"],     _C["success_bg"],      _C["success_border"]),
        "closing":  (_C["purple"],      _C["purple_bg"],       _C["purple_border"]),
        "transfer": (_C["orange"],      _C["orange_bg"],       _C["orange_border"]),
        "auto":     (_C["info"],        _C["info_bg"],         _C["info_border"]),
    }
    return mapping.get(entry_type, (_C["text_sec"], _C["bg_surface_2"], _C["border"]))
```

---

### 34. `ui/tabs/accounting/investors/_investor_form.py` — تعديل imports

استبدل:
```python
from ui.helpers import EditModeMixin
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.panels import FormGroup, ModeLabel, _make_btn, NotesLineEdit
from ui.widgets.shared.input_widgets import DateField, AmountSpinBox
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.mixins.form_mixins import EditModeMixin
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.components.label import ModeLabel
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.forms.inputs import NotesLineEdit, DateField, AmountSpinBox
from ui.theme import _C
from ui.widgets.core.i18n import tr
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل "اسم المستثمر..."
tr("name") + "..."
# بدل "تاريخ الانضمام:"
tr("investor_join_date") + ":"
# بدل "ملاحظات:"
tr("notes") + ":"
# بدل "مستثمر جديد"
tr("investor_new")
# بدل "➕  إضافة مستثمر"
tr("btn_add") + " " + tr("investors")
# بدل "💾  حفظ التعديل"
tr("btn_save")
# بدل "✖  إلغاء"
tr("btn_cancel")
```

---

### 35. `ui/tabs/accounting/investors/_movement_dialog.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.panels import FormGroup, _make_btn, NotesLineEdit
from ui.widgets.shared.input_widgets import DateField, AmountSpinBox
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.forms.inputs import NotesLineEdit, DateField, AmountSpinBox
from ui.theme import _C
from ui.widgets.core.i18n import tr
```

**استبدل الألوان الـ hardcoded في `_build`:**
```python
# بدل "#2e7d32" لرأس المال
_C["investor_capital_text"]
# بدل "#c62828" للمسحوبات
_C["investor_drawings_text"]
# بدل "#f1f8e9" و "#fdecea" للخلفية
_C["investor_capital_bg"] if is_cap else _C["investor_drawings_bg"]
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل "💰  إضافة رأس مال" و "💸  تسجيل مسحوبات"
tr("add_capital_title") if is_cap else tr("add_drawings_title")
# بدل "المبلغ (جنيه):"
tr("amount") + f" ({tr('currency')}):"
# بدل "التاريخ:"
tr("date") + ":"
# بدل "القيد المتوقع:"
tr("expected_entry")
# بدل "ملاحظات:"
tr("notes") + ":"
# بدل "✅  تسجيل"
tr("confirm")
# بدل "✖  إلغاء"
tr("btn_cancel")
```

---

### 36. `ui/tabs/accounting/investors/_link_to_entry_panel.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.panels import (
    FormGroup, spin_field, _make_btn, NotificationBar,
    make_form_layout, required_label, form_label, NotesLineEdit,
)
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.panels.form_group import FormGroup
from ui.widgets.panels.form_fields import spin_field
from ui.widgets.panels.form_labels import required_label, form_label
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.components.notification import NotificationBar
from ui.widgets.forms.inputs import NotesLineEdit
from ui.theme import _C
from ui.widgets.core.i18n import tr
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل "المستثمر:"
tr("investors")
# بدل "نوع الحركة:"
tr("type")
# بدل "رقم القيد:"
tr("ref_no")
# بدل "المبلغ:"
tr("amount")
# بدل "ملاحظات:"
tr("notes")
# بدل "🔗  ربط"
tr("link_entry_btn")
# بدل "💰  رأس مال (capital)" و "💸  مسحوبات (drawings)"
tr("investor_capital_badge") + " (capital)"
tr("investor_drawings_badge") + " (drawings)"
# بدل النص الطويل في lbl_info
tr("link_entry_info")
```

---

### 37. `ui/tabs/accounting/investors/_investor_details.py` — تعديل imports

استبدل:
```python
from ui.helpers import buttons_row, section_label, danger_button
from ui.events import bus
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
from ui.widgets.shared.panels import StatRow, StatItem
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.components.stat_card import StatRow, StatItem
from ui.widgets.components.button import make_btn
from ui.theme import _C
from ui.widgets.core.i18n import tr
```

**استبدل `buttons_row(btn)` بـ layout inline:**
```python
btn_row = QHBoxLayout()
btn_row.setSpacing(8)
btn_row.addWidget(btn_del_move)
btn_row.addStretch()
root.addLayout(btn_row)
```

**استبدل `section_label("نص")` بـ:**
```python
lbl = QLabel(tr("investor_movements"))
lbl.setStyleSheet(f"font-weight:bold; color:{_C['accent']}; font-size:11px; background:transparent; border:none;")
```

**استبدل `danger_button("🗑️  حذف الحركة المحددة")` بـ:**
```python
btn_del_move = make_btn(tr("btn_delete") + "  " + tr("movement_type"), "danger")
```

**استبدل الألوان الـ hardcoded في `_build` و `_refresh`:**
```python
# بدل "#e8f4fd" و "#90caf9"
_C["info_bg"], _C["info_border"]
# بدل "#1565c0"
_C["accent"]
# بدل "#1b5e20"
_C["success"]
# بدل "#b71c1c"
_C["danger"]
```

**استبدل النصوص الـ hardcoded:**
```python
# بدل "اختر مستثمراً لعرض تفاصيله"
tr("detail_select_item")
# بدل "إجمالي رأس المال"
tr("initial_capital")
# بدل "إجمالي المسحوبات"
tr("investor_drawings_badge").replace("💸 ", "")
# بدل "صافي الاستثمار"
tr("balance")
```

---

### 38. `ui/tabs/accounting/investors/_investors_table.py` — تعديل imports

استبدل:
```python
from ui.events import bus
from ui.widgets.shared.panels import (
    make_list_table, _make_btn, confirm_delete, auto_fit_columns,
    form_section_title, ROW_HEIGHT_LARGE,
)
from ui.widgets.shared.safe_conn_mixin import DualConnMixin
```
بـ:
```python
from ui.widgets.core.events import bus
from ui.widgets.core.conn import DualConnMixin
from ui.widgets.tables.tables import make_list_table, auto_fit_columns, ROW_HEIGHT_LARGE
from ui.widgets.components.button import make_btn as _make_btn
from ui.widgets.dialogs.confirm import confirm_delete
from ui.theme import _C
from ui.widgets.core.i18n import tr
```

**استبدل `form_section_title("نص")` بـ:**
```python
lbl = QLabel(tr("investor_list_title"))
lbl.setStyleSheet(f"font-weight:bold; color:{_C['accent']}; font-size:11px; background:transparent; border:none;")
```

**استبدل الألوان الـ hardcoded في `_load`:**
```python
# بدل QColor("#2e7d32")
QColor(_C["success"])
# بدل QColor("#c62828")
QColor(_C["danger"])
# بدل QColor("#1b5e20")
QColor(_C["success"])
# بدل QColor("#b71c1c")
QColor(_C["danger"])
```

**استبدل النصوص الـ hardcoded في أسماء الأزرار:**
```python
# بدل "✏️  تعديل"
tr("btn_edit")
# بدل "🗑️  حذف"
tr("btn_delete")
# بدل "💰  إضافة استثمار"
tr("investor_capital_badge")
# بدل "💸  مسحوبات"
tr("investor_drawings_badge")
# بدل "تنبيه", "اختر مستثمراً أولاً"
msg_info(self, tr("warning"), tr("select_item_first"))
```

---

### 39. `ui/tabs/accounting/investors/_investors_layout.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.tab_builder import make_tabs
```
بـ:
```python
from PyQt5.QtWidgets import QTabWidget
from PyQt5.QtCore import Qt
from ui.widgets.theme.layout_styles import tab_style
from ui.widgets.core.i18n import tr
```

ثم استبدل كل استدعاء `make_tabs(...)` بـ:

```python
def build_investors_tabs(acc_conn, erp_conn, on_investor_selected) -> tuple:
    main_widget, details = build_main_panel(acc_conn, erp_conn, on_investor_selected)

    tabs = QTabWidget()
    tabs.setLayoutDirection(Qt.RightToLeft)
    tabs.setStyleSheet(tab_style())
    tabs.addTab(main_widget, tr("investors"))
    tabs.addTab(_LinkToEntryPanel(acc_conn, erp_conn), tr("link_investor_to_entry"))

    return tabs, details
```

---

### 40. `ui/tabs/accounting/investors/_investors_panel.py` — تعديل imports

استبدل:
```python
from ui.widgets.shared.panels import get_splitter_style
```
بـ:
```python
from ui.widgets.theme.table_styles import splitter_style as get_splitter_style
```

---

### 41. `ui/tabs/accounting/investors/_helpers.py` — حذف الملف بالكامل

هذا الملف يُحذف تماماً. في كل ملف كان يستورد منه، استبدل:

```python
# بدل: from ._helpers import _spin, _stat_card
from ui.widgets.panels.form_fields import spin_field as _spin
from ui.widgets.components.stat_card import stat_card_pair as _stat_card
```

---

### 42. `ui/tabs/accounting/_conn_guard.py` — تعديل imports

```python
# لا يحتاج تعديل imports — الملف يستخدم مباشرة db.companies و db.shared
# لكن تأكد من إزالة أي import من ui.events القديم لو موجود
```

---

### 43. `ui/tabs/accounting/accounting_section.py` — تعديل imports فقط

```python
# لا يحتاج تعديل — الملف نظيف ومش بيستخدم wrappers وهمية
# فقط تأكد أن هذا الـ import موجود:
from ui.widgets.theme.layout_styles import tab_style
# إذا كانت _TAB_STYLE محتاجة، استبدلها بـ: tab_style()
```

---

## سادساً: التحسينات المقترحة

### أ. إنشاء `ui/tabs/accounting/journal/form/_balance_indicator.py` (ملف جديد)

```python
"""
بديل لـ _BalanceBar المستقل — يدعم تحديث الألوان عند تغيير الثيم.
"""
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel
from ui.theme import _C
from ui.widgets.core.events import bus
from ui.widgets.core.i18n import tr


class BalanceBar(QFrame):
    """شريط توازن القيد — يتحدث تلقائياً مع تغيير الثيم واللغة."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        bus.theme_changed.connect(lambda _: self._apply_style())
        bus.language_changed.connect(lambda _: self._update_labels())

    def _apply_style(self):
        self.setStyleSheet(
            f"QFrame {{ background:{_C['journal_header_bg']};"
            f"border:1px solid {_C['journal_header_border']}; border-radius:6px; }}"
        )

    def _update_labels(self):
        self._lbl_dr_title.setText(tr("total_debit") + ":")
        self._lbl_cr_title.setText(tr("total_credit") + ":")
        self._lbl_diff_title.setText(tr("balance_bar_diff"))
```

### ب. إضافة `_on_language_changed` للـ Smart Line

في `_smart_line.py`، أضف:
```python
bus.language_changed.connect(self._on_lang_changed)

def _on_lang_changed(self, _):
    self.rdo_inc.setText(tr("journal_increase"))
    self.rdo_dec.setText(tr("journal_decrease"))
    self.inp_desc.setPlaceholderText(tr("line_description_placeholder"))
```

### ج. استخدام `ProtectedConnection.path_matches` في `_conn_guard.py`

```python
# بدل PRAGMA database_list في verify_conn_belongs_to_company:
def verify_conn_belongs_to_company(conn, expected_company_id: int) -> bool:
    if conn is None or expected_company_id is None:
        return False
    try:
        expected_path = _get_expected_path(expected_company_id)
        if not expected_path:
            return False
        # استخدام path_matches السريعة لو ProtectedConnection
        if hasattr(conn, 'path_matches'):
            return conn.path_matches(expected_path)
        # fallback لـ sqlite3.Connection العادي
        conn.execute("SELECT 1").fetchone()
        row = conn.execute("PRAGMA database_list").fetchone()
        if not row:
            return False
        actual_path   = row[2] if len(row) > 2 else ""
        actual_norm   = os.path.normcase(os.path.realpath(actual_path))
        expected_norm = os.path.normcase(os.path.realpath(expected_path))
        return actual_norm == expected_norm
    except Exception:
        return False
```

---

## سابعاً: ترتيب التطبيق

1. **أضف alias `_on_company_event_safe`** في `ui/widgets/core/conn.py`
2. **أضف الألوان الجديدة** في `ui/theme_manager.py` (كلا الثيمين)
3. **أضف مفاتيح الترجمة** في `ui/i18n/ar.py` و `ui/i18n/en.py`
4. **عدّل ملفات `helpers.py`** و `accounts_combo_widget.py`
5. **عدّل ملفات `ledger/`** (الأبسط — imports فقط)
6. **عدّل ملفات `tree/`** (imports فقط)
7. **عدّل ملفات `financial/`** (imports + section_label)
8. **عدّل ملفات `investors/`** (imports + hardcoded text + colors)
9. **عدّل ملفات `journal/`** (الأعقد — imports + text + colors)
10. **احذف الملفات الوهمية** من `ui/widgets/shared/`
11. **احذف** `ui/tabs/accounting/investors/_helpers.py`

---

## ثامناً: قائمة التحقق قبل التطبيق

- [ ] `_on_company_event_safe` موجود في `SafeConnMixin`
- [ ] كل الألوان الجديدة في كلا الثيمين في `theme_manager.py`
- [ ] كل مفاتيح الترجمة موجودة في `ar.py` **و** `en.py`
- [ ] لا يوجد `from ui.events import bus` — كله `from ui.widgets.core.events import bus`
- [ ] لا يوجد `from ui.app_settings import _C` — كله `from ui.theme import _C`
- [ ] لا يوجد `from ui.helpers import ...`
- [ ] لا يوجد `from ui.widgets.shared.panels import ...`
- [ ] لا يوجد `from ui.widgets.shared.safe_conn_mixin import ...`
- [ ] كل `section_label(...)` تحول لـ `QLabel` مع style من `_C`
- [ ] كل `buttons_row(...)` تحول لـ `QHBoxLayout` مباشرة
- [ ] كل `danger_button(...)` تحول لـ `make_btn(..., "danger")`
- [ ] كل `setup_table_columns(...)` تحول لـ `auto_fit_columns(...)`
- [ ] `_helpers.py` محذوف من `investors/`
- [ ] `emit_company_data_changed()` لا تستخدم `company_state._get_conn` (private)