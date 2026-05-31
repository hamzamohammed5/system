# خطة Refactoring V2
> تنظيم ملفات `ui/` — كل ملف في مكانه الصح، مفيش تكرار، مفيش folder بملف واحد

---

## القاعدة الأساسية

```
ui/                 ← infrastructure فقط (theme, font, constants, events, state)
ui/widgets/         ← كل الـ UI components والـ dialogs والـ logic
ui/main_window.py   ← يفضل كما هو
```

---

## تشخيص كل ملف في `ui/`

| الملف | المشكلة | القرار |
|-------|---------|--------|
| `main_window.py` | ✅ مكانه صح | يفضل |
| `constants.py` | ✅ infrastructure | يفضل |
| `font.py` | ✅ infrastructure | يفضل |
| `app_state.py` | ✅ infrastructure | يفضل |
| `events.py` | ✅ infrastructure | يفضل |
| `theme.py` | ⚠️ فيه تكرار مع `themes/theme_manager.py` في تعريف الألوان | يُنظَّف |
| `settings_dialog.py` | ❌ dialog ضخم في جذر `ui/` | يُنقل لـ `ui/widgets/dialogs/` |
| `themes/theme_manager.py` | ❌ folder بملف واحد + تكرار الألوان | يُعاد هيكلة |
| `i18n/ar.py` | ⚠️ data بعيدة عن اللي بيستخدمها | تفضل — مكانها مقبول |
| `i18n/en.py` | ⚠️ data بعيدة عن اللي بيستخدمها | تفضل — مكانها مقبول |

---

## التغييرات المطلوبة

---

### تغيير 1 — `ui/settings_dialog.py` → `ui/widgets/dialogs/settings_dialog.py`

**السبب:** `SettingsDialog` هو dialog widget، مكانه مع باقي الـ dialogs في `ui/widgets/dialogs/`.

**الـ imports لن تتأثر** لأنها من `ui.font`, `ui.theme`, `ui.widgets.*` — كلها absolute imports تشتغل من أي مكان.

**الـ import الوحيد اللي بيستخدم `settings_dialog` من برة:**
```python
# ui/main_window.py — السطر اللي محتاج يتحدث:

# قبل:
from ui.settings_dialog import SettingsDialog

# بعد:
from ui.widgets.dialogs.settings_dialog import SettingsDialog
```

**الخطوات:**
1. انقل الملف: `ui/settings_dialog.py` → `ui/widgets/dialogs/settings_dialog.py`
2. حدّث السطر في `ui/main_window.py`
3. احذف `ui/settings_dialog.py` القديم

---

### تغيير 2 — حل تكرار الألوان بين `ui/theme.py` و `ui/themes/theme_manager.py`

**المشكلة:**

`ui/theme.py` فيه `_C` dict بالألوان الافتراضية (Warm Neutral) hardcoded:
```python
_C: dict = {
    "bg_page": "#F5F4F0",
    "accent":  "#3D5A80",
    ...  # ~50 لون
}
```

`ui/themes/theme_manager.py` فيه `_LIGHT_THEME` بنفس الألوان بالظبط:
```python
_LIGHT_THEME: Dict[str, str] = {
    "bg_page": "#F5F4F0",
    "accent":  "#3D5A80",
    ...  # نفس الـ 50 لون مكررة!
}
```

**الحل:**

`_C` في `theme.py` يبدأ **فاضي** ويتملى من `_LIGHT_THEME` عند الـ import الأول:

```python
# ui/theme.py — بعد التعديل
_C: dict = {}  # يتملى من theme_manager عند الـ import

def _init_default_theme():
    """يُملّي _C بالثيم الافتراضي عند أول import."""
    from ui.themes.theme_manager import _LIGHT_THEME
    _C.update(_LIGHT_THEME)

_init_default_theme()
```

بكده:
- تعريف الألوان في مكان واحد فقط: `theme_manager.py`
- `_C` دايماً متزامن مع الثيم الحالي
- مفيش تكرار

---

### تغيير 3 — `ui/themes/` folder بملف واحد

**الخيارات:**

**خيار A — نقل `ThemeManager` لـ `ui/theme.py`** *(مش مناسب)*
- هيخلي `theme.py` ضخم جداً ومسؤوليتين في ملف واحد

