"""
ui/tabs/companies/shared_items_dialog.py
=========================================
SharedItemsDialog — نافذة تعديل عنصر مشترك وإدارة الشركات المرتبطة به.

تُفتح لما المستخدم يضغط «🔗 تعديل المشترك» من أي جدول.

الوظائف:
  - عرض بيانات العنصر المشترك (اسم + بيانات حسب النوع)
  - تعديل البيانات (السعر، عدد الدقائق، المعدلات...)
  - إدارة ربط الشركات (أضف / أزل)
  - أي تعديل يتعكس فوراً على كل الشركات المرتبطة
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QPushButton, QDoubleSpinBox,
    QGroupBox, QListWidget, QListWidgetItem,
    QMessageBox, QDialogButtonBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedLineEdit

from services.companies.shared_items_service import SharedItemsService
from services.companies.company_service import CompanyService
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_SM, FS_LG
from ui.constants import (
    SHARED_DLG_MIN_W, SHARED_DLG_MIN_H,
    SHARED_DLG_ROOT_SPACING, SHARED_DLG_ROOT_MARGIN,
    SHARED_DLG_HDR_RADIUS, SHARED_DLG_HDR_PAD_V, SHARED_DLG_HDR_PAD_H,
    SHARED_DLG_GRP_RADIUS, SHARED_DLG_GRP_PAD_TOP, SHARED_DLG_GRP_MARGIN_TOP,
    SHARED_DLG_GRP_TITLE_PAD_H, SHARED_DLG_DATA_SPACING, SHARED_DLG_INPUT_MIN_H,
    SHARED_DLG_LIST_MAX_H, SHARED_DLG_LIST_RADIUS,
    SHARED_DLG_LIST_ITEM_PAD_V, SHARED_DLG_LIST_ITEM_PAD_H,
    SHARED_DLG_LINK_BTN_RADIUS, SHARED_DLG_LINK_BTN_PAD_V, SHARED_DLG_LINK_BTN_PAD_H,
    SHARED_DLG_LINK_BTN_MIN_H, SHARED_DLG_SAVE_BTN_MIN_H,
    SHARED_DLG_SAVE_BTN_RADIUS, SHARED_DLG_SAVE_BTN_PAD_H,
    SHARED_DLG_PREVIEW_RADIUS, SHARED_DLG_PREVIEW_PAD_V, SHARED_DLG_PREVIEW_PAD_H,
    SHARED_DLG_HDR_BORDER_W, SHARED_DLG_LINK_BTN_BORDER_W,
    SHARED_DLG_GRP_BORDER_W, SHARED_DLG_LIST_BORDER_W,
    SHARED_DLG_SPIN_MAX_DEFAULT, SHARED_DLG_SPIN_DEC_DEFAULT,
    SHARED_DLG_SPIN_MAX_MINUTES, SHARED_DLG_SPIN_DEC_MINUTES,
)


def _spin(max_=SHARED_DLG_SPIN_MAX_DEFAULT, dec=SHARED_DLG_SPIN_DEC_DEFAULT):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(SHARED_DLG_INPUT_MIN_H)
    return s


class SharedItemsDialog(QDialog, WidgetMixin):
    """
    نافذة تعديل عنصر مشترك.

    الاستخدام:
        central = get_central_connection()
        dlg = SharedItemsDialog(central, shared_item_id, parent=self)
        dlg.exec_()
        central.close()
    """

    item_updated = pyqtSignal()

    def __init__(self, central_conn, shared_item_id: int, parent=None):
        super().__init__(parent)
        self._conn    = central_conn
        self._svc     = SharedItemsService(central_conn)
        self._co_svc  = CompanyService(central_conn)
        self._item_id = shared_item_id
        self._item    = None
        self._data    = {}

        self.setMinimumSize(SHARED_DLG_MIN_W, SHARED_DLG_MIN_H)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._init_widget_mixin(theme=True, font=True, lang=True, data=False)

        self._load_item()
        self._build()
        self._populate()
        self._refresh_style()
        self._refresh_lang()

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_item(self):
        self._item = self._svc.get_item(self._item_id)
        if not self._item:
            return
        self._data = self._item.data or {}

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        if not self._item:
            lbl_missing = QLabel()
            lbl_missing.setParent(self)
            self._lbl_missing = lbl_missing
            return

        root = QVBoxLayout(self)
        root.setSpacing(SHARED_DLG_ROOT_SPACING)
        root.setContentsMargins(*SHARED_DLG_ROOT_MARGIN)

        # ── Header ──
        self.header = QLabel()
        self.header.setTextFormat(Qt.RichText)
        root.addWidget(self.header)

        # ── بيانات العنصر ──
        self.data_grp = QGroupBox()
        data_lay = QFormLayout(self.data_grp)
        data_lay.setSpacing(SHARED_DLG_DATA_SPACING)
        data_lay.setLabelAlignment(Qt.AlignRight)

        # اسم العنصر
        self.inp_name = ThemedLineEdit(self._item.name)
        self.inp_name.setMinimumHeight(SHARED_DLG_INPUT_MIN_H)
        self._row_name_lbl = QLabel()
        data_lay.addRow(self._row_name_lbl, self.inp_name)

        # حقول حسب النوع
        self._field_widgets = {}
        self._build_type_fields(data_lay)

        root.addWidget(self.data_grp)

        # ── الشركات المرتبطة ──
        self.companies_grp = QGroupBox()
        c_lay = QVBoxLayout(self.companies_grp)

        self.lst_companies = QListWidget()
        self.lst_companies.setMaximumHeight(SHARED_DLG_LIST_MAX_H)
        c_lay.addWidget(self.lst_companies)

        c_btn_row = QHBoxLayout()
        self.btn_link   = QPushButton()
        self.btn_unlink = QPushButton()
        for btn in (self.btn_link, self.btn_unlink):
            btn.setMinimumHeight(SHARED_DLG_LINK_BTN_MIN_H)
        self.btn_link.clicked.connect(self._link_company)
        self.btn_unlink.clicked.connect(self._unlink_company)
        c_btn_row.addWidget(self.btn_link)
        c_btn_row.addWidget(self.btn_unlink)
        c_btn_row.addStretch()
        c_lay.addLayout(c_btn_row)

        root.addWidget(self.companies_grp)

        # ── أزرار الحفظ ──
        btns = QDialogButtonBox()
        self.btn_save   = btns.addButton("", QDialogButtonBox.AcceptRole)
        self.btn_cancel = btns.addButton("", QDialogButtonBox.RejectRole)
        self.btn_save.setMinimumHeight(SHARED_DLG_SAVE_BTN_MIN_H)
        self.btn_cancel.setMinimumHeight(SHARED_DLG_SAVE_BTN_MIN_H)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reject)
        root.addWidget(btns)

    def _refresh_style(self, *_):
        if not self._item:
            return
        from ui.theme import _C

        self.header.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['acc_type_asset']};"
            f"background:{_C['t_account_dr_bg']}; border:{SHARED_DLG_HDR_BORDER_W}px solid {_C['accent_mid']};"
            f"border-radius:{SHARED_DLG_HDR_RADIUS}px;"
            f"padding:{SHARED_DLG_HDR_PAD_V}px {SHARED_DLG_HDR_PAD_H}px;"
        )

        grp_style = f"""
            QGroupBox {{
                font-weight:bold; color:{_C['text_primary']};
                border:{SHARED_DLG_GRP_BORDER_W}px solid {_C['border']}; border-radius:{SHARED_DLG_GRP_RADIUS}px;
                padding-top:{SHARED_DLG_GRP_PAD_TOP}px; margin-top:{SHARED_DLG_GRP_MARGIN_TOP}px;
            }}
            QGroupBox::title {{
                subcontrol-origin:margin; padding:0 {SHARED_DLG_GRP_TITLE_PAD_H}px;
                subcontrol-position:top right;
            }}
        """
        self.data_grp.setStyleSheet(grp_style)
        self.companies_grp.setStyleSheet(grp_style)

        self.lst_companies.setStyleSheet(f"""
            QListWidget {{
                border:{SHARED_DLG_LIST_BORDER_W}px solid {_C['border']}; border-radius:{SHARED_DLG_LIST_RADIUS}px;
                font-size:{FS_SM}px;
            }}
            QListWidget::item {{ padding:{SHARED_DLG_LIST_ITEM_PAD_V}px {SHARED_DLG_LIST_ITEM_PAD_H}px; }}
            QListWidget::item:selected {{
                background:{_C['accent_light']}; color:{_C['accent_text']};
            }}
        """)

        self.btn_link.setStyleSheet(
            f"background:{_C['success_bg']}; color:{_C['success']};"
            f"border:{SHARED_DLG_LINK_BTN_BORDER_W}px solid {_C['success_border']};"
            f"border-radius:{SHARED_DLG_LINK_BTN_RADIUS}px;"
            f"padding:{SHARED_DLG_LINK_BTN_PAD_V}px {SHARED_DLG_LINK_BTN_PAD_H}px;"
            "font-weight:bold;"
        )
        self.btn_unlink.setStyleSheet(
            f"background:{_C['danger_bg']}; color:{_C['danger']};"
            f"border:{SHARED_DLG_LINK_BTN_BORDER_W}px solid {_C['danger_border']};"
            f"border-radius:{SHARED_DLG_LINK_BTN_RADIUS}px;"
            f"padding:{SHARED_DLG_LINK_BTN_PAD_V}px {SHARED_DLG_LINK_BTN_PAD_H}px;"
            "font-weight:bold;"
        )

        self.btn_save.setStyleSheet(
            f"background:{_C['accent']}; color:{_C['bg_surface']}; font-weight:bold;"
            f"border-radius:{SHARED_DLG_SAVE_BTN_RADIUS}px;"
            f"padding:0 {SHARED_DLG_SAVE_BTN_PAD_H}px;"
        )

        self._refresh_type_fields_style()
        if hasattr(self, "lst_companies"):
            self._load_companies_list()

    def _refresh_lang(self, *_):
        if not self._item:
            if hasattr(self, "_lbl_missing"):
                self._lbl_missing.setText(tr("shared_item_not_found"))
            return

        self.setWindowTitle(tr("shared_item_header"))

        from ui.theme import _C
        self.header.setText(
            f"{tr('shared_item_linked_icon')}  {self._item.name}  —  "
            f"<span style='color:{_C['text_muted']};'>{self._type_ar()}</span>"
        )

        self.data_grp.setTitle(tr("shared_item_data_section"))
        self.companies_grp.setTitle(tr("shared_companies_section"))
        self._row_name_lbl.setText(tr("shared_name_colon"))

        self.btn_link.setText(tr("shared_link_btn"))
        self.btn_unlink.setText(tr("shared_unlink_btn"))
        self.btn_save.setText(tr("shared_save_btn"))
        self.btn_cancel.setText(tr("shared_close_btn"))

        self._refresh_type_fields_lang()
        self._load_companies_list()

    def _build_type_fields(self, form_lay: QFormLayout):
        """يبني حقول الإدخال حسب نوع العنصر المشترك (بدون نص/ستايل — تُملأ في _refresh_lang/_refresh_style)."""
        t = self._item.shared_type
        self._type_row_labels = {}

        if t == "raw":
            sp = _spin()
            sp.setValue(float(self._data.get("price", 0.0)))
            self._field_widgets["price"] = sp
            lbl1 = QLabel()
            form_lay.addRow(lbl1, sp)
            self._type_row_labels["raw_price_lbl"] = lbl1

            sp2 = _spin()
            tq = self._data.get("total_qty")
            sp2.setValue(float(tq) if tq else 0.0)
            self._field_widgets["total_qty"] = sp2
            lbl2 = QLabel()
            form_lay.addRow(lbl2, sp2)
            self._type_row_labels["raw_total_qty_lbl"] = lbl2

            # معاينة سعر الوحدة
            self.lbl_unit = QLabel()
            sp.valueChanged.connect(self._update_raw_preview)
            sp2.valueChanged.connect(self._update_raw_preview)
            lbl3 = QLabel()
            form_lay.addRow(lbl3, self.lbl_unit)
            self._type_row_labels["raw_unit_preview_lbl"] = lbl3

        elif t == "machine":
            sp_h = _spin()
            sp_h.setValue(float(self._data.get("rate_per_hour", 0.0)))
            self._field_widgets["rate_per_hour"] = sp_h
            lbl1 = QLabel()
            form_lay.addRow(lbl1, sp_h)
            self._type_row_labels["machine_rate_hour_lbl"] = lbl1

            sp_u = _spin()
            sp_u.setValue(float(self._data.get("rate_per_unit", 0.0)))
            self._field_widgets["rate_per_unit"] = sp_u
            lbl2 = QLabel()
            form_lay.addRow(lbl2, sp_u)
            self._type_row_labels["machine_rate_unit_lbl"] = lbl2

        elif t == "labor_op":
            sp = _spin(SHARED_DLG_SPIN_MAX_MINUTES, SHARED_DLG_SPIN_DEC_MINUTES)
            sp.setValue(float(self._data.get("minutes", 0.0)))
            self._field_widgets["minutes"] = sp
            lbl1 = QLabel()
            form_lay.addRow(lbl1, sp)
            self._type_row_labels["labor_time_lbl"] = lbl1

        elif t == "machine_op":
            sp = _spin()
            sp.setValue(float(self._data.get("value", 0.0)))
            self._field_widgets["value"] = sp
            lbl1 = QLabel()
            form_lay.addRow(lbl1, sp)
            self._type_row_labels["machine_op_value_lbl"] = lbl1

            self.lbl_machine = QLabel()
            lbl2 = QLabel()
            form_lay.addRow(lbl2, self.lbl_machine)
            self._type_row_labels["machine_name_col"] = lbl2

    def _refresh_type_fields_lang(self):
        """يحدّث نصوص حقول النوع — تُستدعى من _refresh_lang."""
        if not hasattr(self, "_type_row_labels"):
            return
        t = self._item.shared_type

        for key, lbl in self._type_row_labels.items():
            if key == "machine_op_value_lbl":
                mode = self._data.get("mode", "time")
                lbl.setText(tr("labor_time_lbl") if mode == "time" else tr("quantity"))
            else:
                lbl.setText(tr(key))

        if t == "raw":
            self._field_widgets["total_qty"].setSpecialValueText(tr("without_value"))
            self._update_raw_preview()

        elif t == "machine_op":
            self.lbl_machine.setText(self._data.get("machine_name", tr("dash")))

    def _refresh_type_fields_style(self):
        """يحدّث ستايل حقول النوع — تُستدعى من _refresh_style."""
        from ui.theme import _C
        t = self._item.shared_type

        if t == "raw" and hasattr(self, "lbl_unit"):
            self.lbl_unit.setStyleSheet(
                f"color:{_C['acc_type_asset']}; font-weight:bold; font-size:{FS_SM}px;"
                f"background:{_C['t_account_dr_bg']};"
                f"border-radius:{SHARED_DLG_PREVIEW_RADIUS}px;"
                f"padding:{SHARED_DLG_PREVIEW_PAD_V}px {SHARED_DLG_PREVIEW_PAD_H}px;"
            )

        elif t == "machine_op" and hasattr(self, "lbl_machine"):
            self.lbl_machine.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px;")

    def _update_raw_preview(self):
        """تحديث معاينة سعر الوحدة للخامات."""
        price = self._field_widgets["price"].value()
        tq    = self._field_widgets["total_qty"].value()
        if tq > 0 and price > 0:
            self.lbl_unit.setText(f"{price/tq:.4f}  {tr('currency_per_unit')}")
        else:
            self.lbl_unit.setText(f"{price:.4f}  {tr('currency_per_unit')}" if price > 0 else tr("dash"))

    # ══════════════════════════════════════════════════════
    # ملء البيانات
    # ══════════════════════════════════════════════════════

    def _populate(self):
        """
        كان يملأ قائمة الشركات ومعاينة سعر الوحدة مباشرة بعد _build.
        نُقل التنفيذ إلى _refresh_lang (عبر _load_companies_list و
        _refresh_type_fields_lang) عشان يتوافق مع تحديث اللغة الديناميكي.
        """
        pass

    def _load_companies_list(self):
        from PyQt5.QtGui import QColor
        from ui.theme import _C
        self.lst_companies.clear()
        linked = {r["id"] for r in self._svc.list_linked_companies(self._item_id)}
        all_cos = self._co_svc.list_companies()
        for co in all_cos:
            icon = tr("shared_linked_company_icon") if co.id in linked else tr("shared_unlinked_company_icon")
            item = QListWidgetItem(f"{icon}  {co.name}")
            item.setData(Qt.UserRole, co.id)
            item.setData(Qt.UserRole + 1, co.id in linked)
            if co.id in linked:
                item.setForeground(QColor(_C["success"]))
            self.lst_companies.addItem(item)

    # ══════════════════════════════════════════════════════
    # أحداث الشركات
    # ══════════════════════════════════════════════════════

    def _link_company(self):
        item = self.lst_companies.currentItem()
        if not item:
            QMessageBox.information(self, tr("notice"), tr("select_item_first"))
            return
        co_id    = item.data(Qt.UserRole)
        is_linked = item.data(Qt.UserRole + 1)
        if is_linked:
            QMessageBox.information(self, tr("notice"), tr("shared_already_linked"))
            return
        self._svc.link_to_company(self._item_id, co_id)
        self._load_companies_list()
        emit_company_data_changed()

    def _unlink_company(self):
        item = self.lst_companies.currentItem()
        if not item:
            QMessageBox.information(self, tr("notice"), tr("select_item_first"))
            return
        co_id    = item.data(Qt.UserRole)
        is_linked = item.data(Qt.UserRole + 1)
        if not is_linked:
            QMessageBox.information(self, tr("notice"), tr("shared_not_linked"))
            return
        reply = QMessageBox.question(
            self, tr("confirm"),
            tr("shared_unlink_confirm"),
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self._svc.unlink_from_company(self._item_id, co_id)
            self._load_companies_list()
            emit_company_data_changed()

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("shared_name_required"))
            return

        new_data = dict(self._data)
        t = self._item.shared_type

        if t == "raw":
            new_data["price"]     = self._field_widgets["price"].value()
            tq = self._field_widgets["total_qty"].value()
            new_data["total_qty"] = tq if tq > 0 else None

        elif t == "machine":
            new_data["rate_per_hour"] = self._field_widgets["rate_per_hour"].value()
            new_data["rate_per_unit"] = self._field_widgets["rate_per_unit"].value()

        elif t == "labor_op":
            new_data["minutes"] = self._field_widgets["minutes"].value()

        elif t == "machine_op":
            new_data["value"] = self._field_widgets["value"].value()

        self._svc.update_item(self._item_id, name, new_data)
        emit_company_data_changed()
        self.item_updated.emit()
        QMessageBox.information(self, tr("done"), tr("shared_updated_msg"))
        self.accept()

    # ══════════════════════════════════════════════════════
    # مساعدات
    # ══════════════════════════════════════════════════════

    def _type_ar(self) -> str:
        return {
            "raw":        tr("shared_type_raw"),
            "machine":    tr("shared_type_machine"),
            "labor_op":   tr("shared_type_labor_op"),
            "machine_op": tr("shared_type_machine_op"),
        }.get(self._item.shared_type if self._item else "", tr("name"))