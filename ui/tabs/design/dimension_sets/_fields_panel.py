"""
ui/tabs/design/dimension_sets/_fields_panel.py
=====================================
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem, QPushButton, QLabel,
    QMessageBox, QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_BASE
from services.design.dimension_set_service import DimensionSetService
from ._field_dialog import _FieldDialog
from ui.widgets.components.button   import make_btn

from ui.widgets.tables.tables       import make_table

from ui.widgets.dialogs.confirm      import confirm_delete
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    DIM_FIELD_PANEL_ROOT_SPACING, DIM_FIELD_PANEL_COL_ORDER_W, DIM_FIELD_PANEL_COL_NAME_W,
    DIM_FIELD_PANEL_COL_UNIT_W, DIM_FIELD_PANEL_COL_TYPE_W, DIM_FIELD_PANEL_COL_REQ_W,
    DIM_FIELD_PANEL_COL_DEP_W, DIM_FIELD_PANEL_BTN_H,
)

class _FieldsPanel(QWidget, WidgetMixin):
    """محرر حقول مجموعة مقاسات — إضافة / تعديل / حذف / ترتيب."""

    fields_changed = pyqtSignal()
    set_selected   = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._svc    = DimensionSetService(conn)
        self._set_id = None
        self._build()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        self._hdr.setStyleSheet(f"font-weight: bold; color: {_C['accent']}; font-size: {FS_BASE}pt;")
        # [إصلاح dark-theme] الجدول (نفس مشكلة _sets_panel.py)
        from ui.widgets.tables.tables import refresh_table_styles
        refresh_table_styles(self)
        # [إصلاح dark-theme] الأزرار المبنية عبر make_btn() بتاخد الستايل
        # وقت الإنشاء بس — refresh_visible_buttons() موجودة في button.py
        # بالظبط لهذا الغرض لكن محدش كان بينادیها من هنا.
        from ui.widgets.components.button import refresh_visible_buttons
        refresh_visible_buttons(self)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(DIM_FIELD_PANEL_ROOT_SPACING)

        hdr = self._hdr = QLabel(tr("dim_field_panel_title"))
        root.addWidget(hdr)

        self.table = make_table(
            [tr("dim_field_col_order"), tr("dim_field_col_name_en"), tr("dim_field_col_label"),
             tr("dim_field_col_unit"), tr("dim_field_col_type"), tr("dim_field_col_required"),
             tr("dim_field_col_depends")],
            stretch_col=2
        )
        self.table.setColumnWidth(0, DIM_FIELD_PANEL_COL_ORDER_W)
        self.table.setColumnWidth(1, DIM_FIELD_PANEL_COL_NAME_W)
        self.table.setColumnWidth(3, DIM_FIELD_PANEL_COL_UNIT_W)
        self.table.setColumnWidth(4, DIM_FIELD_PANEL_COL_TYPE_W)
        self.table.setColumnWidth(5, DIM_FIELD_PANEL_COL_REQ_W)
        self.table.setColumnWidth(6, DIM_FIELD_PANEL_COL_DEP_W)
        root.addWidget(self.table)

        btn_add  = make_btn(tr("dim_field_add_btn"),       style="success")
        btn_edit = make_btn(tr("category_edit"),            style="normal")
        btn_del  = make_btn(tr("category_delete"),          style="danger")
        btn_up   = make_btn(tr("dim_field_move_up_btn"),   style="ghost", fixed_size=False)
        btn_dn   = make_btn(tr("dim_field_move_down_btn"), style="ghost", fixed_size=False)
        
        for btn in (btn_add, btn_edit, btn_del, btn_up, btn_dn):
            btn.setMinimumHeight(DIM_FIELD_PANEL_BTN_H)


        btn_add.clicked.connect(self._add_field)
        btn_edit.clicked.connect(self._edit_field)
        btn_del.clicked.connect(self._del_field)
        btn_up.clicked.connect(self._move_up)
        btn_dn.clicked.connect(self._move_down)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_add)
        btn_row.addWidget(btn_edit)
        btn_row.addWidget(btn_del)
        btn_row.addStretch()
        btn_row.addWidget(btn_up)
        btn_row.addWidget(btn_dn)
        root.addLayout(btn_row)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self._refresh()
        self.set_selected.emit(set_id)

    def clear(self):
        self._set_id = None
        self.table.setRowCount(0)

    def _refresh(self):
        if self._set_id is None:
            self.table.setRowCount(0)
            return
        self.table.setRowCount(0)
        fields = self._svc.list_fields(self._set_id)
        for f in fields:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(f["sort_order"] + 1)))
            self.table.setItem(r, 1, QTableWidgetItem(f["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(f["label"]))
            self.table.setItem(r, 3, QTableWidgetItem(f["unit"] or tr("dim_sets_list_default_unit")))
            self.table.setItem(r, 4, QTableWidgetItem(
                tr("dim_field_type_number") if f["field_type"] == "number" else tr("dim_field_type_text")
            ))
            self.table.setItem(r, 5, QTableWidgetItem(tr("dim_field_required_yes") if f["required"] else ""))

            # ── عمود الاعتمادية — sqlite3.Row لا يدعم .get() ──
            dep_text = ""
            try:
                src_field_id = f["source_field_id"]
            except Exception:
                src_field_id = None

            if src_field_id:
                try:
                    dep_offset = f["dep_offset"] or 0
                except Exception:
                    dep_offset = 0
                sign    = "+" if dep_offset >= 0 else ""
                src_lbl = ""
                src_set = ""
                try:
                    src_lbl = f["source_label"] or ""
                except Exception:
                    pass
                try:
                    src_set = f["source_set_name"] or ""
                except Exception:
                    pass

                dep_text = (
                    f"{src_lbl} ({src_set}) {sign}{dep_offset:g}"
                    if src_set else
                    f"{src_lbl} {sign}{dep_offset:g}"
                )

            self.table.setItem(r, 6, QTableWidgetItem(dep_text))
            self.table.item(r, 0).setData(Qt.UserRole, f["id"])

    def _selected_field_id(self):
        row  = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
        return item.data(Qt.UserRole) if item else None

    def _add_field(self):
        if self._set_id is None:
            QMessageBox.information(self, tr("info"), tr("dim_field_select_first"))
            return
        dlg = _FieldDialog(self.conn, self._set_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh()
            self.fields_changed.emit()

    def _edit_field(self):
        fid = self._selected_field_id()
        if fid is None:
            QMessageBox.information(self, tr("info"), tr("dim_field_select_first"))
            return
        f = self._svc.get_field(fid)
        dlg = _FieldDialog(self.conn, self._set_id, field_data=f, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh()
            self.fields_changed.emit()

    def _del_field(self):
        fid = self._selected_field_id()
        if fid is None:
            QMessageBox.information(self, tr("info"), tr("dim_field_select_first"))
            return
        f = self._svc.get_field(fid)
        if f and confirm_delete(self, f["label"]):
            self._svc.delete_field(fid)
            self._refresh()
            self.fields_changed.emit()

    def _move_up(self):   self._move(-1)
    def _move_down(self): self._move(1)

    def _move(self, direction: int):
        row     = self.table.currentRow()
        new_row = row + direction
        if new_row < 0 or new_row >= self.table.rowCount():
            return
        ids = [
            self.table.item(r, 0).data(Qt.UserRole)
            for r in range(self.table.rowCount())
        ]
        ids[row], ids[new_row] = ids[new_row], ids[row]
        self._svc.reorder_fields(self._set_id, ids)
        self._refresh()
        self.table.selectRow(new_row)
        self.fields_changed.emit()