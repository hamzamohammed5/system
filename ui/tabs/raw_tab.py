"""
ui/tabs/raw_tab.py  (النسخة المعدَّلة — نهائية)
==================
التغييرات:
  • فورم الخامة: حقل "الكمية الإجمالية" جديد
  • جدول الخامات: عمودان جديدان "الكمية الكلية" و"سعر الوحدة"
  • component_row مفيش تغيير فيه — الصف بيفضل زي ما هو
"""

from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QTableWidgetItem,
    QMessageBox, QLabel, QGroupBox, QHeaderView,
    QSplitter, QTabWidget,
)

from db.connection import get_connection
from db.items_repo import (
    fetch_items_by_type, fetch_item,
    insert_item, update_item, delete_item,
)
from models.costing import raw_unit_price
from ui.helpers import (
    EditModeMixin, make_table, buttons_row,
    section_label, confirm_delete, danger_button,
)
from ui.widgets.category_manager import CategoryCombo, CategoryManager
from ui.events import bus

_SPLITTER_STYLE = """
    QSplitter::handle { background: #e0e0e0; border-top: 1px solid #ccc; }
    QSplitter::handle:hover { background: #bbdefb; }
"""


def _labeled(widget, unit: str) -> QWidget:
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lay.addWidget(widget)
    lay.addWidget(QLabel(unit))
    lay.addStretch()
    return w


# ══════════════════════════════════════════════════════════
# فورم الإدخال
# ══════════════════════════════════════════════════════════

