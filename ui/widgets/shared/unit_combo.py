"""
ui/widgets/shared/unit_combo.py
================================
UnitCombo — QComboBox موحد لاختيار وحدة القياس.

المميزات:
  - قائمة وحدات موحدة محفوظة في DB (settings)
  - آخر وحدة تم اختيارها تُحفظ وتُعاد عند فتح الـ combo
  - الوحدات الافتراضية: px, mm, cm, m, inch
  - يُضاف وحدات جديدة من SettingsDialog فقط

الاستخدام:
    from ui.widgets.shared.unit_combo import UnitCombo, make_unit_combo

    # Widget مستقل:
    combo = UnitCombo(conn, last_key="dim_sets_unit")
    combo.current_unit()   # → "mm"

    # دالة مساعدة لبناء QComboBox عادي (للـ dialogs القديمة):
    cmb = make_unit_combo(conn, current="cm", last_key="dim_sets_unit")
"""

import json
import logging
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore    import pyqtSignal

logger = logging.getLogger(__name__)

# ── مفتاح التخزين في settings ──
_UNITS_KEY    = "custom_units"
_DEFAULT_UNITS = [
    ("px",   "px — بكسل"),
    ("mm",   "mm — مليمتر"),
    ("cm",   "cm — سنتيمتر"),
    ("m",    "m  — متر"),
    ("inch", "inch — بوصة"),
]

# FIX 8: cache بسيط لتجنب DB query في كل مرة
# المفتاح: id(conn) — يُبطل بـ invalidate_units_cache() بعد أي تغيير
_units_cache: dict[int, list[tuple[str, str]]] = {}


def invalidate_units_cache(conn=None):
    """يُبطل الـ cache — استدعه بعد add_unit / remove_unit / reset."""
    if conn is None:
        _units_cache.clear()
    else:
        _units_cache.pop(id(conn), None)


# ══════════════════════════════════════════════════════════
# دوال الـ settings
# ══════════════════════════════════════════════════════════

def load_units(conn, force: bool = False) -> list[tuple[str, str]]:
    """
    يجلب قائمة الوحدات من settings مع cache.
    يرجع list of (value, label).

    force=True يتجاوز الـ cache ويجبر إعادة القراءة من DB.
    """
    cache_key = id(conn)

    # FIX 8: أرجع من الـ cache لو موجود
    if not force and cache_key in _units_cache:
        return _units_cache[cache_key]

    result = list(_DEFAULT_UNITS)
    try:
        from db.shared.settings_repo import get_setting
        raw = get_setting(conn, _UNITS_KEY, "")
        if raw:
            data = json.loads(raw)
            result = [(d[0], d[1]) for d in data]
    except Exception as e:
        logger.debug("load_units failed, using defaults: %s", e)

    _units_cache[cache_key] = result
    return result


def save_units(conn, units: list[tuple[str, str]]):
    """يحفظ قائمة الوحدات في settings ويُبطل الـ cache."""
    try:
        from db.shared.settings_repo import set_setting
        set_setting(conn, _UNITS_KEY, json.dumps(units, ensure_ascii=False))
        invalidate_units_cache(conn)
    except Exception as e:
        logger.warning("save_units failed: %s", e)


def get_last_unit(conn, key: str, fallback: str = "cm") -> str:
    """يجلب آخر وحدة تم اختيارها لـ key معين."""
    try:
        from db.shared.settings_repo import get_setting
        val = get_setting(conn, f"last_unit_{key}", "")
        return val if val else fallback
    except Exception as e:
        logger.debug("get_last_unit failed: %s", e)
        return fallback


def set_last_unit(conn, key: str, unit: str):
    """يحفظ آخر وحدة تم اختيارها."""
    try:
        from db.shared.settings_repo import set_setting
        set_setting(conn, f"last_unit_{key}", unit)
    except Exception as e:
        logger.debug("set_last_unit failed: %s", e)


# ══════════════════════════════════════════════════════════
# UnitCombo — QComboBox الموحد
# ══════════════════════════════════════════════════════════

