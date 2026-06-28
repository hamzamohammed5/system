"""
ui/tabs/companies/shared_items_manager_helper/_add_shared_item_dialog.py
==========================================================================
إصلاح: حفظ source_company_id و category_name في data عند النشر
عشان:
  1. نعرف مين هو المصدر ونتجنب إظهار العنصر مرتين في الشركة الأصلية
  2. نعرض التصنيف الحقيقي بدل "مشترك"
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QGroupBox, QListWidget, QListWidgetItem,
    QMessageBox, QDialogButtonBox, QCheckBox,
)
from PyQt5.QtCore import Qt

from db.companies.shared_items_repo import (
    insert_shared_item, link_company,
    fetch_all_shared_items,
)
from db.companies.companies_repo import fetch_all_companies
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_SM
from ui.constants import (
    PUBLISH_DLG_MIN_W, PUBLISH_DLG_MIN_H,
    PUBLISH_DLG_ROOT_SPACING, PUBLISH_DLG_ROOT_MARGIN,
    PUBLISH_DLG_HINT_RADIUS, PUBLISH_DLG_HINT_PAD_V, PUBLISH_DLG_HINT_PAD_H,
    PUBLISH_DLG_GRP_RADIUS, PUBLISH_DLG_GRP_PAD_TOP, PUBLISH_DLG_GRP_MARGIN_TOP,
    PUBLISH_DLG_GRP_TITLE_PAD_H, PUBLISH_DLG_DATA_SPACING, PUBLISH_DLG_INPUT_MIN_H,
    PUBLISH_DLG_LIST_MAX_H, PUBLISH_DLG_LIST_RADIUS,
    PUBLISH_DLG_LIST_ITEM_PAD_V, PUBLISH_DLG_LIST_ITEM_PAD_H,
    PUBLISH_DLG_QUICK_BTN_MIN_H, PUBLISH_DLG_QUICK_BTN_MAX_W,
    PUBLISH_DLG_OK_BTN_MIN_H, PUBLISH_DLG_OK_BTN_RADIUS, PUBLISH_DLG_OK_BTN_PAD_H,
)


def _spin(max_=9999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(PUBLISH_DLG_INPUT_MIN_H)
    return s


class PublishAsSharedDialog(QDialog):
    def __init__(self, central_conn, shared_type: str,
                 item_name: str, item_data: dict, parent=None):
        super().__init__(parent)
        self._conn        = central_conn
        self._shared_type = shared_type
        self._item_name   = item_name
        self._item_data   = item_data or {}

        self.setWindowTitle(tr("shared_publish_title"))
        self.setMinimumSize(PUBLISH_DLG_MIN_W, PUBLISH_DLG_MIN_H)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(PUBLISH_DLG_ROOT_SPACING)
        root.setContentsMargins(*PUBLISH_DLG_ROOT_MARGIN)

        lbl_hint = QLabel(tr("shared_publish_hint"))
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet(
            f"background:{_C['accent_light']}; border:1px solid {_C['accent_mid']}; border-radius:{PUBLISH_DLG_HINT_RADIUS}px;"
            f"padding:{PUBLISH_DLG_HINT_PAD_V}px {PUBLISH_DLG_HINT_PAD_H}px; color:{_C['accent_text']}; font-size:{FS_SM}px;"
        )
        root.addWidget(lbl_hint)

        data_grp = QGroupBox(tr("shared_item_data_section"))
        data_grp.setStyleSheet(
            f"QGroupBox {{ font-weight:bold; border:1px solid {_C['border']};"
            f"border-radius:{PUBLISH_DLG_GRP_RADIUS}px; padding-top:{PUBLISH_DLG_GRP_PAD_TOP}px; margin-top:{PUBLISH_DLG_GRP_MARGIN_TOP}px; }}"
            f"QGroupBox::title {{ subcontrol-origin:margin; padding:0 {PUBLISH_DLG_GRP_TITLE_PAD_H}px;"
            "subcontrol-position:top right; }"
        )
        data_lay = QFormLayout(data_grp)
        data_lay.setSpacing(PUBLISH_DLG_DATA_SPACING)
        data_lay.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit(self._item_name)
        self.inp_name.setMinimumHeight(PUBLISH_DLG_INPUT_MIN_H)
        data_lay.addRow(tr("shared_name_colon"), self.inp_name)

        self._field_widgets = {}
        self._build_type_fields(data_lay)

        root.addWidget(data_grp)

        cos_grp = QGroupBox(tr("shared_companies_share"))
        cos_grp.setStyleSheet(
            f"QGroupBox {{ font-weight:bold; border:1px solid {_C['border']};"
            f"border-radius:{PUBLISH_DLG_GRP_RADIUS}px; padding-top:{PUBLISH_DLG_GRP_PAD_TOP}px; margin-top:{PUBLISH_DLG_GRP_MARGIN_TOP}px; }}"
            f"QGroupBox::title {{ subcontrol-origin:margin; padding:0 {PUBLISH_DLG_GRP_TITLE_PAD_H}px;"
            "subcontrol-position:top right; }"
        )
        cos_lay = QVBoxLayout(cos_grp)

        self.lst_companies = QListWidget()
        self.lst_companies.setMaximumHeight(PUBLISH_DLG_LIST_MAX_H)
        self.lst_companies.setStyleSheet(
            f"QListWidget {{ border:1px solid {_C['border']}; border-radius:{PUBLISH_DLG_LIST_RADIUS}px; }}"
            f"QListWidget::item {{ padding:{PUBLISH_DLG_LIST_ITEM_PAD_V}px {PUBLISH_DLG_LIST_ITEM_PAD_H}px; }}"
            f"QListWidget::item:selected {{ background:{_C['accent_light']}; color:{_C['accent_text']}; }}"
        )
        cos_lay.addWidget(self.lst_companies)

        all_companies = fetch_all_companies(self._conn)

        try:
            from db.companies.company_state import company_state
            current_co_id = company_state.company_id
        except Exception:
            current_co_id = None

        for co in all_companies:
            item = QListWidgetItem(co["name"])
            item.setData(Qt.UserRole, co["id"])
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Checked if co["id"] == current_co_id else Qt.Unchecked
            )
            self.lst_companies.addItem(item)

        quick_row = QHBoxLayout()
        btn_all  = QPushButton(tr("shared_select_all_btn"))
        btn_none = QPushButton(tr("shared_select_none_btn"))
        for btn in (btn_all, btn_none):
            btn.setMinimumHeight(PUBLISH_DLG_QUICK_BTN_MIN_H)
            btn.setMaximumWidth(PUBLISH_DLG_QUICK_BTN_MAX_W)
        btn_all.clicked.connect(lambda: self._check_all(True))
        btn_none.clicked.connect(lambda: self._check_all(False))
        quick_row.addWidget(QLabel(tr("shared_quick_select")))
        quick_row.addWidget(btn_all)
        quick_row.addWidget(btn_none)
        quick_row.addStretch()
        cos_lay.addLayout(quick_row)

        root.addWidget(cos_grp)

        btns = QDialogButtonBox()
        btn_ok     = btns.addButton(tr("shared_publish_btn"), QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton(tr("btn_cancel"),          QDialogButtonBox.RejectRole)
        btn_ok.setMinimumHeight(PUBLISH_DLG_OK_BTN_MIN_H)
        btn_cancel.setMinimumHeight(PUBLISH_DLG_OK_BTN_MIN_H)
        btn_ok.setStyleSheet(
            f"background:{_C['accent']}; color:{_C['bg_surface']}; font-weight:bold;"
            f"border-radius:{PUBLISH_DLG_OK_BTN_RADIUS}px; padding:0 {PUBLISH_DLG_OK_BTN_PAD_H}px;"
        )
        btn_ok.clicked.connect(self._publish)
        btn_cancel.clicked.connect(self.reject)
        root.addWidget(btns)

    def _build_type_fields(self, form_lay: QFormLayout):
        t = self._shared_type
        if t == "raw":
            sp = _spin()
            sp.setValue(float(self._item_data.get("price", 0.0)))
            self._field_widgets["price"] = sp
            form_lay.addRow(tr("raw_price_lbl"), sp)

            sp2 = _spin()
            tq = self._item_data.get("total_qty")
            sp2.setValue(float(tq) if tq else 0.0)
            sp2.setSpecialValueText(tr("without_value"))
            self._field_widgets["total_qty"] = sp2
            form_lay.addRow(tr("raw_total_qty_lbl"), sp2)

        elif t == "machine":
            sp_h = _spin()
            sp_h.setValue(float(self._item_data.get("rate_per_hour", 0.0)))
            self._field_widgets["rate_per_hour"] = sp_h
            form_lay.addRow(tr("machine_rate_hour_lbl"), sp_h)

            sp_u = _spin()
            sp_u.setValue(float(self._item_data.get("rate_per_unit", 0.0)))
            self._field_widgets["rate_per_unit"] = sp_u
            form_lay.addRow(tr("machine_rate_unit_lbl"), sp_u)

        elif t == "labor_op":
            sp = _spin(9999, 2)
            sp.setValue(float(self._item_data.get("minutes", 0.0)))
            self._field_widgets["minutes"] = sp
            form_lay.addRow(tr("labor_time_lbl"), sp)

        elif t == "machine_op":
            sp = _spin()
            sp.setValue(float(self._item_data.get("value", 0.0)))
            self._field_widgets["value"] = sp
            form_lay.addRow(tr("value"), sp)

    def _check_all(self, checked: bool):
        for i in range(self.lst_companies.count()):
            self.lst_companies.item(i).setCheckState(
                Qt.Checked if checked else Qt.Unchecked
            )

    def _publish(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, tr("warning"), tr("shared_name_required"))
            return

        # ── جلب الشركة الحالية (المصدر) ──
        try:
            from db.companies.company_state import company_state
            current_co_id = company_state.company_id
        except Exception:
            current_co_id = None

        # ── بناء data مع source_company_id و category_name ──
        data = {}
        t = self._shared_type
        if t == "raw":
            data["price"] = self._field_widgets["price"].value()
            tq = self._field_widgets["total_qty"].value()
            data["total_qty"] = tq if tq > 0 else None
        elif t == "machine":
            data["rate_per_hour"] = self._field_widgets["rate_per_hour"].value()
            data["rate_per_unit"] = self._field_widgets["rate_per_unit"].value()
        elif t == "labor_op":
            data["minutes"] = self._field_widgets["minutes"].value()
        elif t == "machine_op":
            data["value"] = self._field_widgets["value"].value()
            data["mode"]  = self._item_data.get("mode", "time")
            data["machine_name"]  = self._item_data.get("machine_name", "")
            data["rate_per_hour"] = self._item_data.get("rate_per_hour", 0.0)
            data["rate_per_unit"] = self._item_data.get("rate_per_unit", 0.0)

        # ← إصلاح: احفظ مصدر العنصر والتصنيف الحقيقي
        if current_co_id is not None:
            data["source_company_id"] = current_co_id
        cat_name = self._item_data.get("category_name")
        if cat_name:
            data["category_name"] = cat_name

        # تحقق من وجود تكرار
        existing = fetch_all_shared_items(self._conn, t)
        for ex in existing:
            if ex["name"].strip().lower() == name.lower():
                reply = QMessageBox.question(
                    self, tr("shared_exists_title"),
                    tr("shared_exists_msg").format(name=name),
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    shared_id = ex["id"]
                    self._link_companies(shared_id)
                    emit_company_data_changed()
                    QMessageBox.information(
                        self, tr("done"),
                        tr("shared_linked_msg").format(name=name)
                    )
                    self.accept()
                    return
                break

        shared_id = insert_shared_item(self._conn, name, t, data)
        self._link_companies(shared_id)
        emit_company_data_changed()
        QMessageBox.information(
            self, tr("done"),
            tr("shared_published_msg").format(name=name)
        )
        self.accept()

    def _link_companies(self, shared_id: int):
        for i in range(self.lst_companies.count()):
            item = self.lst_companies.item(i)
            if item.checkState() == Qt.Checked:
                co_id = item.data(Qt.UserRole)
                link_company(self._conn, shared_id, co_id)
