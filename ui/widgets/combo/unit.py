"""
ui/widgets/combo/unit.py
=========================
UnitCombo — QComboBox موحد لاختيار وحدة القياس.

[Refactor V3] Business logic نُقل لـ unit_service.py.
هذا الملف يحتوي على الـ widget فقط + make_unit_combo.

الـ exports التاريخية محفوظة عبر re-import لضمان التوافق:
  load_units, save_units, invalidate_units_cache, get_last_unit,
  set_last_unit, add_unit, remove_unit, get_all_units,
  reset_units_to_default, _DEFAULT_UNITS
"""

import logging
from PyQt5.QtWidgets import QComboBox
from PyQt5.QtCore    import pyqtSignal

from ..utils.signals import blocked_signals

# re-export للتوافق مع الكود القديم
from .unit_service import (  # noqa: F401
    _DEFAULT_UNITS,
    _cache_key,
    invalidate_units_cache,
    load_units,
    save_units,
    get_last_unit,
    set_last_unit,
    add_unit,
    remove_unit,
    get_all_units,
    reset_units_to_default,
)

logger = logging.getLogger(__name__)


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