class _InputPanel(QWidget, EditModeMixin):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        grp = QGroupBox("بيانات الخامة")
        grp_layout = QVBoxLayout(grp)
        grp_layout.setSpacing(10)

        self.lbl_mode = QLabel("─── إضافة خامة جديدة ───")
        self.lbl_mode.setStyleSheet("font-weight: bold; color: #1565c0; font-size: 12px;")
        grp_layout.addWidget(self.lbl_mode)

        form = QFormLayout()
        form.setSpacing(8)
        form.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("أدخل اسم الخامة...")
        self.inp_name.setMinimumHeight(32)

        self.inp_price = QLineEdit()
        self.inp_price.setPlaceholderText("0.00")
        self.inp_price.setFixedWidth(120)

        # ── الكمية الإجمالية (جديد) ──
        self.inp_total_qty = QLineEdit()
        self.inp_total_qty.setPlaceholderText("اتركه فارغاً لو السعر بالوحدة")
        self.inp_total_qty.setFixedWidth(120)

        # hint يتحدث تلقائياً لما يكتب في الحقلين
        self.lbl_hint = QLabel()
        self.lbl_hint.setStyleSheet(
            "color: #1565c0; font-size: 10px;"
            "background: #e8f0fe; border-radius: 4px; padding: 4px 8px;"
        )
        self.lbl_hint.setWordWrap(True)
        self._update_hint()

        self.inp_price.textChanged.connect(lambda _: self._update_hint())
        self.inp_total_qty.textChanged.connect(lambda _: self._update_hint())

        self.cmb_category = CategoryCombo(self.conn, scope="raw")

        form.addRow("اسم الخامة :",       self.inp_name)
        form.addRow("السعر الكلي :",       _labeled(self.inp_price,     "جنيه"))
        form.addRow("الكمية الإجمالية :",  _labeled(self.inp_total_qty, "وحدة"))
        form.addRow("",                   self.lbl_hint)
        form.addRow("التصنيف :",          self.cmb_category)
        grp_layout.addLayout(form)

        self.btn_add    = QPushButton("➕  إضافة خامة")
        self.btn_save   = QPushButton("💾  حفظ التعديل")
        self.btn_cancel = QPushButton("✖  إلغاء")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(32)
        self.btn_add.clicked.connect(self._add)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._cancel_edit)
        grp_layout.addLayout(buttons_row(self.btn_add, self.btn_save, self.btn_cancel))

        root.addWidget(grp)
        root.addStretch()

    # ── تحديث الـ hint ────────────────────────────────────────────────

    def _update_hint(self):
        try:
            price = float(self.inp_price.text() or "0")
        except ValueError:
            price = 0.0
        tq_text = self.inp_total_qty.text().strip()
        try:
            tq = float(tq_text) if tq_text else None
        except ValueError:
            tq = None

        if tq and tq > 0 and price > 0:
            unit = price / tq
            self.lbl_hint.setText(
                f"💡 سعر الوحدة = {price:.2f} ÷ {tq:.4g} = {unit:.4f} جنيه/وحدة"
            )
        elif tq and tq > 0:
            self.lbl_hint.setText("💡 سعر الوحدة = السعر الكلي ÷ الكمية الإجمالية")
        else:
            self.lbl_hint.setText(
                "💡 بدون كمية إجمالية: السعر المسجل = سعر الوحدة مباشرة"
            )

    # ── تحميل للتعديل ─────────────────────────────────────────────────

    def load_for_edit(self, item_id: int):
        item = fetch_item(self.conn, item_id)
        if not item:
            return
        self.inp_name.setText(item["name"])
        self.inp_price.setText(str(item["price"]))
        tq = item["total_qty"]
        self.inp_total_qty.setText(str(tq) if tq is not None else "")
        self.cmb_category.set_category(item["category_id"])
        self.inp_name.setFocus()
        self.enter_edit_mode(item_id, f"─── تعديل: {item['name']} ───")

    # ── حفظ / تعديل / إلغاء ──────────────────────────────────────────

    def _add(self):
        name, price, total_qty = self._collect()
        if name is None:
            return
        insert_item(self.conn, name, "raw", price,
                    category_id=self.cmb_category.get_category(),
                    total_qty=total_qty)
        self._reset()
        bus.data_changed.emit()

    def _save_edit(self):
        name, price, total_qty = self._collect()
        if name is None:
            return
        update_item(self.conn, self._editing_id, name, price,
                    category_id=self.cmb_category.get_category(),
                    total_qty=total_qty)
        self._reset()
        bus.data_changed.emit()

    def _cancel_edit(self):
        self._reset()

    def _collect(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم الخامة")
            return None, None, None
        try:
            price = float(self.inp_price.text() or "0")
        except ValueError:
            QMessageBox.warning(self, "خطأ", "السعر يجب أن يكون رقماً")
            return None, None, None

        tq_text = self.inp_total_qty.text().strip()
        if tq_text:
            try:
                total_qty = float(tq_text)
                if total_qty <= 0:
                    raise ValueError
            except ValueError:
                QMessageBox.warning(self, "خطأ", "الكمية الإجمالية يجب أن تكون رقماً موجباً")
                return None, None, None
        else:
            total_qty = None

        return name, price, total_qty

    def _reset(self):
        self.inp_name.clear()
        self.inp_price.clear()
        self.inp_total_qty.clear()
        self.cmb_category.setCurrentIndex(0)
        self._update_hint()
        self.exit_edit_mode("─── إضافة خامة جديدة ───")


# ══════════════════════════════════════════════════════════
# جدول الخامات
# ══════════════════════════════════════════════════════════

class _TablePanel(QWidget):
    def __init__(self, conn, input_panel: _InputPanel, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self._input_panel = input_panel
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(12, 8, 12, 12)

        root.addWidget(section_label("─── الخامات المحفوظة ───"))

        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "السعر الكلي", "الكمية الكلية", "سعر الوحدة"]
        )
        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(1, 160)
        self.table.setColumnWidth(2, 100)
        self.table.setColumnWidth(3, 85)
        self.table.setColumnWidth(4, 85)
        self.table.setColumnWidth(5, 90)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table)

        btn_edit = QPushButton("✏️  تعديل المحدد")
        btn_del  = danger_button("🗑️  حذف المحدد")
        for btn in (btn_edit, btn_del):
            btn.setMinimumHeight(30)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_edit, btn_del))

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر خامة من الجدول أولاً")
            return
        self._input_panel.load_for_edit(int(self.table.item(row, 0).text()))

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, "تنبيه", "اختر خامة أولاً")
            return
        item_id   = int(self.table.item(row, 0).text())
        item_name = self.table.item(row, 1).text()
        if self._input_panel.is_editing and self._input_panel._editing_id == item_id:
            self._input_panel._reset()
        if confirm_delete(self, item_name):
            delete_item(self.conn, item_id)
            bus.data_changed.emit()

    def _load(self):
        self.table.setRowCount(0)
        for r, row in enumerate(fetch_items_by_type(self.conn, "raw")):
            tq    = row["total_qty"]
            price = row["price"]
            # raw_unit_price تحسب سعر الوحدة مع مراعاة total_qty
            unit  = raw_unit_price(row)

            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(row["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(
                row["category_name"] if row["category_name"] else "—"
            ))
            self.table.setItem(r, 3, QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(
                str(tq) if tq is not None else "—"
            ))
            self.table.setItem(r, 5, QTableWidgetItem(f"{unit:.4f}"))


# ══════════════════════════════════════════════════════════
# تبويب الخامات الرئيسي
# ══════════════════════════════════════════════════════════

class _RawItemsTab(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        splitter = QSplitter(Qt.Vertical)
        splitter.setHandleWidth(6)
        splitter.setStyleSheet(_SPLITTER_STYLE)

        self._input = _InputPanel(conn)
        self._table = _TablePanel(conn, self._input)

        splitter.addWidget(self._input)
        splitter.addWidget(self._table)
        splitter.setSizes([300, 400])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.addWidget(splitter)


# ══════════════════════════════════════════════════════════
# التبويب الرئيسي
# ══════════════════════════════════════════════════════════

class RawTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.conn = get_connection()
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        tabs = QTabWidget()
        tabs.addTab(_RawItemsTab(self.conn),                  "📦  الخامات")
        tabs.addTab(CategoryManager(self.conn, scope="raw"),  "🏷️  التصنيفات")

        root.addWidget(tabs)

    def closeEvent(self, event):
        self.conn.close()
        super().closeEvent(event)