"""
ui/tabs/companies/shared_items_manager.py
==========================================
SharedItemsManagerDialog — نافذة إدارة العناصر المشتركة بين الشركات.

الميزات:
  - عرض كل العناصر المشتركة مقسمة بالنوع
  - إضافة عنصر جديد (خامة / ماكينة / عملية عمالة / عملية تشغيل)
  - تعديل بيانات عنصر → يتزامن فوراً في كل الشركات
  - ربط / فك ربط الشركات بالعنصر
  - حذف العنصر المشترك

التصميم:
  - Splitter: قائمة العناصر (يسار) | لوحة التفاصيل (يمين)
  - لوحة التفاصيل: بيانات العنصر + قائمة الشركات المشتركة
"""

import json

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QWidget, QLabel, QPushButton, QLineEdit,
    QDoubleSpinBox, QComboBox, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QMessageBox, QFrame, QTabWidget,
    QCheckBox, QGroupBox, QFormLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor

from db.companies.shared_items_repo import (
    fetch_all_shared_items, fetch_shared_item,
    insert_shared_item, update_shared_item, delete_shared_item,
    fetch_linked_companies, set_linked_companies,
    get_item_data,
)
from db.companies.companies_repo import fetch_all_companies
from ui.events import bus

_TYPE_LABELS = {
    "raw":        "🧱 خامة",
    "machine":    "🖥️ ماكينة",
    "labor_op":   "👷 عملية عمالة",
    "machine_op": "⚙️ عملية تشغيل",
}

_TYPE_COLORS = {
    "raw":        "#1565c0",
    "machine":    "#6a1b9a",
    "labor_op":   "#2e7d32",
    "machine_op": "#e65100",
}

_SHARED_BG = "#e8f5e9"
_SHARED_FG = "#2e7d52"


def _spin(max_=9_999_999, dec=2) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


