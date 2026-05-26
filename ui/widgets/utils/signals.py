"""
ui/widgets/utils/signals.py
=====================================
أدوات مساعدة موحدة للـ Qt signals.

blocked_signals — context manager يمنع الـ signals مؤقتاً.
"""
from contextlib import contextmanager


@contextmanager
def blocked_signals(*widgets):
    """
    Context manager يوقف signals لواحد أو أكثر من الـ widgets
    ثم يعيدها تلقائياً.

    الاستخدام:
        with blocked_signals(self.cmb_variant):
            self.cmb_variant.clear()
            for item in items:
                self.cmb_variant.addItem(...)

        # أو أكثر من widget في نفس الوقت:
        with blocked_signals(self.cmb_a, self.cmb_b):
            self.cmb_a.clear()
            self.cmb_b.clear()
    """
    for w in widgets:
        w.blockSignals(True)
    try:
        yield
    finally:
        for w in widgets:
            w.blockSignals(False)