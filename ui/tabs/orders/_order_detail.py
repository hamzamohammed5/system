"""
ui/tabs/orders/_order_detail.py  — نسخة محسّنة UX
================================
التحسينات:
  - هيدر منظم: رقم + badge + عميل في صف، بطاقات في صف منفصل
  - أزرار مُجمَّعة: إجراءات أساسية يسار / خطرة يمين
  - بنود الطلب: رسالة واضحة لما الجدول فاضي + زر إضافة بارز
  - سجل الحالة: compact أكثر
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QMessageBox, QDialog, QComboBox, QLineEdit,
    QTextEdit, QSizePolicy,
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
    "pending":     ("⏳ انتظار",   "#f59e0b", "#fffbeb", "#fde68a"),
    "confirmed":   ("✅ مؤكد",     "#3b82f6", "#eff6ff", "#bfdbfe"),
    "in_progress": ("🔧 تنفيذ",   "#8b5cf6", "#f5f3ff", "#ddd6fe"),
    "ready":       ("📦 جاهز",    "#10b981", "#ecfdf5", "#a7f3d0"),
    "delivered":   ("🚚 مُسلَّم",  "#6b7280", "#f9fafb", "#e5e7eb"),
    "cancelled":   ("❌ ملغي",    "#ef4444", "#fef2f2", "#fecaca"),
    "on_hold":     ("⏸ معلق",    "#f97316", "#fff7ed", "#fed7aa"),
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
    "low":    ("⬇ منخفض",  "#9ca3af"),
    "normal": ("➡ عادي",   "#6b7280"),
    "high":   ("⬆ عالي",  "#f59e0b"),
    "urgent": ("🔴 عاجل",  "#ef4444"),
}

TYPE_LABELS = {
    "new":     "🆕 جديد",
    "reorder": "🔄 إعادة طلب",
    "custom":  "⚙️ مخصص",
}

# ─── ألوان موحدة ────────────────────────────────────────
_BG       = "#f8f9fb"
_WHITE    = "#ffffff"
_BORDER   = "#e5e9f0"
_BLUE     = "#1565c0"
_BLUE_LT  = "#e8f0fe"
_RED      = "#dc2626"
_RED_LT   = "#fef2f2"
_RED_BD   = "#fecaca"
_GREEN    = "#10b981"
_GRAY     = "#6b7280"


# ══════════════════════════════════════════════════════════
# بطاقة إحصائية صغيرة
# ══════════════════════════════════════════════════════════

def _stat_card(icon: str, title: str, value: str = "─",
               color: str = _BLUE) -> tuple:
    frame = QFrame()
    frame.setStyleSheet(f"""
        QFrame {{
            background: {_WHITE};
            border: 1px solid {_BORDER};
            border-radius: 8px;
        }}
    """)
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(10, 8, 10, 8)
    lay.setSpacing(2)

    lbl_hdr = QLabel(f"{icon}  {title}")
    lbl_hdr.setStyleSheet(
        f"font-size:10px; color:#9ba5be; background:transparent; border:none;"
    )
    lbl_hdr.setAlignment(Qt.AlignCenter)

    lbl_val = QLabel(value)
    lbl_val.setStyleSheet(
        f"font-size:14px; font-weight:bold; color:{color};"
        "background:transparent; border:none;"
    )
    lbl_val.setAlignment(Qt.AlignCenter)

    lay.addWidget(lbl_hdr)
    lay.addWidget(lbl_val)
    return frame, lbl_val


# ══════════════════════════════════════════════════════════
# زر إجراء
# ══════════════════════════════════════════════════════════

def _action_btn(text: str, style: str = "normal") -> QPushButton:
    btn = QPushButton(text)
    btn.setMinimumHeight(32)
    btn.setCursor(Qt.PointingHandCursor)

    if style == "primary":
        ss = f"""
            QPushButton {{
                background: {_BLUE_LT}; color: {_BLUE};
                border: 1px solid #90caf9; border-radius: 6px;
                padding: 0 14px; font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #bbdefb; }}
            QPushButton:disabled {{ background: #f5f5f5; color: #bbb; border-color: #e0e0e0; }}
        """
    elif style == "danger":
        ss = f"""
            QPushButton {{
                background: {_RED_LT}; color: {_RED};
                border: 1px solid {_RED_BD}; border-radius: 6px;
                padding: 0 14px; font-size: 12px;
            }}
            QPushButton:hover {{ background: #fee2e2; }}
            QPushButton:disabled {{ background: #f5f5f5; color: #bbb; border-color: #e0e0e0; }}
        """
    elif style == "ghost":
        ss = f"""
            QPushButton {{
                background: {_WHITE}; color: #374151;
                border: 1px solid #cdd3e0; border-radius: 6px;
                padding: 0 14px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {_BLUE_LT}; color: {_BLUE}; border-color: #90caf9; }}
            QPushButton:disabled {{ background: #f5f5f5; color: #bbb; border-color: #e0e0e0; }}
        """
    else:  # normal
        ss = f"""
            QPushButton {{
                background: {_BG}; color: #374151;
                border: 1px solid #cdd3e0; border-radius: 6px;
                padding: 0 14px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {_BLUE_LT}; color: {_BLUE}; }}
            QPushButton:disabled {{ background: #f5f5f5; color: #bbb; border-color: #e0e0e0; }}
        """

    btn.setStyleSheet(ss)
    return btn


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

        # ── Header ────────────────────────────────────────
        self._hdr = QFrame()
        self._hdr.setStyleSheet(f"""
            QFrame {{
                background: {_WHITE};
                border-bottom: 2px solid {_BORDER};
            }}
        """)
        hdr_lay = QVBoxLayout(self._hdr)
        hdr_lay.setContentsMargins(16, 12, 16, 12)
        hdr_lay.setSpacing(8)

        # ─ صف 1: رقم الطلب + badge الحالة + النوع ─
        row_title = QHBoxLayout()
        row_title.setSpacing(8)

        self._lbl_order_num = QLabel("طلب جديد")
        f = QFont()
        f.setPointSize(13)
        f.setBold(True)
        self._lbl_order_num.setFont(f)
        self._lbl_order_num.setStyleSheet(
            f"color:#1a2035; background:transparent; border:none;"
        )

        self._lbl_type_badge = QLabel("")
        self._lbl_type_badge.setStyleSheet(
            "font-size:10px; padding:2px 8px; border-radius:8px;"
            "background:#f3f4f6; color:#6b7280; border:1px solid #e5e7eb;"
            "background:transparent; border:none;"
        )

        self._lbl_status_badge = QLabel("")
        self._lbl_status_badge.setStyleSheet(
            "font-size:11px; font-weight:bold; padding:3px 12px;"
            "border-radius:10px; background:#f0f0f0; color:#555;"
        )
        self._lbl_status_badge.setAlignment(Qt.AlignCenter)

        self._lbl_priority_badge = QLabel("")
        self._lbl_priority_badge.setStyleSheet(
            "font-size:10px; padding:2px 8px; border-radius:8px;"
            "background:transparent; border:none; color:#6b7280;"
        )

        row_title.addWidget(self._lbl_order_num)
        row_title.addWidget(self._lbl_type_badge)
        row_title.addStretch()
        row_title.addWidget(self._lbl_priority_badge)
        row_title.addWidget(self._lbl_status_badge)
        hdr_lay.addLayout(row_title)

        # ─ صف 2: بيانات العميل ─
        self._lbl_customer = QLabel("")
        self._lbl_customer.setStyleSheet(
            "color:#5a6680; font-size:11px; background:transparent; border:none;"
        )
        hdr_lay.addWidget(self._lbl_customer)

        # ─ صف 3: بطاقات الأرقام ─
        cards_row = QHBoxLayout()
        cards_row.setSpacing(6)
        f1, self._lbl_total    = _stat_card("💰", "الإجمالي",  color=_BLUE)
        f2, self._lbl_paid     = _stat_card("✅", "المدفوع",  color=_GREEN)
        f3, self._lbl_balance  = _stat_card("⚖️", "المتبقي",  color="#ef4444")
        f4, self._lbl_due_date = _stat_card("📅", "التسليم",  color="#f59e0b")
        for f in (f1, f2, f3, f4):
            cards_row.addWidget(f, stretch=1)
        hdr_lay.addLayout(cards_row)

        # ─ صف 4: الأزرار ─
        # مُقسَّمة: إجراءات أساسية (يمين) | خطرة (يسار)
        btns_row = QHBoxLayout()
        btns_row.setSpacing(6)

        # ── إجراءات خطرة (أقصى يمين الـ layout اللي RTL) ──
        self.btn_delete = _action_btn("🗑️  حذف", "danger")
        self.btn_cancel = _action_btn("❌  إلغاء", "danger")

        # ── فاصل ──
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color:#e5e9f0;")

        # ── إجراءات أساسية ──
        self.btn_edit    = _action_btn("✏️  تعديل", "primary")
        self.btn_status  = _action_btn("🔄  تغيير الحالة", "ghost")
        self.btn_reorder = _action_btn("📋  إعادة طلب", "ghost")

        btns_row.addWidget(self.btn_edit)
        btns_row.addWidget(self.btn_status)
        btns_row.addWidget(self.btn_reorder)
        btns_row.addStretch()
        btns_row.addWidget(sep)
        btns_row.addWidget(self.btn_cancel)
        btns_row.addWidget(self.btn_delete)
        hdr_lay.addLayout(btns_row)

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
        self._content_lay.setSpacing(12)

        # ── قسم البنود ──────────────────────────────────────
        self._build_items_section()

        # ── قسم سجل الحالة ─────────────────────────────────
        self._build_log_section()

        self._content_lay.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

        # ── حالة فارغة ─────────────────────────────────────
        self._empty = QFrame()
        self._empty.setStyleSheet(f"background:{_BG}; border:none;")
        e_lay = QVBoxLayout(self._empty)
        e_lay.setAlignment(Qt.AlignCenter)
        e_lay.setSpacing(10)

        lbl_icon = QLabel("📋")
        lbl_icon.setAlignment(Qt.AlignCenter)
        lbl_icon.setStyleSheet(f"font-size:48px; background:transparent; border:none;")

        lbl_msg = QLabel("اختر طلباً من القائمة\nأو أنشئ طلباً جديداً")
        lbl_msg.setAlignment(Qt.AlignCenter)
        lbl_msg.setStyleSheet(
            f"font-size:13px; color:{_GRAY}; background:transparent; border:none;"
        )

        e_lay.addWidget(lbl_icon)
        e_lay.addWidget(lbl_msg)
        root.addWidget(self._empty)

    def _build_items_section(self):
        # ─ header البنود ─
        items_hdr_row = QHBoxLayout()

        lbl_items = QLabel("📦  بنود الطلب")
        lbl_items.setStyleSheet(
            f"font-size:12px; font-weight:bold; color:#374151; background:transparent;"
        )

        self.btn_add_item = QPushButton("＋  إضافة بند")
        self.btn_add_item.setMinimumHeight(30)
        self.btn_add_item.setCursor(Qt.PointingHandCursor)
        self.btn_add_item.setStyleSheet("""
            QPushButton {
                background: #ecfdf5; color: #065f46;
                border: 1px solid #a7f3d0; border-radius: 5px;
                padding: 0 12px; font-size: 11px; font-weight: bold;
            }
            QPushButton:hover { background: #d1fae5; }
        """)
        self.btn_add_item.clicked.connect(self._add_item)

        items_hdr_row.addWidget(lbl_items)
        items_hdr_row.addStretch()
        items_hdr_row.addWidget(self.btn_add_item)
        self._content_lay.addLayout(items_hdr_row)

        # ─ جدول البنود ─
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(7)
        self.items_table.setHorizontalHeaderLabels([
            "البند", "الوصف", "الكمية", "الوحدة", "السعر", "الخصم%", "الإجمالي"
        ])
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setMinimumHeight(120)
        self.items_table.setMaximumHeight(240)
        self.items_table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {_BORDER};
                border-radius: 8px;
                background: {_WHITE};
                font-size: 11px;
                outline: none;
            }}
            QTableWidget::item {{ padding: 6px 8px; }}
            QTableWidget::item:selected {{ background: #dbeafe; color: #1e40af; }}
            QHeaderView::section {{
                background: {_BG}; color: {_GRAY};
                font-size: 10px; font-weight: bold;
                padding: 5px 8px; border: none;
                border-bottom: 1px solid {_BORDER};
                border-right: 1px solid {_BORDER};
            }}
        """)
        hh = self.items_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 7):
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        hh.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._content_lay.addWidget(self.items_table)

        # ─ رسالة الجدول الفاضي ─
        self._empty_items = QFrame()
        self._empty_items.setStyleSheet(f"""
            QFrame {{
                background: #f0fdf4;
                border: 2px dashed #a7f3d0;
                border-radius: 8px;
            }}
        """)
        self._empty_items.setMinimumHeight(80)
        ei_lay = QVBoxLayout(self._empty_items)
        ei_lay.setAlignment(Qt.AlignCenter)
        lbl_ei = QLabel("لا توجد بنود — اضغط «＋ إضافة بند» لإضافة منتج")
        lbl_ei.setAlignment(Qt.AlignCenter)
        lbl_ei.setStyleSheet(
            "font-size:11px; color:#059669; background:transparent; border:none;"
        )
        ei_lay.addWidget(lbl_ei)
        self._content_lay.addWidget(self._empty_items)

        # ─ أزرار تعديل/حذف البند ─
        item_btns = QHBoxLayout()
        item_btns.setSpacing(6)
        self.btn_edit_item = _action_btn("✏️  تعديل بند", "ghost")
        self.btn_del_item  = _action_btn("🗑️  حذف بند", "danger")
        self.btn_edit_item.setMinimumHeight(28)
        self.btn_del_item.setMinimumHeight(28)
        self.btn_edit_item.clicked.connect(self._edit_item)
        self.btn_del_item.clicked.connect(self._del_item)
        item_btns.addWidget(self.btn_edit_item)
        item_btns.addWidget(self.btn_del_item)
        item_btns.addStretch()
        self._content_lay.addLayout(item_btns)

    def _build_log_section(self):
        # فاصل
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{_BORDER};")
        self._content_lay.addWidget(sep)

        log_hdr = QLabel("📜  سجل تغييرات الحالة")
        log_hdr.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#374151; background:transparent;"
        )
        self._content_lay.addWidget(log_hdr)

        self.log_table = QTableWidget()
        self.log_table.setColumnCount(4)
        self.log_table.setHorizontalHeaderLabels(["من", "إلى", "الملاحظات", "الوقت"])
        self.log_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.log_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setMaximumHeight(160)
        self.log_table.setStyleSheet(self.items_table.styleSheet())
        hh2 = self.log_table.horizontalHeader()
        hh2.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        hh2.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh2.setSectionResizeMode(2, QHeaderView.Stretch)
        hh2.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        hh2.setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._content_lay.addWidget(self.log_table)

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(
            "font-size:12px; font-weight:bold; color:#374151; background:transparent;"
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

        # رقم الطلب + نوعه
        self._lbl_order_num.setText(d['order_number'])
        self._lbl_type_badge.setText(TYPE_LABELS.get(d['order_type'], ''))

        # badge الحالة
        status_info = STATUS_LABELS.get(d["status"], (d["status"], "#555", "#fff", "#eee"))
        status_lbl, status_color = status_info[0], status_info[1]
        status_bg,  status_bd   = status_info[2], status_info[3]
        self._lbl_status_badge.setText(status_lbl)
        self._lbl_status_badge.setStyleSheet(
            f"font-size:11px; font-weight:bold; padding:3px 12px;"
            f"border-radius:10px; color:{status_color};"
            f"background:{status_bg}; border:1px solid {status_bd};"
        )

        # badge الأولوية
        pri_lbl, pri_color = PRIORITY_LABELS.get(d["priority"], ("", _GRAY))
        self._lbl_priority_badge.setText(pri_lbl)
        self._lbl_priority_badge.setStyleSheet(
            f"font-size:10px; color:{pri_color}; background:transparent; border:none;"
        )

        # معلومات العميل
        parts = [f"👤  {d['customer_name']}  ({d['customer_code']})"]
        if d["customer_phone"]: parts.append(f"📞 {d['customer_phone']}")
        if d["customer_city"]:  parts.append(f"📍 {d['customer_city']}")
        self._lbl_customer.setText("   |   ".join(parts))

        # المبالغ
        net    = d["net_amount"]  or 0
        paid   = d["paid_amount"] or 0
        remain = net - paid

        self._lbl_total.setText(f"{net:,.2f} ج")
        self._lbl_paid.setText(f"{paid:,.2f} ج")

        self._lbl_balance.setText(f"{remain:,.2f} ج")
        balance_color = "#ef4444" if remain > 0 else _GREEN
        self._lbl_balance.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{balance_color};"
            "background:transparent; border:none;"
        )

        self._lbl_due_date.setText(d["due_date"] or "─")

        # تفعيل/تعطيل الأزرار
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

            total_val = item['quantity'] * item['unit_price'] * (1 - item['discount_pct'] / 100)
            total_item = QTableWidgetItem(f"{total_val:,.2f}")
            total_item.setForeground(QColor(_BLUE))
            f2 = QFont(); f2.setBold(True)
            total_item.setFont(f2)
            self.items_table.setItem(r, 6, total_item)

            for ci in range(2, 7):
                item_w = self.items_table.item(r, ci)
                if item_w:
                    item_w.setTextAlignment(Qt.AlignCenter | Qt.AlignVCenter)

    def _fill_log(self):
        logs = fetch_status_log(self.conn, self._order_id)
        self.log_table.setRowCount(0)
        for log in logs:
            r = self.log_table.rowCount()
            self.log_table.insertRow(r)
            self.log_table.setRowHeight(r, 34)

            old_lbl = STATUS_LABELS.get(log["old_status"] or "", ("—", "#555"))[0]
            new_info = STATUS_LABELS.get(log["new_status"], (log["new_status"], "#555"))
            new_lbl, new_color = new_info[0], new_info[1]

            self.log_table.setItem(r, 0, QTableWidgetItem(old_lbl))

            new_item = QTableWidgetItem(new_lbl)
            new_item.setForeground(QColor(new_color))
            self.log_table.setItem(r, 1, new_item)

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

STATUS_LABELS_SHORT = {k: v[0] for k, v in STATUS_LABELS.items()}


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
                border: 1px solid #cdd3e0; border-radius: 6px;
                padding: 0 14px;
            }}
            QPushButton:hover {{ background: {_BG}; }}
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