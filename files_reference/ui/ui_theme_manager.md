# دليل الكود — UI / Theme Manager

> `ui/theme_manager.py` (الحزمة المُجمِّعة) + كل ملفات `ui/theme_manager_data/*.py` (5 ملفات).
> المصدر الوحيد لتعريف ألوان الثيمات (Light/Dark) وإدارة تبديل الثيم الحالي في التطبيق.
>
> ⚠️ **[نُقل — استثناء لقاعدة "مسار واحد لكل مرجع"]** `ui/theme.py` (مساره الفعلي
> `ui/theme.py` — **ليس** تحت `ui/theme_manager_data/`) أُضيف لهذا المرجع رغم اختلاف
> مساره، بسبب التبعية المباشرة القوية والوحيدة بينه وبين هذه الحزمة: `theme.py` هو
> المستهلك شبه الحصري لـ `_LIGHT_THEME`/`_DARK_THEME` (لملء `_C` وتطبيق `apply_theme`)،
> ولا يعرّف أي لون بنفسه. راجع `ui_root.md` لبقية الملفات الجذرية في `ui/*.py`.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [theme_manager (مُجمِّع)](#theme_manager-مُجمِّع) | `ui/theme_manager.py` |
| [_light_theme](#_light_theme) | `ui/theme_manager_data/_light_theme.py` |
| [_dark_theme](#_dark_theme) | `ui/theme_manager_data/_dark_theme.py` |
| [_registry](#_registry) | `ui/theme_manager_data/_registry.py` |
| [_card_palettes](#_card_palettes) | `ui/theme_manager_data/_card_palettes.py` |
| [_manager](#_manager) | `ui/theme_manager_data/_manager.py` |
| [theme](#theme) | `ui/theme.py` |

---

## theme_manager (مُجمِّع)

### `ui/theme_manager.py`

**الغرض:** نقطة الدخول الوحيدة لنظام الثيمات الكامل. **[مُقسَّم]** كان ملفاً واحداً (~680 سطر) وتحوّل لحزمة (package) مقسّمة إلى 5 ملفات في `ui/theme_manager_data/`، مع الحفاظ الكامل على واجهة الاستيراد القديمة (`from ui.theme_manager import theme_manager, THEMES, ...` يستمر بالعمل بلا أي تعديل في الكود المستهلك).

```python
from ui.theme_manager_data._light_theme import _LIGHT_THEME
from ui.theme_manager_data._dark_theme import _DARK_THEME
from ui.theme_manager_data._registry import THEMES, THEME_DISPLAY_NAME_KEYS
from ui.theme_manager_data._card_palettes import CARD_PALETTES
from ui.theme_manager_data._manager import ThemeManager

theme_manager = ThemeManager()   # ← Singleton — يُستخدم في كل التطبيق

__all__ = [
    "_LIGHT_THEME", "_DARK_THEME", "THEMES", "THEME_DISPLAY_NAME_KEYS",
    "CARD_PALETTES", "ThemeManager", "theme_manager",
]
```

**يدعم ثيمين:** Light (الافتراضي — Warm Neutral) وDark.

**[تحديث موثّق بالتعليقات] الألوان التالية نُقلت إلى هنا من `colors.py`** لتوحيد مصدر الألوان:
- ألوان الهادر (`waste_high/medium/low`) لكل ثيم.
- ألوان fallback البطاقات (`card_fallback_bg/border`).
- نتيجة ذلك: `colors.py` (خارج نطاق هذا المرجع) لم يعد يحتوي أي لون hardcoded — كل شيء يُقرأ من `_C` (المملوء من هنا).

**[تحديث 2] `CARD_PALETTES`** (lookup tables لألوان البطاقات حسب الثيم) نُقلت أيضاً من `colors.py` (كانت `CARD_PALETTE` و`_DARK_CARD_PALETTE`) لنفس الغرض — توحيد المصدر.

**[دمج events]** المصدر الوحيد لـ bus الأحداث هو `ui.widgets.core.events` — `from ui.widgets.core.events import bus` (يُستخدم داخل `_manager.py`، ليس هنا مباشرة).

**مثال استخدام موثّق في الملف:**
```python
from ui.theme_manager import theme_manager

theme_manager.set_theme("dark")
current = theme_manager.current_theme   # "dark"

theme_manager.theme_changed.connect(my_fn)
# أو عبر bus:
from ui.widgets.core.events import bus
bus.theme_changed.connect(my_fn)
```

**من يستدعي هذا الملف:** `ui/theme.py` (يستورد `_LIGHT_THEME` عند أول import فقط لملء `_C` الافتراضي — راجع قسم `theme` في هذا الملف نفسه أدناه)، `SettingsDialog` (لتبديل الثيم، خارج نطاق هذا المرجع)، `main.py` عند بدء التطبيق (`theme_manager.load_from_db()`).

---

## _light_theme

### `ui/theme_manager_data/_light_theme.py` — `_LIGHT_THEME: Dict[str, str]`

**الغرض:** تعريف كل ألوان الثيم الفاتح (Light — Warm Neutral). **المصدر الوحيد** لهذه القيم — لا يُعاد تعريفها في أي مكان آخر بالمشروع؛ `ui/theme.py` (راجع قسم `theme` أدناه في هذا الملف نفسه) يقرأها فقط عبر `_C.update()`.

**لا imports خارجية** غير `from __future__ import annotations` و`typing.Dict`.

**التصنيفات الرئيسية للمفاتيح (أكثر من 130 مفتاح):**

- **خلفيات أساسية:** `bg_page`, `bg_surface`, `bg_surface_2`, `bg_hover`, `bg_active`, `bg_input`, `bg_input_focus`.
- **حدود:** `border`, `border_med`, `border_focus`, `border_strong`, `border_light`, `border_subtle`.
- **نصوص:** `text_primary`, `text_sec`, `text_muted`, `text_disabled`, `text_state_neutral`, `text_hint`, `text_neutral`, `text_separator`, `group_label_text`.
- **Accent:** `accent`, `accent_hover`, `accent_light`, `accent_mid`, `accent_text`, `btn_primary_text`.
- **حالات (success/danger/warning/info):** كل واحدة بثلاث نُسخ (`_success`, `_success_bg`, `_success_border`) + hover variants (`success_hover`, `danger_hover`, `warning_hover`, `orange_hover`) + `success_hover_bg`, `danger_hover_bg`.
- **Sidebar:** `sidebar_bg`, `sidebar_text`, `sidebar_muted`, `sidebar_hover`, `sidebar_active`, `sidebar_border`.
- **ألوان تصنيفية عامة (blue/purple/orange/teal):** كل واحد بثلاث نُسخ (اللون + `_bg` + `_border`) + `blue_hover`, `blue_strong`.
- **صفوف الجداول:** `row_alt_bg`, `row_alt_border`, `table_gridline`, `scroll_warm_bg`.
- **Waste (نسبة الهادر):** `waste_zero_bg/border/color` + مستويات `waste_high/medium/low` (`_bg`, `_border` لكل واحدة).
- **حالات الإدخال (Input states):** `input_error_bg/border`, `input_positive_bg/border/color`.
- **Card fallback:** `card_fallback_bg`, `card_fallback_border`.
- **Accounting Journal:** `journal_dr_bg/border/accent`, `journal_cr_bg/border/accent`, `journal_neutral_bg/border`, `journal_header_bg/border` — مع تعليقات توضح التطابقات (`journal_dr_accent == badge_dr_text == acc_type_asset`، `journal_cr_accent == badge_cr_text == acc_type_liability`).
- **Investor:** `investor_capital_bg/text`, `investor_drawings_bg/text` (تتطابق مع `badge_cr_*`/`t_account_cr_bg`)، `investor_link_bg/border/text`.
- **Audit Log:** `audit_delete_fg/bg` (=danger), `audit_update_fg/bg` (=warning), `audit_create_fg/bg` (=success) — انعكاس مباشر موثّق بالتعليق.
- **T-Account:** `t_account_dr_bg` (=badge_dr_bg), `t_account_cr_bg` (=badge_cr_bg=investor_drawings_bg), `t_account_frame`.
- **Badge:** `badge_dr_bg/text`, `badge_cr_bg/text`.
- **أنواع الحسابات (Account type colors):** `acc_type_asset` (=badge_dr_text), `acc_type_liability` (=badge_cr_text), `acc_type_capital`, `acc_type_revenue` (=purple), `acc_type_expense` (=orange), `acc_type_drawings`.
- **Shared/Published items:** `shared_item_fg/bg`, `published_item_fg/bg`.
- **Inventory Stock Levels:** `stock_critical_fg`, `stock_low_fg`, `stock_ok_fg`.
- **Design Module:** `design_thumb_bg`, `design_thumb_bg_start/end` (تدرّج placeholder XCF), `design_thumb_border/icon/text`, `card_badge_text/bg/border`.
- **BOM Tree — Scenario node:** `bom_scenario_default_bg/fg`, `bom_scenario_normal_bg/fg` (=blue_bg/blue).
- **متفرقات:** `overlay_bg` (rgba شفافة لـ `LoadingOverlay`)، `dialog_hdr_sub_text` (rgba للـ subtitle)، `color_picker_default`، `icon_btn_color/hover_color`.

**نمط موثّق بالتعليقات داخل الملف نفسه:** كثير من المفاتيح مُعلَّق عليها بعلاقات تكرار صريحة (مثال: `# journal_dr_accent == badge_dr_text == acc_type_asset (#1565c0)`) — هذه التعليقات توثّق أن نفس القيمة اللونية تُستخدم دلالياً في أكثر من سياق، لضمان الاتساق البصري بدل تكرار hex منفصل بلا رابط.

---

## _dark_theme

### `ui/theme_manager_data/_dark_theme.py` — `_DARK_THEME: Dict[str, str]`

**الغرض:** تعريف كل ألوان الثيم الداكن (Dark) — **نفس بنية المفاتيح بالضبط** الموجودة في `_LIGHT_THEME` (نفس الأسماء، قيم hex مختلفة مناسبة للخلفية الداكنة). المصدر الوحيد لهذه القيم.

**لا imports خارجية** غير `from __future__ import annotations` و`typing.Dict`.

**فروقات ملحوظة عن `_light_theme.py` (غير مجرد قلب الألوان):**
- يضيف مفتاحين غير موجودين بنفس الاسم في `_light_theme.py`: `danger_strong` (`#ef5350` — أحمر أعمق لأيقونات التحذير في الوضع الداكن) و`input_accent_border` (`#5c6bc0`).
  > ملاحظة: `_light_theme.py` يحتوي أيضاً `danger_strong` (`#e53935`) و`input_accent_border` (`#c5cae9`) بنفس الأسماء — القيم فقط مختلفة، وليست حصرية للثيم الداكن. البنية إذن متطابقة تماماً بين الملفين.
- كل التصنيفات نفسها الموجودة في `_light_theme.py` (خلفيات، حدود، نصوص، accent، sidebar، حالات، ألوان تصنيفية، Waste، Input states، Card fallback، Accounting Journal، Investor، Audit Log، T-Account، Badge، Account type colors، Shared/Published، Inventory Stock، Design Module، BOM Tree Scenario node) موجودة بنفس الأسماء بالضبط مع قيم hex داكنة مناسبة (خلفيات داكنة جداً مثل `#0F0F0F`, `#1A1A1A` مقابل الفاتحة `#F5F4F0`, `#FAFAF8`).
- نفس نمط التعليقات التوضيحية للتطابقات الدلالية بين المفاتيح موجود هنا أيضاً (مثال: `# journal_dr_accent == badge_dr_text == acc_type_asset == accent (#5B8DB8)`).

**القاعدة الحرجة:** أي مفتاح جديد يُضاف مستقبلاً لـ `_LIGHT_THEME` **يجب** أن يُضاف بنفس الاسم في `_DARK_THEME` (والعكس) — وإلا فسيفشل `_C.update(theme_colors)` في `ui/theme.py` بالوصول لمفتاح غير موجود عند التبديل بين الثيمين (`get_theme_color` يستخدم `fallback` احترازياً، لكن معظم استخدامات `_C['key']` المباشرة في stylesheets لا تحتوي fallback).

---

## _registry

### `ui/theme_manager_data/_registry.py`

**الغرض:** سجل الثيمات المتاحة في التطبيق — يربط اسم الثيم (مفتاح نصي) بقاموس ألوانه الفعلي، ومفتاح الترجمة لاسمه المعروض.

**Imports الداخلية:**
```python
from ui.theme_manager_data._light_theme import _LIGHT_THEME
from ui.theme_manager_data._dark_theme import _DARK_THEME
```

**الثوابت المُصدَّرة:**
```python
THEMES: Dict[str, Dict[str, str]] = {
    "light": _LIGHT_THEME,
    "dark":  _DARK_THEME,
}

THEME_DISPLAY_NAME_KEYS: Dict[str, str] = {
    "light": "theme_light",   # مفتاح tr() لاسم الثيم المعروض
    "dark":  "theme_dark",
}
```

**من يستدعي هذا الملف:** `_manager.py` (`ThemeManager.set_theme()` يتحقق من `theme_name in THEMES`، `load_from_db()` يقرأ `THEMES.get(...)`، `get_available_themes()` يستخدم `THEME_DISPLAY_NAME_KEYS` مع `tr()`)، `ui/theme_manager.py` (يعيد تصديره).

**إضافة ثيم جديد مستقبلاً:** يتطلب (1) ملف `_<name>_theme.py` جديد بنفس بنية مفاتيح `_LIGHT_THEME` بالكامل، (2) إضافة سطر في `THEMES` هنا، (3) إضافة مفتاح ترجمة في `THEME_DISPLAY_NAME_KEYS` + مفاتيح `tr()` الفعلية في ملفات i18n.

---

## _card_palettes

### `ui/theme_manager_data/_card_palettes.py` — `CARD_PALETTES: Dict[str, Dict[str, tuple]]`

**الغرض:** جداول بحث (lookup tables) لتحويل لون "أساسي" (accent hex مُستخدَم كمعرّف فئة، مثل لون تصنيف أو بطاقة) إلى زوج `(خلفية فاتحة/داكنة, حد)` مناسب لكل ثيم — تُستخدم في مكوّنات مثل بطاقات التصنيفات الملوّنة حيث اللون الأساسي يُختار من المستخدم (عبر `ColorPickerWidget`) لكن الخلفية/الحد يجب أن يُشتقّا تلقائياً بتناسق مع الثيم الحالي.

**لا imports خارجية** غير `from __future__ import annotations` و`typing.Dict`.

**البنية:**
```python
CARD_PALETTES: Dict[str, Dict[str, tuple]] = {
    "light": {
        "#1565c0": ("#e8f0fe", "#90caf9"),   # (bg, border)
        # ... مرتبة في مجموعات تعليقية: أزرق / أخضر / أحمر / برتقالي-أصفر / رمادي / بنفسجي-وردي / بني
    },
    "dark": {
        "#1565c0": ("#1a2a3a", "#2a4a6a"),
        # ... نفس مفاتيح hex (نفس الألوان الأساسية) لكن بأزواج (bg, border) داكنة مقابلة
    },
}
```

**[تحديث موثّق بالتعليق] نُقلت من `colors.py`** (كانت باسمي `CARD_PALETTE` و`_DARK_CARD_PALETTE` منفصلين) — توحيد المصدر ضمن `theme_manager_data/`.

**آلية الاستخدام المتوقعة (من الكود المستهلك خارج هذا المرجع):** يُبحث عن اللون الأساسي (hex) كمفتاح في `CARD_PALETTES[theme_name]`؛ لو غير موجود يُفترض fallback عام (غير معرَّف في هذا الملف نفسه — مسؤولية الكود المستهلك).

**من يستدعي هذا الملف:** `ui/theme_manager.py` (يعيد تصديره في `__all__`)؛ الاستهلاك الفعلي في مكوّنات بطاقات ملوّنة خارج نطاق هذا المرجع (غير مرفقة في هذه الدفعة).

---

## _manager

### `ui/theme_manager_data/_manager.py` — `ThemeManager(QObject)`

**الغرض:** الـ Singleton الذي يدير حالة الثيم الحالي للتطبيق بالكامل — التبديل، الحفظ في DB، والإشعار بالتغيير عبر signal + event bus.

**Imports الداخلية:**
```python
from PyQt5.QtCore import QObject, pyqtSignal
from ui.theme_manager_data._registry import THEMES, THEME_DISPLAY_NAME_KEYS
from ui.theme_manager_data._light_theme import _LIGHT_THEME
```

**Class-level signal:**
```python
theme_changed = pyqtSignal(str)   # يُطلَق باسم الثيم الجديد بعد كل set_theme() ناجح
```

**`__init__(self)`**
- `super().__init__()`
- `self._current_theme: str = "light"` (القيمة الافتراضية قبل أي تحميل من DB).

**Properties:**
```python
theme_manager.current_theme -> str    # يرجع self._current_theme
theme_manager.is_dark -> bool         # self._current_theme == "dark"
```

**Methods:**

```python
theme_manager.set_theme(theme_name: str, save: bool = True)
```
- لو `theme_name not in THEMES` → يُستبدَل بـ `"light"` بصمت (fallback آمن، لا exception).
- لو `theme_name == self._current_theme` → `return` فوراً (لا عمل مكرر).
- يُحدّث `self._current_theme = theme_name`، يقرأ `colors = THEMES[theme_name]`.
- يستدعي `ui.theme.apply_theme(colors)` (استيراد محلي داخل الدالة) داخل `try/except` صامت — أي فشل في تطبيق الـ stylesheet لا يوقف بقية التدفق (الحفظ + الإشعار يستمران).
- لو `save=True` → يستدعي `self._save_to_db()`.
- يستدعي `self._emit_theme_changed(theme_name)` (عبر الـ bus) ثم `self.theme_changed.emit(theme_name)` (الـ Qt signal المحلي) — **إشعاران منفصلان**، ليس واحداً بديلاً عن الآخر.

```python
theme_manager.load_from_db(self)
```
- يُنفَّذ بالكامل داخل `try/except` صامت (فشل كامل = لا شيء يحدث، لا exception يتسرّب).
- يقرأ `theme = get_setting(conn, "ui_theme", "light")` (عبر `db.shared.connection.get_connection` و`db.shared.settings_repo.get_setting` — استيراد محلي).
- لو `theme in THEMES` → `self._current_theme = theme`.
- يقرأ `colors = THEMES.get(self._current_theme, _LIGHT_THEME)` (fallback مزدوج للأمان).
- يستدعي `ui.theme.apply_theme(colors)` داخل `try/except` داخلي منفصل.
- **لا يُطلق `theme_changed` أو الـ bus signal** — هذه دالة تحميل أولي عند بدء التطبيق فقط، ليست تبديلاً تفاعلياً.

```python
theme_manager.get_available_themes(self) -> list[dict]
```
- يستورد `tr` من `ui.widgets.core.i18n` محلياً.
- يُرجع قائمة `{"key": key, "name": tr(THEME_DISPLAY_NAME_KEYS.get(key, key)), "active": key == self._current_theme}` لكل مفتاح في `THEMES` — تُستخدم مباشرة لملء واجهة اختيار الثيم في `SettingsDialog` (خارج نطاق هذا المرجع).

**Internal methods (تبدأ بـ `_`):**

```python
theme_manager._emit_theme_changed(self, theme_name: str)
```
- يستورد `bus` من `ui.widgets.core.events` محلياً، يستدعي `bus.theme_changed.emit(theme_name)` داخل `try/except` صامت.

```python
theme_manager._save_to_db(self)
```
- يستورد `get_connection` و`set_setting` محلياً، يستدعي `set_setting(conn, "ui_theme", self._current_theme)` داخل `try/except` صامت — فشل الحفظ لا يمنع تبديل الثيم في الواجهة (best-effort persistence).

**نمط معماري ملحوظ:** كل عمليات I/O (DB، bus، تطبيق stylesheet) في هذا الكلاس مُغلَّفة بـ `try/except` صامت (بدون logging حتى) — يُفضَّل التطبيق دائماً على الفشل الصامت بدل رمي استثناء يكسر تبديل الثيم في الواجهة.

---

## theme

### `ui/theme.py`

> ⚠️ **[نُقل من `ui_root.md`]** مساره الفعلي `ui/theme.py` — مختلف عن `ui/theme_manager.py`/`ui/theme_manager_data/`، لكنه أُدرج هنا بسبب تبعيته المباشرة القوية على هذه الحزمة (راجع تنبيه أعلى الملف).

**الغرض:** المسؤولية الوحيدة لهذا الملف: الاحتفاظ بالألوان النشطة حالياً (`_C`) وبناء الـ stylesheet الكامل للتطبيق. **لا ألوان hardcoded هنا إطلاقاً** — كل قيمة لونية تُقرأ من `_LIGHT_THEME`/`_DARK_THEME` (هذه الحزمة).

```python
_C: dict   # dict الألوان النشطة — يُملأ من _LIGHT_THEME عند الـ import الأول
           # عبر _init_default_theme() التي تستورد من theme_manager

_ss_cache: dict[tuple, str]   # cache key = (font_size, theme_hash)
_current_theme_hash: str      # يُحسب lazy عند الحاجة

_init_default_theme()
# يُملّي _C بـ _LIGHT_THEME من theme_manager عند أول import
# لا ألوان hardcoded في theme.py — كل الألوان من theme_manager.py

apply_theme(theme_colors: dict, app: QApplication = None)
# يُحدّث _C.update(theme_colors)
# يستدعي invalidate_stylesheet_cache()
# يستدعي invalidate_stylesheet_cache() من ui.widgets.components.button صراحةً (try/except)
# يُطبّق stylesheet على app (أو QApplication.instance() لو app=None)
# [إصلاح ثيم — مركزي] بعد setStyleSheet العام، يمر على كل topLevelWidgets()
#   ويستدعي refresh_table_styles(win) من ui.widgets.tables.tables على كل واحدة
#   لأن أي QTableWidget له stylesheet محلي مباشر (self.table.setStyleSheet(table_style()))
#   لا يتحدث تلقائياً مع QApplication.setStyleSheet() — الحل المركزي يغطي كل الجداول
#   دفعة واحدة بدل الاعتماد على كل widget يعمل refresh بنفسه
# يُستدعى من ThemeManager.set_theme() — لا تستدعه مباشرة

get_theme_color(key: str, fallback: str = "#000000") -> str
# يرجع لون من _C بأمان مع fallback

build_stylesheet(base: int) -> str
# cache key = (font_size, theme_hash) عبر _ss_cache dict
# يُقيّد base بـ [MIN_FONT_SIZE, MAX_FONT_SIZE] من ui.constants
# يبني الـ stylesheet الكامل مقسّماً على دوال مساعدة
# يُعيد النتيجة من الـ cache لو موجودة

invalidate_stylesheet_cache()
# يمسح _ss_cache.clear()
# يُعيد ضبط _current_theme_hash = ""
# يستدعي _set_module_font_cache(None) من ui.font
```

**`_compute_theme_hash()` / `_get_theme_hash()`:**
```python
# يحسب hash من tuple(sorted(_C.items()))
# lazy — يُحسب فقط لو _current_theme_hash فارغ
# يُستخدم كجزء من cache key في build_stylesheet
```

**أقسام الـ stylesheet (الدوال المساعدة):**
```python
_ss_base_reset      # QMainWindow، QWidget، * reset
_ss_message_box     # QMessageBox كامل
_ss_dialog          # QDialog كامل
_ss_typography      # QLabel وكل roles (section, card-title, card-value, badge, mode)
_ss_groupbox        # QGroupBox
_ss_buttons         # QPushButton كل الحالات (hover, pressed, disabled, checked)
_ss_inputs          # QLineEdit, QDoubleSpinBox, QSpinBox, QDateEdit, QTimeEdit
_ss_combobox        # QComboBox + QAbstractItemView
_ss_tables          # QTableWidget + QHeaderView
_ss_tree            # QTreeWidget + QHeaderView
_ss_tabs            # QTabWidget + QTabBar
_ss_scrollbars      # QScrollBar vertical + horizontal (لا parameters غير c)
_ss_misc            # QListWidget, QSplitter, QToolTip, QFrame, QScrollArea,
                    # QProgressBar, QCheckBox, QRadioButton, Sidebar nav overrides
```

**مفاتيح `_C`:** العدد كبير جداً (أكثر من 130 مفتاح تغطي: خلفيات، حدود، نصوص، accent، sidebar، حالات success/danger/warning/info، محاسبة (journal/badge/t_account/acc_type)، مستثمرين، audit log، مخزون، تصميمات، BOM scenarios، إلخ). **القائمة الكاملة بقيمها لكل ثيم (light/dark) موجودة أعلاه في هذا المرجع نفسه (أقسام `_light_theme`/`_dark_theme`)** — `theme.py` نفسه لا يعرّف أي مفتاح لون؛ فقط يقرأها من `_LIGHT_THEME`/`_DARK_THEME` عبر `_C.update()` (راجع علاقات الملفات أدناه).

**من يستدعي هذا الملف:** `ui/main_window.py` (`_C` مباشرة — راجع `ui_main_window.md`)، `ui/font.py` (`apply_font()` يستدعي `build_stylesheet()`، راجع `ui_root.md`)، `SettingsDialog` وكل الـ `WidgetMixin` عبر `_refresh_style()` (خارج نطاق هذا المرجع)، `ThemeManager.set_theme()`/`load_from_db()` (أعلى في هذا الملف نفسه، عبر `ui.theme.apply_theme` باستيراد محلي).

---

## علاقات الملفات

- `ui/theme_manager.py` (المُجمِّع) يستورد من كل الـ 5 ملفات الفرعية ويُعيد تصديرها عبر `__all__` — لا منطق أو ألوان مُعرَّفة مباشرة فيه.
- `_registry.py` يستورد من `_light_theme.py` و`_dark_theme.py` مباشرة (لبناء `THEMES` dict) — هو نقطة الربط الوحيدة بين ملفي الألوان.
- `_manager.py` (`ThemeManager`) يستورد من `_registry.py` (`THEMES`, `THEME_DISPLAY_NAME_KEYS`) و`_light_theme.py` (`_LIGHT_THEME` كـ fallback في `load_from_db`) — لا يستورد `_dark_theme.py` مباشرة (يصل له فقط عبر `THEMES` dict).
- `_card_palettes.py` **مستقل تماماً** عن باقي الملفات الأربعة — لا يستورد ولا يُستورَد من أي منها داخلياً؛ فقط يُعاد تصديره من `theme_manager.py` (المُجمِّع) للاستهلاك الخارجي.
- `_light_theme.py` و`_dark_theme.py` **مستقلان عن بعضهما تماماً** (لا استيراد متبادل) لكن **يجب أن يتطابقا في مجموعة المفاتيح بالكامل** — هذا عقد ضمني غير مُفروض بالكود (لا اختبار تلقائي داخل هذه الملفات نفسها) بل موثّق فقط بالتعليقات والانضباط اليدوي.
- **`ui/theme.py` (مُدرَج في هذا المرجع رغم اختلاف مساره — راجع التنبيه أعلى الملف):** يستورد `_LIGHT_THEME` من `_light_theme.py` عند أول `import` لملء `_C` الافتراضي (`_init_default_theme()`)، وهو المُستدعى من `ThemeManager.set_theme()`/`load_from_db()` (في `_manager.py`) عبر `apply_theme()` — العلاقة اتجاهية: بقية ملفات `theme_manager_data/` (`_light_theme`, `_dark_theme`, `_registry`, `_card_palettes`) لا تستورد أي شيء من `theme.py` (لتفادي دورة استيراد)؛ `_manager.py` هو الوحيد الذي يستورد `ui.theme.apply_theme` وبشكل **محلي (lazy، داخل الدالة)** تحديداً لهذا السبب.
- `_manager.py` يستورد أيضاً من خارج نطاق `ui/` بالكامل: `db.shared.connection.get_connection`, `db.shared.settings_repo.get_setting/set_setting` (طبقة الـ DB مباشرة — الاستثناء الوحيد الموثّق لقاعدة عدم الوصول المباشر لـ DB من طبقة الـ UI، وهو مُبرَّر هنا لأن `ThemeManager` هو تحديداً المسؤول عن حفظ/تحميل تفضيل الثيم).
- `_manager.py` يستورد من `ui.widgets.core.events` (`bus`) و`ui.widgets.core.i18n` (`tr`) — كلاهما استيراد محلي داخل الدوال، وكلاهما خارج نطاق هذا المرجع.
- `ui/theme.py` نفسه يستخدم `MIN_FONT_SIZE`/`MAX_FONT_SIZE`/`INPUT_HEIGHT_PAD`/`BTN_HEIGHT_PAD` من `ui.constants` (المُجمِّع — راجع `ui_constants.md` للأبعاد الرقمية، بينما هذا المرجع كله ألوان hex فقط) داخل `build_stylesheet()`، ويستدعي `_set_module_font_cache(None)` من `ui/font.py` (راجع `ui_root.md`) داخل `invalidate_stylesheet_cache()`.
- `ui/theme.py` يُستهلَك مباشرة من `ui/main_window.py` (`_C`) وحزمة `ui/main_window_helper/` بالكامل (راجع `ui_main_window.md`)، ومن `ui/font.py` (`apply_font()` يستدعي `build_stylesheet()`، راجع `ui_root.md`).
