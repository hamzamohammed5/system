"""
ui/widgets/shared/filter_bar.py
========================
FilterBar — شريط فلتر مشترك.

[تحديث v3]:
  - يرث من FilterToolbar مباشرة عشان ما نكرر الكود
  - يحافظ على نفس الـ API القديم للتوافق مع الكود الموجود
  - LiveConnMixin للـ connection
"""

from PyQt5.QtCore import pyqtSignal

from ui.widgets.shared.panles_helper.filter_toolbar import FilterToolbar
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.events import bus


class FilterBar(FilterToolbar, LiveConnMixin):
    """
    شريط فلتر: [🔍 بحث] [🏷 التصنيف] [↺ مسح]

    يرث من FilterToolbar مع إضافة:
      - LiveConnMixin للـ connection
      - ربط تلقائي بـ bus.data_changed لإعادة تحميل التصنيفات
      - set_count() للعداد

    الاستخدام (متوافق مع الكود القديم):
        bar = FilterBar(conn, scope="raw")
        bar.filter_changed.connect(self._apply_filter)
        layout.addWidget(bar)

        if bar.match(row["name"], row["category_id"]):
            ...
        bar.set_count(shown, total)
    """

    filter_changed = pyqtSignal()

    def __init__(self, conn, scope: str = "all", parent=None):
        self.conn  = conn    # LiveConnMixin يقرأ self.conn
        self._scope = scope
        super().__init__(
            conn=conn,
            scope=scope,
            show_category=True,
            show_date=False,
            placeholder="بحث بالاسم...",
            parent=parent,
        )
        bus.data_changed.connect(self._on_data_changed)

    def _on_data_changed(self):
        try:
            conn = self._live_conn()
            self.reload(conn)
        except Exception:
            pass