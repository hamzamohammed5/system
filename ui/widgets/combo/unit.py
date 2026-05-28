"""
widgets/combo/unit.py
======================
UnitCombo — QComboBox موحد لاختيار وحدة القياس.

الإصلاحات:
  - [إصلاح 1] _cache_key ترجع fallback آمن (id(conn)) بدل None
    القديم: ترجع None عند الفشل → يُتجاهل الـ cache كاملاً
    الجديد: ترجع f"_id_{id(conn)}" → cache يعمل دايماً
    UnitCombo عمرها طويل، فـ id(conn) مقبول كـ fallback
  - load_units / invalidate_units_cache محدّثين يعملون مع str دايماً
  - UnitCombo يستخدم blocked_signals() بدل blockSignals() المكررة
"""

import json
import logging
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore    import pyqtSignal

from ..utils.signals import blocked_signals

logger = logging.getLogger(__name__)

_UNITS_KEY     = "custom_units"
_DEFAULT_UNITS = [
    ("px",   "px — بكسل"),
    ("mm",   "mm — مليمتر"),
    ("cm",   "cm — سنتيمتر"),
    ("m",    "m  — متر"),
    ("inch", "inch — بوصة"),
]

# cache: db_path → list[tuple[str, str]]
_units_cache: dict = {}


def _cache_key(conn) -> str:
    """
    يرجع database path كـ cache key.

    [إصلاح 1] بدل إرجاع None عند الفشل (كان يُعطّل الـ cache كاملاً
    ويخلق entries بـ None كـ key مشتركة بين كل الـ connections)،
    الآن نرجع f"_id_{id(conn)}" كـ fallback آمن.

    UnitCombo عمرها طويل (طول فترة الـ widget)، فـ id(conn) مقبول
    كـ key مؤقتة لأنه لن يتكرر خلال هذه الفترة.
    """
    try:
        row = conn.execute("PRAGMA database_list").fetchone()
        if row and row[2]:
            return row[2]
    except Exception:
        pass
    logger.debug("_cache_key: couldn't get db path, using id fallback")
    return f"_id_{id(conn)}"


def invalidate_units_cache(conn=None):
    """يمسح الـ cache — استدعه بعد تغيير الوحدات أو تغيير الشركة."""
    if conn is None:
        _units_cache.clear()
    else:
        key = _cache_key(conn)  # دايماً str الآن — لا حاجة للتحقق من None
        _units_cache.pop(key, None)


# ── دوال الـ settings ─────────────────────────────────────

def load_units(conn, force: bool = False) -> list:
    """يجلب قائمة الوحدات من settings مع cache."""
    key = _cache_key(conn)  # دايماً str الآن

    if not force and key in _units_cache:
        return _units_cache[key]

    result = list(_DEFAULT_UNITS)
    try:
        from db.shared.settings_repo import get_setting
        raw = get_setting(conn, _UNITS_KEY, "")
        if raw:
            result = [(d[0], d[1]) for d in json.loads(raw)]
    except Exception as e:
        logger.debug("load_units failed, using defaults: %s", e)

    _units_cache[key] = result
    return result


def save_units(conn, units: list):
    try:
        from db.shared.settings_repo import set_setting
        set_setting(conn, _UNITS_KEY, json.dumps(units, ensure_ascii=False))
        invalidate_units_cache(conn)
    except Exception as e:
        logger.warning("save_units failed: %s", e)


def get_last_unit(conn, key: str, fallback: str = "cm") -> str:
    try:
        from db.shared.settings_repo import get_setting
        val = get_setting(conn, f"last_unit_{key}", "")
        return val if val else fallback
    except Exception:
        return fallback


def set_last_unit(conn, key: str, unit: str):
    try:
        from db.shared.settings_repo import set_setting
        set_setting(conn, f"last_unit_{key}", unit)
    except Exception as e:
        logger.debug("set_last_unit failed: %s", e)


# ── UnitCombo ─────────────────────────────────────────────

class UnitCombo(QComboBox):
    """
    QComboBox للوحدات مع:
      - تحميل من settings
      - حفظ آخر اختيار تلقائياً
      - fallback للوحدات الافتراضية
    """

    unit_changed = pyqtSignal(str)

    def __init__(self, conn, last_key: str = None,
                 current: str = None, parent=None):
        super().__init__(parent)
        self._conn     = conn
        self._last_key = last_key
        self._populate()

        if current:
            self.set_unit(current)
        elif last_key:
            self.set_unit(get_last_unit(conn, last_key))

        self.currentIndexChanged.connect(self._on_changed)

    def _populate(self):
        prev = self.currentData()

        with blocked_signals(self):
            self.clear()
            for val, label in load_units(self._conn):
                self.addItem(label, val)

        if prev:
            self.set_unit(prev)

    def refresh(self):
        """يعيد تحميل الوحدات بعد تغيير من الإعدادات."""
        invalidate_units_cache(self._conn)
        self._populate()

    def current_unit(self) -> str:
        return self.currentData() or "cm"

    def set_unit(self, unit: str):
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


# ── دالة سريعة ────────────────────────────────────────────

def make_unit_combo(conn=None, current: str = "cm",
                    last_key: str = None) -> QComboBox:
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


# ── دوال إدارة الوحدات ────────────────────────────────────

def add_unit(conn, value: str, label: str) -> bool:
    value, label = value.strip().lower(), label.strip()
    if not value or not label:
        return False
    units = load_units(conn)
    if any(u[0] == value for u in units):
        return False
    units.append((value, label))
    save_units(conn, units)
    return True


def remove_unit(conn, value: str) -> bool:
    if value in {u[0] for u in _DEFAULT_UNITS}:
        return False
    units = load_units(conn)
    new_units = [u for u in units if u[0] != value]
    if len(new_units) == len(units):
        return False
    save_units(conn, new_units)
    return True


def get_all_units(conn) -> list:
    return load_units(conn)


def reset_units_to_default(conn):
    save_units(conn, list(_DEFAULT_UNITS))