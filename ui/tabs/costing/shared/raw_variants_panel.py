"""
ui/tabs/costing/shared/raw_variants_panel.py
=================================
_RawVariantsPanel — لوحة إدارة variants الخامة (صفوف الإنتاج).

[Refactor] ربط bus.theme_changed لتحديث stylesheet ديناميكياً.
[Refactor] استخدام VariantService بدل raw_variants_repo مباشرة.
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

from services.costing.variant_service import VariantService
from ui.theme          import _C
from ui.widgets.core.i18n     import tr
from ui.widgets.core.events   import emit_company_data_changed
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_XS, FS_SM
from ui.constants import (
    RAW_VARIANTS_SPIN_MAX, RAW_VARIANTS_SPIN_MIN, RAW_VARIANTS_SPIN_DEC,
    RAW_VARIANTS_SPIN_H, RAW_VARIANTS_SPIN_W, RAW_VARIANTS_INP_H,
    RAW_VARIANTS_PREVIEW_MIN_W, RAW_VARIANTS_CANCEL_BTN_W, RAW_VARIANTS_BTN_H,
    RAW_VARIANTS_TABLE_MAX_H, RAW_VARIANTS_COL_COUNT,
    RAW_VARIANTS_COL2_W, RAW_VARIANTS_COL3_W,
    RAW_VARIANTS_EDIT_BTN_H,
    RAW_VARIANTS_ROOT_SPACING, RAW_VARIANTS_ROOT_MARGIN_H,
    RAW_VARIANTS_ROOT_MARGIN_T, RAW_VARIANTS_ROOT_MARGIN_B,
    RAW_VARIANTS_FORM_SPACING,
    RAW_VARIANTS_GRP_BORDER_RADIUS, RAW_VARIANTS_GRP_MARGIN_TOP,
    RAW_VARIANTS_GRP_PADDING_TOP, RAW_VARIANTS_GRP_TITLE_PAD_H,
    RAW_VARIANTS_INFO_RADIUS, RAW_VARIANTS_INFO_PAD_V, RAW_VARIANTS_INFO_PAD_H,
    RAW_VARIANTS_INP_RADIUS, RAW_VARIANTS_INP_PAD_V, RAW_VARIANTS_INP_PAD_H,
)


def _spin_pieces(max_=RAW_VARIANTS_SPIN_MAX, dec=RAW_VARIANTS_SPIN_DEC):
    s = QDoubleSpinBox()
    s.setRange(RAW_VARIANTS_SPIN_MIN, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(RAW_VARIANTS_SPIN_H)
    s.setValue(1.0)
    return s


class _RawVariantsPanel(QGroupBox, WidgetMixin):
    """
    لوحة إدارة variants الخامة — تُضاف داخل فورم الخامة.

    الاستخدام:
        self._variants_panel = _RawVariantsPanel(conn)
        self._variants_panel.load_item(item_id, item_price)
    """

    def __init__(self, conn, parent=None):
        super().__init__(f"{tr('raw_variants_icon')}{tr('raw_variants')}", parent)
        self.conn        = conn
        self._item_id    = None
        self._item_price = 0.0
        self._editing_id = None
        self._build()
        self.setEnabled(False)
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _build(self):
        self._apply_group_style()

        root = QVBoxLayout(self)
        root.setSpacing(RAW_VARIANTS_ROOT_SPACING)
        root.setContentsMargins(RAW_VARIANTS_ROOT_MARGIN_H, RAW_VARIANTS_ROOT_MARGIN_T,
                                RAW_VARIANTS_ROOT_MARGIN_H, RAW_VARIANTS_ROOT_MARGIN_B)

        # ── شرح ──
        self.lbl_info = QLabel(
            f"{tr('raw_variants_info_icon')}{tr('variant_description_line1')}\n"
            f"   {tr('variant_unit_cost_formula')}"
        )
        self.lbl_info.setWordWrap(True)
        root.addWidget(self.lbl_info)

        # ── فورم إضافة/تعديل ──
        form_row = QHBoxLayout()
        form_row.setSpacing(RAW_VARIANTS_FORM_SPACING)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("variant_name_placeholder"))
        self.inp_name.setMinimumHeight(RAW_VARIANTS_INP_H)

        lbl_pieces = QLabel(f"{tr('pieces_count')}:")
        self._lbl_pieces = lbl_pieces

        self.sp_pieces = _spin_pieces()
        self.sp_pieces.setFixedWidth(RAW_VARIANTS_SPIN_W)
        self.sp_pieces.setToolTip(
            f"{tr('pieces_tooltip_line1')}\n{tr('variant_unit_cost_formula')}"
        )

        self.lbl_preview = QLabel(tr("amount_dash_placeholder"))
        self.lbl_preview.setMinimumWidth(RAW_VARIANTS_PREVIEW_MIN_W)
        self.sp_pieces.valueChanged.connect(self._update_preview)

        self.btn_add    = QPushButton(f"{tr('raw_variants_add_icon')}{tr('add')}")
        self.btn_save   = QPushButton(f"{tr('raw_variants_save_icon')}{tr('save')}")
        self.btn_cancel = QPushButton(tr("dismiss_icon"))
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.setFixedWidth(RAW_VARIANTS_CANCEL_BTN_W)

        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(RAW_VARIANTS_BTN_H)

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
        self.table.setColumnCount(RAW_VARIANTS_COL_COUNT)
        self.table.setHorizontalHeaderLabels([
            tr("id_col"),
            tr("name"),
            tr("pieces_count"),
            tr("cost_per_unit"),
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(RAW_VARIANTS_TABLE_MAX_H)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 0)
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(2, RAW_VARIANTS_COL2_W)
        self.table.setColumnWidth(3, RAW_VARIANTS_COL3_W)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        # ── أزرار التعديل والحذف ──
        btn_row = QHBoxLayout()
        self.btn_edit = QPushButton(f"{tr('raw_variants_edit_icon')}{tr('edit')}")
        self.btn_del  = QPushButton(f"{tr('raw_variants_del_icon')}{tr('delete')}")
        for btn in (self.btn_edit, self.btn_del):
            btn.setMinimumHeight(RAW_VARIANTS_EDIT_BTN_H)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_del.clicked.connect(self._delete)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

    def _apply_group_style(self):
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {_C['accent']};
                border: 1px solid {_C['info_border']};
                border-radius: {RAW_VARIANTS_GRP_BORDER_RADIUS}px;
                margin-top: {RAW_VARIANTS_GRP_MARGIN_TOP}px;
                padding-top: {RAW_VARIANTS_GRP_PADDING_TOP}px;
                background: {_C['bg_surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                padding: 0 {RAW_VARIANTS_GRP_TITLE_PAD_H}px;
            }}
        """)

    def _refresh_style(self, *_):
        """يُطبق الـ stylesheet عند تغيير الثيم."""
        self._apply_group_style()
        if hasattr(self, "lbl_info"):
            self.lbl_info.setStyleSheet(
                f"font-size:{FS_XS}px; color:{_C['text_sec']}; font-weight:normal;"
                f"background:{_C['info_bg']}; border-radius:{RAW_VARIANTS_INFO_RADIUS}px;"
                f"padding:{RAW_VARIANTS_INFO_PAD_V}px {RAW_VARIANTS_INFO_PAD_H}px;"
                f"border:1px solid {_C['info_border']};"
            )
        if hasattr(self, "inp_name"):
            self.inp_name.setStyleSheet(
                f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
                f"border-radius:{RAW_VARIANTS_INP_RADIUS}px;"
                f"padding:{RAW_VARIANTS_INP_PAD_V}px {RAW_VARIANTS_INP_PAD_H}px;"
                f"color:{_C['text_primary']};"
            )
        if hasattr(self, "_lbl_pieces"):
            self._lbl_pieces.setStyleSheet(
                f"font-weight:bold; font-size:{FS_SM}px; color:{_C['text_primary']};"
            )
        if hasattr(self, "lbl_preview"):
            self.lbl_preview.setStyleSheet(
                f"color:{_C['accent']}; font-weight:bold; font-size:{FS_SM}px;"
            )
        if hasattr(self, "table"):
            self.table.setStyleSheet(
                f"QTableWidget {{ background:{_C['bg_surface']}; "
                f"color:{_C['text_primary']}; border:1px solid {_C['border']}; }}"
                f"QTableWidget::item:selected {{ background:{_C['accent_light']}; "
                f"color:{_C['accent']}; }}"
            )
        if hasattr(self, "btn_del"):
            self.btn_del.setStyleSheet(f"color:{_C['danger']};")

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_item(self, item_id: int, item_price: float):
        self._item_id    = item_id
        self._item_price = item_price
        self.setEnabled(True)
        self._reset_form()
        self._load_table()

    def clear(self):
        self._item_id    = None
        self._item_price = 0.0
        self._editing_id = None
        self.table.setRowCount(0)
        self.inp_name.clear()
        self.sp_pieces.setValue(1.0)
        self.lbl_preview.setText(tr("amount_dash_placeholder"))
        self.setEnabled(False)

    def refresh_price(self, new_price: float):
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

        # [Refactor] استخدام VariantService بدل raw_variants_repo مباشرة
        svc      = VariantService(self.conn)
        variants = svc.list(self._item_id)

        for var in variants:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(var.id)))
            self.table.setItem(r, 1, QTableWidgetItem(var.name))

            pieces_item = QTableWidgetItem(f"{var.pieces:,.4g}")
            pieces_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 2, pieces_item)

            pieces = float(var.pieces)
            if pieces > 0 and self._item_price > 0:
                unit_cost = self._item_price / pieces
                cost_text = f"{unit_cost:.4f}  {tr('currency_abbr')}"
            else:
                cost_text = tr("amount_dash_placeholder")
            cost_item = QTableWidgetItem(cost_text)
            cost_item.setForeground(QColor(_C['accent']))
            cost_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, cost_item)

    # ══════════════════════════════════════════════════════
    # معاينة حية
    # ══════════════════════════════════════════════════════

    def _update_preview(self):
        pieces = self.sp_pieces.value()
        if pieces > 0 and self._item_price > 0:
            unit_cost = self._item_price / pieces
            self.lbl_preview.setText(
                f"{tr('raw_variants_equals_sign')}{unit_cost:.4f}  {tr('currency_per_piece')}"
            )
        else:
            self.lbl_preview.setText(tr("amount_dash_placeholder"))

    # ══════════════════════════════════════════════════════
    # CRUD — [Refactor] كل العمليات عبر VariantService
    # ══════════════════════════════════════════════════════

    def _add(self):
        name   = self.inp_name.text().strip()
        pieces = self.sp_pieces.value()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("enter_variant_name"))
            return
        if self._item_id is None:
            return
        try:
            svc = VariantService(self.conn)
            svc.add(self._item_id, name, pieces)
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), str(e))
            return
        self._reset_form()
        self._load_table()
        emit_company_data_changed()

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, tr("notice"), tr("select_variant_first"))
            return
        vid = int(self.table.item(row, 0).text())
        try:
            svc = VariantService(self.conn)
            var = svc.get(vid)
        except Exception:
            var = None
        if not var:
            return
        self._editing_id = vid
        self.inp_name.setText(var.name)
        self.sp_pieces.setValue(float(var.pieces))
        self._update_preview()
        self.btn_add.setVisible(False)
        self.btn_save.setVisible(True)
        self.btn_cancel.setVisible(True)

    def _save_edit(self):
        name   = self.inp_name.text().strip()
        pieces = self.sp_pieces.value()
        if not name or self._editing_id is None:
            return
        try:
            svc = VariantService(self.conn)
            svc.update(self._editing_id, name, pieces)
        except Exception as e:
            QMessageBox.warning(self, tr("warning"), str(e))
            return
        self._reset_form()
        self._load_table()
        emit_company_data_changed()

    def _delete(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, tr("notice"), tr("select_variant_first"))
            return
        vid  = int(self.table.item(row, 0).text())
        name = self.table.item(row, 1).text()
        if QMessageBox.question(
            self, tr("confirm"),
            tr("delete_variant_confirm_msg").format(name=name),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            try:
                svc = VariantService(self.conn)
                svc.delete(vid)
            except Exception as e:
                QMessageBox.warning(self, tr("warning"), str(e))
                return
            self._load_table()
            emit_company_data_changed()

    def _reset_form(self):
        self._editing_id = None
        self.inp_name.clear()
        self.sp_pieces.setValue(1.0)
        self._update_preview()
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)