class UnitCombo(QComboBox):
    """
    QComboBox للوحدات مع:
      - تحميل الوحدات من settings
      - حفظ آخر اختيار تلقائياً
      - fallback للوحدات الافتراضية لو settings فارغة

    المعاملات:
        conn     : اتصال قاعدة البيانات
        last_key : مفتاح تخزين آخر اختيار (مثل "dim_sets_unit")
                   لو None → لا يُحفظ الاختيار
        current  : الوحدة المحددة مبدئياً (تتجاوز last_key لو محدد)
    """

    unit_changed = pyqtSignal(str)

    def __init__(self, conn, last_key: str = None,
                 current: str = None, parent=None):
        super().__init__(parent)
        self._conn     = conn
        self._last_key = last_key

        self._populate()

        # تحديد الوحدة الأولية
        if current:
            self.set_unit(current)
        elif last_key:
            self.set_unit(get_last_unit(conn, last_key))

        self.currentIndexChanged.connect(self._on_changed)

    def _populate(self):
        """
        يملأ الـ combo بالوحدات من settings أو الافتراضية.

        FIX 2: يستخدم blockSignals() بدل _loading flag
        عشان يكون آمن وصريح — blockSignals هو الطريقة الصحيحة في Qt
        """
        prev = self.currentData()
        self.blockSignals(True)
        self.clear()

        for val, label in load_units(self._conn):
            self.addItem(label, val)

        self.blockSignals(False)

        # استعادة الاختيار السابق
        if prev:
            self.set_unit(prev)

    def refresh(self):
        """يعيد تحميل الوحدات (بعد إضافة وحدات جديدة من الإعدادات)."""
        # أبطل الـ cache قبل إعادة التحميل
        invalidate_units_cache(self._conn)
        self._populate()

    def current_unit(self) -> str:
        """يرجع قيمة الوحدة الحالية (مثل 'mm')."""
        return self.currentData() or "cm"

    def set_unit(self, unit: str):
        """يحدد الوحدة المطلوبة."""
        for i in range(self.count()):
            if self.itemData(i) == unit:
                self.setCurrentIndex(i)
                return
        if self.count():
            self.setCurrentIndex(0)

    def _on_changed(self, _):
        unit = self.current_unit()
        if self._last_key and self._conn:
            set_last_unit(self._conn, self._last_key, unit)
        self.unit_changed.emit(unit)


# ══════════════════════════════════════════════════════════
# دالة مساعدة للتوافق مع الكود القديم
# ══════════════════════════════════════════════════════════

def make_unit_combo(conn=None, current: str = "cm",
                    last_key: str = None) -> QComboBox:
    """
    يبني QComboBox للوحدات — بديل للدالة القديمة في _groups_panel.py و _field_dialog.py.

    لو conn=None → يستخدم الوحدات الافتراضية فقط.
    """
    if conn is not None:
        combo = UnitCombo(conn, last_key=last_key, current=current)
    else:
        combo = QComboBox()
        for val, label in _DEFAULT_UNITS:
            combo.addItem(label, val)

    for i in range(combo.count()):
        if combo.itemData(i) == current:
            combo.setCurrentIndex(i)
            break

    return combo


# ══════════════════════════════════════════════════════════
# دوال إدارة الوحدات (تُستدعى من SettingsDialog)
# ══════════════════════════════════════════════════════════

def add_unit(conn, value: str, label: str) -> bool:
    """
    يضيف وحدة جديدة.
    يرجع True لو نجح، False لو الوحدة موجودة بالفعل.
    """
    value = value.strip().lower()
    label = label.strip()
    if not value or not label:
        return False

    units = load_units(conn)
    if any(u[0] == value for u in units):
        return False

    units.append((value, label))
    save_units(conn, units)
    return True


def remove_unit(conn, value: str) -> bool:
    """
    يحذف وحدة.
    لا يحذف الوحدات الافتراضية.
    يرجع True لو نجح.
    """
    default_vals = {u[0] for u in _DEFAULT_UNITS}
    if value in default_vals:
        return False

    units = load_units(conn)
    new_units = [u for u in units if u[0] != value]
    if len(new_units) == len(units):
        return False

    save_units(conn, new_units)
    return True


def get_all_units(conn) -> list[tuple[str, str]]:
    """يرجع كل الوحدات الحالية."""
    return load_units(conn)


def reset_units_to_default(conn):
    """يعيد الوحدات للافتراضية."""
    save_units(conn, list(_DEFAULT_UNITS))