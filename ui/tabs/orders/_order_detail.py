"""
ui/tabs/orders/_order_detail.py
================================
لوحة تفاصيل الطلب.

✅ الـ header والمحتوى كلهم جوا scroll واحد
✅ الـ scroll بيحرك كل حاجة مع بعض
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea,
    QMessageBox, QDialog, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.orders.orders_repo import (
    fetch_order, fetch_order_items,
    change_order_status, cancel_order, delete_order,
    reorder as do_reorder,
    delete_order_item,
)
from ui.tabs.orders._order_form import _OrderForm
from ui.tabs.orders._item_form  import _ItemForm

from ui.widgets.shared.panels import (
    DetailHeader, StatCard, EmptyState,
)

from ui.tabs.orders.order_detail._items_section import (
    _build_items_section, _fill_items,
)
from ui.tabs.orders.order_detail._log_section import (
    _build_log_section, _fill_log,
)
from ui.tabs.orders.order_detail._header_fill import _fill_header
from ui.tabs.orders.order_detail._status_config import STATUS_TRANSITIONS
from ui.tabs.orders.order_detail._status_dialog import _StatusDialog

from ui.app_settings import _C

_BG    = "#f8f9fb"
_BLUE  = "#1565c0"
_GREEN = "#10b981"

_SCROLL_SS = f"""
    QScrollArea {{
        border: none;
        background: {_BG};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-height: 20px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-width: 20px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{ width: 0; }}
"""


class _OrderDetail(QWidget):
    saved          = pyqtSignal(int)
    deleted        = pyqtSignal()
    status_changed = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._order_id   = None
        self._order_data = None
        self._build()
        self._show_empty()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══ Scroll يلف كل حاجة: header + content ══
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll.setStyleSheet(_SCROLL_SS)

        # ── الـ inner container له min width عشان الـ horizontal scroll يظهر لما يضيق ──
        self._inner = QWidget()
        self._inner.setMinimumWidth(520)
        self._inner.setStyleSheet(f"background:{_BG};")

        inner_lay = QVBoxLayout(self._inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.setSpacing(0)

        # ── Header (جوا الـ scroll) ──
        self._hdr = DetailHeader()
        self._card_total   = self._hdr.add_stat_card("💰", "الإجمالي",  color=_BLUE)
        self._card_paid    = self._hdr.add_stat_card("✅", "المدفوع",   color=_GREEN)
        self._card_balance = self._hdr.add_stat_card("⚖️", "المتبقي",   color="#ef4444")
        self._card_due     = self._hdr.add_stat_card("📅", "التسليم",   color="#f59e0b")

        self.btn_edit    = self._hdr.toolbar.add_action("✏️  تعديل",        "primary")
        self.btn_status  = self._hdr.toolbar.add_action("🔄  تغيير الحالة", "ghost")
        self.btn_reorder = self._hdr.toolbar.add_action("📋  إعادة طلب",    "ghost")
        self.btn_cancel  = self._hdr.toolbar.add_danger("❌  إلغاء")
        self.btn_delete  = self._hdr.toolbar.add_danger("🗑️  حذف")

        self.btn_edit.clicked.connect(self._edit_order)
        self.btn_status.clicked.connect(self._change_status_dialog)
        self.btn_reorder.clicked.connect(self._do_reorder)
        self.btn_cancel.clicked.connect(self._cancel_order)
        self.btn_delete.clicked.connect(self._delete_order)

        inner_lay.addWidget(self._hdr)

        # ── المحتوى ──
        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 12, 16, 12)
        self._content_lay.setSpacing(10)

        _build_items_section(self)
        _build_log_section(self)

        self._content_lay.addStretch()
        inner_lay.addWidget(content, stretch=1)

        self._scroll.setWidget(self._inner)
        root.addWidget(self._scroll, stretch=1)

        # ── حالة فارغة (برّا الـ scroll) ──
        self._empty = EmptyState(
            icon="📋",
            title="اختر طلباً من القائمة",
            subtitle="أو أنشئ طلباً جديداً بالضغط على ＋ طلب جديد",
            style="plain",
            color="#6b7280",
            min_height=200,
        )
        root.addWidget(self._empty)

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def load_order(self, order_id: int):
        self._order_id   = order_id
        row = fetch_order(self.conn, order_id)
        self._order_data = dict(row) if row else None
        if not self._order_data:
            return
        self._show_detail()
        _fill_header(self)
        _fill_items(self)
        _fill_log(self)

    def clear(self):
        self._order_id   = None
        self._order_data = None
        self._show_empty()

    def new_order(self):
        dlg = _OrderForm(self.conn, parent=self)
        dlg.saved.connect(self._on_form_saved)
        dlg.exec_()

    def _show_empty(self):
        self._scroll.setVisible(False)
        self._empty.setVisible(True)

    def _show_detail(self):
        self._empty.setVisible(False)
        self._scroll.setVisible(True)
        self._hdr.setVisible(True)
        if hasattr(self, '_log_card'):
            self._log_card.setVisible(True)

    # ══════════════════════════════════════════════════════
    # إجراءات
    # ══════════════════════════════════════════════════════

    def _edit_order(self):
        if not self._order_id:
            return
        dlg = _OrderForm(self.conn, order_id=self._order_id, parent=self)
        dlg.saved.connect(self._on_form_saved)
        dlg.exec_()

    def _on_form_saved(self, order_id: int):
        self.load_order(order_id)
        self.saved.emit(order_id)

    def _change_status_dialog(self):
        if not self._order_id or not self._order_data:
            return
        current       = self._order_data["status"]
        next_statuses = STATUS_TRANSITIONS.get(current, [])
        if not next_statuses:
            return
        dlg = _StatusDialog(current, next_statuses, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            new_status, note = dlg.get_result()
            change_order_status(self.conn, self._order_id, new_status, note)
            self.status_changed.emit(self._order_id)

    def _cancel_order(self):
        if not self._order_id:
            return
        d = self._order_data
        if d["status"] in ("delivered", "cancelled"):
            return
        reason, ok = _get_text_input(
            self, "إلغاء الطلب",
            f"سبب إلغاء الطلب {d['order_number']}:"
        )
        if ok:
            cancel_order(self.conn, self._order_id, reason)
            self.status_changed.emit(self._order_id)

    def _delete_order(self):
        if not self._order_id:
            return
        d = self._order_data
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف الطلب {d['order_number']} نهائياً؟\nلا يمكن التراجع عن هذا الإجراء.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            if delete_order(self.conn, self._order_id):
                self.deleted.emit()
            else:
                QMessageBox.warning(
                    self, "تعذر الحذف",
                    "لا يمكن حذف الطلب إلا في حالة الانتظار أو الإلغاء."
                )

    def _do_reorder(self):
        if not self._order_id:
            return
        d = self._order_data
        if QMessageBox.question(
            self, "إعادة طلب",
            f"إنشاء طلب جديد بناءً على {d['order_number']}؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            new_id = do_reorder(self.conn, self._order_id)
            if new_id:
                self.load_order(new_id)
                self.saved.emit(new_id)

    def _add_item(self):
        if not self._order_id:
            return
        if self._order_data and self._order_data["status"] in ("delivered", "cancelled"):
            QMessageBox.information(self, "تنبيه", "لا يمكن تعديل طلب مكتمل أو ملغي.")
            return
        dlg = _ItemForm(self.conn, self._order_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            _fill_items(self)
            self._fill_header_amounts()

    def _edit_item(self):
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "تنبيه", "اختر بنداً أولاً")
            return
        item_id = self.items_table.item(row, 0).data(Qt.UserRole)
        dlg = _ItemForm(self.conn, self._order_id, item_id=item_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            _fill_items(self)
            self._fill_header_amounts()

    def _del_item(self):
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "تنبيه", "اختر بنداً أولاً")
            return
        item_id = self.items_table.item(row, 0).data(Qt.UserRole)
        name    = self.items_table.item(row, 0).text()
        if QMessageBox.question(
            self, "تأكيد الحذف", f"حذف البند «{name}»؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_order_item(self.conn, item_id)
            _fill_items(self)
            self._fill_header_amounts()

    def _fill_header_amounts(self):
        if not self._order_id:
            return
        row = fetch_order(self.conn, self._order_id)
        self._order_data = dict(row) if row else None
        if self._order_data:
            net    = self._order_data.get("net_amount")  or 0
            paid   = self._order_data.get("paid_amount") or 0
            remain = net - paid
            self._card_total.set_value(f"{net:,.2f} ج")
            self._card_paid.set_value(f"{paid:,.2f} ج")
            self._card_balance.set_value(f"{remain:,.2f} ج")
            self._card_balance.set_color("#ef4444" if remain > 0 else _GREEN)


# ══════════════════════════════════════════════════════════
# مساعد: إدخال نص
# ══════════════════════════════════════════════════════════

def _get_text_input(parent, title, prompt):
    from PyQt5.QtWidgets import QInputDialog
    return QInputDialog.getText(parent, title, prompt)