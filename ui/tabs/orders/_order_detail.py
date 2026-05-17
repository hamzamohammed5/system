"""
ui/tabs/orders/_order_detail.py
================================
لوحة تفاصيل الطلب الكاملة:
  - Header: معلومات الطلب + أزرار الإجراءات
  - بنود الطلب (إضافة / تعديل / حذف)
  - سجل تغييرات الحالة
  - فورم إنشاء / تعديل الطلب
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QComboBox, QLineEdit,
    QTextEdit,
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

# ── ثوابت ──
STATUS_LABELS = {
    "pending":     ("⏳ انتظار",   "#f59e0b"),
    "confirmed":   ("✅ مؤكد",     "#3b82f6"),
    "in_progress": ("🔧 تنفيذ",   "#8b5cf6"),
    "ready":       ("📦 جاهز",    "#10b981"),
    "delivered":   ("🚚 مُسلَّم",  "#6b7280"),
    "cancelled":   ("❌ ملغي",    "#ef4444"),
    "on_hold":     ("⏸ معلق",    "#f97316"),
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
    "low":    "⬇ منخفض",
    "normal": "➡ عادي",
    "high":   "⬆ عالي",
    "urgent": "🔴 عاجل",
}

TYPE_LABELS = {
    "new":     "🆕 جديد",
    "reorder": "🔄 إعادة طلب",
    "custom":  "⚙️ مخصص",
}


def _stat_card(icon: str, title: str, value: str = "─",
               color: str = "#1565c0") -> tuple:
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: white;
            border: 1px solid #e5e9f0;
            border-radius: 8px;
        }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(12, 10, 12, 10)
    lay.setSpacing(3)

    lbl_icon = QLabel(f"{icon}  {title}")
    lbl_icon.setStyleSheet(
        "font-size:10px; color:#9ba5be; background:transparent; border:none;"
    )

    lbl_val = QLabel(value)
    lbl_val.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lbl_val.setAlignment(Qt.AlignCenter)

    lay.addWidget(lbl_icon)
    lay.addWidget(lbl_val)
    return frame, lbl_val


class _OrderDetail(QWidget):
    saved          = pyqtSignal(int)
    deleted        = pyqtSignal()
    status_changed = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._order_id  = None
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

        # ── Header ────────────────────────────────────────
        self._hdr = QFrame()
        self._hdr.setStyleSheet("""
            QFrame {
                background: white;
                border-bottom: 1px solid #e5e9f0;
            }
        """)
        hdr_lay = QVBoxLayout(self._hdr)
        hdr_lay.setContentsMargins(18, 14, 18, 14)
        hdr_lay.setSpacing(10)

        # صف العنوان
        title_row = QHBoxLayout()
        self._lbl_order_num = QLabel("طلب جديد")
        f = QFont()
        f.setPointSize(13)
        f.setBold(True)
        self._lbl_order_num.setFont(f)
        self._lbl_order_num.setStyleSheet(
            "color:#1a2035; background:transparent;"
        )

        self._lbl_status_badge = QLabel("")
        self._lbl_status_badge.setStyleSheet(
            "font-size:11px; font-weight:bold; padding:3px 10px;"
            "border-radius:10px; background:#f0f0f0; color:#555;"
        )

        title_row.addWidget(self._lbl_order_num)
        title_row.addWidget(self._lbl_status_badge)
        title_row.addStretch()
        hdr_lay.addLayout(title_row)

        # معلومات العميل
        self._lbl_customer = QLabel("")
        self._lbl_customer.setStyleSheet(
            "color:#5a6680; font-size:12px; background:transparent;"
        )
        hdr_lay.addWidget(self._lbl_customer)

        # بطاقات الإحصائيات
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        f1, self._lbl_total    = _stat_card("💰", "الإجمالي",     color="#1565c0")
        f2, self._lbl_paid     = _stat_card("✅", "المدفوع",     color="#10b981")
        f3, self._lbl_balance  = _stat_card("⚖️", "المتبقي",     color="#ef4444")
        f4, self._lbl_due_date = _stat_card("📅", "التسليم",     color="#f59e0b")
        for f in (f1, f2, f3, f4):
            stats_row.addWidget(f, stretch=1)
        hdr_lay.addLayout(stats_row)

        # أزرار الإجراءات
        actions_row = QHBoxLayout()
        actions_row.setSpacing(6)

        self.btn_edit = QPushButton("✏️  تعديل")
        self.btn_edit.setMinimumHeight(32)

        self.btn_status = QPushButton("🔄  تغيير الحالة")
        self.btn_status.setMinimumHeight(32)

        self.btn_reorder = QPushButton("📋  إعادة طلب")
        self.btn_reorder.setMinimumHeight(32)

        self.btn_cancel = QPushButton("❌  إلغاء")
        self.btn_cancel.setMinimumHeight(32)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                color: #dc2626;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 12px;
            }
            QPushButton:hover { background: #fee2e2; }
        """)

        self.btn_delete = QPushButton("🗑️  حذف")
        self.btn_delete.setMinimumHeight(32)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background: #fef2f2;
                color: #991b1b;
                border: 1px solid #fecaca;
                border-radius: 6px;
                padding: 0 12px;
                font-size: 12px;
            }
            QPushButton:hover { background: #fee2e2; }
        """)

        for btn in (self.btn_edit, self.btn_status, self.btn_reorder):
            btn.setStyleSheet("""
                QPushButton {
                    background: #f8f9fb;
                    color: #374151;
                    border: 1px solid #cdd3e0;
                    border-radius: 6px;
                    padding: 0 12px;
                    font-size: 12px;
                }
                QPushButton:hover { background: #dbeafe; color: #1565c0; }
            """)

        self.btn_edit.clicked.connect(self._edit_order)
        self.btn_status.clicked.connect(self._change_status_dialog)
        self.btn_reorder.clicked.connect(self._do_reorder)
        self.btn_cancel.clicked.connect(self._cancel_order)
        self.btn_delete.clicked.connect(self._delete_order)

        actions_row.addWidget(self.btn_edit)
        actions_row.addWidget(self.btn_status)
        actions_row.addWidget(self.btn_reorder)
        actions_row.addStretch()
        actions_row.addWidget(self.btn_cancel)
        actions_row.addWidget(self.btn_delete)
        hdr_lay.addLayout(actions_row)

        root.addWidget(self._hdr)

        # ── محتوى قابل للتمرير ─────────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: #f8f9fb; }
            QScrollBar:vertical {
                background: #f0f0f0; width: 5px; border-radius: 2px;
            }
            QScrollBar::handle:vertical {
                background: #cdd3e0; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height:0; }
        """)

        content = QWidget()
        content.setStyleSheet("background:#f8f9fb;")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(18, 14, 18, 14)
        self._content_lay.setSpacing(14)

        # ── قسم البنود ──────────────────────────────────────
        items_hdr = self._section_header("📦  بنود الطلب")
        self._content_lay.addWidget(items_hdr)

        btn_add_item = QPushButton("+ إضافة بند")
        btn_add_item.setMinimumHeight(30)
        btn_add_item.setStyleSheet("""
            QPushButton {
                background: #ecfdf5;
                color: #065f46;
                border: 1px solid #a7f3d0;
                border-radius: 5px;
                padding: 0 12px;
                font-size: 11px;
            }
            QPushButton:hover { background: #d1fae5; }
        """)
        btn_add_item.clicked.connect(self._add_item)
        self._content_lay.addWidget(btn_add_item)

        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "البند", "الوصف", "الكمية", "الوحدة", "السعر", "الخصم%", "الإجمالي"
        ])
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setMaximumHeight(220)
        self.items_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #e5e9f0;
                border-radius: 8px;
                background: white;
                font-size: 11px;
                outline: none;
            }
            QTableWidget::item { padding: 5px 8px; }
            QTableWidget::item:selected { background: #dbeafe; color: #1e40af; }
            QHeaderView::section {
                background: #f8f9fb; color: #6b7280;
                font-size: 10px; font-weight: bold;
                padding: 5px 8px; border: none;
                border-bottom: 1px solid #e5e9f0;
                border-right: 1px solid #e5e9f0;
            }
        """)
        hh = self.items_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 7):
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._content_lay.addWidget(self.items_table)

        # أزرار تعديل/حذف البند
        item_btns = QHBoxLayout()
        btn_edit_item = QPushButton("✏️  تعديل بند")
        btn_del_item  = QPushButton("🗑️  حذف بند")
        for b, color in [(btn_edit_item, "#f8f9fb"), (btn_del_item, "#fef2f2")]:
            b.setMinimumHeight(28)
            b.setStyleSheet(f"""
                QPushButton {{
                    background: {color};
                    border: 1px solid #cdd3e0;
                    border-radius: 5px;
                    padding: 0 10px;
                    font-size: 11px;
                    color: #374151;
                }}
                QPushButton:hover {{ background: #dbeafe; }}
            """)
        btn_edit_item.clicked.connect(self._edit_item)
        btn_del_item.clicked.connect(self._del_item)
        item_btns.addWidget(btn_edit_item)
        item_btns.addWidget(btn_del_item)
        item_btns.addStretch()
        self._content_lay.addLayout(item_btns)

        # ── قسم سجل الحالة ─────────────────────────────────
        log_hdr = self._section_header("📜  سجل تغييرات الحالة")
        self._content_lay.addWidget(log_hdr)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(
            ["من", "إلى", "الملاحظات", "الوقت"]
        )
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.log_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setMaximumHeight(180)
        self.log_table.setStyleSheet(self.items_table.styleSheet())
        hh2 = self.log_table.horizontalHeader()
        hh2.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh2.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh2.setSectionResizeMode(2, QHeaderView.Stretch)
        hh2.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh2.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._content_lay.addWidget(self.log_table)

        self._content_lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # ── حالة فارغة ─────────────────────────────────────
        self._empty = QFrame()
        self._empty.setStyleSheet("background:#f8f9fb; border:none;")
        e_lay = QVBoxLayout(self._empty)
        e_lay.setAlignment(Qt.AlignCenter)
        for text, style in [
            ("📋", "font-size:40px; background:transparent;"),
            ("اختر طلباً من القائمة أو أنشئ طلباً جديداً",
             "font-size:13px; color:#6b7280; background:transparent;"),
        ]:
            lbl = QLabel(text)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(style)
            e_lay.addWidget(lbl)
        root.addWidget(self._empty)

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#374151;"
            "background:transparent;"
        )
        return lbl

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def load_order(self, order_id: int):
        self._order_id   = order_id
        self._order_data = fetch_order(self.conn, order_id)
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

    def _show_detail(self):
        self._empty.setVisible(False)
        self._hdr.setVisible(True)

    def _fill_header(self):
        d = self._order_data
        self._lbl_order_num.setText(
            f"{d['order_number']}  —  {TYPE_LABELS.get(d['order_type'], '')}"
        )

        status_lbl, status_color = STATUS_LABELS.get(
            d["status"], (d["status"], "#555")
        )
        self._lbl_status_badge.setText(status_lbl)
        self._lbl_status_badge.setStyleSheet(
            f"font-size:11px; font-weight:bold; padding:3px 12px;"
            f"border-radius:10px; color:{status_color};"
            f"background:{status_color}22; border:1px solid {status_color}44;"
        )

        customer_info = f"👤  {d['customer_name']}  ({d['customer_code']})"
        if d["customer_phone"]:
            customer_info += f"  |  📞  {d['customer_phone']}"
        if d["customer_city"]:
            customer_info += f"  |  📍  {d['customer_city']}"
        self._lbl_customer.setText(customer_info)

        net    = d["net_amount"]   or 0
        paid   = d["paid_amount"]  or 0
        remain = net - paid

        self._lbl_total.setText(f"{net:,.2f} ج")
        self._lbl_paid.setText(f"{paid:,.2f} ج")
        self._lbl_balance.setText(f"{remain:,.2f} ج")
        self._lbl_due_date.setText(d["due_date"] or "─")

        # تعطيل الأزرار حسب الحالة
        status = d["status"]
        can_edit   = status not in ("delivered", "cancelled")
        can_cancel = status not in ("delivered", "cancelled")
        can_delete = status in ("pending", "cancelled")
        can_change = bool(STATUS_TRANSITIONS.get(status))

        self.btn_edit.setEnabled(can_edit)
        self.btn_cancel.setEnabled(can_cancel)
        self.btn_delete.setEnabled(can_delete)
        self.btn_status.setEnabled(can_change)

    def _fill_items(self):
        items = fetch_order_items(self.conn, self._order_id)
        self.items_table.setRowCount(0)
        for item in items:
            r = self.items_table.rowCount()
            self.items_table.insertRow(r)
            self.items_table.setRowHeight(r, 38)

            name_item = QTableWidgetItem(item["item_name"])
            name_item.setData(Qt.UserRole, item["id"])
            f = QFont()
            f.setWeight(QFont.Medium)
            name_item.setFont(f)
            self.items_table.setItem(r, 0, name_item)
            self.items_table.setItem(r, 1, QTableWidgetItem(item["description"] or ""))
            self.items_table.setItem(r, 2, QTableWidgetItem(f"{item['quantity']:g}"))
            self.items_table.setItem(r, 3, QTableWidgetItem(item["unit"]))
            self.items_table.setItem(r, 4, QTableWidgetItem(f"{item['unit_price']:,.2f}"))
            self.items_table.setItem(r, 5, QTableWidgetItem(f"{item['discount_pct']:g}%"))
            self.items_table.setItem(r, 6, QTableWidgetItem(f"{item['total_price']:,.2f}"))

        for ci in range(2, 7):
            for ri in range(self.items_table.rowCount()):
                item = self.items_table.item(ri, ci)
                if item:
                    item.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

    def _fill_log(self):
        logs = fetch_status_log(self.conn, self._order_id)
        self.log_table.setRowCount(0)
        for log in logs:
            r = self.log_table.rowCount()
            self.log_table.insertRow(r)
            self.log_table.setRowHeight(r, 36)

            old_lbl = STATUS_LABELS.get(log["old_status"] or "", ("—", "#555"))[0]
            new_lbl = STATUS_LABELS.get(log["new_status"], (log["new_status"], "#555"))[0]

            self.log_table.setItem(r, 0, QTableWidgetItem(old_lbl))
            self.log_table.setItem(r, 1, QTableWidgetItem(new_lbl))
            self.log_table.setItem(r, 2, QTableWidgetItem(log["notes"] or ""))
            self.log_table.setItem(r, 3, QTableWidgetItem(
                log["changed_at"][:16] if log["changed_at"] else ""
            ))

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
            return
        item_id = self.items_table.item(row, 0).data(Qt.UserRole)
        dlg = _ItemForm(self.conn, self._order_id, item_id=item_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._fill_items()
            self._fill_header_amounts()

    def _del_item(self):
        row = self.items_table.currentRow()
        if row < 0:
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
        """تحديث المبالغ في الهيدر بعد تغيير البنود."""
        if not self._order_id:
            return
        self._order_data = fetch_order(self.conn, self._order_id)
        if self._order_data:
            net    = self._order_data["net_amount"]  or 0
            paid   = self._order_data["paid_amount"] or 0
            remain = net - paid
            self._lbl_total.setText(f"{net:,.2f} ج")
            self._lbl_paid.setText(f"{paid:,.2f} ج")
            self._lbl_balance.setText(f"{remain:,.2f} ج")


# ══════════════════════════════════════════════════════════
# Dialog تغيير الحالة
# ══════════════════════════════════════════════════════════

STATUS_LABELS_SHORT = {
    "pending":     "⏳ انتظار",
    "confirmed":   "✅ مؤكد",
    "in_progress": "🔧 تنفيذ",
    "ready":       "📦 جاهز",
    "delivered":   "🚚 مُسلَّم",
    "cancelled":   "❌ ملغي",
    "on_hold":     "⏸ معلق",
}


class _StatusDialog(QDialog):
    def __init__(self, current_status: str, next_statuses: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تغيير حالة الطلب")
        self.setMinimumWidth(380)
        self.setModal(True)
        self._result = (next_statuses[0] if next_statuses else current_status, "")
        self._build(current_status, next_statuses)

    def _build(self, current, nexts):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(12)

        lbl = QLabel(
            f"الحالة الحالية:  <b>{STATUS_LABELS_SHORT.get(current, current)}</b>"
        )
        lbl.setStyleSheet("font-size:12px; color:#374151;")
        lay.addWidget(lbl)

        lbl2 = QLabel("تغيير إلى:")
        lbl2.setStyleSheet("font-size:11px; color:#6b7280;")
        lay.addWidget(lbl2)

        self._cmb = QComboBox()
        self._cmb.setMinimumHeight(34)
        for s in nexts:
            self._cmb.addItem(STATUS_LABELS_SHORT.get(s, s), s)
        lay.addWidget(self._cmb)

        lbl3 = QLabel("ملاحظات (اختياري):")
        lbl3.setStyleSheet("font-size:11px; color:#6b7280;")
        lay.addWidget(lbl3)

        self._note = QLineEdit()
        self._note.setPlaceholderText("سبب التغيير...")
        self._note.setMinimumHeight(34)
        lay.addWidget(self._note)

        btns = QHBoxLayout()
        btn_ok = QPushButton("✅  تغيير")
        btn_ok.setMinimumHeight(36)
        btn_ok.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                border: none; border-radius: 6px;
                padding: 0 18px; font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_ok.clicked.connect(self._save)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: white; color: #374151;
                border: 1px solid #cdd3e0; border-radius: 6px;
                padding: 0 14px;
            }
            QPushButton:hover { background: #f8f9fb; }
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