class _DataForm(QWidget):
    """فورم بيانات العنصر حسب نوعه."""

    changed = pyqtSignal()  # يُطلق عند أي تغيير

    def __init__(self, parent=None):
        super().__init__(parent)
        self._shared_type = None
        self._build()

    def _build(self):
        self._lay = QFormLayout(self)
        self._lay.setSpacing(8)
        self._lay.setLabelAlignment(Qt.AlignRight)
        self._fields: dict = {}

    def load(self, shared_type: str, data: dict):
        """يعيد بناء الفورم حسب نوع العنصر."""
        self._shared_type = shared_type
        # حذف كل الصفوف القديمة
        while self._lay.rowCount():
            self._lay.removeRow(0)
        self._fields.clear()

        if shared_type == "raw":
            sp_price = _spin()
            sp_price.setValue(data.get("price", 0.0))
            sp_price.valueChanged.connect(self.changed.emit)
            sp_qty = _spin()
            sp_qty.setSpecialValueText("—")
            tq = data.get("total_qty")
            sp_qty.setValue(float(tq) if tq else 0.0)
            sp_qty.valueChanged.connect(self.changed.emit)
            self._lay.addRow("السعر الكلي :", sp_price)
            self._lay.addRow("الكمية الكلية :", sp_qty)
            self._fields["price"]     = sp_price
            self._fields["total_qty"] = sp_qty

        elif shared_type == "machine":
            sp_hour = _spin()
            sp_hour.setValue(data.get("rate_per_hour", 0.0))
            sp_hour.valueChanged.connect(self.changed.emit)
            sp_unit = _spin()
            sp_unit.setValue(data.get("rate_per_unit", 0.0))
            sp_unit.valueChanged.connect(self.changed.emit)
            self._lay.addRow("جنيه / ساعة :", sp_hour)
            self._lay.addRow("جنيه / وحدة :", sp_unit)
            self._fields["rate_per_hour"] = sp_hour
            self._fields["rate_per_unit"] = sp_unit

        elif shared_type == "labor_op":
            sp_min = _spin(99_999, 2)
            sp_min.setValue(data.get("minutes", 0.0))
            sp_min.valueChanged.connect(self.changed.emit)
            self._lay.addRow("الوقت (دقيقة) :", sp_min)
            self._fields["minutes"] = sp_min

        elif shared_type == "machine_op":
            inp_machine = QLineEdit()
            inp_machine.setPlaceholderText("اسم الماكينة...")
            inp_machine.setText(data.get("machine_name", ""))
            inp_machine.setMinimumHeight(30)
            inp_machine.textChanged.connect(self.changed.emit)

            cmb_mode = QComboBox()
            cmb_mode.addItem("⏱ وقت (time)", "time")
            cmb_mode.addItem("📦 وحدة (unit)", "unit")
            idx = 0 if data.get("mode", "time") == "time" else 1
            cmb_mode.setCurrentIndex(idx)
            cmb_mode.currentIndexChanged.connect(self.changed.emit)

            sp_val = _spin()
            sp_val.setValue(data.get("value", 0.0))
            sp_val.valueChanged.connect(self.changed.emit)

            sp_rh = _spin()
            sp_rh.setValue(data.get("rate_per_hour", 0.0))
            sp_rh.valueChanged.connect(self.changed.emit)

            sp_ru = _spin()
            sp_ru.setValue(data.get("rate_per_unit", 0.0))
            sp_ru.valueChanged.connect(self.changed.emit)

            self._lay.addRow("اسم الماكينة :", inp_machine)
            self._lay.addRow("وضع الحساب :",   cmb_mode)
            self._lay.addRow("القيمة :",        sp_val)
            self._lay.addRow("جنيه / ساعة :",  sp_rh)
            self._lay.addRow("جنيه / وحدة :",  sp_ru)
            self._fields["machine_name"] = inp_machine
            self._fields["mode"]         = cmb_mode
            self._fields["value"]        = sp_val
            self._fields["rate_per_hour"] = sp_rh
            self._fields["rate_per_unit"] = sp_ru

    def collect(self) -> dict:
        """يجمع بيانات الفورم الحالية."""
        if self._shared_type == "raw":
            tq_val = self._fields["total_qty"].value()
            return {
                "price":     self._fields["price"].value(),
                "total_qty": tq_val if tq_val > 0 else None,
            }
        elif self._shared_type == "machine":
            return {
                "rate_per_hour": self._fields["rate_per_hour"].value(),
                "rate_per_unit": self._fields["rate_per_unit"].value(),
            }
        elif self._shared_type == "labor_op":
            return {"minutes": self._fields["minutes"].value()}
        elif self._shared_type == "machine_op":
            return {
                "machine_name": self._fields["machine_name"].text().strip(),
                "mode":         self._fields["mode"].currentData(),
                "value":        self._fields["value"].value(),
                "rate_per_hour": self._fields["rate_per_hour"].value(),
                "rate_per_unit": self._fields["rate_per_unit"].value(),
            }
        return {}

    def clear(self):
        while self._lay.rowCount():
            self._lay.removeRow(0)
        self._fields.clear()
        self._shared_type = None


class _CompaniesPanel(QWidget):
    """لوحة تحديد الشركات المشتركة في عنصر."""

    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self._central = central_conn
        self._shared_id: int | None = None
        self._checkboxes: dict[int, QCheckBox] = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(4)

        lbl = QLabel("الشركات المشتركة في هذا العنصر:")
        lbl.setStyleSheet("font-weight:bold; color:#333;")
        root.addWidget(lbl)

        self._list_widget = QWidget()
        self._list_lay    = QVBoxLayout(self._list_widget)
        self._list_lay.setSpacing(4)
        self._list_lay.setContentsMargins(4, 4, 4, 4)
        root.addWidget(self._list_widget, stretch=1)

        hint = QLabel("✅ ضع علامة على الشركات التي تريد مشاركة هذا العنصر معها")
        hint.setStyleSheet(
            "color:#666; font-size:10px; "
            "background:#f0f4ff; border-radius:4px; padding:4px 8px;"
        )
        hint.setWordWrap(True)
        root.addWidget(hint)

    def load(self, shared_id: int):
        """يحمل قائمة الشركات مع تحديد المشتركة منها."""
        self._shared_id = shared_id

        # مسح القديم
        for i in reversed(range(self._list_lay.count())):
            item = self._list_lay.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()

        try:
            all_companies  = fetch_all_companies(self._central)
            linked_ids     = {
                r["id"] for r in fetch_linked_companies(self._central, shared_id)
            }
        except Exception:
            all_companies = []
            linked_ids    = set()

        for company in all_companies:
            cb = QCheckBox(company["name"])
            cb.setChecked(company["id"] in linked_ids)
            color = company["color"] or "#1565c0"
            cb.setStyleSheet(f"""
                QCheckBox {{ color: #333; padding: 4px; }}
                QCheckBox::indicator:checked {{ background: {color}; border-color: {color}; }}
            """)
            self._checkboxes[company["id"]] = cb
            self._list_lay.addWidget(cb)

        self._list_lay.addStretch()

    def get_selected_company_ids(self) -> list[int]:
        return [cid for cid, cb in self._checkboxes.items() if cb.isChecked()]

    def save(self, shared_id: int):
        """يحفظ ربط الشركات."""
        try:
            set_linked_companies(self._central, shared_id, self.get_selected_company_ids())
        except Exception as e:
            print(f"[_CompaniesPanel] save error: {e}")

    def clear(self):
        for i in reversed(range(self._list_lay.count())):
            item = self._list_lay.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()
        self._shared_id = None


