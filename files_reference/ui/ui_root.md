# دليل الكود — UI / Root: Font, State

> الملفات الجذرية في `ui/` التي ليس لها مرجع مستقل خاص بها.
> `ui/font.py`, `ui/app_state.py`
>
> ⚠️ `ui/constants.py` و `ui/theme_manager.py` هما أيضاً ملفات جذرية في `ui/*.py`،
> لكن كلاً منهما (بصفته مُجمِّعاً aggregator) له **مرجع مستقل خاص به** يغطيه هو
> وكل الملفات التي يستدعيها من مجلد الـ `_data` الفرعي التابع له، حسب نفس مبدأ
> هذا الملف تماماً:
> - `ui/constants.py` + كل `ui/constants_data/*.py` → **`ui_constants.md`**
> - `ui/theme_manager.py` + كل `ui/theme_manager_data/*.py` → **`ui_theme_manager.md`**
>
> ⚠️ **[نُقل]** `ui/theme.py` نُقل من هذا الملف إلى **`ui_theme_manager.md`** رغم
> اختلاف مساره عن `ui/theme_manager.py` — بسبب التبعية المباشرة القوية بينهما
> (`theme.py` يقرأ `_LIGHT_THEME`/`_DARK_THEME` من `theme_manager.py` مباشرة).
>
> ⚠️ **[نُقل]** `ui/main_window.py` نُقل بالكامل إلى **`ui_main_window.md`**
> (كان مكرراً هنا وهناك) — راجعه هناك فقط.
>
> لذلك لا يُكرَّر محتواهما هنا — هذا الملف يغطي فقط الملفين الجذريين
> المتبقيين اللذين لا يتبعان أي مجلد بيانات فرعي مخصص ولا مرجع آخر.

---

## فهرس

