"""
ui/tabs/orders/_order_detail.py  — نسخة UX v3 محسّنة
================================
التحسينات:
  - DetailHeader من panels.py المحسّن — هيدر واضح ومنظم
  - make_detail_table من table_utils.py — جدول موحد
  - CollapsibleCard للسجل — قابل للطي بتصميم محسّن
  - EmptyState أنيق مع دعوة للإجراء
  - ألوان متناسقة ومتسقة عبر كل الواجهة
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

from ui.widgets.shared.panels import (
    DetailHeader, StatCard, SectionHeader,
    EmptyState, CollapsibleCard, ActionToolbar,
    _make_btn,
)
from ui.widgets.shared.table_utils import (
    make_detail_table, make_compact_table,
    make_table_item, color_item, bold_item, muted_item,
    insert_row, ROW_HEIGHT_NORMAL, ROW_HEIGHT_COMPACT,
)
from ui.app_settings import _C

# ── ثوابت الحالة ──
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

_BG     = "#f8f9fb"
_WHITE  = "#ffffff"
_BLUE   = "#1565c0"
_GREEN  = "#10b981"
_BORDER = "#e5e9f0"

# ── stylesheet الـ scroll ──────────────────────────────────
_SCROLL_SS = f"""
    QScrollArea {{ border: none; background: {_BG}; }}
    QScrollBar:vertical {{
        background: transparent; width: 5px; border-radius: 2px; margin: 2px;
    }}
    QScrollBar::handle:vertical {{
        background: {_C['border_med']}; border-radius: 2px; min-height: 24px;
    }}
    QScrollBar::handle:vertical:hover {{ background: {_C['border_strong']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
"""


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
        self.setStyleSheet(f"background:{_BG};")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header موحد ──────────────────────────────────
        self._hdr = DetailHeader(bg=_WHITE)

        # بطاقات الإحصائيات
        self._card_total   = self._hdr.add_stat_card("💰", "الإجمالي",  color=_BLUE)
        self._card_paid    = self._hdr.add_stat_card("✅", "المدفوع",   color=_GREEN)
        self._card_balance = self._hdr.add_stat_card("⚖️", "المتبقي",   color="#ef4444")
        self._card_due     = self._hdr.add_stat_card("📅", "التسليم",   color="#f59e0b")

        # أزرار الإجراءات
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

        root.addWidget(self._hdr)

        # ── محتوى قابل للتمرير ──────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(_SCROLL_SS)

        content = QWidget()
        content.setStyleSheet(f"background:{_BG};")
        self._content_lay = QVBoxLayout(content)
        self._content_lay.setContentsMargins(16, 14, 16, 16)
        self._content_lay.setSpacing(12)

        self._build_items_section()
        self._build_log_section()

        self._content_lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # ── حالة فارغة ──────────────────────────────────
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
        # ── رأس القسم ──
        items_hdr = SectionHeader("بنود الطلب")
        self.btn_add_item = items_hdr.add_button(
            "＋  إضافة بند", self._add_item, "success"
        )
        self._content_lay.addWidget(items_hdr)

        # ── جدول البنود ──
        self.items_table = make_detail_table(
            columns=["البند", "الوصف", "الكمية", "الوحدة", "السعر", "الخصم%", "الإجمالي"],
            stretch_col=0,
            col_widths={2: 65, 3: 65, 4: 90, 5: 60, 6: 95},
            max_height=280,
            min_height=60,
            row_height=ROW_HEIGHT_NORMAL,
        )
        self._content_lay.addWidget(self.items_table)

        # ── EmptyState للبنود ──
        self._empty_items = EmptyState(
            icon="📦",
            title="لا توجد بنود في هذا الطلب",
            subtitle="اضغط «＋ إضافة بند» لإضافة منتج",
            style="dashed",
            color=_GREEN,
            min_height=90,
        )
        self._empty_items.action_clicked.connect(self._add_item)
        self._content_lay.addWidget(self._empty_items)

        # ── أزرار تعديل/حذف البند ──
        item_toolbar = QWidget()
        item_toolbar.setStyleSheet("background:transparent;")
        itb_lay = QHBoxLayout(item_toolbar)
        itb_lay.setContentsMargins(0, 0, 0, 0)
        itb_lay.setSpacing(6)

        self.btn_edit_item = _make_btn("✏️  تعديل البند", "ghost")
        self.btn_edit_item.setMinimumHeight(28)
        self.btn_edit_item.clicked.connect(self._edit_item)

        self.btn_del_item = _make_btn("🗑️  حذف البند", "danger")
        self.btn_del_item.setMinimumHeight(28)
        self.btn_del_item.clicked.connect(self._del_item)

        itb_lay.addWidget(self.btn_edit_item)
        itb_lay.addWidget(self.btn_del_item)
        itb_lay.addStretch()
        self._content_lay.addWidget(item_toolbar)

    def _build_log_section(self):
        self._log_card = CollapsibleCard("سجل تغييرات الحالة", expanded=False)

        self.log_table = make_compact_table(
            columns=["من", "إلى", "الملاحظات", "الوقت"],
            stretch_col=2,
            col_widths={0: 95, 1: 95, 3: 130},
            max_height=160,
        )
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

        status_info = STATUS_LABELS.get(
            d["status"], (d["status"], "#555", "#fff", "#eee")
        )
        self._hdr.set_status_badge(
            status_info[0], status_info[1], status_info[2], status_info[3]
        )

        pri_lbl, pri_color = PRIORITY_LABELS.get(d["priority"], ("", "#6b7280"))
        self._hdr.set_priority_badge(pri_lbl, pri_color)

        parts = [f"👤  {d['customer_name']}  ({d['customer_code']})"]
        if d.get("customer_phone"):
            parts.append(f"📞 {d['customer_phone']}")
        if d.get("customer_city"):
            parts.append(f"📍 {d['customer_city']}")
        self._hdr.set_info(parts)

        net    = d.get("net_amount")  or 0
        paid   = d.get("paid_amount") or 0
        remain = net - paid

        self._card_total.set_value(f"{net:,.2f} ج")
        self._card_paid.set_value(f"{paid:,.2f} ج")
        self._card_balance.set_value(f"{remain:,.2f} ج")
        self._card_balance.set_color("#ef4444" if remain > 0 else _GREEN)
        self._card_due.set_value(d.get("due_date") or "─")

        # تفعيل/تعطيل الأزرار
        status    = d["status"]
        can_edit  = status not in ("delivered", "cancelled")
        can_cancel= status not in ("delivered", "cancelled")
        can_delete= status in ("pending", "cancelled")
        can_change= bool(STATUS_TRANSITIONS.get(status))

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

            self.items_table.setItem(r, 1,
                make_table_item(item.get("description") or ""))

            self.items_table.setItem(r, 2,
                make_table_item(f"{item['quantity']:g}", align=Qt.AlignCenter))

            unit_item = make_table_item(item["unit"], align=Qt.AlignCenter)
            muted_item(unit_item)
            self.items_table.setItem(r, 3, unit_item)

            self.items_table.setItem(r, 4,
                make_table_item(f"{item['unit_price']:,.2f}", align=Qt.AlignCenter))

            disc_item = make_table_item(
                f"{item['discount_pct']:g}%", align=Qt.AlignCenter
            )
            muted_item(disc_item)
            self.items_table.setItem(r, 5, disc_item)

            total_val = (
                item["quantity"] * item["unit_price"]
                * (1 - item["discount_pct"] / 100)
            )
            total_item = make_table_item(f"{total_val:,.2f}", align=Qt.AlignCenter)
            bold_item(total_item)
            color_item(total_item, _BLUE)
            self.items_table.setItem(r, 6, total_item)

    def _fill_log(self):
        logs = [dict(r) for r in fetch_status_log(self.conn, self._order_id)]
        self.log_table.setRowCount(0)

        for log in logs:
            r = insert_row(self.log_table, ROW_HEIGHT_COMPACT)

            old_lbl  = STATUS_LABELS.get(log.get("old_status") or "", ("—",))[0]
            new_info = STATUS_LABELS.get(
                log.get("new_status", ""),
                (log.get("new_status", ""), "#555")
            )
            new_lbl, new_color = new_info[0], new_info[1]

            self.log_table.setItem(r, 0, muted_item(make_table_item(old_lbl)))
            new_item = make_table_item(new_lbl)
            color_item(new_item, new_color)
            bold_item(new_item)
            self.log_table.setItem(r, 1, new_item)
            self.log_table.setItem(r, 2,
                make_table_item(log.get("notes") or ""))
            time_str = (log.get("changed_at") or "")[:16]
            self.log_table.setItem(r, 3,
                muted_item(make_table_item(time_str, align=Qt.AlignCenter)))

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
            QMessageBox.information(
                self, "تنبيه", "لا يمكن تعديل طلب مكتمل أو ملغي."
            )
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
# Dialog تغيير الحالة — محسّن
# ══════════════════════════════════════════════════════════

STATUS_LABELS_SHORT = {k: v[0] for k, v in STATUS_LABELS.items()}

_STATUS_COLORS = {
    k: (v[1], v[2], v[3]) for k, v in STATUS_LABELS.items()
}


class _StatusDialog(QDialog):
    def __init__(self, current_status: str, next_statuses: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("تغيير حالة الطلب")
        self.setMinimumWidth(400)
        self.setModal(True)
        self._result = (
            next_statuses[0] if next_statuses else current_status, ""
        )
        self._build(current_status, next_statuses)

    def _build(self, current, nexts):
        self.setStyleSheet(f"""
            QDialog {{ background: {_C['bg_surface']}; }}
            QLineEdit {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 12px;
                min-height: 34px;
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; }}
        """)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 18, 20, 18)
        lay.setSpacing(12)

        # ── العنوان ──
        lbl_hdr = QLabel("تغيير حالة الطلب")
        lbl_hdr.setStyleSheet(f"""
            font-size: 14px; font-weight: bold; color: {_C['accent_text']};
            background: {_C['accent_light']}; border-radius: 8px;
            padding: 8px 14px; border: none;
        """)
        lay.addWidget(lbl_hdr)

        # ── الحالة الحالية ──
        cur_info = _STATUS_COLORS.get(current, ("#555", "#f5f5f5", "#e0e0e0"))
        lbl_cur = QLabel(
            f"الحالة الحالية:  {STATUS_LABELS_SHORT.get(current, current)}"
        )
        lbl_cur.setStyleSheet(
            f"color:{cur_info[0]}; font-weight:600; font-size:12px;"
            f"background:{cur_info[1]}; border:1px solid {cur_info[2]};"
            "border-radius:6px; padding:6px 10px;"
        )
        lay.addWidget(lbl_cur)

        # ── اختيار الحالة الجديدة ──
        lbl_new = QLabel("الحالة الجديدة:")
        lbl_new.setStyleSheet(f"color:{_C['text_sec']}; font-size:11px;")
        lay.addWidget(lbl_new)

        self._cmb = QComboBox()
        self._cmb.setMinimumHeight(36)
        self._cmb.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_input']}; color: {_C['text_primary']};
                border: 1.5px solid {_C['border_med']}; border-radius: 6px;
                padding: 4px 10px; font-size: 12px;
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
            QComboBox::drop-down {{ border: none; width: 20px; }}
        """)
        for s in nexts:
            self._cmb.addItem(STATUS_LABELS_SHORT.get(s, s), s)
        lay.addWidget(self._cmb)

        # ── الملاحظات ──
        lbl_note = QLabel("ملاحظات (اختياري):")
        lbl_note.setStyleSheet(f"color:{_C['text_sec']}; font-size:11px;")
        lay.addWidget(lbl_note)

        self._note = QLineEdit()
        self._note.setPlaceholderText("سبب التغيير...")
        lay.addWidget(self._note)

        # ── الأزرار ──
        btns = QHBoxLayout()
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']}; color: {_C['text_sec']};
                border: 1px solid {_C['border_med']}; border-radius: 6px;
                padding: 0 16px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_ok = QPushButton("✅  تغيير الحالة")
        btn_ok.setMinimumHeight(38)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border: 1.5px solid {_C['accent_mid']}; border-radius: 6px;
                padding: 0 20px; font-weight: bold; font-size: 12px;
            }}
            QPushButton:hover {{ background: {_C['accent_mid']}; }}
        """)
        btn_ok.clicked.connect(self._save)

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