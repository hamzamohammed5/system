"""
ui/tabs/costing/shared/raw_variants_panel.py
=================================
_RawVariantsPanel — لوحة إدارة variants الخامة (صفوف الإنتاج).

[Refactor] ربط bus.theme_changed لتحديث stylesheet ديناميكياً.
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

from db.costing.raw_variants_repo import (
    fetch_variants_for_item,
    insert_variant, update_variant, delete_variant,
    fetch_variant,
)
from ui.app_settings          import _C
from ui.widgets.core.i18n     import tr
from ui.widgets.core.events   import emit_company_data_changed
from ui.events                import bus


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
        super().__init__(f"📐  {tr('raw_variants')}", parent)
        self.conn        = conn
        self._item_id    = None
        self._item_price = 0.0
        self._editing_id = None
        self._build()
        self.setEnabled(False)
        bus.theme_changed.connect(self._apply_theme)

    def _build(self):
        self._apply_group_style()

        root = QVBoxLayout(self)
        root.setSpacing(8)
        root.setContentsMargins(10, 12, 10, 10)

        # ── شرح ──
        self.lbl_info = QLabel(
            f"💡 {tr('variant_description_line1')}\n"
            f"   {tr('variant_unit_cost_formula')}"
        )
        self.lbl_info.setWordWrap(True)
        root.addWidget(self.lbl_info)

        # ── فورم إضافة/تعديل ──
        form_row = QHBoxLayout()
        form_row.setSpacing(8)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("variant_name_placeholder"))
        self.inp_name.setMinimumHeight(30)

        lbl_pieces = QLabel(f"{tr('pieces_count')}:")
        self._lbl_pieces = lbl_pieces

        self.sp_pieces = _spin_pieces()
        self.sp_pieces.setFixedWidth(100)
        self.sp_pieces.setToolTip(
            f"{tr('pieces_tooltip_line1')}\n{tr('variant_unit_cost_formula')}"
        )

        self.lbl_preview = QLabel("─")
        self.lbl_preview.setMinimumWidth(120)
        self.sp_pieces.valueChanged.connect(self._update_preview)

        self.btn_add    = QPushButton(f"➕ {tr('add')}")
        self.btn_save   = QPushButton(f"💾 {tr('save')}")
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
        self.table.setHorizontalHeaderLabels([
            "ID",
            tr("name"),
            tr("pieces_count"),
            tr("cost_per_unit"),
        ])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setMaximumHeight(160)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Fixed)
        hh.setSectionResizeMode(1, QHeaderView.Stretch)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 0)
        self.table.setColumnHidden(0, True)
        self.table.setColumnWidth(2, 90)
        self.table.setColumnWidth(3, 110)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table)

        # ── أزرار التعديل والحذف ──
        btn_row = QHBoxLayout()
        self.btn_edit = QPushButton(f"✏️ {tr('edit')}")
        self.btn_del  = QPushButton(f"🗑️ {tr('delete')}")
        for btn in (self.btn_edit, self.btn_del):
            btn.setMinimumHeight(26)
        self.btn_edit.clicked.connect(self._edit)
        self.btn_del.clicked.connect(self._delete)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_del)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._apply_theme()

    def _apply_group_style(self):
        self.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                color: {_C['accent']};
                border: 1px solid {_C['info_border']};
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 8px;
                background: {_C['bg_surface']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                padding: 0 6px;
            }}
        """)

    def _apply_theme(self, _=None):
        """يُطبق الـ stylesheet عند تغيير الثيم."""
        self._apply_group_style()
        if hasattr(self, "lbl_info"):
            self.lbl_info.setStyleSheet(
                f"font-size:10px; color:{_C['text_sec']}; font-weight:normal;"
                f"background:{_C['info_bg']}; border-radius:4px; padding:5px 8px;"
                f"border:1px solid {_C['info_border']};"
            )
        if hasattr(self, "inp_name"):
            self.inp_name.setStyleSheet(
                f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
                f"border-radius:4px; padding:2px 6px; color:{_C['text_primary']};"
            )
        if hasattr(self, "_lbl_pieces"):
            self._lbl_pieces.setStyleSheet(
                f"font-weight:bold; font-size:11px; color:{_C['text_primary']};"
            )
        if hasattr(self, "lbl_preview"):
            self.lbl_preview.setStyleSheet(
                f"color:{_C['accent']}; font-weight:bold; font-size:11px;"
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
        self.lbl_preview.setText("─")
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
                cost_text = f"{unit_cost:.4f}  {tr('currency_abbr')}"
            else:
                cost_text = "─"
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
                f"= {unit_cost:.4f}  {tr('currency_per_piece')}"
            )
        else:
            self.lbl_preview.setText("─")

    # ══════════════════════════════════════════════════════
    # CRUD
    # ══════════════════════════════════════════════════════

    def _add(self):
        name   = self.inp_name.text().strip()
        pieces = self.sp_pieces.value()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("enter_variant_name"))
            return
        if self._item_id is None:
            return
        insert_variant(self.conn, self._item_id, name, pieces)
        self._reset_form()
        self._load_table()
        # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
        emit_company_data_changed()

    def _edit(self):
        row = self.table.currentRow()
        if row == -1:
            QMessageBox.information(self, tr("notice"), tr("select_variant_first"))
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
        # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
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
            f"{tr('delete_variant_confirm')} «{name}»؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_variant(self.conn, vid)
            self._load_table()
            # [Fix] emit_company_data_changed بدل bus.data_changed.emit()
            emit_company_data_changed()

    def _reset_form(self):
        self._editing_id = None
        self.inp_name.clear()
        self.sp_pieces.setValue(1.0)
        self._update_preview()
        self.btn_add.setVisible(True)
        self.btn_save.setVisible(False)
        self.btn_cancel.setVisible(False)