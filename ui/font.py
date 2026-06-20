"""
ui/font.py
==========
إدارة حجم الخط — المصدر الوحيد لكل عمليات الخط في طبقة الـ UI.

══════════════════════════════════════════════════════════════
التسلسل الكامل لحجم الخط (اقرأ هذا أولاً)
══════════════════════════════════════════════════════════════

  المستخدم يغيّر الخط في SettingsDialog
            ↓
  font.set_font_size(size)          ← نقطة الدخول الوحيدة من UI
            ↓
  AppState.on_font_changed(size)    ← cache مركزي + تنسيق
            ↓
  FontService.save(size)            ← الوسيط مع قاعدة البيانات
            ↓
  settings_repo.set_setting(...)    ← كتابة لـ DB
            ↓
  SQLite / DB

للقراءة عند بدء التطبيق:
  font.get_font_size()
        ↓  (module cache فارغ)
  AppState.font_size()
        ↓  (class cache فارغ)
  FontService.load()
        ↓
  settings_repo.get_setting(...)
        ↓
  SQLite / DB

══════════════════════════════════════════════════════════════
قاعدة الـ Layering
══════════════════════════════════════════════════════════════
  font.py  →  AppState  →  FontService  →  settings_repo  →  DB

  ✓ font.py يكلّم AppState فقط — لا يعرف FontService أو DB
  ✓ AppState يكلّم FontService فقط — لا يعرف settings_repo أو DB
  ✓ FontService يكلّم settings_repo فقط — هو الوحيد الذي يعرف DB
  ✓ أي تغيير في طريقة التخزين (online/offline) يحدث في FontService فقط

══════════════════════════════════════════════════════════════
API العام
══════════════════════════════════════════════════════════════

  get_font_size() → int
      يرجع حجم الخط الحالي (من cache أو DB).

  set_font_size(size: int)
      يحدّث حجم الخط في cache وDB عبر AppState → FontService.

  apply_font(app, size=None)
      يطبّق حجم الخط على كامل التطبيق ويُعيد بناء الـ stylesheet.

  fs(base, delta=0) → int
      يرجع حجم خط نسبي (للاستخدام في stylesheet ديناميكي).

  FS_XS / FS_SM / FS_BASE / FS_MD / FS_LG / FS_XL
      ثوابت ثابتة للـ stylesheet — استخدمها بدلاً من كتابة الأرقام مباشرة.

══════════════════════════════════════════════════════════════
استخدام الثوابت (FS_*) مقابل get_font_size()
══════════════════════════════════════════════════════════════

  FS_*          → للـ stylesheet الثابت (رؤوس، تسميات، أزرار)
                  مثال: f"font-size: {FS_BASE}px;"

  get_font_size() → للـ stylesheet الديناميكي الذي يتغير مع إعدادات المستخدم
                    مثال: في build_stylesheet() أو apply_font()

  fs(base, delta) → لحسابات نسبية
                    مثال: f"font-size: {fs(get_font_size(), -1)}px;"

══════════════════════════════════════════════════════════════
التحديث الديناميكي عند تغيير المستخدم لحجم الخط
══════════════════════════════════════════════════════════════

  لو استخدمت get_font_size() في stylesheet داخل widget،
  الخط مش هيتغير تلقائياً لأن setStyleSheet اتنفّذ مرة واحدة في __init__.

  السطر ده مش ممكن يتكتب في font.py مرة واحدة للكل —
  لأن font.py بيشتغل قبل ما أي widget يتعمل، فمفيش instance يتربط بيه.
  لازم يتكتب في __init__ كل widget محتاج التحديث الديناميكي:

      from ui.widgets.core.events import bus

      class MyWidget(QWidget):
          def __init__(self):
              self._apply_styles()
              bus.font_changed.connect(self._apply_styles)

          def _apply_styles(self, size: int = None):
              size = size or get_font_size()
              self.lbl.setStyleSheet(f"font-size: {size}px;")

  ملاحظة: مش محتاج disconnect —
  Qt بيشيل الـ connection تلقائياً لما الـ widget يتحذف.
"""

