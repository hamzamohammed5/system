"""
ui/events.py
=============
Bus للأحداث العامة بين الـ widgets.

company_data_changed(int):
  يُطلق بعد أي تغيير في بيانات شركة محددة.
  الـ widgets تتحقق من الـ company_id قبل إعادة التحميل.

data_changed():
  الحدث العام القديم — يُبقى للتوافق مع الكود الذي لم يُحدَّث بعد.
"""

from PyQt5.QtCore import QObject, pyqtSignal


class _Bus(QObject):
    # الحدث العام (للتوافق مع الكود القديم)
    data_changed         = pyqtSignal()

    # الحدث المقيّد بالشركة — الأولوية للاستخدام هنا
    company_data_changed = pyqtSignal(int)   # company_id


bus = _Bus()