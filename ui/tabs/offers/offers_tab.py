"""
ui/tabs/offers/offers_tab.py
==============================
OffersTab — التبويب الرئيسي للعروض.

يجمع:
  - _OfferForm    (offer_form.py)      → فورم إنشاء/تعديل العرض
  - _OffersTable  (offers_table.py)    → جدول العروض المحفوظة
  - _OfferDetails (offer_details.py)   → لوحة تفاصيل العرض المختار
  - CategoryManager                    → إدارة تصنيفات العروض

التخطيط:
  - Splitter رأسي: فورم (أعلى) | (جدول + تفاصيل) (أسفل)
  - Splitter أفقي داخلي: جدول (يسار) | تفاصيل (يمين)
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QSplitter, QTabWidget, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.connection  import get_connection
from db.offers_repo import fetch_offer, delete_offer
from ui.helpers     import confirm_delete
from ui.widgets.category_manager import CategoryManager
from ui.events      import bus

from .offer_form    import _OfferForm
from .offer_details import _OfferDetails
from .offers_table  import _OffersTable

_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #ffe0b2; }
"""


class OffersTab(QWidget):
    """التبويب الرئيسي للعروض."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabBar::tab:selected { color: #e65100; border-top: 2px solid #e65100; }
        """)

        # ── التبويب الرئيسي: العروض ──
        main_widget = QWidget()
        main_lay = QVBoxLayout(main_widget)
        main_lay.setContentsMargins(0, 0, 0, 0)

        # Splitter رأسي: فورم / (جدول + تفاصيل)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._form = _OfferForm(self.conn)
        splitter.addWidget(self._form)

        # Splitter أفقي: جدول / تفاصيل
        bottom = QSplitter(Qt.Horizontal)
        bottom.setHandleWidth(6)
        bottom.setStyleSheet(_SPLITTER_STYLE)

        self._offers_table = _OffersTable(
            self.conn,
            on_edit   = self._edit_offer,
            on_delete = self._delete_offer,
            on_select = self._show_details,
        )
        self._details = _OfferDetails(self.conn)
        bottom.addWidget(self._offers_table)
        bottom.addWidget(self._details)
        bottom.setSizes([480, 420])

        splitter.addWidget(bottom)
        splitter.setSizes([320, 480])
        splitter.setCollapsible(0, True)

        main_lay.addWidget(splitter)

        tabs.addTab(main_widget,                               "🎁  العروض")
        tabs.addTab(CategoryManager(self.conn, scope="all"),   "🏷️  تصنيفات العروض")

        root.addWidget(tabs)

    # ══════════════════════════════════════════════════════
    # أحداث
    # ══════════════════════════════════════════════════════

    def _edit_offer(self, offer_id):
        if offer_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عرضاً أولاً")
            return
        self._form.load_offer(offer_id)

    def _delete_offer(self, offer_id):
        if offer_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عرضاً أولاً")
            return
        offer = fetch_offer(self.conn, offer_id)
        if not offer:
            return
        if confirm_delete(self, offer["name"]):
            if self._form._editing_id == offer_id:
                self._form.reset()
            delete_offer(self.conn, offer_id)
            self._details.clear()
            bus.data_changed.emit()

    def _show_details(self, offer_id):
        self._details.load(offer_id)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)
