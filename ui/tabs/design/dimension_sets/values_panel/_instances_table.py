"""
ui/tabs/design/dimension_sets/values_panel/_instances_table.py
=====================================

"""


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, 
    QMessageBox, QFrame,
    QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from db.designs.dimension_sets_repo import (
    fetch_fields_for_set,
    fetch_instances_for_set, fetch_instance,
    delete_instance, duplicate_instance,
    fetch_instance_values
)
from ._instance_popup import _BTN_GHOST, _BTN_PRIMARY, _InstancePopup


_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_RED        = "#c62828"
_RED_LT     = "#fdecea"
_GRAY_BG    = "#f8f9fc"
_BORDER     = "#e0e7f3"
_TEXT       = "#1a2340"
_TEXT_MUTED = "#7a869a"


_BTN_DANGER = f"""
    QPushButton {{
        background: {_RED_LT};
        color: {_RED};
        border: 1.5px solid #ef9a9a;
        border-radius: 7px;
        padding: 5px 14px;
        font-size: 12px;
    }}
    QPushButton:hover {{ background: #ffcdd2; }}
"""
# ══════════════════════════════════════════════════════════
# جدول الـ Instances (يمين)
# ══════════════════════════════════════════════════════════

class _InstancesTable(QWidget):
    """
    يعرض instances المجموعة المختارة في جدول واضح.
    الأعمدة: الاسم + قيمة كل حقل.
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._fields = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        t_lay = QHBoxLayout(toolbar)
        t_lay.setContentsMargins(14, 10, 14, 10)
        t_lay.setSpacing(10)

        self.lbl_set_name = QLabel("اختر مجموعة مقاسات من القايمة")
        self.lbl_set_name.setStyleSheet(f"""
            font-weight: bold;
            font-size: 13px;
            color: {_TEXT};
            background: transparent;
        """)

        t_lay.addWidget(self.lbl_set_name, stretch=1)

        self.btn_add = QPushButton("➕  إضافة قيمة")
        self.btn_add.setStyleSheet(_BTN_PRIMARY)
        self.btn_add.setMinimumHeight(34)
        self.btn_add.setEnabled(False)
        self.btn_add.clicked.connect(self._add_instance)

        self.btn_edit = QPushButton("✏️  تعديل")
        self.btn_edit.setStyleSheet(_BTN_GHOST)
        self.btn_edit.setMinimumHeight(34)
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._edit_instance)

        self.btn_copy = QPushButton("📋  نسخ")
        self.btn_copy.setStyleSheet(_BTN_GHOST)
        self.btn_copy.setMinimumHeight(34)
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._copy_instance)

        self.btn_del = QPushButton("🗑️  حذف")
        self.btn_del.setStyleSheet(_BTN_DANGER)
        self.btn_del.setMinimumHeight(34)
        self.btn_del.setEnabled(False)
        self.btn_del.clicked.connect(self._delete_instance)

        t_lay.addWidget(self.btn_add)
        t_lay.addWidget(self.btn_edit)
        t_lay.addWidget(self.btn_copy)
        t_lay.addWidget(self.btn_del)

        root.addWidget(toolbar)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: white;
                alternate-background-color: #fafbff;
                gridline-color: {_BORDER};
                font-size: 12px;
                color: {_TEXT};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
            }}
            QTableWidget::item:selected {{
                background: {_BLUE_LIGHT};
                color: {_BLUE};
            }}
            QHeaderView::section {{
                background: {_GRAY_BG};
                color: {_TEXT_MUTED};
                font-weight: bold;
                font-size: 11px;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid {_BORDER};
                border-right: 1px solid {_BORDER};
            }}
        """)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.horizontalHeader().setMinimumSectionSize(60)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(lambda: self._edit_instance())
        root.addWidget(self.table, stretch=1)

        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_GRAY_BG};
            color: {_TEXT_MUTED};
            font-size: 10px;
            padding: 6px;
            border-top: 1px solid {_BORDER};
        """)
        root.addWidget(self._status_bar)

        self._empty_state = QFrame()
        self._empty_state.setStyleSheet("background: white; border: none;")
        e_lay = QVBoxLayout(self._empty_state)
        e_lay.setAlignment(Qt.AlignCenter)
        e_lbl = QLabel("📋")
        e_lbl.setAlignment(Qt.AlignCenter)
        e_lbl.setStyleSheet("font-size: 40px; background: transparent;")
        e_msg = QLabel("اختر مجموعة مقاسات لعرض قيمها")
        e_msg.setAlignment(Qt.AlignCenter)
        e_msg.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px; background: transparent;")
        e_hint = QLabel("اضغط على أي مجموعة من القايمة على اليسار")
        e_hint.setAlignment(Qt.AlignCenter)
        e_hint.setStyleSheet(f"color: #b0bec5; font-size: 11px; background: transparent;")
        e_lay.addWidget(e_lbl)
        e_lay.addSpacing(8)
        e_lay.addWidget(e_msg)
        e_lay.addWidget(e_hint)

        root.addWidget(self._empty_state)
        self.table.setVisible(False)
        self._status_bar.setVisible(False)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self.btn_add.setEnabled(True)

        try:
            ds = self.conn.execute(
                "SELECT name FROM dimension_sets WHERE id=?", (set_id,)
            ).fetchone()
            set_name = ds["name"] if ds else f"مجموعة #{set_id}"
        except Exception:
            set_name = f"مجموعة #{set_id}"
        self.lbl_set_name.setText(f"📐  {set_name}")

        self._fields = [
            f for f in fetch_fields_for_set(self.conn, set_id)
            if f["field_type"] == "number"
        ]
        self._empty_state.setVisible(False)
        self.table.setVisible(True)
        self._status_bar.setVisible(True)
        self._refresh_table()

    def _refresh_table(self):
        if not self._set_id:
            return

        prev_row = self.table.currentRow()
        self.table.blockSignals(True)
        self.table.clear()
        self.table.setRowCount(0)

        col_labels = ["الاسم"] + [f["label"] for f in self._fields]
        self.table.setColumnCount(len(col_labels))
        self.table.setHorizontalHeaderLabels(col_labels)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 160)
        for i in range(1, len(col_labels)):
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            self.table.setColumnWidth(i, 110)
        if len(col_labels) > 1:
            hh.setSectionResizeMode(len(col_labels) - 1, QHeaderView.Stretch)

        instances = fetch_instances_for_set(self.conn, self._set_id)
        for inst in instances:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 42)

            name = inst["name"].strip() if inst["name"].strip() else f"مجموعة #{inst['id']}"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, inst["id"])
            name_item.setFont(QFont("", -1, QFont.Bold))
            name_item.setForeground(QColor(_BLUE))
            self.table.setItem(r, 0, name_item)

            values = fetch_instance_values(self.conn, inst["id"])
            for ci, f in enumerate(self._fields, start=1):
                val_info = values.get(f["id"], {})
                val = val_info.get("value_num")
                unit = f["unit"] or ""
                if val is not None:
                    txt = f"{val:g}  {unit}".strip()
                else:
                    txt = "—"
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if val is None:
                    item.setForeground(QColor(_TEXT_MUTED))
                self.table.setItem(r, ci, item)

        self.table.blockSignals(False)

        cnt = self.table.rowCount()
        self._status_bar.setText(f"{cnt} مجموعة قيم  ·  انقر مرتين للتعديل")

        if prev_row >= 0 and prev_row < cnt:
            self.table.selectRow(prev_row)

        self._update_action_btns()

    def _selected_instance_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        self._update_action_btns()

    def _update_action_btns(self):
        has_sel = self._selected_instance_id() is not None
        self.btn_edit.setEnabled(has_sel)
        self.btn_copy.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel)

    def _add_instance(self):
        if not self._set_id:
            return
        popup = _InstancePopup(self.conn, self._set_id, parent=self)
        popup.saved.connect(self._on_saved)
        popup.exec_()

    def _edit_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        popup = _InstancePopup(self.conn, self._set_id,
                                instance_id=iid, parent=self)
        popup.saved.connect(self._on_saved)
        popup.exec_()

    def _copy_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        inst = fetch_instance(self.conn, iid)
        src_name = inst["name"] if inst else ""
        name, ok = QInputDialog.getText(
            self, "نسخ مجموعة القيم",
            "اسم النسخة الجديدة:",
            text=f"{src_name} (نسخة)" if src_name else "نسخة جديدة"
        )
        if ok:
            duplicate_instance(self.conn, iid, name.strip())
            self._refresh_table()

    def _delete_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        inst = fetch_instance(self.conn, iid)
        name = inst["name"] if inst and inst["name"] else f"مجموعة #{iid}"
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف «{name}» وكل قيمها؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_instance(self.conn, iid)
            self._refresh_table()

    def _on_saved(self, instance_id: int):
        self._refresh_table()
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == instance_id:
                self.table.selectRow(r)
                break

    def clear(self):
        self._set_id = None
        self._fields = []
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.table.setVisible(False)
        self._status_bar.setVisible(False)
        self._empty_state.setVisible(True)
        self.lbl_set_name.setText("اختر مجموعة مقاسات من القايمة")
        self.btn_add.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_copy.setEnabled(False)
        self.btn_del.setEnabled(False)