| القسم | الملفات |
|-------|---------|
| [font](#font) | `ui/font.py` |
| [app_state](#app_state) | `ui/app_state.py` |

---

## font

### `ui/font.py`

```python
# Module-level cache [تحسين 43]
_module_font_size: int | None = None

_set_module_font_cache(size: int | None)
# يُحدّث _module_font_size — للاستخدام الداخلي فقط
# يُستدعى من: get_font_size()، set_font_size()، apply_font()
#              AppState.on_font_changed()، invalidate_stylesheet_cache()

get_font_size() -> int
# 1. يقرأ من _module_font_size (module-level cache — الأسرع)
# 2. لو None → AppState.font_size() ثم يُخزّن في _module_font_size
# لا يقرأ من DB مباشرة أبداً

set_font_size(size: int)
# يُقيّد بـ [MIN_FONT_SIZE, MAX_FONT_SIZE]
# يُحدّث: _set_module_font_cache(size) → AppState.on_font_changed(size) → DB

fs(base: int, delta: int = 0) -> int
# حجم خط نسبي — الحد الأدنى MIN_FONT_SIZE دائماً
# = max(MIN_FONT_SIZE, base + delta)

apply_font(app: QApplication, size: int = None)
# يُطبّق حجم الخط على الـ app عبر build_stylesheet()
# size=None → يستخدم get_font_size()
# يُحدّث الـ cache + AppState + يُعيد بناء stylesheet
```

**[تحديث] تسلسل القراءة الكامل — الآن عبر `FontService` وسيط (لا DB مباشرة من AppState):**
```
ui/font.py  →  AppState  →  FontService  →  settings_repo  →  DB

get_font_size()
  → _module_font_size (module cache، أسرع — لا I/O)
  → AppState.font_size()
    → _font_size (class cache)
    → AppState._load_font_size() → services.shared.font_service.FontService.load()
      → settings_repo → DB
      → fallback: DEFAULT_FONT_SIZE (try/except على مستوى AppState._load_font_size)
```

**القاعدة الذهبية (موثّقة بالتعليق في الملف):** كل طبقة تكلّم الطبقة اللي تحتها مباشرة فقط —
`font.py` يكلّم `AppState` فقط (لا يعرف `FontService` ولا `DB`)، و`AppState` يكلّم `FontService` فقط (لا يعرف `settings_repo` ولا `DB`)، و`FontService` هو الوحيد الذي يعرف `settings_repo`/`DB`. أي تغيير مستقبلي في طريقة التخزين (مثلاً online/offline) يحدث في `FontService` فقط.

**ثوابت أحجام خط إضافية في `font.py` (module-level، ثابتة لا تتغير بإعدادات المستخدم):**
```python
FS_XS   = 10   # تلميحات صغيرة جداً
FS_SM   = 11   # تسميات ثانوية، وحدات
FS_BASE = 12   # نص أساسي، أزرار، حقول إدخال
FS_MD   = 13   # رؤوس أقسام ونوافذ
FS_LG   = 14   # رؤوس أكبر، أيقونات تفاعلية
FS_XL   = 16   # عناوين رئيسية كبيرة
```
الفرق عن `get_font_size()`: هذه ثوابت لا تتغير مع إعدادات المستخدم (للـ stylesheet الثابت)، بينما `get_font_size()`/`fs()` ديناميكية وتُستخدم في `build_stylesheet()` أو أي مكان يجب أن يعكس تفضيل المستخدم.

---

## app_state

### `ui/app_state.py` — `AppState`

Cache مركزي لإعدادات التطبيق — كل الـ attributes كـ class-level (لا instance). **لا يتواصل مع DB أو `settings_repo` مباشرة أبداً — كل القراءة/الكتابة تمر عبر `FontService`.**

```python
_font_size: int | None = None   # class-level cache
```

```python
AppState.font_size() -> int
# يرجع من cls._font_size لو موجود
# لو None → يستدعي cls._load_font_size() ويخزّن النتيجة

AppState.on_font_changed(size: int)
# يُقيّد بـ [MIN_FONT_SIZE, MAX_FONT_SIZE]
# 1. cls._font_size = size
# 2. يستدعي _set_module_font_cache(size) من ui.font (داخل try/except)
# 3. يستدعي FontService.save(size) من services.shared.font_service (داخل try/except، logger.debug لو فشل)
# 4. يستدعي cls._invalidate_button_cache()
# 5. logger.debug تأكيدي بالقيمة الجديدة

AppState.invalidate()
# cls._font_size = None
# يستدعي invalidate_stylesheet_cache() من ui.theme (داخل try/except)
# fallback لو فشل: يستدعي cls._invalidate_button_cache() مباشرة + logger.debug بالخطأ
# logger.debug تأكيدي "cache cleared"
# يُستدعى من MainWindow._on_company_changed() عند تغيير الشركة النشطة

AppState._load_font_size() -> int   # classmethod — داخلي
# يستدعي FontService.load() من services.shared.font_service (داخل try/except)
# fallback: DEFAULT_FONT_SIZE عند أي exception (مع logger.debug)
# لا يتواصل مع DB مباشرة — الوسيط الوحيد هو FontService

AppState._invalidate_button_cache()   # classmethod — داخلي
# يستدعي invalidate_stylesheet_cache() من ui.widgets.components.button (داخل try/except، logger.debug لو فشل)
```

**من يستدعي هذا الملف:** `ui/font.py` (عبر `get_font_size()`/`set_font_size()`)، `ui/main_window.py` (`_on_company_changed`) — راجع `ui_main_window.md`.

---

## علاقات الملفات

- `ui/font.py` يستورد من `ui/app_state.py` (`AppState.font_size()`, `AppState.on_font_changed()`) — لا يتواصل مع DB أو `FontService` مباشرة.
- `ui/app_state.py` يستورد من `services.shared.font_service.FontService` (خارج `ui/`) ومن `ui/theme.py` (`invalidate_stylesheet_cache`، راجع `ui_theme_manager.md`) ومن `ui/widgets/components/button.py` (`invalidate_stylesheet_cache`).
- **نمط الـ Layering المشترك بين `font.py` و`app_state.py`:** كل طبقة تعرف فقط الطبقة التي تحتها مباشرة (`font.py → AppState → FontService → settings_repo → DB`) — لا قفزات في السلسلة.
- `ui/font.py` يُستهلَك من `ui/theme.py` (`_set_module_font_cache`) — راجع `ui_theme_manager.md` — ومن `ui/main_window.py` وحزمة `ui/main_window_helper/` — راجع `ui_main_window.md`.
- `ui/app_state.py` يُستدعى من `ui/main_window.py` (`AppState.invalidate()` عند `_on_company_changed`) — راجع `ui_main_window.md`.
- `ui/theme.py` (المصدر الوحيد لـ `_C` وبناء الـ stylesheet) و`ui/main_window.py` (النافذة الرئيسية) لم يعودا ضمن نطاق هذا الملف — راجع `ui_theme_manager.md` و`ui_main_window.md` على التوالي.
