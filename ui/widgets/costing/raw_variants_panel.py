"""
ui/widgets/costing/raw_variants_panel.py
=================================
_RawVariantsPanel — لوحة إدارة variants الخامة (صفوف الإنتاج).

تُستخدم داخل فورم الخامة (raw_input_panel.py) وتظهر بعد اختيار الخامة.

كل variant بيحدد:
  - الاسم (مثال: "قميص كبير")
  - عدد القطع اللي بتنتجها من الخامة (مثال: 2)

لو سعر الخامة 100 جنيه وعدد القطع 2 → تكلفة الوحدة = 50 جنيه
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.costing.raw_variants_repo import (
    fetch_variants_for_item,
    insert_variant, update_variant, delete_variant,
    fetch_variant,
)
from ui.events import bus


def _spin_pieces(max_=999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0.0001, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(28)
    s.setValue(1.0)
    return s


class _RawVariantsPanel(QGroupBox):
    """
    لوحة إدارة variants الخامة — تُضاف داخل فورم الخامة.

    الاستخدام:
        self._variants_panel = _RawVariantsPanel(conn)
        self._variants_panel.load_item(item_id, item_price)
    """

    def __init__(self, conn, parent=None):
        super().__init__("📐  وحدات الإنتاج (Variants)", parent)
        self.conn       = conn
        self._item_id   = None
        self._item_price = 0.0
        self._editing_id = None
        self._build()
        self.setEnabled(False)   # معطل لحد ما يتحدد item_id

    def _build(self):
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold; color: #1565c0;
                border: 1px solid #c5cae9;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                padding: 0 6px;
            }
        """)

        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 12, 10, 10)

        # ── شرح ──
        lbl_info = QLabel(
            "💡 كل variant بيحدد عدد القطع اللي بتنتجها من هذه الخامة.\n"
            "   تكلفة الوحدة = سعر الخامة ÷ عدد القطع"
        )
        lbl_info.setStyleSheet(
            "font-size:10px; color:#555; font-weight:normal;"
            "background:#e8f0fe; border-radius:4px; padding:5px 8px;"
            "border:1px solid #c5cae9;"
        )
        lbl_info.setWordWrap(True)
        root.addWidget(lbl_info)

        # ── فورم إضافة/تعديل ──
        form_row = QHBoxLayout()
        form_row.setSpacing(8)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم الـ variant  (مثال: قميص كبير)")
        self.inp_name.setMinimumHeight(30)

        lbl_pieces = QLabel("عدد القطع:")
        lbl_pieces.setStyleSheet("font-weight:bold; font-size:11px;")

        self.sp_pieces = _spin_pieces()
        self.sp_pieces.setFixedWidth(100)
        self.sp_pieces.setToolTip(
            "عدد القطع اللي بتنتجها من الخامة دي\n"
            "تكلفة الوحدة = سعر الخامة ÷ عدد القطع"
        )

        # معاينة حية
        self.lbl_preview = QLabel("─")
        self.lbl_preview.setStyleSheet(
            "color:#1565c0; font-weight:bold; font-size:11px; min-width:120px;"
        )
        self.sp_pieces.valueChanged.connect(self._update_preview)

        self.btn_add    = QPushButton("➕ إضافة")
        self.btn_save   = QPushButton("💾 حفظ")
        self.btn_cancel = QPushButton("✖")
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.setFixedWidth(28)

        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)

        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._reset_form)

        form_row.addWidget(self.inp_name, stretch=2)
        form_row.addWidget(lbl_pieces)
        form_row.addWidget(self.sp_pieces)
        form_row.addWidget(self.lbl_preview)
        form_row.addWidget(self.btn_add)
        form_row.addWidget(self.btn_save)
        form_row.addWidget(self.btn_cancel)
        root.addLayout(form_row)

        # ── جدول الـ variants ──
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "الاسم", "عدد القطع", "تكلفة/قطعة"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(160)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 0)   # إخفاء ID
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 110)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        # ── أزرار التعديل والحذف ──
        btn_row = QHBoxLayout()
        btn_edit = QPushButton("✏️ تعديل")
        btn_del  = QPushButton("🗑️ حذف")
        btn_del.setStyleSheet("color:#c0392b;")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(26)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_item(self, item_id: int, item_price: float):
        """تحميل variants خامة معينة."""
        self._item_id    = item_id
        self._item_price = item_price
        self.setEnabled(True)
        self._reset_form()
        self._load_table()

    def clear(self):
        """مسح اللوحة لما لا توجد خامة محددة."""
        self._item_id    = None
        self._item_price = 0.0
        self._editing_id = None
        self.table.setRowCount(0)
        self.inp_name.clear()
        self.sp_pieces.setValue(1.0)
        self.lbl_preview.setText("─")
        self.setEnabled(False)

    def refresh_price(self, new_price: float):
        """تحديث السعر لو تغير في الفورم."""
        self._item_price = new_price
        self._update_preview()
        self._load_table()

    # ══════════════════════════════════════════════════════
    # تحميل الجدول
    # ══════════════════════════════════════════════════════

    def _load_table(self):
        self.table.setRowCount(0)
        if self._item_id is None:
            return
        for var in fetch_variants_for_item(self.conn, self._item_id):
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(var["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(var["name"]))

            pieces_item = QTableWidgetItem(f"{var['pieces']:,.4g}")
            pieces_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, pieces_item)

            pieces = float(var["pieces"])
            if pieces > 0 and self._item_price > 0:
                unit_cost = self._item_price / pieces
                cost_text = f"{unit_cost:.4f}  ج"
            else:
                cost_text = "─"
            cost_item = QTableWidgetItem(cost_text)
            cost_item.setForeground(QColor("#1565c0"))
            cost_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, cost_item)

    # ══════════════════════════════════════════════════════
    # معاينة حية
    # ══════════════════════════════════════════════════════

    def _update_preview(self):
        pieces = self.sp_pieces.value()
        if pieces > 0 and self._item_price > 0:
            unit_cost = self._item_price / pieces
            self.lbl_preview.setText(f"= {unit_cost:.4f}  ج/قطعة")
        else:
            self.lbl_preview.setText("─")

    # ══════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════

    def _add(self):
        name   = self.inp_name.text().strip()
        pieces = self.sp_pieces.value()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الـ variant")
            return
        if self._item_id is None:
            return
        insert_variant(self.conn, self._item_id, name, pieces)
        self._reset_form()
        self._load_table()
        bus.data_changed.emit()

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر variant أولاً")
            return
        vid = int(self.table.item(row, 0).text())
        var = fetch_variant(self.conn, vid)
        if not var:
            return
        self._editing_id = vid
        self.inp_name.setText(var["name"])
        self.sp_pieces.setValue(float(var["pieces"]))
        self._update_preview()
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        name   = self.inp_name.text().strip()
        pieces = self.sp_pieces.value()
        if not name or self._editing_id is None:
            return
        update_variant(self.conn, self._editing_id, name, pieces)
        self._reset_form()
        self._load_table()
        bus.data_changed.emit()

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر variant أولاً")
            return
        vid  = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        if QMessageBox.question(
            self, "تأكيد", f"حذف variant «{name}»؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_variant(self.conn, vid)
            self._load_table()
            bus.data_changed.emit()

    def _reset_form(self):
        self._editing_id = None
        self.inp_name.clear()
        self.sp_pieces.setValue(1.0)
        self._update_preview()
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)