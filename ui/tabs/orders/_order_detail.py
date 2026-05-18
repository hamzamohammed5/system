"""
ui/tabs/orders/_order_detail.py  — نسخة محسّنة UX v2
================================
التحسينات:
  - DetailHeader من panels.py — هيدر موحد ومرتب
  - make_detail_table من table_utils.py — جدول موحد
  - CollapsibleCard للسجل — قابل للطي
  - EmptyState واضح مع دعوة للإجراء
  - ActionToolbar موحد — فصل أزرار أساسية وخطرة
  - جدول السجل: أعمدة قابلة للتعديل يدوياً من الـ UI
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QComboBox, QLineEdit,
    QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QFont

from db.orders.orders_repo import (
    fetch_order, fetch_order_items, fetch_status_log,
    change_order_status, cancel_order, delete_order,
    reorder as do_reorder,
    insert_order_item, update_order_item, delete_order_item,
)
from ui.tabs.orders._order_form import _OrderForm
from ui.tabs.orders._item_form  import _ItemForm

# مكونات مشتركة
from ui.widgets.shared.panels import (
    DetailHeader, StatCard, SectionHeader,
    EmptyState, CollapsibleCard, ActionToolbar,
)
from ui.widgets.shared.table_utils import (
    make_detail_table, make_compact_table,
    make_table_item, color_item, bold_item, muted_item,
    insert_row, ROW_HEIGHT_NORMAL, ROW_HEIGHT_COMPACT,
)

# ── ثوابت ──
STATUS_LABELS = {
    "pending":     ("⏳ انتظار",   "#b45309", "#fffbeb", "#fde68a"),
    "confirmed":   ("✅ مؤكد",     "#1d4ed8", "#eff6ff", "#bfdbfe"),
    "in_progress": ("🔧 تنفيذ",   "#6d28d9", "#f5f3ff", "#ddd6fe"),
    "ready":       ("📦 جاهز",    "#065f46", "#ecfdf5", "#a7f3d0"),
    "delivered":   ("🚚 مُسلَّم",  "#374151", "#f9fafb", "#e5e7eb"),
    "cancelled":   ("❌ ملغي",    "#991b1b", "#fef2f2", "#fecaca"),
    "on_hold":     ("⏸ معلق",    "#9a3412", "#fff7ed", "#fed7aa"),
}

STATUS_TRANSITIONS = {
    "pending":     ["confirmed", "cancelled", "on_hold"],
    "confirmed":   ["in_progress", "cancelled", "on_hold"],
    "in_progress": ["ready", "cancelled", "on_hold"],
    "ready":       ["delivered", "cancelled"],
    "on_hold":     ["pending", "confirmed", "cancelled"],
    "delivered":   [],
    "cancelled":   ["pending"],
}

PRIORITY_LABELS = {
    "low":    ("⬇ منخفض", "#9ca3af"),
    "normal": ("➡ عادي",  "#6b7280"),
    "high":   ("⬆ عالي", "#f59e0b"),
    "urgent": ("🔴 عاجل", "#ef4444"),
}

TYPE_LABELS = {
    "new":     "🆕 جديد",
    "reorder": "🔄 إعادة طلب",
    "custom":  "⚙️ مخصص",
}

# ألوان
_BG     = "#f8f9fb"
_WHITE  = "#ffffff"
_BLUE   = "#1565c0"
_GREEN  = "#10b981"
_BORDER = "#e5e9f0"


# ══════════════════════════════════════════════════════════
# _OrderDetail
# ══════════════════════════════════════════════════════════

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

        # ── Header موحد ───────────────────────────────────
        self._hdr = DetailHeader()

        # بطاقات الإحصائيات
        self._card_total   = self._hdr.add_stat_card("💰", "الإجمالي",  color=_BLUE)
        self._card_paid    = self._hdr.add_stat_card("✅", "المدفوع",   color=_GREEN)
        self._card_balance = self._hdr.add_stat_card("⚖️", "المتبقي",   color="#ef4444")
        self._card_due     = self._hdr.add_stat_card("📅", "التسليم",   color="#f59e0b")

        # أزرار الإجراءات
        self.btn_edit    = self._hdr.toolbar.add_action("✏️  تعديل",       "primary")
        self.btn_status  = self._hdr.toolbar.add_action("🔄  تغيير الحالة","ghost")
        self.btn_reorder = self._hdr.toolbar.add_action("📋  إعادة طلب",   "ghost")
        self.btn_cancel  = self._hdr.toolbar.add_danger("❌  إلغاء")
        self.btn_delete  = self._hdr.toolbar.add_danger("🗑️  حذف")

        self.btn_edit.clicked.connect(self._edit_order)
        self.btn_status.clicked.connect(self._change_status_dialog)
        self.btn_reorder.clicked.connect(self._do_reorder)
        self.btn_cancel.clicked.connect(self._cancel_order)
        self.btn_delete.clicked.connect(self._delete_order)

        root.addWidget(self._hdr)

        # ── محتوى قابل للتمرير ─────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {_BG}; }}
            QScrollBar:vertical {{
                background: #f0f0f0; width: 5px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: #cdd3e0; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 12, 16, 12)
        self._content_lay.setSpacing(10)

        self._build_items_section()
        self._build_log_section()

        self._content_lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # ── حالة فارغة ─────────────────────────────────────
        self._empty = EmptyState(
            icon="📋",
            title="اختر طلباً من القائمة",
            subtitle="أو أنشئ طلباً جديداً بالضغط على ＋ طلب جديد",
            style="plain",
            color="#6b7280",
            min_height=200,
        )
        root.addWidget(self._empty)

    def _build_items_section(self):
        # رأس القسم
        items_hdr = SectionHeader("📦  بنود الطلب")
        self.btn_add_item = items_hdr.add_button("＋  إضافة بند", self._add_item, "success")
        self._content_lay.addWidget(items_hdr)

        # جدول البنود
        self.items_table = make_detail_table(
            columns=["البند", "الوصف", "الكمية", "الوحدة", "السعر", "الخصم%", "الإجمالي"],
            stretch_col=0,
            col_widths={2: 65, 3: 65, 4: 85, 5: 65, 6: 90},
            max_height=260,
            min_height=60,
            row_height=ROW_HEIGHT_NORMAL,
        )
        self._content_lay.addWidget(self.items_table)

        # EmptyState للبنود
        self._empty_items = EmptyState(
            icon="📦",
            title="لا توجد بنود في هذا الطلب",
            subtitle="اضغط «＋ إضافة بند» لإضافة منتج",
            style="dashed",
            color="#10b981",
            min_height=80,
        )
        self._empty_items.action_clicked.connect(self._add_item)
        self._content_lay.addWidget(self._empty_items)

        # أزرار تعديل/حذف البند
        item_toolbar = ActionToolbar()
        self.btn_edit_item = item_toolbar.add_action("✏️  تعديل بند", "ghost", self._edit_item)
        self.btn_del_item  = item_toolbar.add_danger("🗑️  حذف بند",            self._del_item)
        self.btn_edit_item.setMinimumHeight(28)
        self.btn_del_item.setMinimumHeight(28)
        self._content_lay.addWidget(item_toolbar)

    def _build_log_section(self):
        # بطاقة قابلة للطي
        self._log_card = CollapsibleCard("📜  سجل تغييرات الحالة", expanded=False)

        # جدول السجل بدون col_widths ثابتة
        self.log_table = make_compact_table(
            columns=["من", "إلى", "الملاحظات", "الوقت"],
            stretch_col=-1,        # بدون stretch تلقائي
            max_height=160,
        )

        # ── تفعيل resize يدوي لكل الأعمدة ──
        hh = self.log_table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Interactive)   # كل الأعمدة قابلة للسحب
        hh.setStretchLastSection(False)                    # بدون تمدد تلقائي للأخير
        hh.setMinimumSectionSize(40)

        # عرض ابتدائي مناسب (قابل للتعديل لاحقاً)
        self.log_table.setColumnWidth(0, 90)
        self.log_table.setColumnWidth(1, 90)
        self.log_table.setColumnWidth(2, 200)
        self.log_table.setColumnWidth(3, 130)

        self._log_card.content_layout.addWidget(self.log_table)
        self._content_lay.addWidget(self._log_card)

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
        self._fill_header()
        self._fill_items()
        self._fill_log()

    def clear(self):
        self._order_id   = None
        self._order_data = None
        self._show_empty()

    def new_order(self):
        dlg = _OrderForm(self.conn, parent=self)
        dlg.saved.connect(self._on_form_saved)
        dlg.exec_()

    def _show_empty(self):
        self._empty.setVisible(True)
        self._hdr.setVisible(False)
        self._log_card.setVisible(False)
        self.items_table.setVisible(False)
        self._empty_items.setVisible(False)

    def _show_detail(self):
        self._empty.setVisible(False)
        self._hdr.setVisible(True)
        self._log_card.setVisible(True)

    # ══════════════════════════════════════════════════════
    # ملء البيانات
    # ══════════════════════════════════════════════════════

    def _fill_header(self):
        d = self._order_data

        self._hdr.set_title(d["order_number"])
        self._hdr.set_type_badge(TYPE_LABELS.get(d["order_type"], ""))

        status_info = STATUS_LABELS.get(d["status"], (d["status"], "#555", "#fff", "#eee"))
        self._hdr.set_status_badge(status_info[0], status_info[1], status_info[2], status_info[3])

        pri_lbl, pri_color = PRIORITY_LABELS.get(d["priority"], ("", "#6b7280"))
        self._hdr.set_priority_badge(pri_lbl, pri_color)

        parts = [f"👤  {d['customer_name']}  ({d['customer_code']})"]
        if d.get("customer_phone"): parts.append(f"📞 {d['customer_phone']}")
        if d.get("customer_city"):  parts.append(f"📍 {d['customer_city']}")
        self._hdr.set_info(parts)

        net    = d.get("net_amount")  or 0
        paid   = d.get("paid_amount") or 0
        remain = net - paid

        self._card_total.set_value(f"{net:,.2f} ج")
        self._card_paid.set_value(f"{paid:,.2f} ج")
        self._card_balance.set_value(f"{remain:,.2f} ج")
        self._card_balance.set_color("#ef4444" if remain > 0 else _GREEN)
        self._card_due.set_value(d.get("due_date") or "─")

        status = d["status"]
        can_edit   = status not in ("delivered", "cancelled")
        can_cancel = status not in ("delivered", "cancelled")
        can_delete = status in ("pending", "cancelled")
        can_change = bool(STATUS_TRANSITIONS.get(status))

        self.btn_edit.setEnabled(can_edit)
        self.btn_cancel.setEnabled(can_cancel)
        self.btn_delete.setEnabled(can_delete)
        self.btn_status.setEnabled(can_change)
        self.btn_add_item.setEnabled(can_edit)

    def _fill_items(self):
        items = fetch_order_items(self.conn, self._order_id)
        self.items_table.setRowCount(0)

        has_items = bool(items)
        self.items_table.setVisible(has_items)
        self._empty_items.setVisible(not has_items)
        self.btn_edit_item.setVisible(has_items)
        self.btn_del_item.setVisible(has_items)

        for item in items:
            r = insert_row(self.items_table, ROW_HEIGHT_NORMAL)

            name_item = make_table_item(item["item_name"], user_data=item["id"])
            bold_item(name_item)
            self.items_table.setItem(r, 0, name_item)

            self.items_table.setItem(r, 1, make_table_item(item.get("description") or ""))

            qty_item = make_table_item(f"{item['quantity']:g}", align=Qt.AlignCenter)
            self.items_table.setItem(r, 2, qty_item)

            unit_item = make_table_item(item["unit"], align=Qt.AlignCenter)
            muted_item(unit_item)
            self.items_table.setItem(r, 3, unit_item)

            price_item = make_table_item(f"{item['unit_price']:,.2f}", align=Qt.AlignCenter)
            self.items_table.setItem(r, 4, price_item)

            disc_item = make_table_item(f"{item['discount_pct']:g}%", align=Qt.AlignCenter)
            muted_item(disc_item)
            self.items_table.setItem(r, 5, disc_item)

            total_val  = item["quantity"] * item["unit_price"] * (1 - item["discount_pct"] / 100)
            total_item = make_table_item(f"{total_val:,.2f}", align=Qt.AlignCenter)
            bold_item(total_item)
            color_item(total_item, _BLUE)
            self.items_table.setItem(r, 6, total_item)

    def _fill_log(self):
        logs = [dict(r) for r in fetch_status_log(self.conn, self._order_id)]
        self.log_table.setRowCount(0)

        for log in logs:
            r = insert_row(self.log_table, ROW_HEIGHT_COMPACT)

            old_lbl = STATUS_LABELS.get(log.get("old_status") or "", ("—",))[0]
            new_info = STATUS_LABELS.get(log.get("new_status", ""), (log.get("new_status",""), "#555"))
            new_lbl, new_color = new_info[0], new_info[1]

            self.log_table.setItem(r, 0, muted_item(make_table_item(old_lbl)))
            new_item = make_table_item(new_lbl)
            color_item(new_item, new_color)
            self.log_table.setItem(r, 1, new_item)
            self.log_table.setItem(r, 2, make_table_item(log.get("notes") or ""))
            time_str = (log.get("changed_at") or "")[:16]
            self.log_table.setItem(r, 3, muted_item(make_table_item(time_str, align=Qt.AlignCenter)))

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
        current = self._order_data["status"]
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
            self._fill_items()
            self._fill_header_amounts()

    def _edit_item(self):
        row = self.items_table.currentRow()
        if row < 0:
            QMessageBox.information(self, "تنبيه", "اختر بنداً أولاً")
            return
        item_id = self.items_table.item(row, 0).data(Qt.UserRole)
        dlg = _ItemForm(self.conn, self._order_id, item_id=item_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._fill_items()
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
            self._fill_items()
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
# Dialog تغيير الحالة
# ══════════════════════════════════════════════════════════

STATUS_LABELS_SHORT = {k: v[0] for k, v in STATUS_LABELS.items()}

_BG_DLG    = "#f8f9fb"
_BORDER_DLG = "#cdd3e0"


class _StatusDialog(QDialog):
    def __init__(self, current_status: str, next_statuses: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تغيير حالة الطلب")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._result = (next_statuses[0] if next_statuses else current_status, "")
        self._build(current_status, next_statuses)

    def _build(self, current, nexts):
        self.setStyleSheet(f"QDialog {{ background: {_BG_DLG}; }}")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(10)

        lbl = QLabel(
            f"الحالة الحالية:  <b>{STATUS_LABELS_SHORT.get(current, current)}</b>"
        )
        lbl.setStyleSheet("color:#374151;")
        lay.addWidget(lbl)

        self._cmb = QComboBox()
        self._cmb.setMinimumHeight(34)
        for s in nexts:
            self._cmb.addItem(STATUS_LABELS_SHORT.get(s, s), s)
        lay.addWidget(self._cmb)

        lbl3 = QLabel("ملاحظات (اختياري):")
        lbl3.setStyleSheet("color:#6b7280;")
        lay.addWidget(lbl3)

        self._note = QLineEdit()
        self._note.setPlaceholderText("سبب التغيير...")
        self._note.setMinimumHeight(34)
        lay.addWidget(self._note)

        btns = QHBoxLayout()
        btn_ok = QPushButton("✅  تغيير")
        btn_ok.setMinimumHeight(36)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: white;
                border: none; border-radius: 6px;
                padding: 0 18px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
        """)
        btn_ok.clicked.connect(self._save)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: white; color: #374151;
                border: 1px solid {_BORDER_DLG}; border-radius: 6px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {_BG_DLG}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_ok, stretch=1)
        lay.addLayout(btns)

    def _save(self):
        self._result = (self._cmb.currentData(), self._note.text().strip())
        self.accept()

    def get_result(self):
        return self._result


# ══════════════════════════════════════════════════════════
# مساعد: إدخال نص
# ══════════════════════════════════════════════════════════

def _get_text_input(parent, title, prompt):
    from PyQt5.QtWidgets import QInputDialog
    return QInputDialog.getText(parent, title, prompt)