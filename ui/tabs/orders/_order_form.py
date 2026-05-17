"""
ui/tabs/orders/_order_form.py
==============================
Dialog لإنشاء طلب جديد أو تعديل طلب موجود.
يدعم:
  - اختيار عميل موجود أو إنشاء عميل جديد
  - تحديد نوع الطلب / الأولوية / تاريخ التسليم
  - إضافة وتعديل وحذف بنود الطلب مباشرة من الفورم
  - اختيار المنتج من قائمة المنتجات المسعّرة (مجمّعة بالتصنيف)
  - اختيار عروض جاهزة وإضافة بنودها دفعة واحدة
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QDateEdit,
    QMessageBox, QGroupBox,
    QDoubleSpinBox, QFrame, QScrollArea,
    QWidget, QSizePolicy, QAbstractItemView,
    QTableWidget, QTableWidgetItem, QHeaderView,
)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui  import QFont, QColor

from db.orders.customers_repo import fetch_all_customers, search_customers
from db.orders.orders_repo import (
    fetch_order, insert_order, update_order,
    fetch_order_items, insert_order_item,
    update_order_item, delete_order_item,
)

STATUS_OPTIONS = [
    ("pending",     "⏳ انتظار"),
    ("confirmed",   "✅ مؤكد"),
    ("in_progress", "🔧 تنفيذ"),
    ("ready",       "📦 جاهز"),
]

PRIORITY_OPTIONS = [
    ("low",    "⬇ منخفض"),
    ("normal", "➡ عادي"),
    ("high",   "⬆ عالي"),
    ("urgent", "🔴 عاجل"),
]

TYPE_OPTIONS = [
    ("new",     "🆕 جديد"),
    ("reorder", "🔄 إعادة طلب"),
    ("custom",  "⚙️ مخصص"),
]

# ── ألوان ──
_BLUE   = "#1565c0"
_ORANGE = "#e65100"
_GREEN  = "#2e7d32"
_GRAY   = "#6b7280"
_BG     = "#f8f9fb"
_BORDER = "#cdd3e0"
_WHITE  = "#ffffff"


def _input_ss():
    return f"""
        QLineEdit, QTextEdit, QComboBox, QDoubleSpinBox, QDateEdit {{
            background: {_BG};
            border: 1px solid {_BORDER};
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 12px;
            color: #1a2035;
            min-height: 32px;
        }}
        QLineEdit:focus, QTextEdit:focus,
        QComboBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {{
            border-color: {_BLUE};
            background: {_WHITE};
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
    """


def _group_ss(accent: str = _BLUE):
    return f"""
        QGroupBox {{
            font-weight: bold;
            color: #374151;
            border: 1px solid #e5e9f0;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 10px;
            background: {_WHITE};
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            right: 12px; padding: 0 6px;
            font-size: 11px;
            color: {accent};
        }}
    """


def _btn(text, bg=_BLUE, color=_WHITE, border=None):
    b = border or bg
    return f"""
        QPushButton {{
            background: {bg}; color: {color};
            border: 1px solid {b}; border-radius: 6px;
            padding: 0 14px; font-size: 12px; min-height: 32px;
        }}
        QPushButton:hover {{ opacity: 0.85; }}
    """


# ══════════════════════════════════════════════════════════════════════════════
# جلب المنتجات المسعّرة من erp.db مصنفةً ومرتبة
# ══════════════════════════════════════════════════════════════════════════════

def _fetch_priced_products():
    """
    يجلب المنتجات المسعّرة من erp.db مع تصنيفاتها وأسعارها.
    يرجع list of dict:
      {id, name, category_id, category_name, category_color, price, type}
    مرتبة بـ (category_name, name).
    """
    try:
        from db.shared.connection import get_costing_connection
        conn = get_costing_connection()
        rows = conn.execute("""
            SELECT
                i.id,
                i.name,
                i.type,
                i.category_id,
                c.name  AS category_name,
                c.color AS category_color,
                p.price
            FROM   items i
            JOIN   pricing p ON p.item_id = i.id
            LEFT JOIN categories c ON c.id = i.category_id
            WHERE  i.type IN ('final', 'semi')
            ORDER  BY
                COALESCE(c.name, 'ω') ASC,
                i.name ASC
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _fetch_offers():
    """يجلب العروض المتاحة من erp.db."""
    try:
        from db.shared.connection import get_costing_connection
        conn = get_costing_connection()
        rows = conn.execute("""
            SELECT o.id, o.name, o.discount,
                   c.name AS category_name
            FROM   offers o
            LEFT JOIN categories c ON c.id = o.category_id
            ORDER  BY o.name
        """).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _fetch_offer_lines(offer_id: int):
    """يجلب بنود عرض معين مع أسعاره."""
    try:
        from db.shared.connection import get_costing_connection
        conn = get_costing_connection()
        rows = conn.execute("""
            SELECT oi.item_id, oi.qty,
                   i.name AS item_name,
                   p.price
            FROM   offer_items oi
            JOIN   items i  ON i.id = oi.item_id
            LEFT JOIN pricing p ON p.item_id = oi.item_id
            WHERE  oi.offer_id = ?
        """, (offer_id,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


# ══════════════════════════════════════════════════════════════════════════════
# صف بند واحد داخل الفورم
# ══════════════════════════════════════════════════════════════════════════════

class _ItemRowWidget(QFrame):
    """
    صف بند طلب واحد — يعرض:
      [التصنيف/المنتج combo] [سعر] [كمية] [خصم%] [إجمالي] [ملاحظات] [حذف]
    """
    changed = pyqtSignal()
    removed = pyqtSignal(object)   # يمرر self

    # كاش المنتجات المسعّرة (يُحمَّل مرة واحدة)
    _products_cache: list = None

    @classmethod
    def _get_products(cls) -> list:
        if cls._products_cache is None:
            cls._products_cache = _fetch_priced_products()
        return cls._products_cache

    @classmethod
    def invalidate_cache(cls):
        cls._products_cache = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self._db_item_id = None   # id من order_items لو كان موجوداً
        self._build()

    # ── بناء الواجهة ──────────────────────────────────────────────────────────

    def _build(self):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_WHITE};
                border: 1px solid #e5e9f0;
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: #93c5fd;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        # ── صف 1: اختيار المنتج + بحث ──
        row1 = QHBoxLayout()
        row1.setSpacing(6)

        # بحث
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(100)
        self.inp_search.setMinimumHeight(30)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: #f0f4ff; border: 1px solid #c5cae9;
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: {_WHITE}; }}
        """)
        self.inp_search.textChanged.connect(self._on_search)

        # btn مسح البحث
        self.btn_clr = QPushButton("✖")
        self.btn_clr.setFixedSize(22, 22)
        self.btn_clr.setStyleSheet(
            "QPushButton{background:transparent;border:none;color:#aaa;font-size:10px;}"
            "QPushButton:hover{color:#e53935;}"
        )
        self.btn_clr.clicked.connect(lambda: self.inp_search.clear())
        self.btn_clr.setVisible(False)
        self.inp_search.textChanged.connect(
            lambda t: self.btn_clr.setVisible(bool(t))
        )

        # combo المنتج
        self.cmb_product = QComboBox()
        self.cmb_product.setMinimumHeight(30)
        self.cmb_product.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb_product.setStyleSheet(f"""
            QComboBox {{
                background: {_BG}; border: 1px solid {_BORDER};
                border-radius: 5px; padding: 2px 8px; font-size: 12px;
            }}
            QComboBox:focus {{ border-color: {_BLUE}; }}
            QComboBox::drop-down {{ border: none; width: 18px; }}
        """)
        self._populate_combo()
        self.cmb_product.currentIndexChanged.connect(self._on_product_changed)

        # السعر
        lbl_price = QLabel("سعر:")
        lbl_price.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.sp_price = QDoubleSpinBox()
        self.sp_price.setRange(0, 9_999_999)
        self.sp_price.setDecimals(2)
        self.sp_price.setMinimumHeight(30)
        self.sp_price.setFixedWidth(100)
        self.sp_price.setSuffix(" ج")
        self.sp_price.valueChanged.connect(self._recalc)

        row1.addWidget(self.inp_search)
        row1.addWidget(self.btn_clr)
        row1.addWidget(self.cmb_product, stretch=1)
        row1.addWidget(lbl_price)
        row1.addWidget(self.sp_price)
        root.addLayout(row1)

        # ── صف 2: كمية / خصم / وحدة / إجمالي / حذف ──
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        lbl_name = QLabel("اسم مخصص:")
        lbl_name.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اختياري — يُستخدم اسم المنتج افتراضياً")
        self.inp_name.setMinimumHeight(30)
        self.inp_name.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG}; border: 1px solid {_BORDER};
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; }}
        """)

        lbl_qty = QLabel("الكمية:")
        lbl_qty.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.sp_qty = QDoubleSpinBox()
        self.sp_qty.setRange(0.001, 99_999)
        self.sp_qty.setDecimals(3)
        self.sp_qty.setValue(1)
        self.sp_qty.setMinimumHeight(30)
        self.sp_qty.setFixedWidth(80)
        self.sp_qty.valueChanged.connect(self._recalc)

        lbl_unit = QLabel("وحدة:")
        lbl_unit.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.inp_unit = QLineEdit("قطعة")
        self.inp_unit.setFixedWidth(60)
        self.inp_unit.setMinimumHeight(30)
        self.inp_unit.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG}; border: 1px solid {_BORDER};
                border-radius: 5px; padding: 2px 6px; font-size: 11px;
            }}
        """)

        lbl_disc = QLabel("خصم:")
        lbl_disc.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.sp_disc = QDoubleSpinBox()
        self.sp_disc.setRange(0, 100)
        self.sp_disc.setDecimals(2)
        self.sp_disc.setMinimumHeight(30)
        self.sp_disc.setFixedWidth(70)
        self.sp_disc.setSuffix(" %")
        self.sp_disc.valueChanged.connect(self._recalc)

        # الإجمالي
        self.lbl_total = QLabel("0.00 ج")
        self.lbl_total.setStyleSheet(
            f"font-size:13px; font-weight:bold; color:{_BLUE};"
            f"background:#eff6ff; border:1px solid #bfdbfe;"
            "border-radius:5px; padding:3px 10px;"
        )
        self.lbl_total.setMinimumWidth(90)
        self.lbl_total.setAlignment(Qt.AlignCenter)

        # ملاحظات
        lbl_note = QLabel("ملاحظات:")
        lbl_note.setStyleSheet(f"color:{_GRAY}; font-size:11px;")
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("...")
        self.inp_notes.setMinimumHeight(30)
        self.inp_notes.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG}; border: 1px solid {_BORDER};
                border-radius: 5px; padding: 2px 8px; font-size: 11px;
            }}
        """)

        # حذف
        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(30, 30)
        btn_del.setToolTip("حذف هذا البند")
        btn_del.setStyleSheet("""
            QPushButton{background:#fef2f2;border:1px solid #fecaca;
            border-radius:5px;font-size:13px;}
            QPushButton:hover{background:#fee2e2;}
        """)
        btn_del.clicked.connect(lambda: self.removed.emit(self))

        row2.addWidget(lbl_name)
        row2.addWidget(self.inp_name, stretch=1)
        row2.addWidget(lbl_qty)
        row2.addWidget(self.sp_qty)
        row2.addWidget(lbl_unit)
        row2.addWidget(self.inp_unit)
        row2.addWidget(lbl_disc)
        row2.addWidget(self.sp_disc)
        row2.addWidget(self.lbl_total)
        row2.addWidget(lbl_note)
        row2.addWidget(self.inp_notes, stretch=1)
        row2.addWidget(btn_del)
        root.addLayout(row2)

    # ── ملء combo المنتجات ───────────────────────────────────────────────────

    def _populate_combo(self, filter_text: str = ""):
        prev = self.cmb_product.currentData()
        self.cmb_product.blockSignals(True)
        self.cmb_product.clear()
        self.cmb_product.addItem("— اختر منتجاً —", None)

        products = self._get_products()
        q = filter_text.strip().lower()

        current_cat = None
        for p in products:
            name = p["name"]
            if q and q not in name.lower():
                continue

            cat = p.get("category_name") or "بدون تصنيف"
            icon = "🏭" if p["type"] == "final" else "🔧"

            # رأس التصنيف
            if cat != current_cat:
                current_cat = cat
                sep_idx = self.cmb_product.count()
                self.cmb_product.addItem(f"── {cat} ──", f"__cat__{cat}")
                # تعطيل السيباريتور
                model = self.cmb_product.model()
                item  = model.item(sep_idx)
                if item:
                    item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)
                    from PyQt5.QtGui import QFont as QF, QBrush
                    f = QF(); f.setBold(True); f.setPointSize(f.pointSize() - 1)
                    item.setFont(f)
                    item.setForeground(QBrush(QColor("#78909c")))

            self.cmb_product.addItem(f"  {icon} {name}", p["id"])

        self.cmb_product.blockSignals(False)

        # استعادة الاختيار
        if prev and not isinstance(prev, str):
            for i in range(self.cmb_product.count()):
                if self.cmb_product.itemData(i) == prev:
                    self.cmb_product.setCurrentIndex(i)
                    return
        self.cmb_product.setCurrentIndex(0)
        self._on_product_changed()

    def _on_search(self, text: str):
        self._populate_combo(filter_text=text)

    # ── منطق ──────────────────────────────────────────────────────────────────

    def _on_product_changed(self):
        pid = self.cmb_product.currentData()
        if not pid or isinstance(pid, str):
            self.sp_price.setValue(0)
            self.lbl_total.setText("0.00 ج")
            self.changed.emit()
            return
        # جلب السعر من الكاش
        for p in self._get_products():
            if p["id"] == pid:
                self.sp_price.blockSignals(True)
                self.sp_price.setValue(p.get("price") or 0)
                self.sp_price.blockSignals(False)
                break
        self._recalc()

    def _recalc(self):
        qty   = self.sp_qty.value()
        price = self.sp_price.value()
        disc  = self.sp_disc.value()
        total = qty * price * (1 - disc / 100)
        self.lbl_total.setText(f"{total:,.2f} ج")
        self.changed.emit()

    # ── API ───────────────────────────────────────────────────────────────────

    def get_product_id(self):
        pid = self.cmb_product.currentData()
        if not pid or isinstance(pid, str):
            return None
        return pid

    def get_product_name(self) -> str:
        custom = self.inp_name.text().strip()
        if custom:
            return custom
        pid = self.get_product_id()
        if pid:
            for p in self._get_products():
                if p["id"] == pid:
                    return p["name"]
        return ""

    def get_data(self) -> dict | None:
        name = self.get_product_name()
        if not name:
            return None
        return {
            "item_name":    name,
            "description":  "",
            "quantity":     self.sp_qty.value(),
            "unit":         self.inp_unit.text().strip() or "قطعة",
            "unit_price":   self.sp_price.value(),
            "discount_pct": self.sp_disc.value(),
            "design_ref":   "",
            "notes":        self.inp_notes.text().strip(),
        }

    def get_total(self) -> float:
        qty   = self.sp_qty.value()
        price = self.sp_price.value()
        disc  = self.sp_disc.value()
        return qty * price * (1 - disc / 100)

    def load_from_order_item(self, item: dict):
        """تحميل بيانات بند موجود للتعديل."""
        self._db_item_id = item["id"]
        # البحث عن المنتج في الـ combo (لو كان مرتبطاً)
        name = item["item_name"]
        # نحاول نوجد المنتج بالاسم في الكاش
        found = False
        for p in self._get_products():
            if p["name"] == name:
                for i in range(self.cmb_product.count()):
                    if self.cmb_product.itemData(i) == p["id"]:
                        self.cmb_product.setCurrentIndex(i)
                        found = True
                        break
                if found:
                    break
        if not found:
            # منتج يدوي — نكتب الاسم في الحقل المخصص
            self.inp_name.setText(name)

        self.sp_price.setValue(item["unit_price"])
        self.sp_qty.setValue(item["quantity"])
        self.inp_unit.setText(item["unit"] or "قطعة")
        self.sp_disc.setValue(item["discount_pct"])
        self.inp_notes.setText(item["notes"] or "")
        self._recalc()

    @property
    def db_item_id(self):
        return self._db_item_id


