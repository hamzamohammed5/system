"""
ui/widgets/bulk_replace_dialog.py
==================================
نافذة "الاستبدال الشامل" — تُفتح من تبويبات الخامات / العمالة / التشغيل.

الوظيفة:
  - تعرض كل المنتجات (نصف مصنع + نهائي) التي تحتوي على العنصر المحدد
  - تتيح:
      ① إحلال العنصر بعنصر آخر من نفس النوع
      ② تعديل الكمية في المنتجات المختارة
      ③ الاثنين معاً
  - تتيح تصفية المنتجات بالتصنيف أو اختيار يدوي

الاستخدام:
    from ui.widgets.bulk_replace_dialog import BulkReplaceDialog

    dlg = BulkReplaceDialog(
        conn       = conn,
        child_type = "raw",          # "raw" | "labor_op" | "machine_op"
        child_id   = item_id,
        child_name = item_name,
        parent     = self,
    )
    dlg.exec_()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QComboBox, QDoubleSpinBox, QPushButton,
    QCheckBox, QScrollArea, QWidget, QFrame,
    QMessageBox, QRadioButton,
    QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.items_repo      import (
    fetch_items_by_type, fetch_item,
    replace_bom, fetch_bom,
)
from db.operations_repo import fetch_all_labor_ops, fetch_all_machine_ops
from models.costing     import calc_cost
from ui.events          import bus


# ══════════════════════════════════════════════════════════
# مساعدات
# ══════════════════════════════════════════════════════════

def _get_element_name(conn, child_type: str, child_id: int) -> str:
    if child_type in ("raw", "semi"):
        row = conn.execute("SELECT name FROM items WHERE id=?", (child_id,)).fetchone()
    elif child_type == "labor_op":
        row = conn.execute("SELECT name FROM labor_ops WHERE id=?", (child_id,)).fetchone()
    elif child_type == "machine_op":
        row = conn.execute("SELECT name FROM machine_ops WHERE id=?", (child_id,)).fetchone()
    else:
        row = None
    return row["name"] if row else f"ID:{child_id}"


def _fetch_candidates(conn, child_type: str, exclude_id: int) -> list:
    """
    يرجع عناصر بديلة من نفس النوع (بدون العنصر الحالي).
    يرجع list of (id, name, category_name)
    """
    if child_type == "raw":
        rows = fetch_items_by_type(conn, "raw")
        return [(r["id"], r["name"], r["category_name"] or "")
                for r in rows if r["id"] != exclude_id]
    elif child_type == "labor_op":
        rows = fetch_all_labor_ops(conn)
        return [(r["id"], r["name"], r["category_name"] or "")
                for r in rows if r["id"] != exclude_id]
    elif child_type == "machine_op":
        rows = fetch_all_machine_ops(conn)
        return [(r["id"], r["name"], r["category_name"] or "")
                for r in rows if r["id"] != exclude_id]
    return []


def _fetch_affected_products(conn, child_type: str, child_id: int) -> list:
    """
    يرجع كل المنتجات (semi + final) التي تحتوي على العنصر مباشرةً في BOM.
    يرجع list of dicts: {id, name, type, qty, category_id, category_name, cost}
    """
    rows = conn.execute("""
        SELECT b.parent_id, b.qty,
               i.name, i.type, i.category_id,
               c.name AS category_name
        FROM   bom b
        JOIN   items i ON i.id = b.parent_id
        LEFT JOIN categories c ON c.id = i.category_id
        WHERE  b.child_type = ?
          AND  b.child_id   = ?
          AND  i.type IN ('semi','final')
        ORDER  BY i.name
    """, (child_type, child_id)).fetchall()

    result = []
    for r in rows:
        result.append({
            "id":            r["parent_id"],
            "name":          r["name"],
            "type":          r["type"],
            "qty":           r["qty"],
            "category_id":   r["category_id"],
            "category_name": r["category_name"] or "—",
            "cost":          calc_cost(conn, r["parent_id"]),
        })
    return result


# ══════════════════════════════════════════════════════════
# صف منتج واحد في اللوحة
# ══════════════════════════════════════════════════════════

class _ProductRow(QFrame):
    """
    صف يعرض معلومات منتج واحد مع:
      - checkbox للاختيار
      - حقل الكمية الحالية (قابل للتعديل)
      - بيانات المنتج (اسم، نوع، تصنيف، تكلفة)
    """

    def __init__(self, product: dict, parent=None):
        super().__init__(parent)
        self._product = product
        self._build()

    def _build(self):
        self.setFrameShape(QFrame.StyledPanel)
        self._apply_style(checked=True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(10)

        # ── checkbox ──
        self.chk = QCheckBox()
        self.chk.setChecked(True)
        self.chk.setFixedWidth(20)
        self.chk.toggled.connect(self._on_toggle)
        lay.addWidget(self.chk)

        # ── نوع المنتج ──
        type_icon = "🔧" if self._product["type"] == "semi" else "🏭"
        lbl_type = QLabel(type_icon)
        lbl_type.setFixedWidth(20)
        lbl_type.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_type)

        # ── الاسم والتصنيف ──
        info = QVBoxLayout()
        info.setSpacing(2)
        self.lbl_name = QLabel(self._product["name"])
        self.lbl_name.setStyleSheet("font-weight:bold; font-size:12px; color:#212121;")

        lbl_cat = QLabel(
            f"🏷 {self._product['category_name']}  "
            f"│  💰 {self._product['cost']:.2f} جنيه"
        )
        lbl_cat.setStyleSheet("color:#757575; font-size:10px;")
        info.addWidget(self.lbl_name)
        info.addWidget(lbl_cat)
        lay.addLayout(info, stretch=1)

        # ── الكمية الحالية ──
        lay.addWidget(QLabel("الكمية:"))
        self.sp_qty = QDoubleSpinBox()
        self.sp_qty.setRange(0.0001, 999999)
        self.sp_qty.setDecimals(4)
        self.sp_qty.setValue(self._product["qty"])
        self.sp_qty.setFixedWidth(90)
        self.sp_qty.setMinimumHeight(28)
        self.sp_qty.setToolTip("الكمية المستخدمة من هذا العنصر في هذا المنتج")
        lay.addWidget(self.sp_qty)

    def _apply_style(self, checked: bool):
        if checked:
            self.setStyleSheet("""
                QFrame {
                    background: #ffffff;
                    border: 1px solid #e0e0e0;
                    border-radius: 6px;
                    margin: 1px 0;
                }
                QFrame:hover {
                    border-color: #90caf9;
                    background: #f8fbff;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background: #fafafa;
                    border: 1px solid #f0f0f0;
                    border-radius: 6px;
                    margin: 1px 0;
                }
            """)

    def _on_toggle(self, checked: bool):
        self.sp_qty.setEnabled(checked)
        self._apply_style(checked)
        if hasattr(self, 'lbl_name'):
            color = "#212121" if checked else "#bdbdbd"
            self.lbl_name.setStyleSheet(
                f"font-weight:bold; font-size:12px; color:{color};"
            )

    @property
    def is_selected(self) -> bool:
        return self.chk.isChecked()

    @property
    def product_id(self) -> int:
        return self._product["id"]

    @property
    def new_qty(self) -> float:
        return self.sp_qty.value()

    def set_selected(self, val: bool):
        self.chk.setChecked(val)


# ══════════════════════════════════════════════════════════
# نافذة الاستبدال الشامل
# ══════════════════════════════════════════════════════════

class BulkReplaceDialog(QDialog):
    def __init__(self, conn, child_type: str, child_id: int,
                 child_name: str = None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self.child_type = child_type
        self.child_id   = child_id
        self.child_name = child_name or _get_element_name(conn, child_type, child_id)

        self._all_products   = []   # كل المنتجات المرتبطة
        self._product_rows   = []   # _ProductRow widgets
        self._filter_cat_id  = None

        self.setWindowTitle("🔄  استبدال / تعديل شامل")
        self.setMinimumSize(750, 620)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()
        self._load_products()
        self._load_candidates()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header ──
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #1976d2);
                border-bottom: 2px solid #0d47a1;
            }
        """)
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)

        lbl_icon = QLabel("🔄")
        lbl_icon.setStyleSheet("font-size:28px; background:transparent; border:none;")
        lbl_title = QLabel(
            f"استبدال شامل  —  <span style='color:#90caf9;'>{self.child_name}</span>"
        )
        lbl_title.setStyleSheet(
            "font-size:15px; font-weight:bold; color:white;"
            "background:transparent; border:none;"
        )
        lbl_title.setTextFormat(Qt.RichText)
        h_lay.addWidget(lbl_icon)
        h_lay.addSpacing(10)
        h_lay.addWidget(lbl_title)
        h_lay.addStretch()
        root.addWidget(header)

        # ── Body ──
        body = QWidget()
        body.setStyleSheet("background: #f5f7fa;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 14, 16, 14)
        body_lay.setSpacing(12)

        body_lay.addWidget(self._build_operation_section())
        body_lay.addWidget(self._build_products_section(), stretch=1)
        body_lay.addWidget(self._build_quick_bar())
        body_lay.addLayout(self._build_action_buttons())

        root.addWidget(body, stretch=1)

    # ── قسم العملية ──────────────────────────────────────

    def _build_operation_section(self) -> QGroupBox:
        grp = QGroupBox("⚙️  العملية المطلوبة")
        grp.setStyleSheet("""
            QGroupBox {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                font-weight: bold;
                color: #1565c0;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
            }
        """)
        lay = QVBoxLayout(grp)
        lay.setSpacing(10)

        # ── خيارات العملية ──
        ops_row = QHBoxLayout()
        self._rdo_replace = QRadioButton("🔀  استبدال العنصر")
        self._rdo_qty     = QRadioButton("🔢  تعديل الكمية فقط")
        self._rdo_both    = QRadioButton("✅  الاثنين معاً")
        self._rdo_both.setChecked(True)

        for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
            rdo.setStyleSheet("font-size:12px;")
            ops_row.addWidget(rdo)
        ops_row.addStretch()
        lay.addLayout(ops_row)

        # ── اختيار البديل ──
        self._replace_frame = QFrame()
        self._replace_frame.setStyleSheet(
            "QFrame { background:#f8fbff; border:1px solid #bbdefb;"
            "border-radius:6px; padding:4px; }"
        )
        rf_lay = QFormLayout(self._replace_frame)
        rf_lay.setSpacing(8)
        rf_lay.setLabelAlignment(Qt.AlignRight)

        self.cmb_replacement = QComboBox()
        self.cmb_replacement.setMinimumHeight(32)
        self.cmb_replacement.setMinimumWidth(280)
        self.cmb_replacement.setSizeAdjustPolicy(QComboBox.AdjustToContents)

        lbl_new_type = {
            "raw":        "🧱  الخامة البديلة :",
            "labor_op":   "👷  العملية البديلة :",
            "machine_op": "⚙️  العملية البديلة :",
        }.get(self.child_type, "البديل :")
        rf_lay.addRow(lbl_new_type, self.cmb_replacement)

        # ── تعديل موحد للكمية ──
        qty_row = QHBoxLayout()
        self.chk_uniform_qty = QCheckBox("تطبيق كمية موحدة على المنتجات المختارة:")
        self.chk_uniform_qty.setStyleSheet("font-size:11px;")
        self.sp_uniform_qty = QDoubleSpinBox()
        self.sp_uniform_qty.setRange(0.0001, 999999)
        self.sp_uniform_qty.setDecimals(4)
        self.sp_uniform_qty.setValue(1.0)
        self.sp_uniform_qty.setFixedWidth(100)
        self.sp_uniform_qty.setEnabled(False)
        self.chk_uniform_qty.toggled.connect(self.sp_uniform_qty.setEnabled)
        qty_row.addWidget(self.chk_uniform_qty)
        qty_row.addWidget(self.sp_uniform_qty)
        qty_row.addStretch()
        rf_lay.addRow("", qty_row)

        lay.addWidget(self._replace_frame)

        # تفعيل/تعطيل حقل الاستبدال حسب الخيار
        self._rdo_replace.toggled.connect(self._update_op_ui)
        self._rdo_qty.toggled.connect(self._update_op_ui)
        self._rdo_both.toggled.connect(self._update_op_ui)
        self._update_op_ui()

        return grp

    def _update_op_ui(self):
        show_replace = self._rdo_replace.isChecked() or self._rdo_both.isChecked()
        self.cmb_replacement.setEnabled(show_replace)
        if self._rdo_qty.isChecked():
            self._replace_frame.setStyleSheet(
                "QFrame { background:#f5f5f5; border:1px solid #e0e0e0;"
                "border-radius:6px; padding:4px; }"
            )
        else:
            self._replace_frame.setStyleSheet(
                "QFrame { background:#f8fbff; border:1px solid #bbdefb;"
                "border-radius:6px; padding:4px; }"
            )

    # ── قسم المنتجات ─────────────────────────────────────

    def _build_products_section(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)

        # ── شريط الفلتر ──
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("🏷  فلتر بالتصنيف:"))

        self.cmb_cat_filter = QComboBox()
        self.cmb_cat_filter.setMinimumHeight(30)
        self.cmb_cat_filter.setFixedWidth(200)
        self.cmb_cat_filter.addItem("— الكل —", None)
        self._fill_category_filter()
        self.cmb_cat_filter.currentIndexChanged.connect(self._apply_filter)

        self.lbl_count = QLabel()
        self.lbl_count.setStyleSheet("color:#1565c0; font-weight:bold; font-size:11px;")

        filter_row.addWidget(self.cmb_cat_filter)
        filter_row.addSpacing(16)
        filter_row.addWidget(self.lbl_count)
        filter_row.addStretch()
        lay.addLayout(filter_row)

        # ── Scroll area للمنتجات ──
        self._scroll_content = QWidget()
        self._scroll_content.setStyleSheet("background: transparent;")
        self._rows_layout = QVBoxLayout(self._scroll_content)
        self._rows_layout.setSpacing(4)
        self._rows_layout.setContentsMargins(0, 0, 4, 0)
        self._rows_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._scroll_content)
        scroll.setMinimumHeight(200)
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                background: #f9f9f9;
            }
        """)
        lay.addWidget(scroll, stretch=1)

        return container

    def _build_quick_bar(self) -> QFrame:
        bar = QFrame()
        bar.setStyleSheet(
            "QFrame { background:white; border:1px solid #e0e0e0;"
            "border-radius:6px; padding:2px; }"
        )
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)

        lbl = QLabel("تحديد سريع:")
        lbl.setStyleSheet("font-size:11px; color:#555;")
        btn_all  = QPushButton("✅ الكل")
        btn_none = QPushButton("☐ لا شيء")
        btn_inv  = QPushButton("⇄ عكس")

        for btn in (btn_all, btn_none, btn_inv):
            btn.setMinimumHeight(26)
            btn.setStyleSheet(
                "QPushButton { background:#f5f5f5; border:1px solid #ddd;"
                "border-radius:4px; padding:2px 10px; font-size:11px; }"
                "QPushButton:hover { background:#e3f2fd; border-color:#90caf9; }"
            )

        btn_all.clicked.connect(lambda: self._select_all(True))
        btn_none.clicked.connect(lambda: self._select_all(False))
        btn_inv.clicked.connect(self._invert_selection)

        lay.addWidget(lbl)
        lay.addWidget(btn_all)
        lay.addWidget(btn_none)
        lay.addWidget(btn_inv)
        lay.addStretch()
        return bar

    def _build_action_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self.btn_apply = QPushButton("🚀  تطبيق على المحدد")
        self.btn_apply.setMinimumHeight(38)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background: #1565c0;
                color: white;
                font-weight: bold;
                font-size: 13px;
                border-radius: 6px;
                padding: 0 20px;
            }
            QPushButton:hover { background: #1976d2; }
            QPushButton:pressed { background: #0d47a1; }
            QPushButton:disabled { background: #90a4ae; }
        """)
        self.btn_apply.clicked.connect(self._apply)

        btn_cancel = QPushButton("✖  إغلاق")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #555;
                border: 1px solid #ddd;
                border-radius: 6px;
                padding: 0 16px;
                font-size: 12px;
            }
            QPushButton:hover { background: #eeeeee; }
        """)
        btn_cancel.clicked.connect(self.reject)

        row.addStretch()
        row.addWidget(btn_cancel)
        row.addWidget(self.btn_apply)
        return row

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_products(self):
        self._all_products = _fetch_affected_products(
            self.conn, self.child_type, self.child_id
        )
        self._rebuild_rows(self._all_products)

    def _rebuild_rows(self, products: list):
        # احذف الصفوف القديمة
        while self._rows_layout.count() > 1:
            item = self._rows_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._product_rows.clear()

        if not products:
            lbl = QLabel("⚠️  لا توجد منتجات مرتبطة بهذا العنصر")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color:#999; font-size:12px; padding:20px;")
            self._rows_layout.insertWidget(0, lbl)
            self.btn_apply.setEnabled(False)
            self._update_count()
            return

        self.btn_apply.setEnabled(True)
        for prod in products:
            row = _ProductRow(prod)
            self._product_rows.append(row)
            self._rows_layout.insertWidget(self._rows_layout.count() - 1, row)

        self._update_count()

    def _load_candidates(self):
        """يملأ combo الاستبدال بالعناصر البديلة مجمّعة بالتصنيف."""
        candidates = _fetch_candidates(self.conn, self.child_type, self.child_id)
        self.cmb_replacement.clear()
        self.cmb_replacement.addItem("— اختر البديل —", None)

        last_cat = object()   # sentinel فريد
        for cid, cname, cat_name in candidates:
            if cat_name != last_cat:
                # فاصل تصنيف
                sep_text = f"─── {cat_name or 'بدون تصنيف'} ───"
                self.cmb_replacement.addItem(sep_text, "__sep__")
                idx = self.cmb_replacement.count() - 1
                # تعطيل الفاصل
                model = self.cmb_replacement.model()
                item  = model.item(idx)
                if item:
                    from PyQt5.QtCore import Qt as _Qt
                    item.setFlags(item.flags() & ~_Qt.ItemIsEnabled & ~_Qt.ItemIsSelectable)
                    from PyQt5.QtGui import QColor as _QColor, QFont as _QFont
                    item.setForeground(_QColor("#78909c"))
                    f = _QFont()
                    f.setBold(True)
                    f.setPointSize(f.pointSize() - 1)
                    item.setFont(f)
                last_cat = cat_name

            self.cmb_replacement.addItem(f"{cid} — {cname}", cid)

        if self.cmb_replacement.count() == 1:
            # لا يوجد بدائل
            self.cmb_replacement.addItem("لا توجد عناصر بديلة", "__empty__")
            self.cmb_replacement.setEnabled(False)
            self._rdo_qty.setChecked(True)
            self._rdo_replace.setEnabled(False)
            self._rdo_both.setEnabled(False)

    def _fill_category_filter(self):
        """يملأ combo الفلتر بالتصنيفات الموجودة فعلاً في المنتجات المرتبطة."""
        seen_cats: dict[int | None, str] = {}
        for prod in self._all_products:
            cid  = prod["category_id"]
            cname = prod["category_name"]
            if cid not in seen_cats:
                seen_cats[cid] = cname

        for cid, cname in sorted(seen_cats.items(), key=lambda x: x[1] or ""):
            self.cmb_cat_filter.addItem(cname, cid)

    # ══════════════════════════════════════════════════════
    # الفلتر والتحديد
    # ══════════════════════════════════════════════════════

    def _apply_filter(self):
        cat_id = self.cmb_cat_filter.currentData()
        if cat_id is None:
            filtered = self._all_products
        else:
            filtered = [p for p in self._all_products if p["category_id"] == cat_id]
        self._rebuild_rows(filtered)

    def _select_all(self, val: bool):
        for row in self._product_rows:
            row.set_selected(val)

    def _invert_selection(self):
        for row in self._product_rows:
            row.set_selected(not row.is_selected)

    def _update_count(self):
        total    = len(self._product_rows)
        selected = sum(1 for r in self._product_rows if r.is_selected)
        self.lbl_count.setText(f"إجمالي: {total}  │  محدد: {selected}")

    # ══════════════════════════════════════════════════════
    # تطبيق التعديل
    # ══════════════════════════════════════════════════════

    def _apply(self):
        selected_rows = [r for r in self._product_rows if r.is_selected]
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "اختر منتجاً واحداً على الأقل")
            return

        do_replace = self._rdo_replace.isChecked() or self._rdo_both.isChecked()
        do_qty     = self._rdo_qty.isChecked()     or self._rdo_both.isChecked()

        # ── التحقق من البديل ──
        new_child_id = None
        if do_replace:
            new_child_id = self.cmb_replacement.currentData()
            if not new_child_id or new_child_id in (None, "__sep__", "__empty__"):
                QMessageBox.warning(
                    self, "تنبيه",
                    "اختر العنصر البديل أولاً\n"
                    "أو اختر «تعديل الكمية فقط» لو لا تريد الاستبدال."
                )
                return

        # ── تأكيد ──
        op_desc = []
        if do_replace:
            new_name = _get_element_name(self.conn, self.child_type, new_child_id)
            op_desc.append(f"• استبدال  «{self.child_name}»  بـ  «{new_name}»")
        if do_qty:
            if self.chk_uniform_qty.isChecked():
                op_desc.append(f"• تعيين الكمية = {self.sp_uniform_qty.value():.4f} لكل المنتجات المختارة")
            else:
                op_desc.append("• الاحتفاظ بالكمية المعدَّلة لكل منتج")

        msg = (
            f"سيتم تطبيق التالي على {len(selected_rows)} منتج:\n\n"
            + "\n".join(op_desc)
            + "\n\nهل تريد المتابعة؟"
        )
        if QMessageBox.question(
            self, "تأكيد التطبيق", msg,
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        # ── التطبيق ──
        errors = []
        updated = 0

        for prod_row in selected_rows:
            pid = prod_row.product_id
            try:
                bom = fetch_bom(self.conn, pid)
                new_bom = []
                for child_type, child_id, qty in bom:
                    if child_type == self.child_type and child_id == self.child_id:
                        # هذا هو العنصر المستهدف
                        final_child_id = new_child_id if do_replace else child_id
                        final_qty      = (
                            self.sp_uniform_qty.value()
                            if (do_qty and self.chk_uniform_qty.isChecked())
                            else (prod_row.new_qty if do_qty else qty)
                        )
                        new_bom.append((child_type, final_child_id, final_qty, None))
                    else:
                        new_bom.append((child_type, child_id, qty, None))

                replace_bom(self.conn, pid, new_bom)
                updated += 1
            except Exception as e:
                item = fetch_item(self.conn, pid)
                name = item["name"] if item else f"ID:{pid}"
                errors.append(f"• {name}: {e}")

        bus.data_changed.emit()

        # ── تقرير النتيجة ──
        if errors:
            QMessageBox.warning(
                self, "اكتمل مع أخطاء",
                f"✅ تم تحديث {updated} منتج بنجاح\n\n"
                f"⚠️ فشل {len(errors)} منتج:\n" + "\n".join(errors)
            )
        else:
            QMessageBox.information(
                self, "تم",
                f"✅ تم تحديث {updated} منتج بنجاح"
            )

        # تحديث قائمة المنتجات بعد الاستبدال
        self._all_products = _fetch_affected_products(
            self.conn,
            new_child_id if do_replace else self.child_id,
            new_child_id if do_replace else self.child_id,
        )
        # لو استبدلنا، نقلق النافذة — لا يوجد شيء يُعرض للعنصر القديم
        if do_replace:
            self.accept()
        else:
            # تحديث بيانات المنتجات في الواجهة (الكميات تغيرت)
            self._all_products = _fetch_affected_products(
                self.conn, self.child_type, self.child_id
            )
            self._rebuild_rows(self._all_products)