"""
ui/tabs/companies/shared_items_dialog.py
=========================================
SharedItemsDialog — نافذة خفيفة لعرض/تعديل عنصر مشترك واحد.
تُفتح من أزرار "تعديل المشترك" في الجداول المحلية.

الفرق عن SharedItemsManagerDialog:
  - مركّزة على عنصر واحد محدد مسبقاً
  - أسرع وأبسط — بدون قائمة عناصر جانبية
  - بعد الحفظ تطلق bus.data_changed مباشرة
"""

import json

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QDoubleSpinBox,
    QComboBox, QGroupBox, QFormLayout,
    QWidget, QCheckBox, QScrollArea, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.companies.shared_items_repo import (
    fetch_shared_item, update_shared_item,
    fetch_linked_companies, set_linked_companies,
)
from db.companies.companies_repo import fetch_all_companies
from ui.events import bus

_TYPE_LABELS = {
    "raw":        "🧱 خامة",
    "machine":    "🖥️ ماكينة",
    "labor_op":   "👷 عملية عمالة",
    "machine_op": "⚙️ عملية تشغيل",
}


def _spin(max_=9_999_999, dec=2) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _decode(data_str):
    try:
        return json.loads(data_str) if data_str else {}
    except Exception:
        return {}


class SharedItemsDialog(QDialog):
    """
    نافذة تعديل عنصر مشترك واحد + ربط الشركات.
    تُستخدم من:
      raw_table_panel.py   → btn_edit_shared
      machine_table.py     → btn_edit_shared
      labor_op_table.py    → btn_edit_shared
    """

    saved = pyqtSignal()  # يُطلق بعد الحفظ

    def __init__(self, central_conn, shared_id: int, parent=None):
        super().__init__(parent)
        self._central   = central_conn
        self._shared_id = shared_id
        self._fields    = {}
        self._shared_type = None

        self.setModal(True)
        self.setMinimumWidth(480)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()
        self._load()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(10)
        root.setContentsMargins(16, 14, 16, 14)

        # ── Header ──
        self._lbl_title = QLabel("تعديل عنصر مشترك")
        self._lbl_title.setStyleSheet(
            "font-weight:bold; font-size:14px; color:#2e7d52;"
        )
        root.addWidget(self._lbl_title)

        # ── اسم العنصر ──
        name_grp = QGroupBox("الاسم")
        name_lay = QVBoxLayout(name_grp)
        self._inp_name = QLineEdit()
        self._inp_name.setMinimumHeight(32)
        name_lay.addWidget(self._inp_name)
        root.addWidget(name_grp)

        # ── بيانات العنصر (ديناميكي) ──
        self._data_grp = QGroupBox("البيانات")
        self._data_lay = QFormLayout(self._data_grp)
        self._data_lay.setSpacing(8)
        self._data_lay.setLabelAlignment(Qt.AlignRight)
        root.addWidget(self._data_grp)

        # ── الشركات المشتركة ──
        comp_grp = QGroupBox("الشركات المشتركة")
        comp_lay = QVBoxLayout(comp_grp)

        self._comp_scroll_widget = QWidget()
        self._comp_layout        = QVBoxLayout(self._comp_scroll_widget)
        self._comp_layout.setSpacing(4)
        self._comp_layout.setContentsMargins(4, 4, 4, 4)

        comp_scroll = QScrollArea()
        comp_scroll.setWidgetResizable(True)
        comp_scroll.setMaximumHeight(160)
        comp_scroll.setStyleSheet("border:none;")
        comp_scroll.setWidget(self._comp_scroll_widget)

        comp_lay.addWidget(comp_scroll)
        hint = QLabel("✅ ضع علامة على الشركات التي تريد مشاركة العنصر معها")
        hint.setStyleSheet(
            "color:#666; font-size:10px; "
            "background:#f0f4ff; border-radius:4px; padding:4px 8px;"
        )
        hint.setWordWrap(True)
        comp_lay.addWidget(hint)
        root.addWidget(comp_grp)

        # ── أزرار ──
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        btn_save = QPushButton("💾  حفظ التغييرات")
        btn_save.setMinimumHeight(36)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #2e7d52; color: white;
                border: none; border-radius: 6px;
                font-weight: bold; padding: 0 18px;
            }
            QPushButton:hover { background: #1b5e38; }
        """)
        btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        root.addLayout(btn_row)

        self._checkboxes: dict[int, QCheckBox] = {}

    # ══════════════════════════════════════════════════════
    # تحميل بيانات العنصر
    # ══════════════════════════════════════════════════════

    def _load(self):
        try:
            row = fetch_shared_item(self._central, self._shared_id)
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
            self.reject()
            return

        if not row:
            QMessageBox.warning(self, "تنبيه", "العنصر غير موجود")
            self.reject()
            return

        self._shared_type = row["shared_type"]
        type_label        = _TYPE_LABELS.get(self._shared_type, self._shared_type)

        self.setWindowTitle(f"تعديل {type_label}")
        self._lbl_title.setText(f"تعديل {type_label}  —  مشترك بين الشركات")
        self._data_grp.setTitle(f"بيانات {type_label}")

        self._inp_name.setText(row["name"])

        data = _decode(row["data"])
        self._build_data_fields(self._shared_type, data)
        self._load_companies()

    def _build_data_fields(self, shared_type: str, data: dict):
        """بناء حقول البيانات حسب نوع العنصر."""
        while self._data_lay.rowCount():
            self._data_lay.removeRow(0)
        self._fields.clear()

        if shared_type == "raw":
            sp_price = _spin()
            sp_price.setValue(data.get("price", 0.0))
            sp_qty = _spin()
            sp_qty.setSpecialValueText("—")
            tq = data.get("total_qty")
            sp_qty.setValue(float(tq) if tq else 0.0)
            self._data_lay.addRow("السعر الكلي :", sp_price)
            self._data_lay.addRow("الكمية الكلية :", sp_qty)
            self._fields["price"]     = sp_price
            self._fields["total_qty"] = sp_qty

        elif shared_type == "machine":
            sp_h = _spin()
            sp_h.setValue(data.get("rate_per_hour", 0.0))
            sp_u = _spin()
            sp_u.setValue(data.get("rate_per_unit", 0.0))
            self._data_lay.addRow("جنيه / ساعة :", sp_h)
            self._data_lay.addRow("جنيه / وحدة :", sp_u)
            self._fields["rate_per_hour"] = sp_h
            self._fields["rate_per_unit"] = sp_u

        elif shared_type == "labor_op":
            sp_m = _spin(99_999, 2)
            sp_m.setValue(data.get("minutes", 0.0))
            self._data_lay.addRow("الوقت (دقيقة) :", sp_m)
            self._fields["minutes"] = sp_m

        elif shared_type == "machine_op":
            inp_machine = QLineEdit()
            inp_machine.setText(data.get("machine_name", ""))
            inp_machine.setMinimumHeight(30)
            cmb_mode = QComboBox()
            cmb_mode.addItem("⏱ وقت (time)", "time")
            cmb_mode.addItem("📦 وحدة (unit)", "unit")
            cmb_mode.setCurrentIndex(0 if data.get("mode", "time") == "time" else 1)
            sp_val = _spin()
            sp_val.setValue(data.get("value", 0.0))
            sp_rh = _spin()
            sp_rh.setValue(data.get("rate_per_hour", 0.0))
            sp_ru = _spin()
            sp_ru.setValue(data.get("rate_per_unit", 0.0))
            self._data_lay.addRow("اسم الماكينة :", inp_machine)
            self._data_lay.addRow("وضع الحساب :",   cmb_mode)
            self._data_lay.addRow("القيمة :",        sp_val)
            self._data_lay.addRow("جنيه / ساعة :",  sp_rh)
            self._data_lay.addRow("جنيه / وحدة :",  sp_ru)
            self._fields["machine_name"]  = inp_machine
            self._fields["mode"]          = cmb_mode
            self._fields["value"]         = sp_val
            self._fields["rate_per_hour"] = sp_rh
            self._fields["rate_per_unit"] = sp_ru

    def _load_companies(self):
        """تحميل قائمة الشركات مع تحديد المشتركة."""
        for i in reversed(range(self._comp_layout.count())):
            item = self._comp_layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()

        try:
            all_companies = fetch_all_companies(self._central)
            linked_ids    = {
                r["id"] for r in fetch_linked_companies(self._central, self._shared_id)
            }
        except Exception:
            all_companies = []
            linked_ids    = set()

        for company in all_companies:
            cb = QCheckBox(company["name"])
            cb.setChecked(company["id"] in linked_ids)
            color = company["color"] or "#1565c0"
            cb.setStyleSheet(f"""
                QCheckBox {{ color: #333; padding: 3px 6px; }}
                QCheckBox::indicator:checked {{
                    background: {color};
                    border-color: {color};
                }}
            """)
            self._checkboxes[company["id"]] = cb
            self._comp_layout.addWidget(cb)
        self._comp_layout.addStretch()

    # ══════════════════════════════════════════════════════
    # جمع البيانات وحفظها
    # ══════════════════════════════════════════════════════

    def _collect_data(self) -> dict:
        st = self._shared_type
        if st == "raw":
            tq = self._fields["total_qty"].value()
            return {
                "price":     self._fields["price"].value(),
                "total_qty": tq if tq > 0 else None,
            }
        elif st == "machine":
            return {
                "rate_per_hour": self._fields["rate_per_hour"].value(),
                "rate_per_unit": self._fields["rate_per_unit"].value(),
            }
        elif st == "labor_op":
            return {"minutes": self._fields["minutes"].value()}
        elif st == "machine_op":
            return {
                "machine_name":  self._fields["machine_name"].text().strip(),
                "mode":          self._fields["mode"].currentData(),
                "value":         self._fields["value"].value(),
                "rate_per_hour": self._fields["rate_per_hour"].value(),
                "rate_per_unit": self._fields["rate_per_unit"].value(),
            }
        return {}

    def _save(self):
        name = self._inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل الاسم أولاً")
            return

        data = self._collect_data()
        selected_company_ids = [
            cid for cid, cb in self._checkboxes.items() if cb.isChecked()
        ]

        try:
            # 1. تحديث بيانات العنصر في companies.db
            update_shared_item(self._central, self._shared_id, name, data)

            # 2. تحديث ربط الشركات
            set_linked_companies(self._central, self._shared_id, selected_company_ids)

        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return

        # 3. إطلاق bus.data_changed → كل الجداول المفتوحة تتحدث فوراً
        try:
            bus.data_changed.emit()
        except Exception:
            pass

        self.saved.emit()
        self.accept()