# ══════════════════════════════════════════════════════════════════════════════
# _OrderForm — الفورم الرئيسي
# ══════════════════════════════════════════════════════════════════════════════

class _OrderForm(QDialog):
    saved = pyqtSignal(int)   # order_id

    def __init__(self, conn, order_id: int = None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self.order_id   = order_id
        self._customer_id = None
        self._item_rows: list[_ItemRowWidget] = []

        # إعادة تحميل كاش المنتجات في كل مرة
        _ItemRowWidget.invalidate_cache()

        title = "تعديل الطلب" if order_id else "طلب جديد"
        self.setWindowTitle(title)
        self.setMinimumWidth(880)
        self.setMinimumHeight(760)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {_BG}; }}")

        self._build()
        if order_id:
            self._load()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        # ── scroll wrapper ──
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #f0f0f0; width: 6px; border-radius: 3px;
            }
            QScrollBar::handle:vertical {
                background: #cdd3e0; border-radius: 3px; min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)

        content = QWidget()
        content.setStyleSheet(f"background: {_BG};")
        root = QVBoxLayout(content)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)
        scroll.setWidget(content)
        outer.addWidget(scroll)

        self.setStyleSheet(self.styleSheet() + _input_ss())

        # ── رأس ──
        hdr = QLabel("✏️  تعديل الطلب" if self.order_id else "📋  طلب جديد")
        hdr.setStyleSheet(f"""
            font-size: 15px; font-weight: bold; color: {_BLUE};
            background: #e8f0fe; border-radius: 8px; padding: 10px 16px;
        """)
        root.addWidget(hdr)

        # ════════════════════════════════════════════════
        # قسم 1: العميل
        # ════════════════════════════════════════════════
        cust_grp = QGroupBox("👤  بيانات العميل")
        cust_grp.setStyleSheet(_group_ss(_BLUE))
        c_lay = QVBoxLayout(cust_grp)
        c_lay.setSpacing(8)

        search_row = QHBoxLayout()
        self.inp_cust_search = QLineEdit()
        self.inp_cust_search.setPlaceholderText("ابحث عن عميل بالاسم أو الهاتف أو الكود...")
        self.inp_cust_search.textChanged.connect(self._search_customers)

        btn_new_cust = QPushButton("+ عميل جديد")
        btn_new_cust.setMinimumHeight(34)
        btn_new_cust.setStyleSheet(_btn("+ عميل جديد", "#ecfdf5", "#065f46", "#a7f3d0"))
        btn_new_cust.clicked.connect(self._new_customer)

        search_row.addWidget(self.inp_cust_search, stretch=1)
        search_row.addWidget(btn_new_cust)
        c_lay.addLayout(search_row)

        self.cmb_customer = QComboBox()
        self.cmb_customer.setPlaceholderText("─ اختر عميل ─")
        self._all_customers = fetch_all_customers(self.conn, active_only=True)
        for c in self._all_customers:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or 'بدون هاتف'})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.currentIndexChanged.connect(self._on_customer_changed)
        c_lay.addWidget(self.cmb_customer)

        self._lbl_cust_info = QLabel("")
        self._lbl_cust_info.setStyleSheet(
            f"font-size:11px; color:#6b7280; background:{_BG};"
            "border:1px solid #e5e9f0; border-radius:6px; padding:6px 10px;"
        )
        self._lbl_cust_info.setVisible(False)
        c_lay.addWidget(self._lbl_cust_info)
        root.addWidget(cust_grp)

        # ════════════════════════════════════════════════
        # قسم 2: تفاصيل الطلب
        # ════════════════════════════════════════════════
        order_grp = QGroupBox("📋  تفاصيل الطلب")
        order_grp.setStyleSheet(_group_ss(_BLUE))
        form = QFormLayout(order_grp)
        form.setSpacing(10)
        form.setLabelAlignment(Qt.AlignRight)

        self.cmb_type = QComboBox()
        for k, v in TYPE_OPTIONS:
            self.cmb_type.addItem(v, k)
        form.addRow("نوع الطلب :", self.cmb_type)

        self.cmb_status = QComboBox()
        for k, v in STATUS_OPTIONS:
            self.cmb_status.addItem(v, k)
        if not self.order_id:
            self.cmb_status.setVisible(False)
        form.addRow("الحالة :", self.cmb_status)

        self.cmb_priority = QComboBox()
        for k, v in PRIORITY_OPTIONS:
            self.cmb_priority.addItem(v, k)
        self.cmb_priority.setCurrentIndex(1)
        form.addRow("الأولوية :", self.cmb_priority)

        self.inp_due_date = QDateEdit()
        self.inp_due_date.setCalendarPopup(True)
        self.inp_due_date.setDate(QDate.currentDate().addDays(7))
        self.inp_due_date.setDisplayFormat("yyyy-MM-dd")
        form.addRow("تاريخ التسليم :", self.inp_due_date)

        self.sp_discount = QDoubleSpinBox()
        self.sp_discount.setRange(0, 99_999)
        self.sp_discount.setDecimals(2)
        self.sp_discount.setSuffix(" ج")
        form.addRow("الخصم الكلي :", self.sp_discount)

        self.sp_paid = QDoubleSpinBox()
        self.sp_paid.setRange(0, 9_999_999)
        self.sp_paid.setDecimals(2)
        self.sp_paid.setSuffix(" ج")
        form.addRow("المدفوع :", self.sp_paid)

        root.addWidget(order_grp)

        # ════════════════════════════════════════════════
        # قسم 3: بنود الطلب
        # ════════════════════════════════════════════════
        items_grp = QGroupBox("📦  بنود الطلب")
        items_grp.setStyleSheet(_group_ss(_ORANGE))
        items_lay = QVBoxLayout(items_grp)
        items_lay.setSpacing(8)

        # ── شريط الأدوات: إضافة بند / استيراد عرض ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        btn_add_item = QPushButton("➕  إضافة بند")
        btn_add_item.setMinimumHeight(34)
        btn_add_item.setStyleSheet(_btn("", "#ecfdf5", "#065f46", "#a7f3d0"))
        btn_add_item.clicked.connect(self._add_item_row)

        lbl_offer = QLabel("أو استورد عرضاً:")
        lbl_offer.setStyleSheet(f"color:{_GRAY}; font-size:11px;")

        self.cmb_offers = QComboBox()
        self.cmb_offers.setMinimumHeight(34)
        self.cmb_offers.setMinimumWidth(200)
        self._load_offers_combo()

        btn_import_offer = QPushButton("📥  استيراد")
        btn_import_offer.setMinimumHeight(34)
        btn_import_offer.setStyleSheet(_btn("", "#e8f0fe", _BLUE, "#90caf9"))
        btn_import_offer.clicked.connect(self._import_offer)

        toolbar.addWidget(btn_add_item)
        toolbar.addStretch()
        toolbar.addWidget(lbl_offer)
        toolbar.addWidget(self.cmb_offers, stretch=1)
        toolbar.addWidget(btn_import_offer)
        items_lay.addLayout(toolbar)

        # ── حاوية صفوف البنود ──
        self._rows_container = QWidget()
        self._rows_container.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._rows_container)
        self._rows_layout.setSpacing(6)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)

        items_lay.addWidget(self._rows_container)

        # ── شريط الإجمالي ──
        total_bar = QFrame()
        total_bar.setStyleSheet(f"""
            QFrame {{
                background: #e8f0fe;
                border: 1px solid #90caf9;
                border-radius: 6px;
            }}
        """)
        total_row = QHBoxLayout(total_bar)
        total_row.setContentsMargins(14, 8, 14, 8)

        lbl_items_count = QLabel("البنود:")
        lbl_items_count.setStyleSheet(f"color:{_GRAY}; font-size:11px; background:transparent;")
        self.lbl_items_count = QLabel("0")
        self.lbl_items_count.setStyleSheet(f"font-weight:bold; color:{_BLUE}; background:transparent;")

        lbl_subtotal_txt = QLabel("الإجمالي قبل الخصم:")
        lbl_subtotal_txt.setStyleSheet(f"color:{_GRAY}; font-size:11px; background:transparent;")
        self.lbl_subtotal = QLabel("0.00 ج")
        self.lbl_subtotal.setStyleSheet(f"font-weight:bold; color:{_BLUE}; font-size:13px; background:transparent;")

        total_row.addWidget(lbl_items_count)
        total_row.addWidget(self.lbl_items_count)
        total_row.addStretch()
        total_row.addWidget(lbl_subtotal_txt)
        total_row.addWidget(self.lbl_subtotal)
        items_lay.addWidget(total_bar)

        root.addWidget(items_grp)

        # ════════════════════════════════════════════════
        # قسم 4: الملاحظات
        # ════════════════════════════════════════════════
        notes_grp = QGroupBox("📝  الملاحظات")
        notes_grp.setStyleSheet(_group_ss(_GRAY))
        n_lay = QVBoxLayout(notes_grp)
        n_lay.setSpacing(8)

        self.inp_notes = QTextEdit()
        self.inp_notes.setPlaceholderText("ملاحظات للعميل...")
        self.inp_notes.setMaximumHeight(65)
        n_lay.addWidget(QLabel("ملاحظات للعميل:"))
        n_lay.addWidget(self.inp_notes)

        self.inp_internal = QTextEdit()
        self.inp_internal.setPlaceholderText("ملاحظات داخلية (لا تظهر للعميل)...")
        self.inp_internal.setMaximumHeight(65)
        n_lay.addWidget(QLabel("ملاحظات داخلية:"))
        n_lay.addWidget(self.inp_internal)
        root.addWidget(notes_grp)

        # ════════════════════════════════════════════════
        # أزرار الحفظ
        # ════════════════════════════════════════════════
        btns = QHBoxLayout()

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(40)
        btn_cancel.setStyleSheet(_btn("", _WHITE, "#374151", _BORDER))
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾  حفظ الطلب")
        btn_save.setMinimumHeight(40)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: {_WHITE};
                border: none; border-radius: 8px;
                padding: 0 24px; font-weight: bold; font-size: 13px;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
        """)
        btn_save.clicked.connect(self._save)

        btns.addWidget(btn_cancel)
        btns.addWidget(btn_save, stretch=1)
        root.addLayout(btns)

        # بند أول فارغ
        self._add_item_row()

    # ══════════════════════════════════════════════════════
    # عمليات صفوف البنود
    # ══════════════════════════════════════════════════════

    def _add_item_row(self, prefill: dict = None) -> _ItemRowWidget:
        row = _ItemRowWidget()
        row.changed.connect(self._update_totals)
        row.removed.connect(self._remove_item_row)
        self._item_rows.append(row)
        self._rows_layout.addWidget(row)
        if prefill:
            row.load_from_order_item(prefill)
        self._update_totals()
        return row

    def _remove_item_row(self, row_widget: _ItemRowWidget):
        if row_widget in self._item_rows:
            self._item_rows.remove(row_widget)
        self._rows_layout.removeWidget(row_widget)
        row_widget.deleteLater()
        self._update_totals()

    def _update_totals(self):
        total = sum(r.get_total() for r in self._item_rows)
        valid = sum(1 for r in self._item_rows if r.get_product_name())
        self.lbl_items_count.setText(str(valid))
        self.lbl_subtotal.setText(f"{total:,.2f} ج")

    # ══════════════════════════════════════════════════════
    # العروض
    # ══════════════════════════════════════════════════════

    def _load_offers_combo(self):
        self.cmb_offers.clear()
        self.cmb_offers.addItem("— اختر عرضاً —", None)
        for o in _fetch_offers():
            cat = f" [{o['category_name']}]" if o.get("category_name") else ""
            label = f"🎁 {o['name']}  —  خصم {o['discount']:.0f}%{cat}"
            self.cmb_offers.addItem(label, o["id"])

    def _import_offer(self):
        oid = self.cmb_offers.currentData()
        if not oid:
            return
        lines = _fetch_offer_lines(oid)
        if not lines:
            QMessageBox.information(self, "تنبيه", "هذا العرض لا يحتوي على بنود.")
            return

        # حذف الصفوف الفارغة أولاً
        for r in list(self._item_rows):
            if not r.get_product_name():
                self._remove_item_row(r)

        for line in lines:
            fake_item = {
                "id":           None,
                "item_name":    line["item_name"],
                "description":  "",
                "quantity":     line["qty"],
                "unit":         "قطعة",
                "unit_price":   line.get("price") or 0,
                "discount_pct": 0,
                "design_ref":   "",
                "notes":        "",
            }
            row = self._add_item_row()
            # البحث عن المنتج في الكاش بالـ id
            pid = line.get("item_id")
            if pid:
                # حدد المنتج في الـ combo
                cmb = row.cmb_product
                for i in range(cmb.count()):
                    if cmb.itemData(i) == pid:
                        cmb.setCurrentIndex(i)
                        break
            row.sp_qty.setValue(line["qty"])
            row.sp_price.setValue(line.get("price") or 0)
            row._recalc()

        self.cmb_offers.setCurrentIndex(0)

    # ══════════════════════════════════════════════════════
    # العميل
    # ══════════════════════════════════════════════════════

    def _search_customers(self, text: str):
        if len(text) < 2:
            return
        results = search_customers(self.conn, text)
        self.cmb_customer.blockSignals(True)
        self.cmb_customer.clear()
        for c in results:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or 'بدون هاتف'})"
            self.cmb_customer.addItem(label, c["id"])
        self.cmb_customer.blockSignals(False)
        if results:
            self.cmb_customer.setCurrentIndex(0)
            self._on_customer_changed(0)

    def _on_customer_changed(self, idx: int):
        cid = self.cmb_customer.currentData()
        self._customer_id = cid
        if cid:
            from db.orders.customers_repo import fetch_customer
            c = fetch_customer(self.conn, cid)
            if c:
                parts = []
                if c["phone"]:  parts.append(f"📞 {c['phone']}")
                if c["city"]:   parts.append(f"📍 {c['city']}")
                if c["email"]:  parts.append(f"✉️ {c['email']}")
                self._lbl_cust_info.setText("  |  ".join(parts) if parts else "")
                self._lbl_cust_info.setVisible(bool(parts))
        else:
            self._lbl_cust_info.setVisible(False)

    def _new_customer(self):
        from ui.tabs.orders._customer_form import _CustomerForm
        dlg = _CustomerForm(self.conn, parent=self)
        dlg.saved.connect(self._on_customer_created)
        dlg.exec_()

    def _on_customer_created(self, customer_id: int):
        from db.orders.customers_repo import fetch_customer
        c = fetch_customer(self.conn, customer_id)
        if c:
            label = f"{c['code']}  —  {c['name']}  ({c['phone'] or 'بدون هاتف'})"
            self.cmb_customer.insertItem(0, label, customer_id)
            self.cmb_customer.setCurrentIndex(0)
            self._customer_id = customer_id

    # ══════════════════════════════════════════════════════
    # تحميل بيانات طلب للتعديل
    # ══════════════════════════════════════════════════════

    def _load(self):
        d = fetch_order(self.conn, self.order_id)
        if not d:
            return

        # العميل
        for i in range(self.cmb_customer.count()):
            if self.cmb_customer.itemData(i) == d["customer_id"]:
                self.cmb_customer.setCurrentIndex(i)
                break

        # النوع والأولوية والحالة
        for cmb, key in [(self.cmb_type, "order_type"),
                         (self.cmb_priority, "priority"),
                         (self.cmb_status, "status")]:
            for i in range(cmb.count()):
                if cmb.itemData(i) == d[key]:
                    cmb.setCurrentIndex(i)
                    break

        # التاريخ والمبالغ
        if d["due_date"]:
            self.inp_due_date.setDate(QDate.fromString(d["due_date"], "yyyy-MM-dd"))
        self.sp_discount.setValue(d["discount"] or 0)
        self.sp_paid.setValue(d["paid_amount"] or 0)
        self.inp_notes.setPlainText(d["notes"] or "")
        self.inp_internal.setPlainText(d["internal_notes"] or "")

        # ── تحميل البنود الموجودة ──
        # نحذف الصف الفارغ الأولي
        for r in list(self._item_rows):
            self._remove_item_row(r)

        items = fetch_order_items(self.conn, self.order_id)
        for item in items:
            self._add_item_row(prefill=dict(item))

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def _save(self):
        if not self._customer_id:
            QMessageBox.warning(self, "تنبيه", "اختر عميلاً أولاً")
            return

        # جمع بنود صالحة
        valid_rows = [r for r in self._item_rows if r.get_product_name()]
        if not valid_rows:
            QMessageBox.warning(self, "تنبيه", "أضف بنداً واحداً على الأقل")
            return

        priority   = self.cmb_priority.currentData()
        order_type = self.cmb_type.currentData()
        due_date   = self.inp_due_date.date().toString("yyyy-MM-dd")
        discount   = self.sp_discount.value()
        paid       = self.sp_paid.value()
        notes      = self.inp_notes.toPlainText().strip()
        internal   = self.inp_internal.toPlainText().strip()

        if self.order_id:
            # ── تعديل الطلب ──
            update_order(
                self.conn, self.order_id,
                priority=priority,
                due_date=due_date,
                discount=discount,
                paid_amount=paid,
                notes=notes,
                internal_notes=internal,
            )
            # حذف كل البنود القديمة وإعادة إدراجها
            existing = fetch_order_items(self.conn, self.order_id)
            existing_ids = {i["id"] for i in existing}
            # حذف القديمة
            for eid in existing_ids:
                delete_order_item(self.conn, eid)
            # إدراج الجديدة
            for idx, row in enumerate(valid_rows):
                d = row.get_data()
                insert_order_item(
                    self.conn, self.order_id,
                    item_name   = d["item_name"],
                    description = d["description"],
                    quantity    = d["quantity"],
                    unit        = d["unit"],
                    unit_price  = d["unit_price"],
                    discount_pct= d["discount_pct"],
                    design_ref  = d["design_ref"],
                    notes       = d["notes"],
                    sort_order  = idx,
                )
            self.saved.emit(self.order_id)
        else:
            # ── طلب جديد ──
            oid = insert_order(
                self.conn,
                customer_id   = self._customer_id,
                order_type    = order_type,
                priority      = priority,
                due_date      = due_date,
                discount      = discount,
                paid_amount   = paid,
                notes         = notes,
                internal_notes= internal,
            )
            for idx, row in enumerate(valid_rows):
                d = row.get_data()
                insert_order_item(
                    self.conn, oid,
                    item_name   = d["item_name"],
                    description = d["description"],
                    quantity    = d["quantity"],
                    unit        = d["unit"],
                    unit_price  = d["unit_price"],
                    discount_pct= d["discount_pct"],
                    design_ref  = d["design_ref"],
                    notes       = d["notes"],
                    sort_order  = idx,
                )
            self.saved.emit(oid)

        self.accept()