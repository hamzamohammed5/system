# دليل الكود — Services المحاسبة (services/accounting/)

> `services/accounting/` — الحسابات، سجل التدقيق، الترحيل المحاسبي للمخزون، المستثمرون، القيود اليومية، القوائم المالية.
> **الملفات الفعلية:** `accounts_service.py`, `audit_service.py`, `inventory_posting_service.py`, `investors_service.py`, `journal_service.py`, `statements_service.py`

---

## فهرس

| الملف | الوصف |
|-------|-------|
| [accounts_service.py](#accounts_servicepy) | AccountsService — شجرة الحسابات وتصنيفاتها (account_groups) |
| [journal_service.py](#journal_servicepy) | JournalService — القيود المحاسبية: إنشاء/تعديل/عكس/حذف |
| [statements_service.py](#statements_servicepy) | StatementsService — ميزان المراجعة، قائمة الدخل، الميزانية، حقوق الملكية |
| [investors_service.py](#investors_servicepy) | InvestorsService — CRUD المستثمرين وربطهم بالقيود |
| [audit_service.py](#audit_servicepy) | AuditService — قراءة سجل التدقيق (audit_log) فقط |
| [inventory_posting_service.py](#inventory_posting_servicepy) | InventoryPostingService — شراء مخزون + قيد محاسبي معاً |

---

## accounts_service.py

### `services/accounting/accounts_service.py`

**الغرض:** Business Logic لحسابات الشجرة المحاسبية (`accounts`) وتصنيفاتها (`account_groups`). يغطي الاستخدامات السابقة في `ui/tabs/accounting/account_combo.py`, `accounts_tree.py`, `helpers.py`.

**Imports (top-level):** لا يوجد — كل استيرادات `db.accounting.accounting_accounts_repo` و `db.accounting.accounting_schema_constants` تتم بشكل **lazy** داخل كل method.

**من يستدعي هذا الملف:** `services/inventory/inventory_service.py` (composition — `AccountsService(acc_conn)` لجلب قوائم حسابات الدفع). متوقع أيضاً من `ui/tabs/accounting/account_combo.py`, `accounts_tree.py`, `group_manager.py` حسب توثيق الملف نفسه.

### Dataclasses

```python
@dataclass
class DeleteAccountPreview:
    account_id      : int
    account_name    : str
    has_lines       : bool
    lines_count     : int
    child_ids       : list = field(default_factory=list)
    can_delete      : bool = True
    reason          : str  = ""
```
- `.child_count -> int` (property): `len(child_ids) - 1` لو `child_ids` موجودة، وإلا `0`.
- `.warning_text() -> str`.

```python
@dataclass
class DeleteGroupPreview:
    group_id     : int
    group_name   : str
    linked_count : int
```
- `.warning_text() -> str`.

### Class: `AccountsService`
لا يرث من شيء.

```python
AccountsService(conn)
```

**Methods — قراءة الحسابات:**
- **`list_accounts_basic(self, acc_type=None) -> list`**: حسابات بدون أرصدة — للـ dropdowns والـ combos، عبر `fetch_all_accounts_basic`.
- **`list_accounts_with_balance(self, acc_type=None) -> list`**: حسابات مع أرصدتها — للتقارير والقوائم المالية، عبر `fetch_all_accounts_with_balance`.
- **`list_all_accounts(self, acc_type=None) -> list`**: للتوافق — يستخدم `fetch_all_accounts` (يساوي `with_balance`).
- **`get_account(self, account_id)`**: عبر `fetch_account`.
- **`get_account_by_code(self, code)`**: عبر `fetch_account_by_code`.
- **`list_leaf_accounts(self, acc_types: list = None) -> list`**: حسابات الأوراق (`is_leaf=1`) عبر `fetch_leaf_accounts`؛ لو `acc_types` محدد بأكثر من نوع، يفلتر بعد الجلب (مطابق لسلوك `account_combo.py` الأصلي).

**Methods — كتابة الحسابات:**
- **`add_account(self, code, name, acc_type, parent_id=None, group_id=None, subtype=None, notes=None) -> int`**: يتحقق `name`/`code` غير فارغَين (بعد `.strip()`)، وإلا `ValueError`. عبر `insert_account`.
- **`update_account(self, account_id, name, group_id=None, notes=None)`**: يتحقق `name` غير فارغ. عبر `update_account` من الـ repo.
- **`get_delete_preview(self, account_id) -> DeleteAccountPreview | None`**: **[منقول من `accounts_tree.py._delete`]** — كان منطق SQL مباشر في الـ UI. يجمع كل IDs الحساب وأبنائه عبر `_get_all_descendant_ids` (تكراري)، يعدّ `journal_lines` المرتبطة بأي منهم؛ لو `lines_count > 0` → `can_delete=False`.
- **`delete_account_cascade(self, account_id) -> bool`**: يحذف الحساب وكل حساباته الفرعية (بترتيب عكسي `reversed(preview.child_ids)`) فقط لو لا توجد قيود مرتبطة (`can_delete`)؛ يرجع `False` وإلا.
- **`_get_all_descendant_ids(self, account_id) -> list`**: تكرارية — تجمع `account_id` نفسه + كل الأبناء عبر `SELECT id FROM accounts WHERE parent_id=?`.

**Methods — أرصدة الحسابات:**
- **`get_account_balance(self, account_id) -> float`**: عبر `get_account_balance` من الـ repo.
- **`get_account_natural_balance(self, account_id) -> float`**: عبر `get_account_natural_balance`.
- **`get_normal_balance(self, acc_type) -> str`**: `"dr"` أو `"cr"` — عبر `get_normal_balance` من الـ repo.
- **`get_type_labels_map(self) -> dict`**: يرجع نسخة `dict` كاملة من `TYPE_AR` — بديل لاستيراد `TYPE_AR` من `accounting_schema` مباشرة في `tabs/` (ثابت عرض وليس بيانات، نفس منطق `statements_service.get_type_label`).
- **`get_equity_types(self) -> set`**: يرجع `set` من `EQUITY_TYPES` (capital, drawings, revenue, expense) — بديل لاستيراد `EQUITY_TYPES` مباشرة في `tabs/`.
- **`calc_signed_amount(self, acc_type, increase, amount) -> tuple`**: عبر `calc_signed_amount` من الـ repo.
- **`get_balances_by_type(self) -> dict`**: عبر `get_balances_by_type`.

**Methods — تصنيفات الحسابات (`account_groups`):**
- **`list_groups(self, acc_type=None) -> list`**: عبر `fetch_all_groups`.
- **`get_group(self, group_id)`**: عبر `fetch_group`.
- **`build_group_tree(self, rows) -> list`**: عبر `build_group_tree` من الـ repo.
- **`get_group_descendants(self, group_id) -> set`**: **wrapper رسمي** حول `_get_group_descendants` (دالة `private` في الـ repo) — أي كود UI يحتاج descendants يستدعي هذه الدالة بدل استيراد الدالة الخاصة مباشرة.
- **`add_group(self, name, acc_type, parent_id=None, color="#607d8b") -> int`**: يتحقق `name` غير فارغ. عبر `insert_group`.
- **`update_group(self, group_id, name, parent_id=None, color="#607d8b")`**: يتحقق `name` غير فارغ. عبر `update_group`.
- **`get_group_delete_preview(self, group_id) -> DeleteGroupPreview | None`**: يعدّ الحسابات المرتبطة بالتصنيف (`accounts WHERE group_id=?`).
- **`delete_group(self, group_id)`**: عبر `delete_group` من الـ repo.
- **`count_accounts_in_group(self, group_id) -> int`**: `accounts WHERE group_id=? AND is_leaf=1` — تُستخدم في `group_manager.py` لعرض عدد الحسابات لكل تصنيف في الشجرة.
- **`count_all_accounts_in_group(self, group_id) -> int`**: نفس الشيء **بدون** فلتر `is_leaf` (يحسب كل الحسابات، فروع وأوراق) — تُستخدم في `group_manager.py._delete` لعرض تحذير قبل حذف تصنيف؛ استعلام SQL منقول حرفياً من الأصل.

---

## journal_service.py

### `services/accounting/journal_service.py`

**الغرض:** Business Logic للقيود المحاسبية — إنشاء/تعديل/حذف/عكس القيود + حساب الأرصدة.

**Imports (top-level):**
```python
from dataclasses import dataclass, field
from datetime import datetime
```
كل استيرادات `db.accounting.accounting_journal_repo`, `accounting_repo`, `accounting_repo_ui_helpers` تتم بشكل **lazy** داخل كل method.

**من يستدعي هذا الملف:** متوقع من `ui/tabs/accounting/journal/journal_form.py`, `journal_tree_table.py`, `journal_tab_widget.py`, `ledger/ledger_t_account.py`, `journal/group_combo/_tree_group_combo.py` حسب توثيق الملف نفسه — لكن محتواها غير مرفق.

**[إصلاح 35] موثّق في الكود:** مزامنة الـ imports مع الدوال الفعلية في `accounting_journal_repo`:
- `insert_journal_entry` → **`insert_entry`**
- `insert_journal_line` → **`add_entry_lines`** (batch، وليست دالة واحدة لكل سطر)
- `update_journal_entry` → **`update_entry`** غير موجودة أصلاً في الـ repo؛ استُبدلت بـ SQL مباشر داخل الـ service نفسه
- `delete_journal_lines` → **`_delete_entry_lines`** دالة مساعدة داخلية جديدة
- `delete_journal_entry` → **`delete_entry`**

### Dataclasses

```python
@dataclass
class JournalLine:
    account_id : int
    dr         : float = 0.0
    cr         : float = 0.0
    note       : str   = ""
```
- `.is_valid() -> bool` — `(dr > 0) != (cr > 0)` — صف واحد فيه `dr` أو `cr` وليس الاثنين معاً.
- `.amount() -> float` — يرجع `dr` لو `dr > 0` وإلا `cr`.
- `.side() -> str` — `"dr"` أو `"cr"`.

```python
@dataclass
class BalanceCheck:
    total_dr : float
    total_cr : float
```
- `.is_balanced -> bool` (property): `abs(total_dr - total_cr) < 0.001`.
- `.diff -> float` (property).
- `.error_text() -> str | None`: رسالة الفرق لو غير متوازن، وإلا `None`.

```python
@dataclass
class EntryResult:
    entry_id    : int
    is_new      : bool
    total_dr    : float
    total_cr    : float
    lines_count : int
```

```python
@dataclass
class DeletePreview:
    entry_id   : int
    entry_ref  : str
    is_posted  : bool
    can_delete : bool
    reason     : str = ""
```
- `.warning_text() -> str`.

```python
@dataclass
class AccountBalance:
    account_id   : int
    account_name : str
    total_dr     : float
    total_cr     : float
```
- `.balance -> float` (property): `total_dr - total_cr`.
- `.side -> str` (property): `"dr"` لو `balance >= 0` وإلا `"cr"`.

### Class: `JournalService`
لا يرث من شيء.

```python
JournalService(conn)
```

**Methods — Validation:**
- **`check_balance(self, lines: list[JournalLine]) -> BalanceCheck`**.
- **`validate_lines(self, lines) -> list[str]`**: يتحقق: وجود صفوف (وإلا رسالة واحدة فقط وتوقف)، لكل صف: `account_id` غير فارغ، مبالغ غير سالبة، `dr` أو `cr` (ليس صفر ولا الاثنين معاً)، ثم التوازن الكلي عبر `check_balance`.

**Methods — قراءة:**
- **`get_account_balance(self, account_id, date_from=None, date_to=None) -> AccountBalance`**: SQL مباشر — `JOIN journal_lines + journal_entries + accounts`، فلترة اختيارية بـ `date_from`/`date_to`. لو لا توجد حركات → يجلب اسم الحساب من `accounts` ويرجع أرصدة صفرية.
- **`get_entry_by_ref(self, ref_no)`**: يستدعي `fetch_entry_by_ref` من `accounting_repo_ui_helpers` (يعيد استخدام repo helper جاهزة).
- **`get_t_account(self, account_id)`**: بيانات حساب T كاملة (`account`, `normal_balance`, `lines`) عبر `fetch_t_account` — منقولة من `ledger_t_account.py.load` (بديل لاستيراد `db.accounting.accounting_repo` مباشرة في `tabs/`).
- **`get_line_id(self, entry_id, side) -> int`**: يرجع `id` أول سطر من الجانب المطلوب. `side="credit"` → أول سطر دائن (لقيود رأس المال) عبر `fetch_capital_line_for_entry`. `side="debit"` → أول سطر مدين (لقيود المسحوبات) عبر `fetch_drawings_line_for_entry`. غير ذلك → `ValueError`.
- **`list_entries_with_lines(self, limit=200) -> list`**: يرجع كل القيود مع سطورها المتداخلة — منقولة من `journal_tree_table.py._load` (كانت تستدعي `fetch_all_entries`/`fetch_entry_lines` مباشرة من `tabs/`). شكل كل عنصر: `{id, ref_no, date, type, description, total_debit, total_credit, lines: [...]}`.
- **`get_entry_ids_for_groups(self, group_ids) -> set`**: يرجع `entry_id` لكل القيود التي تحتوي سطراً على حساب منتمٍ لأي `group_ids`. منقولة من `_tree_group_combo.py._update_selection` (كانت SQL خام في `tabs/`).

**Methods — Post Entry:**
- **`post_entry(self, entry_data: dict, lines: list[JournalLine]) -> EntryResult`**: `entry_data`: `{date, description, ref?, entry_type?, notes?}`. يستدعي `validate_lines` أولاً (يرمي `ValueError` مجمّعة بـ `"\n".join(errors)` لو فشلت). `date=None` → `datetime.now().strftime("%Y-%m-%d")`. `desc` مطلوب وإلا `ValueError`. **[إصلاح 35]** يستخدم `insert_entry` + `add_entry_lines` (تحويل `JournalLine` → `dict {account_id, debit, credit, description}`). يرجع `EntryResult(is_new=True, ...)`.
- **`update_entry(self, entry_id, entry_data, lines) -> EntryResult`**: يرفض (`ValueError`) لو `entry["status"] == "reversed"`. يتحقق الصفوف. **[إصلاح 35]** يُحدّث `journal_entries` بـ **SQL مباشر** (`UPDATE journal_entries SET date=?, description=? WHERE id=?` + `commit`) لأن `update_journal_entry` غير موجودة في الـ repo. يستدعي `_delete_entry_lines(entry_id)` ثم `add_entry_lines` للجديدة. يرجع `EntryResult(is_new=False, ...)`.

**Methods — Reverse:**
- **`reverse_entry(self, entry_id, note="") -> EntryResult`**: يجلب صفوف القيد عبر `fetch_entry_lines` (الاسم الفعلي). يرفض لو لا صفوف (`ValueError`). يبني `reversed_lines` بعكس `dr`/`cr` لكل صف. يبني وصف `"عكس القيد رقم {ref_no}"` (+ `note` لو مُمرَّر). يستدعي `post_entry` داخلياً ويرجع النتيجة.

**Methods — Delete:**
- **`get_delete_preview(self, entry_id) -> DeletePreview | None`**: يرفض (`can_delete=False`) لو `status == "reversed"` مع سبب "القيد مُعكوس".
- **`delete(self, entry_id) -> bool`**: يتحقق `get_delete_preview` أولاً، وإلا `False`. **[إصلاح 35]** يستخدم `delete_entry` (الاسم الفعلي).

**Methods — Helpers (داخلية):**
- **`_get_entry_or_raise(self, entry_id) -> dict`**: `SELECT * FROM journal_entries WHERE id=?` — يرمي `ValueError` لو غير موجود.
- **`_delete_entry_lines(self, entry_id)`**: **[إصلاح 35]** دالة مساعدة داخلية — بديل عن `delete_journal_lines` غير الموجودة في الـ repo. `DELETE FROM journal_lines WHERE entry_id=?` + `commit`. `journal_lines` لديها CASCADE على `entry_id` لكن يُستخدم `DELETE` المباشر صراحة.

---

## statements_service.py

### `services/accounting/statements_service.py`

**الغرض:** Business Logic للقوائم المالية — ميزان المراجعة، قائمة الدخل، الميزانية العمومية، قائمة حقوق الملكية. يغطي `income_statement_tab.py`, `owners_equity_tab.py`, `trial_balance_tab.py`.

**Imports (top-level):** `from dataclasses import dataclass, field` فقط — كل استيرادات `db.accounting.accounting_statements_repo`, `accounting_accounts_repo`, `accounting_schema_constants` تتم بشكل **lazy**.

**من يستدعي هذا الملف:** `ui/tabs/accounting/financial/income_statement_tab.py`, `owners_equity_tab.py`, `trial_balance_tab.py` (حسب توثيق الملف نفسه؛ محتواها غير مرفق).

**ملاحظة معمارية موثّقة (بنفس منطق `accounts_service.py`):** `TYPE_AR` ثابت عرض (`dict` ثابت لا يُقرأ من DB) وليس بيانات — لذلك يُعرَض هنا كدالة `get_type_label` بدل تحويله لاستعلام، حتى لا تحتاج `tabs/` لاستيراد `accounting_schema_constants` مباشرة.

### Dataclasses

```python
@dataclass
class TrialBalanceRow:
    code : str
    name : str
    type : str
    total_debit  : float
    total_credit : float
    balance      : float
```
> ملاحظة: هذا الـ dataclass معرَّف لكن **لا يُستخدم فعلياً** في `get_trial_balance` (التي ترجع `list[dict]` صراحةً — راجع التعليق في الكود نفسه).

```python
@dataclass
class IncomeStatementResult:
    revenues   : list = field(default_factory=list)
    expenses   : list = field(default_factory=list)
    total_rev  : float = 0.0
    total_exp  : float = 0.0
    net_income : float = 0.0
```
> نفس الملاحظة: `get_income_statement` ترجع `dict` مباشرة وليس هذا الـ dataclass.

```python
@dataclass
class OwnersEquityResult:
    capital_accounts  : list = field(default_factory=list)
    drawings_accounts : list = field(default_factory=list)
    net_income        : float = 0.0
    total_capital     : float = 0.0
    total_drawings    : float = 0.0
    total_equity      : float = 0.0
```

```python
@dataclass
class BalanceSheetResult:
    assets       : list = field(default_factory=list)
    liabilities  : list = field(default_factory=list)
    capital      : list = field(default_factory=list)
    drawings     : list = field(default_factory=list)
    net_income   : float = 0.0
    total_assets : float = 0.0
    total_liab   : float = 0.0
    total_equity : float = 0.0
```

### Class: `StatementsService`
لا يرث من شيء.

```python
StatementsService(conn)
```

- **`get_trial_balance(self) -> list`**: يرجع `list[dict]` بنفس شكل `accounting_statements_repo.trial_balance` (`code, name, type, total_debit, total_credit, balance`) — **شكل الإرجاع `dict` وليس `TrialBalanceRow`** حفاظاً على توافق الـ UI الحالي الذي يقرأ `row["code"]`, `row["balance"]` مباشرة.
- **`get_normal_balance(self, acc_type) -> str`**: `"dr"` أو `"cr"` — بديل لاستيراد `get_normal_balance` من `accounting_accounts_repo` مباشرة.
- **`get_income_statement(self) -> dict`**: `{revenues, expenses, total_rev, total_exp, net_income}` عبر `income_statement` من الـ repo — نفس الشكل، وليس `IncomeStatementResult`.
- **`get_balance_sheet(self) -> dict`**: `{assets, liabilities, capital, drawings, net_income, total_assets, total_liab, total_equity}` عبر `balance_sheet`.
- **`get_owners_equity_statement(self) -> dict`**: `{capital_accounts, drawings_accounts, net_income, total_capital, total_drawings, total_equity}` عبر `owners_equity_statement`.
- **`get_type_label(self, acc_type) -> str`**: التسمية العربية لنوع الحساب — عبر `TYPE_AR.get(acc_type, acc_type)` من `accounting_schema_constants`.

---

## investors_service.py

### `services/accounting/investors_service.py`

**الغرض:** Business Logic للمستثمرين — CRUD، ربط/فك ربط بالقيود المحاسبية، وتقارير الملخص. يغطي `ui/tabs/accounting/investors_tab.py` وكل ملفات `ui/tabs/accounting/investors/*`.

**Imports (top-level):** `from dataclasses import dataclass` فقط — كل استيرادات `db.accounting.investors_repo` و `accounting_repo_ui_helpers` تتم بشكل **lazy**.

**من يستدعي هذا الملف:** `ui/tabs/accounting/investors_tab.py` وملفات `ui/tabs/accounting/investors/*` (`_investors_panel.py`, `_investor_form.py`, `_movement_dialog.py`, إلخ حسب `system_arch.txt`؛ محتواها غير مرفق).

**ملاحظة معمارية موثّقة:** `investors_repo.py` يعيش في `db/accounting/` لأن جداوله (`investors`, `investor_entries`) مرتبطة بـ `journal_entries` في `accounting.db`، لكن بعض القراءات (تفاصيل القيد والسطر) تحتاج `acc_conn` منفصل — لذلك هذا الـ service يقبل الاثنين، تماماً كما كان في `investors_tab.py` القديم.

### Dataclass

```python
@dataclass
class InvestorSaveResult:
    investor_id : int
    is_new      : bool
    name        : str
```

### Class: `InvestorsService`
لا يرث من شيء.

```python
InvestorsService(conn, acc_conn=None)
```
- `conn`: اتصال على القاعدة التي تحوي جداول `investors`/`investor_entries`.
- `acc_conn`: اتصال على `accounting.db` لجلب تفاصيل القيود (اختياري).

**Methods — Migration:**
- **`migrate(self)`**: يستدعي `_migrate_investors(self._conn)` (دالة `private` في الـ repo) داخل `try/except` — يطبع خطأ لو فشل. تُستدعى مرة عند بناء التبويب.

**Methods — CRUD مستثمرين:**
- **`list_investors(self) -> list`**: عبر `fetch_all_investors`.
- **`get_investor(self, investor_id)`**: عبر `fetch_investor`.
- **`investor_exists(self, name)`**: عبر `investor_exists` من الـ repo.
- **`add_investor(self, name, notes=None, joined_at=None) -> InvestorSaveResult`**: يتحقق `name` غير فارغ (`ValueError`)، ويتحقق عدم وجود مستثمر بنفس الاسم (`ValueError` "يوجد مستثمر بنفس الاسم"). عبر `insert_investor`.
- **`update_investor(self, investor_id, name, notes=None, joined_at=None) -> InvestorSaveResult`**: يتحقق `name` غير فارغ. عبر `update_investor` من الـ repo.
- **`delete_investor(self, investor_id)`**: **[ملاحظة موثّقة]** لا يفحص وجود روابط `investor_entries` قبل الحذف — نفس سلوك `delete_investor` في الـ repo الأصلي (حذف مباشر بدون فحص CASCADE). لمنع الحذف عند وجود روابط، استخدم `get_investor_links_count` أولاً.
- **`get_investor_links_count(self, investor_id) -> int`**: `SELECT COUNT(*) FROM investor_entries WHERE investor_id=?` — يساعد الـ UI على تحذير المستخدم قبل حذف مستثمر له حركات مسجلة. يرجع `0` عند أي استثناء.
- **`get_entry_id_for_link(self, link_id)`**: يرجع `entry_id` المرتبط بـ `link_id` عبر `fetch_investor_entry_id` — يُستخدم قبل حذف القيد عند حذف حركة مستثمر.

**Methods — ربط المستثمر بالقيود:**
- **`link_to_line(self, investor_id, entry_id, line_id, move_type, amount, notes=None) -> int`**: يتحقق `move_type in ("capital", "drawings")` وإلا `ValueError`. يتحقق `amount > 0` وإلا `ValueError`. عبر `link_investor_to_line`.
- **`get_entry_investor_links(self, entry_id) -> list`**: عبر `fetch_entry_investor_links`.
- **`unlink(self, link_id)`**: عبر `delete_investor_link`.
- **`unlink_entry(self, entry_id)`**: يفك كل روابط المستثمرين بقيد معين — يُستخدم قبل حذف القيد نفسه، عبر `delete_entry_investor_links`.

**Methods — التقارير:**
- **`get_investor_summary(self, investor_id) -> dict`**: ملخص مستثمر واحد (رأس مال/مسحوبات/صافي) + حركاته، عبر `calc_investor_summary(acc_conn=self._acc_conn)`.
- **`get_all_investors_summary(self) -> list`**: ملخص كل المستثمرين مرتبين تنازلياً حسب صافي الاستثمار، عبر `calc_all_investors_summary(acc_conn=self._acc_conn)`.
- **`get_investor_entries(self, investor_id) -> list`**: عبر `fetch_investor_entries(acc_conn=self._acc_conn)`.

---

## audit_service.py

### `services/accounting/audit_service.py`

**الغرض:** Business Logic لسجل التدقيق (Audit Log) — **قراءة فقط، بدون كتابة مباشرة من الـ UI**. يغطي `ui/tabs/accounting/audit_log_tab.py`.

**Imports (top-level):** `from dataclasses import dataclass` فقط — كل استيرادات `db.accounting.accounting_audit_repo` تتم بشكل **lazy**.

**من يستدعي هذا الملف:** `ui/tabs/accounting/audit_log_tab.py` (حسب توثيق الملف نفسه).

### Dataclass

```python
@dataclass
class AuditPage:
    rows        : list
    total_count : int
    offset      : int
    limit       : int
```
- `.has_more -> bool` (property): `offset + len(rows) < total_count`.

### Class: `AuditService`
لا يرث من شيء.

```python
AuditService(conn)
```

- **`count(self, table_name=None, action=None) -> int`**: عبر `fetch_audit_log_count`.
- **`list(self, table_name=None, action=None, limit=200, offset=0) -> list`**: عبر `fetch_audit_log`.
- **`get_page(self, table_name=None, action=None, limit=200, offset=0) -> AuditPage`**: يجمع `count` + `list` في نداء واحد — يُستخدم في `audit_log_tab._fetch_and_fill` بدل استدعاءين منفصلين مع منطق "لو `offset == 0`" يدوي في الـ UI. **`total` يُحسب فقط لو `offset == 0`** (تحسين أداء — لا يُعاد حساب العدد الكلي في كل صفحة)؛ لو `offset != 0`، `total_count` يُعاد `-1` كإشارة "غير محسوب في هذه الصفحة".
- **`get_record_history(self, table_name, record_id) -> list`**: عبر `fetch_record_history`.

---

## inventory_posting_service.py

### `services/accounting/inventory_posting_service.py`

**الغرض:** Business Logic لعمليات المخزون التي تتطلب ترحيل قيد محاسبي معاً (دومين عابر: مخزون + محاسبة في معاملة واحدة).

**Imports (top-level):** `from dataclasses import dataclass` فقط — استيراد `db.accounting.accounting_inventory_repo.purchase_inventory` يتم بشكل **lazy** داخل `purchase`.

**من يستدعي هذا الملف:** غير محدد بثقة من المرفقات الحالية (نقطة الدخول الموصى بها من `tabs/` حسب توثيق الملف نفسه، مقابل استدعاء `accounting_inventory_repo` مباشرة).

**ملاحظة معمارية موثّقة — لماذا service منفصل عن `InventoryService`؟**
`InventoryService` (في `services/inventory/`) هو الوحيد المسموح له استدعاء `db.inventory.inventory_repo` — مبدأ عزل صريح موثّق في رأس ذلك الملف. عمليات مثل الشراء (`purchase`) تُنشئ قيداً محاسبياً كاملاً (`accounting.db`) بالإضافة لحركة المخزون، عبر دالة واحدة في `db.accounting.accounting_inventory_repo` (وليس `db.inventory`) — فمكانها الطبيعي طبقة service محاسبية مستقلة، لا داخل `InventoryService` ولا مقحمة في `AccountsService`/`JournalService` (كلاهما لا يغطي منطقياً "شراء صنف مخزون + قيد" كوحدة واحدة).

### Dataclass

```python
@dataclass
class PurchaseResult:
    inv_id      : int
    qty         : float
    unit_cost   : float
    total_cost  : float
```

### Class: `InventoryPostingService`
لا يرث من شيء. يقبل اتصالي المخزون والمحاسبة معاً، بنفس منطق `InventoryService`.

```python
InventoryPostingService(inv_conn, acc_conn)
```

- **`purchase(self, inv_id, qty, unit_cost, date, payment_account_id, notes=None) -> PurchaseResult`**: يسجل عملية شراء/استلام مخزن: قيد محاسبي (مدين مخزون / دائن حساب الدفع) + حركة وارد في المخزون معاً، عبر `db.accounting.accounting_inventory_repo.purchase_inventory` — نقطة الدخول الوحيدة الموصى بها من `tabs/` لهذه العملية. يتحقق: `qty > 0`، `unit_cost >= 0`، `payment_account_id` موجود (وإلا `ValueError` لكل حالة). يرجع `PurchaseResult` مع `total_cost = qty × unit_cost` محسوبة يدوياً في الـ service.

---

## علاقات الملفات

- لا يوجد استيراد مباشر بين ملفات هذا المسار مع بعضها البعض، **باستثناء**: `inventory_posting_service.py` يعتمد منطقياً (موثّق في التعليقات) على معرفة وجود `InventoryService` (`services/inventory/`) و`AccountsService`/`JournalService` (نفس المسار) لتبرير سبب انفصاله، لكنه **لا يستوردهم فعلياً**.
- **نمط مشترك:** كل الملفات في هذا المسار (عدا `investors_service.py` و`inventory_posting_service.py` اللذين يقبلان اتصالين) تتبع نمط constructor بسيط `Service(conn)` مع `self._conn = conn`.
- **نمط مشترك آخر:** كل الملفات تقريباً تؤجل استيراد دوال `db.accounting.*` إلى داخل كل method (lazy import) بدل استيرادها أعلى الملف — بلا استثناء في هذه الحزمة (حتى `accounts_service.py` و`journal_service.py` الكبيرين).
- تبعية خارج هذا المسار: كل الملفات تعتمد على حزمة `db/accounting/*`. `inventory_posting_service.py` يعتمد أيضاً منطقياً على وجود `services/inventory/inventory_service.py` (راجع `services_inventory.md`) و`services/accounting/accounts_service.py`/`journal_service.py` (نفس هذا المرجع) كسياق تبريري فقط.
- `services/inventory/inventory_service.py` (خارج هذا المسار) يستورد `AccountsService` من هذا الملف مباشرة (`from services.accounting.accounts_service import AccountsService`) — راجع `services_inventory.md`.