**خيار B — نقل `theme_manager.py` لـ `ui/` مباشرة** *(الأنسب)*
```
ui/themes/theme_manager.py  →  ui/theme_manager.py
```

**الـ imports المتأثرة:**
```python
# كل import من themes/theme_manager:

# قبل:
from ui.themes.theme_manager import theme_manager, THEMES, THEME_DISPLAY_NAMES
from ui.themes import theme_manager

# بعد:
from ui.theme_manager import theme_manager, THEMES, THEME_DISPLAY_NAMES
```

**الملفات اللي بتستورد من `ui.themes`:**
- `ui/settings_dialog.py` → (بعد نقله: `ui/widgets/dialogs/settings_dialog.py`)
- `ui/main_window.py` — **لا يوجد** import مباشر لـ theme_manager
- `ui/widgets/base/detail_panel.py` — لا يوجد
- أي ملف فيه `from ui.themes` محتاج تحديث

**الخطوات:**
1. انقل: `ui/themes/theme_manager.py` → `ui/theme_manager.py`
2. حدّث كل `from ui.themes.theme_manager` → `from ui.theme_manager`
3. حدّث كل `from ui.themes import` → `from ui.theme_manager import`
4. احذف folder `ui/themes/`

---

### تغيير 4 — `ui/i18n/` — يفضل كما هو

**السبب:** القواميس `ar.py` و `en.py` هي data files، مكانها في `ui/i18n/` منطقي ومقبول.

`ui/widgets/core/i18n.py` بيستوردهم بـ relative import:
```python
from ...i18n.ar import AR_STRINGS
from ...i18n.en import EN_STRINGS
```

**التحسين المطلوب فقط:** تحويل الـ relative imports لـ absolute:
```python
# قبل (هش):
from ...i18n.ar import AR_STRINGS

# بعد (أكثر وضوحاً):
from ui.i18n.ar import AR_STRINGS
from ui.i18n.en import EN_STRINGS
```

---

## ملخص التغييرات

| # | التغيير | الملفات المتأثرة |
|---|---------|-----------------|
| 1 | نقل `settings_dialog.py` → `widgets/dialogs/` | `main_window.py` |
| 2 | حل تكرار الألوان في `theme.py` | `theme.py` فقط |
| 3 | نقل `themes/theme_manager.py` → `theme_manager.py` + حذف folder | كل ملف فيه `from ui.themes` |
| 4 | تحويل relative imports في `core/i18n.py` → absolute | `core/i18n.py` فقط |

---

## البنية النهائية لـ `ui/`

```
ui/
├── main_window.py        ← يفضل كما هو
├── constants.py          ← infrastructure ✅
├── font.py               ← infrastructure ✅
├── theme.py              ← infrastructure (بدون تكرار الألوان) ✅
├── theme_manager.py      ← نُقل من themes/ (المصدر الوحيد للألوان)
├── app_state.py          ← infrastructure ✅
├── events.py             ← infrastructure ✅
└── i18n/
    ├── ar.py             ← data فقط ✅
    └── en.py             ← data فقط ✅

ui/widgets/
└── dialogs/
    ├── settings_dialog.py  ← نُقل من ui/
    ├── dialogs_base.py
    ├── message.py
    └── confirm.py
```

---

## الـ grep commands للتحقق

```bash
# 1. إيجاد كل import من settings_dialog:
grep -rn "from ui.settings_dialog\|import settings_dialog" --include="*.py" .

# 2. إيجاد كل import من ui.themes:
grep -rn "from ui\.themes\|from ui import.*theme_manager" --include="*.py" .

# 3. التحقق من التكرار — ألوان موجودة في الاتنين:
grep -n "bg_page\|accent.*3D5A80" ui/theme.py ui/themes/theme_manager.py

# 4. إيجاد الـ relative imports في core/i18n.py:
grep -n "from \.\.\." ui/widgets/core/i18n.py
```

---

## ترتيب التنفيذ

```
1. نقل ui/settings_dialog.py → ui/widgets/dialogs/settings_dialog.py
2. تحديث import في ui/main_window.py
3. نقل ui/themes/theme_manager.py → ui/theme_manager.py
4. grep + تحديث كل "from ui.themes" في الـ codebase
5. حذف ui/themes/ folder
6. تعديل ui/theme.py — حذف الـ hardcoded _C و استخدام _LIGHT_THEME
7. تحديث relative imports في ui/widgets/core/i18n.py → absolute
```