class SharedItemsManagerDialog(QDialog):
    """
    نافذة إدارة العناصر المشتركة بين الشركات.

    تُفتح من:
      - زر "العناصر المشتركة" في الـ sidebar
      - أزرار "تعديل المشترك" في الجداول المحلية
    """

    items_changed = pyqtSignal()

    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self._central   = central_conn
        self._editing_id: int | None = None
        self.setWindowTitle("🔗  إدارة العناصر المشتركة")
        self.setMinimumSize(920, 620)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()
        self._load_list()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header ──
        header = QLabel("  🔗  إدارة العناصر المشتركة بين الشركات")
        header.setFixedHeight(46)
        header.setStyleSheet("""
            QLabel {
                background: #1e1d1a;
                color: #e8e6e1;
                font-size: 14px;
                font-weight: bold;
                padding-right: 16px;
                border-bottom: 2px solid #2e7d52;
            }
        """)
        root.addWidget(header)

        # ── Body: Splitter ──
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setStyleSheet("QSplitter::handle { background: #ddd; }")

        # ── الجانب الأيمن: قائمة العناصر ──
        left_panel = QWidget()
        left_panel.setFixedWidth(300)
        left_panel.setStyleSheet("background:#fafafa; border-left:1px solid #e0e0e0;")
        left_lay = QVBoxLayout(left_panel)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(0)

        # شريط فلتر النوع
        filter_bar = QWidget()
        filter_bar.setStyleSheet("background:#f0f0f0; border-bottom:1px solid #e0e0e0;")
        filter_lay = QHBoxLayout(filter_bar)
        filter_lay.setContentsMargins(8, 6, 8, 6)
        filter_lay.setSpacing(4)

        self._cmb_type = QComboBox()
        self._cmb_type.addItem("الكل", None)
        for k, v in _TYPE_LABELS.items():
            self._cmb_type.addItem(v, k)
        self._cmb_type.currentIndexChanged.connect(self._load_list)
        self._cmb_type.setMinimumHeight(30)
        filter_lay.addWidget(QLabel("النوع:"))
        filter_lay.addWidget(self._cmb_type, stretch=1)
        left_lay.addWidget(filter_bar)

        self._items_table = QTableWidget()
        self._items_table.setColumnCount(2)
        self._items_table.setHorizontalHeaderLabels(["النوع", "الاسم"])
        self._items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
        self._items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self._items_table.setColumnWidth(0, 70)
        self._items_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._items_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._items_table.setAlternatingRowColors(True)
        self._items_table.setStyleSheet("border:none;")
        self._items_table.itemSelectionChanged.connect(self._on_select)
        left_lay.addWidget(self._items_table, stretch=1)

        btn_new = QPushButton("➕  عنصر مشترك جديد")
        btn_new.setMinimumHeight(36)
        btn_new.setStyleSheet("""
            QPushButton {
                background: #2e7d52; color: white;
                border: none; font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover { background: #1b5e38; }
        """)
        btn_new.clicked.connect(self._new_item)
        left_lay.addWidget(btn_new)

        splitter.addWidget(left_panel)

        # ── الجانب الأيسر: لوحة التفاصيل ──
        right_panel = QWidget()
        right_panel.setStyleSheet("background:white;")
        right_lay = QVBoxLayout(right_panel)
        right_lay.setContentsMargins(16, 12, 16, 12)
        right_lay.setSpacing(10)

        self._lbl_mode = QLabel("اختر عنصراً أو أنشئ واحداً جديداً")
        self._lbl_mode.setStyleSheet(
            "font-weight:bold; color:#2e7d52; font-size:13px;"
        )
        right_lay.addWidget(self._lbl_mode)

        # ── اسم العنصر + النوع ──
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        lbl_name = QLabel("الاسم:")
        lbl_name.setStyleSheet("font-weight:bold;")
        self._inp_name = QLineEdit()
        self._inp_name.setPlaceholderText("اسم العنصر المشترك...")
        self._inp_name.setMinimumHeight(32)

        lbl_type = QLabel("النوع:")
        lbl_type.setStyleSheet("font-weight:bold;")
        self._cmb_shared_type = QComboBox()
        self._cmb_shared_type.setMinimumHeight(32)
        self._cmb_shared_type.setFixedWidth(150)
        for k, v in _TYPE_LABELS.items():
            self._cmb_shared_type.addItem(v, k)
        self._cmb_shared_type.currentIndexChanged.connect(self._on_type_changed)

        name_row.addWidget(lbl_name)
        name_row.addWidget(self._inp_name, stretch=2)
        name_row.addWidget(lbl_type)
        name_row.addWidget(self._cmb_shared_type)
        right_lay.addLayout(name_row)

        # ── Tabs: بيانات العنصر | الشركات المشتركة ──
        detail_tabs = QTabWidget()
        detail_tabs.setStyleSheet("""
            QTabBar::tab:selected { color:#2e7d52; border-top:2px solid #2e7d52; }
        """)

        # Tab 1: بيانات العنصر
        self._data_form = _DataForm()
        data_scroll_w   = QWidget()
        data_scroll_lay = QVBoxLayout(data_scroll_w)
        data_scroll_lay.setContentsMargins(8, 8, 8, 8)
        data_scroll_lay.addWidget(self._data_form)
        data_scroll_lay.addStretch()
        detail_tabs.addTab(data_scroll_w, "📋  بيانات العنصر")

        # Tab 2: الشركات
        self._companies_panel = _CompaniesPanel(self._central)
        detail_tabs.addTab(self._companies_panel, "🏢  الشركات المشتركة")

        right_lay.addWidget(detail_tabs, stretch=1)

        # ── أزرار الحفظ / حذف ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        self._btn_save = QPushButton("💾  حفظ التغييرات")
        self._btn_save.setMinimumHeight(36)
        self._btn_save.setStyleSheet("""
            QPushButton {
                background: #2e7d52; color: white;
                border: none; border-radius: 6px;
                font-weight: bold; padding: 0 18px;
            }
            QPushButton:hover { background: #1b5e38; }
            QPushButton:disabled { background: #ccc; }
        """)
        self._btn_save.clicked.connect(self._save)

        self._btn_delete = QPushButton("🗑️  حذف العنصر")
        self._btn_delete.setMinimumHeight(36)
        self._btn_delete.setVisible(False)
        self._btn_delete.setStyleSheet("""
            QPushButton {
                background: #fdecea; color: #c62828;
                border: 1px solid #ef9a9a; border-radius: 6px;
                font-weight: bold; padding: 0 14px;
            }
            QPushButton:hover { background: #ffcdd2; }
        """)
        self._btn_delete.clicked.connect(self._delete)

        btn_cancel = QPushButton("✖  إغلاق")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.accept)

        btn_row.addWidget(self._btn_save)
        btn_row.addWidget(self._btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        right_lay.addLayout(btn_row)

        splitter.addWidget(right_panel)
        splitter.setSizes([300, 620])

        root_body = QVBoxLayout()
        root_body.setContentsMargins(0, 0, 0, 0)
        root_body.addWidget(splitter)

        container = QWidget()
        container.setLayout(root_body)
        root.addWidget(container, stretch=1)

        # تهيئة الفورم بالنوع الافتراضي
        self._data_form.load("raw", {})

    # ══════════════════════════════════════════════════════
    # تحميل القائمة
    # ══════════════════════════════════════════════════════

    def _load_list(self):
        selected_type = self._cmb_type.currentData()
        try:
            rows = fetch_all_shared_items(self._central, selected_type)
        except Exception:
            rows = []

        self._items_table.setRowCount(0)
        for row in rows:
            r = self._items_table.rowCount()
            self._items_table.insertRow(r)

            type_lbl = _TYPE_LABELS.get(row["shared_type"], row["shared_type"])
            color    = _TYPE_COLORS.get(row["shared_type"], "#333")

            type_item = QTableWidgetItem(type_lbl)
            type_item.setForeground(QColor(color))
            type_item.setData(Qt.UserRole, row["id"])
            self._items_table.setItem(r, 0, type_item)
            self._items_table.setItem(r, 1, QTableWidgetItem(row["name"]))

    # ══════════════════════════════════════════════════════
    # أحداث
    # ══════════════════════════════════════════════════════

    def _on_select(self):
        row = self._items_table.currentRow()
        if row == -1:
            return
        shared_id = self._items_table.item(row, 0).data(Qt.UserRole)
        self._load_for_edit(shared_id)

    def _load_for_edit(self, shared_id: int):
        """يحمل عنصراً موجوداً للتعديل — يُستدعى أيضاً من الجداول الخارجية."""
        try:
            row = fetch_shared_item(self._central, shared_id)
        except Exception:
            return
        if not row:
            return

        self._editing_id = shared_id
        self._inp_name.setText(row["name"])

        # ضبط نوع العنصر في الـ combo
        for i in range(self._cmb_shared_type.count()):
            if self._cmb_shared_type.itemData(i) == row["shared_type"]:
                self._cmb_shared_type.blockSignals(True)
                self._cmb_shared_type.setCurrentIndex(i)
                self._cmb_shared_type.blockSignals(False)
                break
        self._cmb_shared_type.setEnabled(False)  # لا يتغير النوع بعد الإنشاء

        data = {}
        try:
            data = json.loads(row["data"]) if row["data"] else {}
        except Exception:
            pass
        self._data_form.load(row["shared_type"], data)
        self._companies_panel.load(shared_id)

        type_label = _TYPE_LABELS.get(row["shared_type"], "")
        self._lbl_mode.setText(f"تعديل: {type_label}  «{row['name']}»")
        self._btn_delete.setVisible(True)
        self._btn_save.setEnabled(True)

        # تحديد الصف في القائمة لو الاستدعاء من خارج
        for r in range(self._items_table.rowCount()):
            if self._items_table.item(r, 0).data(Qt.UserRole) == shared_id:
                self._items_table.selectRow(r)
                break

    def _new_item(self):
        """إعادة تهيئة الفورم لإنشاء عنصر جديد."""
        self._editing_id = None
        self._inp_name.clear()
        self._cmb_shared_type.setEnabled(True)
        self._cmb_shared_type.setCurrentIndex(0)
        self._data_form.load(self._cmb_shared_type.currentData() or "raw", {})
        self._companies_panel.clear()
        self._lbl_mode.setText("─── عنصر مشترك جديد ───")
        self._btn_delete.setVisible(False)
        self._btn_save.setEnabled(True)
        self._items_table.clearSelection()
        self._inp_name.setFocus()

    def _on_type_changed(self):
        shared_type = self._cmb_shared_type.currentData() or "raw"
        self._data_form.load(shared_type, {})

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def _save(self):
        name = self._inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العنصر أولاً")
            return

        shared_type = self._cmb_shared_type.currentData() or "raw"
        data        = self._data_form.collect()

        try:
            if self._editing_id is not None:
                # تحديث
                update_shared_item(self._central, self._editing_id, name, data)
                sid = self._editing_id
            else:
                # إنشاء جديد
                sid = insert_shared_item(self._central, name, shared_type, data)
                self._editing_id = sid
                self._cmb_shared_type.setEnabled(False)
                self._btn_delete.setVisible(True)

            # حفظ ربط الشركات
            self._companies_panel.save(sid)

        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return

        self._load_list()
        self._lbl_mode.setText(
            f"✅ تم الحفظ — {_TYPE_LABELS.get(shared_type, '')}  «{name}»"
        )
        self.items_changed.emit()

        # مزامنة تلقائية — يُطلق bus.data_changed لكل الجداول
        try:
            from ui.events import bus as _bus
            _bus.data_changed.emit()
        except Exception:
            pass

    # ══════════════════════════════════════════════════════
    # حذف
    # ══════════════════════════════════════════════════════

    def _delete(self):
        if self._editing_id is None:
            return
        name = self._inp_name.text().strip() or f"ID:{self._editing_id}"
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف العنصر المشترك «{name}»؟\n"
            "سيُزال من كل الشركات المشتركة فيه.",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                delete_shared_item(self._central, self._editing_id)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            self._editing_id = None
            self._load_list()
            self._new_item()
            self.items_changed.emit()
            try:
                from ui.events import bus as _bus
                _bus.data_changed.emit()
            except Exception:
                pass