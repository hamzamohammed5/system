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

import json

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QPushButton, QDoubleSpinBox,
    QGroupBox, QListWidget, QListWidgetItem,
    QMessageBox, QFrame, QDialogButtonBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.companies.shared_items_repo import (
    fetch_shared_item, update_shared_item,
    fetch_linked_companies, link_company, unlink_company,
    get_item_data,
)
from db.companies.companies_repo import fetch_all_companies
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.theme import _C


def _spin(max_=9999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(32)
    return s


class SharedItemsDialog(QDialog):
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
        self._item_id = shared_item_id
        self._item    = None
        self._data    = {}

        self.setWindowTitle(tr("shared_item_header"))
        self.setMinimumSize(600, 500)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)

        self._load_item()
        self._build()
        self._populate()

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_item(self):
        self._item = fetch_shared_item(self._conn, self._item_id)
        if not self._item:
            return
        try:
            self._data = json.loads(self._item["data"]) if self._item["data"] else {}
        except Exception:
            self._data = {}

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        if not self._item:
            QLabel(tr("shared_item_not_found")).setParent(self)
            return

        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 12)

        # ── Header ──
        header = QLabel(
            f"🔗  {self._item['name']}  —  "
            f"<span style='color:{_C['text_muted']};'>{self._type_ar()}</span>"
        )
        header.setTextFormat(Qt.RichText)
        header.setStyleSheet(
            f"font-size:14px; font-weight:bold; color:{_C['acc_type_asset']};"
            f"background:{_C['t_account_dr_bg']}; border:1px solid {_C['accent_mid']};"
            "border-radius:8px; padding:8px 16px;"
        )
        root.addWidget(header)

        # ── بيانات العنصر ──
        data_grp = QGroupBox(tr("shared_item_data_section"))
        data_grp.setStyleSheet(f"""
            QGroupBox {{
                font-weight:bold; color:{_C['text_primary']};
                border:1px solid {_C['border']}; border-radius:8px;
                padding-top:10px; margin-top:6px;
            }}
            QGroupBox::title {{
                subcontrol-origin:margin; padding:0 8px;
                subcontrol-position:top right;
            }}
        """)
        data_lay = QFormLayout(data_grp)
        data_lay.setSpacing(10)
        data_lay.setLabelAlignment(Qt.AlignRight)

        # اسم العنصر
        self.inp_name = QLineEdit(self._item["name"])
        self.inp_name.setMinimumHeight(32)
        data_lay.addRow(tr("shared_name_colon"), self.inp_name)

        # حقول حسب النوع
        self._field_widgets = {}
        self._build_type_fields(data_lay)

        root.addWidget(data_grp)

        # ── الشركات المرتبطة ──
        companies_grp = QGroupBox(tr("shared_companies_section"))
        companies_grp.setStyleSheet(f"""
            QGroupBox {{
                font-weight:bold; color:{_C['text_primary']};
                border:1px solid {_C['border']}; border-radius:8px;
                padding-top:10px; margin-top:6px;
            }}
            QGroupBox::title {{
                subcontrol-origin:margin; padding:0 8px;
                subcontrol-position:top right;
            }}
        """)
        c_lay = QVBoxLayout(companies_grp)

        self.lst_companies = QListWidget()
        self.lst_companies.setMaximumHeight(130)
        self.lst_companies.setStyleSheet(f"""
            QListWidget {{
                border:1px solid {_C['border']}; border-radius:6px;
                font-size:11px;
            }}
            QListWidget::item {{ padding:5px 10px; }}
            QListWidget::item:selected {{
                background:{_C['accent_light']}; color:{_C['accent_text']};
            }}
        """)
        c_lay.addWidget(self.lst_companies)

        c_btn_row = QHBoxLayout()
        self.btn_link   = QPushButton(tr("shared_link_btn"))
        self.btn_unlink = QPushButton(tr("shared_unlink_btn"))
        self.btn_link.setStyleSheet(
            f"background:{_C['success_bg']}; color:{_C['success']};"
            f"border:1px solid {_C['success_border']};"
            "border-radius:4px; padding:4px 12px; font-weight:bold;"
        )
        self.btn_unlink.setStyleSheet(
            f"background:{_C['danger_bg']}; color:{_C['danger']};"
            f"border:1px solid {_C['danger_border']};"
            "border-radius:4px; padding:4px 12px; font-weight:bold;"
        )
        for btn in (self.btn_link, self.btn_unlink):
            btn.setMinimumHeight(30)
        self.btn_link.clicked.connect(self._link_company)
        self.btn_unlink.clicked.connect(self._unlink_company)
        c_btn_row.addWidget(self.btn_link)
        c_btn_row.addWidget(self.btn_unlink)
        c_btn_row.addStretch()
        c_lay.addLayout(c_btn_row)

        root.addWidget(companies_grp)

        # ── أزرار الحفظ ──
        btns = QDialogButtonBox()
        btn_save   = btns.addButton(tr("shared_save_btn"), QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton(tr("shared_close_btn"), QDialogButtonBox.RejectRole)
        btn_save.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_save.setStyleSheet(
            f"background:{_C['accent']}; color:{_C['bg_surface']}; font-weight:bold;"
            "border-radius:6px; padding:0 18px;"
        )
        btn_save.clicked.connect(self._save)
        btn_cancel.clicked.connect(self.reject)
        root.addWidget(btns)

    def _build_type_fields(self, form_lay: QFormLayout):
        """يبني حقول الإدخال حسب نوع العنصر المشترك."""
        t = self._item["shared_type"]

        if t == "raw":
            sp = _spin()
            sp.setValue(float(self._data.get("price", 0.0)))
            self._field_widgets["price"] = sp
            form_lay.addRow(tr("raw_price_lbl"), sp)

            sp2 = _spin()
            tq = self._data.get("total_qty")
            sp2.setValue(float(tq) if tq else 0.0)
            sp2.setSpecialValueText(tr("without_value"))
            self._field_widgets["total_qty"] = sp2
            form_lay.addRow(tr("raw_total_qty_lbl"), sp2)

            # معاينة سعر الوحدة
            self.lbl_unit = QLabel(tr("dash"))
            self.lbl_unit.setStyleSheet(
                f"color:{_C['acc_type_asset']}; font-weight:bold; font-size:11px;"
                f"background:{_C['t_account_dr_bg']}; border-radius:4px; padding:4px 8px;"
            )
            sp.valueChanged.connect(self._update_raw_preview)
            sp2.valueChanged.connect(self._update_raw_preview)
            form_lay.addRow(tr("raw_unit_preview_lbl"), self.lbl_unit)

        elif t == "machine":
            sp_h = _spin()
            sp_h.setValue(float(self._data.get("rate_per_hour", 0.0)))
            self._field_widgets["rate_per_hour"] = sp_h
            form_lay.addRow(tr("machine_rate_hour_lbl"), sp_h)

            sp_u = _spin()
            sp_u.setValue(float(self._data.get("rate_per_unit", 0.0)))
            self._field_widgets["rate_per_unit"] = sp_u
            form_lay.addRow(tr("machine_rate_unit_lbl"), sp_u)

        elif t == "labor_op":
            sp = _spin(9999, 2)
            sp.setValue(float(self._data.get("minutes", 0.0)))
            self._field_widgets["minutes"] = sp
            form_lay.addRow(tr("labor_time_lbl"), sp)

        elif t == "machine_op":
            sp = _spin()
            sp.setValue(float(self._data.get("value", 0.0)))
            self._field_widgets["value"] = sp
            mode = self._data.get("mode", "time")
            lbl  = tr("labor_time_lbl") if mode == "time" else tr("quantity")
            form_lay.addRow(lbl, sp)

            lbl_machine = QLabel(self._data.get("machine_name", tr("dash")))
            lbl_machine.setStyleSheet(f"color:{_C['text_muted']}; font-size:11px;")
            form_lay.addRow(tr("machine_name_col"), lbl_machine)

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
        if not self._item:
            return
        self._load_companies_list()
        if self._item["shared_type"] == "raw":
            self._update_raw_preview()

    def _load_companies_list(self):
        self.lst_companies.clear()
        linked = {r["id"] for r in fetch_linked_companies(self._conn, self._item_id)}
        all_cos = fetch_all_companies(self._conn)
        for co in all_cos:
            item = QListWidgetItem(
                f"{'✅' if co['id'] in linked else '○'}  {co['name']}"
            )
            item.setData(Qt.UserRole, co["id"])
            item.setData(Qt.UserRole + 1, co["id"] in linked)
            if co["id"] in linked:
                from PyQt5.QtGui import QColor
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
        link_company(self._conn, self._item_id, co_id)
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
            unlink_company(self._conn, self._item_id, co_id)
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
        t = self._item["shared_type"]

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

        update_shared_item(self._conn, self._item_id, name, new_data)
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
        }.get(self._item["shared_type"] if self._item else "", tr("name"))