"""
ui/tabs/costing/shared/machine_op_rows_editor.py
=====================================
_OpRowsEditor — محرر صفوف عملية التشغيل.

[Refactor] ربط bus.theme_changed لتحديث stylesheet ديناميكياً.
[Refactor] استخدام MachineOpRowsService بدل machine_op_rows_repo مباشرة.
[Fix] استخدام emit_company_data_changed بدل bus.data_changed.emit()
      حسب توصية files_reference/models&services.md
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QGroupBox, QMessageBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from services.costing.machine_op_rows_service import MachineOpRowsService
from ui.theme          import _C
from ui.widgets.core.i18n     import tr
from ui.widgets.core.events   import emit_company_data_changed
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_XS, FS_SM, FS_BASE
from ui.constants import (
    OP_ROWS_ROOT_MARGIN_H, OP_ROWS_ROOT_MARGIN_T, OP_ROWS_ROOT_MARGIN_B,
    OP_ROWS_ROOT_SPACING, OP_ROWS_INP_MIN_H, OP_ROWS_SP_VALUE_W,
    OP_ROWS_SP_COUNT_W, OP_ROWS_PREVIEW_MIN_W, OP_ROWS_BTN_CANCEL_W,
    OP_ROWS_BTN_MIN_H, OP_ROWS_TABLE_MAX_H, OP_ROWS_TABLE_MIN_H,
    OP_ROWS_COL_VALUE_W, OP_ROWS_COL_COUNT_W, OP_ROWS_COL_COST_W,
    OP_ROWS_TOTAL_MIN_W, OP_ROWS_BTN_EDIT_MIN_H, OP_ROWS_GRP_BORDER_RADIUS,
    OP_ROWS_GRP_MARGIN_TOP, OP_ROWS_GRP_PAD_TOP, OP_ROWS_INNER_BORDER_RADIUS,
    OP_ROWS_INFO_PAD_V, OP_ROWS_INFO_PAD_H, OP_ROWS_INP_PAD_V,
    OP_ROWS_INP_PAD_H, OP_ROWS_TOTAL_PAD_V, OP_ROWS_TOTAL_PAD_H,
    OP_ROWS_FORM_SPACING, OP_ROWS_GRP_TITLE_PAD_H,
    OP_ROWS_SP_VALUE_MAX, OP_ROWS_SP_COUNT_MIN, OP_ROWS_SP_COUNT_MAX,
)



class _OpRowsEditor(QGroupBox, WidgetMixin):
    """
    محرر صفوف عملية التشغيل.

    الاستخدام:
        self._rows_editor = _OpRowsEditor(conn)
        self._rows_editor.load_op(op_id, machine_mode, rate_per_hour, rate_per_unit)
    """

    def __init__(self, conn, parent=None):
        super().__init__(f"{tr('op_rows_editor_icon')}{tr('op_rows_editor')}", parent)
        self.conn            = conn
        self._op_id          = None
        self._mode           = "time"
        self._rate_hour      = 0.0
        self._rate_unit      = 0.0
        self._editing_row_id = None
        self._build()
        self.setEnabled(False)
        self._init_widget_mixin(lang=False, data=False)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        self._apply_group_style()

        root = QVBoxLayout(self)
        root.setSpacing(OP_ROWS_ROOT_SPACING)
        root.setContentsMargins(OP_ROWS_ROOT_MARGIN_H, OP_ROWS_ROOT_MARGIN_T,
                                OP_ROWS_ROOT_MARGIN_H, OP_ROWS_ROOT_MARGIN_B)

        # ── شرح الوضع الحالي ──
        self.lbl_mode_info = QLabel(f"{tr('op_rows_time_icon')} {tr('calc_mode')}: {tr('by_time')}")
        self._apply_info_style()
        root.addWidget(self.lbl_mode_info)

        # ── فورم إضافة/تعديل صف ──
        form_row = QHBoxLayout()
        form_row.setSpacing(OP_ROWS_FORM_SPACING)

        lbl_label = QLabel(f"{tr('description')}:")
        self._lbl_label = lbl_label
        self.inp_label = QLineEdit()
        self.inp_label.setPlaceholderText(tr("row_description_placeholder"))
        self.inp_label.setMinimumHeight(OP_ROWS_INP_MIN_H)

        self.lbl_value = QLabel(f"{tr('value_minutes')}:")
        self.sp_value = QDoubleSpinBox()
        self.sp_value.setRange(0, OP_ROWS_SP_VALUE_MAX)
        self.sp_value.setDecimals(4)
        self.sp_value.setMinimumHeight(OP_ROWS_INP_MIN_H)
        self.sp_value.setFixedWidth(OP_ROWS_SP_VALUE_W)
        self.sp_value.valueChanged.connect(self._update_preview)

        lbl_count = QLabel(f"{tr('count')}:")
        self._lbl_count = lbl_count
        self.sp_count = QDoubleSpinBox()
        self.sp_count.setRange(OP_ROWS_SP_COUNT_MIN, OP_ROWS_SP_COUNT_MAX)
        self.sp_count.setDecimals(4)
        self.sp_count.setValue(1.0)
        self.sp_count.setMinimumHeight(OP_ROWS_INP_MIN_H)
        self.sp_count.setFixedWidth(OP_ROWS_SP_COUNT_W)
        self.sp_count.valueChanged.connect(self._update_preview)

        self.lbl_preview = QLabel(tr("preview_eq_dash"))
        self.lbl_preview.setMinimumWidth(OP_ROWS_PREVIEW_MIN_W)

        self.btn_add    = QPushButton(f"{tr('op_rows_add_icon')}{tr('add_row')}")
        self.btn_save   = QPushButton(f"{tr('op_rows_save_icon')}{tr('save')}")
        self.btn_cancel = QPushButton(tr("dismiss_icon"))
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.setFixedWidth(OP_ROWS_BTN_CANCEL_W)
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(OP_ROWS_BTN_MIN_H)

        self.btn_add.clicked.connect(self._add_row)
        self.btn_save.clicked.connect(self._save_edit)
        self.btn_cancel.clicked.connect(self._reset_form)

        form_row.addWidget(lbl_label)
        form_row.addWidget(self.inp_label, stretch=2)
        form_row.addWidget(self.lbl_value)
        form_row.addWidget(self.sp_value)
        form_row.addWidget(lbl_count)
        form_row.addWidget(self.sp_count)
        form_row.addWidget(self.lbl_preview)
        form_row.addWidget(self.btn_add)
        form_row.addWidget(self.btn_save)
        form_row.addWidget(self.btn_cancel)
        root.addLayout(form_row)

        # ── جدول الصفوف ──
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            tr("id_col"),
            tr("description"),
            tr("value"),
            tr("count"),
            tr("cost_per_unit"),
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(OP_ROWS_TABLE_MAX_H)
        self.table.setMinimumHeight(OP_ROWS_TABLE_MIN_H)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        hh.setSectionResizeMode(4, QHeaderView.Interactive)
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(2, OP_ROWS_COL_VALUE_W)
        self.table.setColumnWidth(3, OP_ROWS_COL_COUNT_W)
        self.table.setColumnWidth(4, OP_ROWS_COL_COST_W)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight)
        root.addWidget(self.table)

        # ── مجموع التكلفة ──
        total_row = QHBoxLayout()
        total_row.addStretch()
        lbl_total_lbl = QLabel(f"{tr('total_op_cost')}:")
        self._lbl_total_lbl = lbl_total_lbl
        self.lbl_total = QLabel(tr('amount_dash_placeholder'))
        self.lbl_total.setMinimumWidth(OP_ROWS_TOTAL_MIN_W)
        total_row.addWidget(lbl_total_lbl)
        total_row.addWidget(self.lbl_total)
        root.addLayout(total_row)

        # ── أزرار تعديل/حذف ──
        btn_row = QHBoxLayout()
        self.btn_edit_row = QPushButton(f"{tr('op_rows_edit_icon')}{tr('edit_row')}")
        self.btn_del_row  = QPushButton(f"{tr('op_rows_del_icon')}{tr('delete_row')}")
        for btn in (self.btn_edit_row, self.btn_del_row):
            btn.setMinimumHeight(OP_ROWS_BTN_EDIT_MIN_H)
        self.btn_edit_row.clicked.connect(self._edit_row)
        self.btn_del_row.clicked.connect(self._delete_row)
        btn_row.addWidget(self.btn_edit_row)
        btn_row.addWidget(self.btn_del_row)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._refresh_style()

    def _apply_group_style(self):
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {_C['orange']};
                border: 1px solid {_C['orange_border']};
                border-radius: {OP_ROWS_GRP_BORDER_RADIUS}px;
                margin-top: {OP_ROWS_GRP_MARGIN_TOP}px;
                padding-top: {OP_ROWS_GRP_PAD_TOP}px;
                background: {_C['warning_bg']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                padding: 0 {OP_ROWS_GRP_TITLE_PAD_H}px;
            }}
        """)

    def _apply_info_style(self):
        self.lbl_mode_info.setStyleSheet(
            f"font-size:{FS_XS}px; color:{_C['text_sec']}; font-weight:normal;"
            f"background:{_C['info_bg']}; border-radius:{OP_ROWS_INNER_BORDER_RADIUS}px;"
            f"padding:{OP_ROWS_INFO_PAD_V}px {OP_ROWS_INFO_PAD_H}px;"
            f"border:1px solid {_C['info_border']};"
        )

    def _refresh_style(self, _=None):
        """يُطبق الـ stylesheet عند تغيير الثيم."""
        self._apply_group_style()
        if hasattr(self, "lbl_mode_info"):
            self._apply_info_style()
        if hasattr(self, "inp_label"):
            self.inp_label.setStyleSheet(
                f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
                f"border-radius:{OP_ROWS_INNER_BORDER_RADIUS}px;"
                f"padding:{OP_ROWS_INP_PAD_V}px {OP_ROWS_INP_PAD_H}px;"
                f"color:{_C['text_primary']};"
            )
        if hasattr(self, "lbl_preview"):
            self.lbl_preview.setStyleSheet(
                f"color:{_C['orange']}; font-weight:bold; font-size:{FS_SM}px;"
            )
        if hasattr(self, "table"):
            self.table.setStyleSheet(
                f"QTableWidget {{ background:{_C['bg_surface']}; "
                f"color:{_C['text_primary']}; border:1px solid {_C['border']}; }}"
                f"QTableWidget::item:selected {{ background:{_C['accent_light']}; "
                f"color:{_C['accent']}; }}"
            )
        if hasattr(self, "lbl_total"):
            self.lbl_total.setStyleSheet(
                f"color:{_C['success']}; font-weight:bold; font-size:{FS_BASE}px;"
                f"background:{_C['success_bg']}; border:1px solid {_C['success_border']};"
                f"border-radius:{OP_ROWS_INNER_BORDER_RADIUS}px;"
                f"padding:{OP_ROWS_TOTAL_PAD_V}px {OP_ROWS_TOTAL_PAD_H}px;"
            )
        if hasattr(self, "_lbl_label"):
            for lbl in (self._lbl_label, self._lbl_count, self.lbl_value):
                lbl.setStyleSheet(
                    f"font-weight:bold; font-size:{FS_SM}px; color:{_C['text_primary']};"
                )
        if hasattr(self, "_lbl_total_lbl"):
            self._lbl_total_lbl.setStyleSheet(
                f"font-size:{FS_SM}px; font-weight:bold; color:{_C['text_primary']};"
            )
        if hasattr(self, "btn_del_row"):
            self.btn_del_row.setStyleSheet(f"color:{_C['danger']};")

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_op(self, op_id: int, mode: str,
                rate_per_hour: float, rate_per_unit: float):
        self._op_id     = op_id
        self._mode      = mode
        self._rate_hour = rate_per_hour
        self._rate_unit = rate_per_unit
        self.setEnabled(True)
        self._update_mode_ui()
        self._reset_form()
        self._load_table()

    def update_rates(self, mode: str, rate_per_hour: float, rate_per_unit: float):
        self._mode      = mode
        self._rate_hour = rate_per_hour
        self._rate_unit = rate_per_unit
        self._update_mode_ui()
        self._update_preview()
        if self._op_id:
            self._load_table()

    def clear(self):
        self._op_id = None
        self.table.setRowCount(0)
        self.lbl_total.setText(tr('amount_dash_placeholder'))
        self._reset_form()
        self.setEnabled(False)

    # ══════════════════════════════════════════════════════
    # منطق الـ UI
    # ══════════════════════════════════════════════════════

    def _update_mode_ui(self):
        if self._mode == "time":
            self.lbl_mode_info.setText(
                f"{tr('op_rows_time_icon')} {tr('calc_mode')}: {tr('by_time')}  {tr('vertical_separator')}  "
                f"{tr('rate')}: {self._rate_hour:.2f} {tr('currency_per_hour')}"
            )
            self.lbl_value.setText(f"{tr('time_minutes')}:")
        else:
            self.lbl_mode_info.setText(
                f"{tr('op_rows_unit_icon')} {tr('calc_mode')}: {tr('by_unit')}  {tr('vertical_separator')}  "
                f"{tr('rate')}: {self._rate_unit:.2f} {tr('currency_per_unit')}"
            )
            self.lbl_value.setText(f"{tr('units')}:")

    def _update_preview(self):
        value = self.sp_value.value()
        count = max(self.sp_count.value(), 0.0001)
        if self._mode == "time":
            raw = (value / 60.0) * self._rate_hour
        else:
            raw = value * self._rate_unit
        unit_cost = raw / count
        self.lbl_preview.setText(
            f"= {unit_cost:.4f} {tr('currency_per_piece')}"
        )

    def _load_table(self):
        if self._op_id is None:
            return
        self.table.setRowCount(0)

        # [Refactor] استخدام MachineOpRowsService بدل machine_op_rows_repo مباشرة
        svc  = MachineOpRowsService(self.conn)
        rows = svc.list(self._op_id)

        for row in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(row.id)))
            self.table.setItem(r, 1, QTableWidgetItem(row.label or tr('value_dash')))

            val_txt = (
                f"{row.value:.4g} {tr('minutes_abbr')}"
                if self._mode == "time"
                else f"{row.value:.4g} {tr('unit')}"
            )
            val_item = QTableWidgetItem(val_txt)
            val_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, val_item)

            cnt_item = QTableWidgetItem(f"{row.count:.4g}")
            cnt_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, cnt_item)

            row_cost  = svc.calc_row_cost(row.id)
            cost_item = QTableWidgetItem(
                f"{row_cost:.4f} {tr('currency_abbr')}"
            )
            cost_item.setForeground(QColor(_C['accent']))
            cost_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 4, cost_item)

        total = svc.calc_total_cost(self._op_id)
        self.lbl_total.setText(
            f"{total:.4f} {tr('currency')} {tr('slash_separator')} {tr('piece')}"
        )

    # ══════════════════════════════════════════════════════
    # CRUD — [Refactor] كل العمليات عبر MachineOpRowsService
    # ══════════════════════════════════════════════════════

    def _add_row(self):
        if self._op_id is None:
            return
        value = self.sp_value.value()
        count = self.sp_count.value()
        label = self.inp_label.text().strip()
        try:
            svc = MachineOpRowsService(self.conn)
            svc.add(
                self._op_id, label, value, count,
                sort_order=self.table.rowCount()
            )
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), str(e))
            return
        self._reset_form()
        self._load_table()
        emit_company_data_changed()

    def _edit_row(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, tr("notice"), tr("select_row_first"))
            return
        rid = int(self.table.item(row, 0).text())
        try:
            svc = MachineOpRowsService(self.conn)
            r   = svc.get(rid)
        except Exception:
            r = None
        if not r:
            return
        self._editing_row_id = rid
        self.inp_label.setText(r.label or "")
        self.sp_value.setValue(float(r.value))
        self.sp_count.setValue(float(r.count))
        self._update_preview()
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        if self._editing_row_id is None:
            return
        try:
            svc = MachineOpRowsService(self.conn)
            svc.update(
                self._editing_row_id,
                self.inp_label.text().strip(),
                self.sp_value.value(),
                self.sp_count.value(),
            )
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), str(e))
            return
        self._reset_form()
        self._load_table()
        emit_company_data_changed()

    def _delete_row(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, tr("notice"), tr("select_row_first"))
            return
        if self.table.rowCount() <= 1:
            QMessageBox.warning(
                self, tr("warning"),
                tr("min_one_row_required")
            )
            return
        rid = int(self.table.item(row, 0).text())
        try:
            svc = MachineOpRowsService(self.conn)
            svc.delete(rid)
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), str(e))
            return
        self._load_table()
        emit_company_data_changed()

    def _reset_form(self):
        self._editing_row_id = None
        self.inp_label.clear()
        self.sp_value.setValue(0.0)
        self.sp_count.setValue(1.0)
        self._update_preview()
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)