from __future__ import annotations
from PyQt5.QtWidgets import QApplication
from ui.constants import DEFAULT_FONT_SIZE, MIN_FONT_SIZE, MAX_FONT_SIZE


# ══════════════════════════════════════════════════════════
# Module-level cache
# ══════════════════════════════════════════════════════════
# يُخزن حجم الخط الحالي هنا لتجنب رحلة إلى AppState/DB في كل مرة.
# يُحدَّث عند: بدء التطبيق، تغيير الإعدادات، تغيير الشركة النشطة.

_module_font_size: int | None = None


def _set_module_font_cache(size: int | None):
    """
    يحدّث الـ module-level font cache.
    للاستخدام الداخلي فقط — يُستدعى من AppState.on_font_changed().
    لا تستدعيه مباشرة من خارج هذا الملف.
    """
    global _module_font_size
    _module_font_size = size


# ══════════════════════════════════════════════════════════
# API العام
# ══════════════════════════════════════════════════════════

def get_font_size() -> int:
    """
    يرجع حجم الخط الحالي.

    الأولوية:
      1. module cache (الأسرع — لا I/O)
      2. AppState.font_size() ← الذي يقرأ من FontService → DB

    لا يتواصل مع DB مباشرة.
    """
    global _module_font_size
    if _module_font_size is not None:
        return _module_font_size
    from ui.app_state import AppState
    size = AppState.font_size()
    _module_font_size = size
    return size


def set_font_size(size: int):
    """
    يحدّث حجم الخط.

    التسلسل:
      font.set_font_size(size)
            ↓
      AppState.on_font_changed(size)   ← cache + إبطال widgets
            ↓
      FontService.save(size)           ← حفظ في DB

    لا يتواصل مع DB مباشرة.
    """
    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
    _set_module_font_cache(size)
    from ui.app_state import AppState
    AppState.on_font_changed(size)


def apply_font(app: QApplication, size: int = None):
    """
    يطبّق حجم الخط على كامل التطبيق ويُعيد بناء الـ stylesheet.

    يُستدعى عادةً من:
      - main.py عند بدء التطبيق
      - SettingsDialog بعد تغيير المستخدم للخط

    لا يتواصل مع DB مباشرة.
    """
    if size is None:
        size = get_font_size()
    size = max(MIN_FONT_SIZE, min(MAX_FONT_SIZE, size))
    _set_module_font_cache(size)
    from ui.app_state import AppState
    AppState.on_font_changed(size)
    # الـ stylesheet يُبنى من theme.py
    from ui.theme import build_stylesheet
    app.setStyleSheet(build_stylesheet(size))


def fs(base: int, delta: int = 0) -> int:
    """
    يرجع حجم خط نسبي بناءً على قيمة أساسية.
    الحد الأدنى = MIN_FONT_SIZE دائماً.

    مثال:
        fs(get_font_size(), -1)   # أصغر من الحالي بـ 1
        fs(FS_BASE, +2)           # أكبر من BASE بـ 2
    """
    return max(MIN_FONT_SIZE, base + delta)


# ══════════════════════════════════════════════════════════
# ثوابت أحجام الخط للـ UI
# ══════════════════════════════════════════════════════════
# استخدم هذه الثوابت في أي stylesheet ثابت بدلاً من كتابة الأرقام.
# مثال: f"font-size: {FS_BASE}px;"
#
# الفرق بين FS_* وget_font_size():
#   FS_*           → ثابت — لا يتغير بإعدادات المستخدم
#                    مناسب لـ: أزرار، تسميات، رؤوس الأقسام
#   get_font_size() → ديناميكي — يتغير مع إعدادات المستخدم
#                    مناسب لـ: build_stylesheet()، نصوص المحتوى الرئيسي

FS_XS   = 10   # تلميحات صغيرة جداً (hint labels, tooltips)
FS_SM   = 11   # تسميات ثانوية، وحدات، تفاصيل صغيرة
FS_BASE = 12   # النص الأساسي، أزرار، حقول إدخال
FS_MD   = 13   # رؤوس الأقسام والنوافذ (section headers)
FS_LG   = 14   # رؤوس أكبر، أيقونات تفاعلية
FS_XL   = 16   # عناوين رئيسية كبيرة