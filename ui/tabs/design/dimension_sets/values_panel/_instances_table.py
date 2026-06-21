"""
ui/tabs/design/dimension_sets/values_panel/_instances_table.py
=====================================
مع دعم تغيير حجم الخط ديناميكياً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel,
    QMessageBox, QFrame,
    QInputDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

from db.designs.dimension_sets_repo import (
    fetch_fields_for_set,
    fetch_instances_for_set, fetch_instance,
    delete_instance, duplicate_instance,
    fetch_instance_values,
)
from ._instance_popup import _InstancePopup
from ui.font import get_font_size, fs, FS_XL
from ui.widgets.core.i18n import tr
from ui.theme import _C

_BLUE       = _C["acc_type_asset"]
_BLUE_LIGHT = _C["accent_light"]
_RED        = _C["danger"]
_RED_LT     = _C["danger_bg"]
_GRAY_BG    = _C["bg_surface"]
_BORDER     = _C["border"]
_TEXT       = _C["text_primary"]
_TEXT_MUTED = _C["text_muted"]


def _btn_danger_ss(base: int) -> str:
    return (
        f"QPushButton {{"
        f"  background: {_C['danger_bg']}; color: {_C['danger']};"
        f"  border: 1.5px solid {_C['danger_border']}; border-radius: 7px;"
        f"  padding: 5px 14px; font-size: {fs(base,0)}pt;"
        f"}}"
        f"QPushButton:hover {{ background: {_C['danger_bg']}; border-color: {_C['danger']}; }}"
    )


def _btn_ghost_ss(base: int) -> str:
    return (
        f"QPushButton {{"
        f"  background: {_C['bg_input']}; color: {_C['accent']};"
        f"  border: 1.5px solid {_C['accent_light']}; border-radius: 7px;"
        f"  padding: 5px 14px; font-size: {fs(base,0)}pt;"
        f"}}"
        f"QPushButton:hover {{ background: {_C['accent_light']}; }}"
    )


def _btn_primary_ss(base: int) -> str:
    return (
        f"QPushButton {{"
        f"  background: {_C['accent']}; color: {_C['accent_text']};"
        f"  border: none; border-radius: 7px;"
        f"  padding: 6px 18px; font-weight: bold; font-size: {fs(base,0)}pt;"
        f"}}"
        f"QPushButton:hover  {{ background: {_C['accent_hover']}; }}"
        f"QPushButton:disabled {{ background: {_C['border_med']}; }}"
    )


class _InstancesTable(QWidget):
    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._fields = []
        self._build()

    def _on_font_changed(self, size: int):
        """يُستدعى من _ValuesPanel عند تغيير حجم الخط."""
        base = size

        # تحديث الـ toolbar label
        self._lbl_set_name.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_TEXT};
            background: transparent;
        """)

        # تحديث الأزرار
        self.btn_add.setStyleSheet(_btn_primary_ss(base))
        self.btn_edit.setStyleSheet(_btn_ghost_ss(base))
        self.btn_copy.setStyleSheet(_btn_ghost_ss(base))
        self.btn_del.setStyleSheet(_btn_danger_ss(base))

        # تحديث الجدول
        self.table.setStyleSheet(self._table_ss())

        # تحديث الـ status bar
        self._status_bar.setStyleSheet(f"""
            background: {_GRAY_BG};
            color: {_TEXT_MUTED};
            font-size: {fs(base,-1)}pt;
            padding: 6px;
            border-top: 1px solid {_BORDER};
        """)

    def _table_ss(self) -> str:
        base = get_font_size()
        return f"""
            QTableWidget {{
                border: none;
                background: {_C['bg_input']};
                alternate-background-color: {_C['bg_surface']};
                gridline-color: {_C['border']};
                font-size: {fs(base,0)}pt;
                color: {_C['text_primary']};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
            }}
            QTableWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent']};
            }}
            QHeaderView::section {{
                background: {_C['bg_surface']};
                color: {_C['text_muted']};
                font-weight: bold;
                font-size: {fs(base,-1)}pt;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid {_C['border']};
                border-right: 1px solid {_C['border']};
            }}
        """

    def _build(self):
        base = get_font_size()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border-bottom: 1px solid {_C['border']};
            }}
        """)
        t_lay = QHBoxLayout(toolbar)
        t_lay.setContentsMargins(14, 10, 14, 10)
        t_lay.setSpacing(10)

        self._lbl_set_name = QLabel(tr("dim_inst_table_placeholder"))
        self._lbl_set_name.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_TEXT};
            background: transparent;
        """)
        t_lay.addWidget(self._lbl_set_name, stretch=1)

        self.btn_add = QPushButton(tr("dim_inst_add_btn"))
        self.btn_add.setStyleSheet(_btn_primary_ss(base))
        self.btn_add.setMinimumHeight(34)
        self.btn_add.setEnabled(False)
        self.btn_add.clicked.connect(self._add_instance)

        self.btn_edit = QPushButton(tr("dim_inst_edit_btn"))
        self.btn_edit.setStyleSheet(_btn_ghost_ss(base))
        self.btn_edit.setMinimumHeight(34)
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._edit_instance)

        self.btn_copy = QPushButton(tr("dim_inst_copy_btn"))
        self.btn_copy.setStyleSheet(_btn_ghost_ss(base))
        self.btn_copy.setMinimumHeight(34)
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._copy_instance)

        self.btn_del = QPushButton(tr("btn_delete"))
        self.btn_del.setStyleSheet(_btn_danger_ss(base))
        self.btn_del.setMinimumHeight(34)
        self.btn_del.setEnabled(False)
        self.btn_del.clicked.connect(self._delete_instance)

        t_lay.addWidget(self.btn_add)
        t_lay.addWidget(self.btn_edit)
        t_lay.addWidget(self.btn_copy)
        t_lay.addWidget(self.btn_del)

        root.addWidget(toolbar)

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setStyleSheet(self._table_ss())
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.horizontalHeader().setMinimumSectionSize(60)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(lambda: self._edit_instance())
        root.addWidget(self.table, stretch=1)

        # ── Status Bar ──
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_GRAY_BG};
            color: {_TEXT_MUTED};
            font-size: {fs(base,-1)}pt;
            padding: 6px;
            border-top: 1px solid {_BORDER};
        """)
        root.addWidget(self._status_bar)

        # ── Empty State ──
        self._empty_state = QFrame()
        self._empty_state.setStyleSheet(f"background: {_C['bg_input']}; border: none;")
        e_lay = QVBoxLayout(self._empty_state)
        e_lay.setAlignment(Qt.AlignCenter)
        e_lbl = QLabel(tr("dim_inst_empty_icon"))
        e_lbl.setAlignment(Qt.AlignCenter)
        e_lbl.setStyleSheet(f"font-size: {fs(FS_XL, +24)}pt; background: transparent;")
        e_msg = QLabel(tr("dim_inst_table_placeholder"))
        e_msg.setAlignment(Qt.AlignCenter)
        e_msg.setStyleSheet(f"color: {_C['text_muted']}; font-size: {fs(base,+1)}pt; background: transparent;")
        e_hint = QLabel(tr("dim_sets_empty_select_hint"))
        e_hint.setAlignment(Qt.AlignCenter)
        e_hint.setStyleSheet(f"color: {_C['border_med']}; font-size: {fs(base,-1)}pt; background: transparent;")
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
            set_name = ds["name"] if ds else tr("dim_unnamed_set_fallback").format(id=set_id)
        except Exception:
            set_name = tr("dim_unnamed_set_fallback").format(id=set_id)
        self._lbl_set_name.setText(f"{tr('dim_sets_set_icon')}  {set_name}")

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

        col_labels = [tr("dim_inst_col_name")] + [f["label"] for f in self._fields]
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
        base = get_font_size()
        for inst in instances:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, fs(base, 0) * 3 + 6)

            name = inst["name"].strip() if inst["name"].strip() else tr("dim_unnamed_set_fallback").format(id=inst['id'])
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
                txt  = f"{val:g}  {unit}".strip() if val is not None else tr("dim_value_empty")
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if val is None:
                    item.setForeground(QColor(_TEXT_MUTED))
                self.table.setItem(r, ci, item)

        self.table.blockSignals(False)

        cnt = self.table.rowCount()
        self._status_bar.setText(tr("dim_inst_table_status").format(count=cnt))

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
            self, tr("dim_inst_copy_title"),
            tr("dim_inst_copy_label"),
            text=tr("dim_inst_copy_default").format(name=src_name) if src_name else ""
        )
        if ok:
            duplicate_instance(self.conn, iid, name.strip())
            self._refresh_table()

    def _delete_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        inst = fetch_instance(self.conn, iid)
        name = inst["name"] if inst and inst["name"] else f"#{iid}"
        if QMessageBox.question(
            self, tr("confirm_delete"),
            tr("dim_inst_delete_confirm").format(name=name),
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
        self._lbl_set_name.setText(tr("dim_inst_table_placeholder"))
        self.btn_add.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_copy.setEnabled(False)
        self.btn_del.setEnabled(False)