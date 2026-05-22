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
from ui.events import bus


def _spin(max_=9999999, dec=4):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(32)
    return s


class PublishAsSharedDialog(QDialog):
    def __init__(self, central_conn, shared_type: str,
                 item_name: str, item_data: dict, parent=None):
        super().__init__(parent)
        self._conn        = central_conn
        self._shared_type = shared_type
        self._item_name   = item_name
        self._item_data   = item_data or {}

        self.setWindowTitle("📤  نشر عنصر كمشترك")
        self.setMinimumSize(480, 440)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(16, 16, 16, 12)

        lbl_hint = QLabel(
            "💡  العنصر المشترك يُحفظ مركزياً ويظهر في كل الشركات المختارة.\n"
            "    أي تعديل على بياناته سيتعكس فوراً على كل الشركات."
        )
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet(
            "background:#e3f2fd; border:1px solid #90caf9; border-radius:6px;"
            "padding:8px 12px; color:#1565c0; font-size:11px;"
        )
        root.addWidget(lbl_hint)

        data_grp = QGroupBox("بيانات العنصر المشترك")
        data_grp.setStyleSheet(
            "QGroupBox { font-weight:bold; border:1px solid #e0e0e0;"
            "border-radius:8px; padding-top:10px; margin-top:6px; }"
            "QGroupBox::title { subcontrol-origin:margin; padding:0 8px;"
            "subcontrol-position:top right; }"
        )
        data_lay = QFormLayout(data_grp)
        data_lay.setSpacing(10)
        data_lay.setLabelAlignment(Qt.AlignRight)

        self.inp_name = QLineEdit(self._item_name)
        self.inp_name.setMinimumHeight(32)
        data_lay.addRow("الاسم:", self.inp_name)

        self._field_widgets = {}
        self._build_type_fields(data_lay)

        root.addWidget(data_grp)

        cos_grp = QGroupBox("مشاركة مع الشركات")
        cos_grp.setStyleSheet(
            "QGroupBox { font-weight:bold; border:1px solid #e0e0e0;"
            "border-radius:8px; padding-top:10px; margin-top:6px; }"
            "QGroupBox::title { subcontrol-origin:margin; padding:0 8px;"
            "subcontrol-position:top right; }"
        )
        cos_lay = QVBoxLayout(cos_grp)

        self.lst_companies = QListWidget()
        self.lst_companies.setMaximumHeight(120)
        self.lst_companies.setStyleSheet(
            "QListWidget { border:1px solid #e0e0e0; border-radius:6px; }"
            "QListWidget::item { padding:5px 10px; }"
            "QListWidget::item:selected { background:#e3f2fd; color:#1565c0; }"
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
        btn_all  = QPushButton("✅ الكل")
        btn_none = QPushButton("☐ لا شيء")
        for btn in (btn_all, btn_none):
            btn.setMinimumHeight(26)
            btn.setMaximumWidth(90)
        btn_all.clicked.connect(lambda: self._check_all(True))
        btn_none.clicked.connect(lambda: self._check_all(False))
        quick_row.addWidget(QLabel("تحديد سريع:"))
        quick_row.addWidget(btn_all)
        quick_row.addWidget(btn_none)
        quick_row.addStretch()
        cos_lay.addLayout(quick_row)

        root.addWidget(cos_grp)

        btns = QDialogButtonBox()
        btn_ok     = btns.addButton("📤  نشر العنصر", QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton("✖  إلغاء",        QDialogButtonBox.RejectRole)
        btn_ok.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_ok.setStyleSheet(
            "background:#1565c0; color:white; font-weight:bold;"
            "border-radius:6px; padding:0 18px;"
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
            form_lay.addRow("السعر الكلي (جنيه):", sp)

            sp2 = _spin()
            tq = self._item_data.get("total_qty")
            sp2.setValue(float(tq) if tq else 0.0)
            sp2.setSpecialValueText("─ بدون")
            self._field_widgets["total_qty"] = sp2
            form_lay.addRow("الكمية الإجمالية:", sp2)

        elif t == "machine":
            sp_h = _spin()
            sp_h.setValue(float(self._item_data.get("rate_per_hour", 0.0)))
            self._field_widgets["rate_per_hour"] = sp_h
            form_lay.addRow("معدل / ساعة (جنيه):", sp_h)

            sp_u = _spin()
            sp_u.setValue(float(self._item_data.get("rate_per_unit", 0.0)))
            self._field_widgets["rate_per_unit"] = sp_u
            form_lay.addRow("معدل / وحدة (جنيه):", sp_u)

        elif t == "labor_op":
            sp = _spin(9999, 2)
            sp.setValue(float(self._item_data.get("minutes", 0.0)))
            self._field_widgets["minutes"] = sp
            form_lay.addRow("الوقت (دقيقة):", sp)

        elif t == "machine_op":
            sp = _spin()
            sp.setValue(float(self._item_data.get("value", 0.0)))
            self._field_widgets["value"] = sp
            form_lay.addRow("القيمة:", sp)

    def _check_all(self, checked: bool):
        for i in range(self.lst_companies.count()):
            self.lst_companies.item(i).setCheckState(
                Qt.Checked if checked else Qt.Unchecked
            )

    def _publish(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم العنصر")
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
                    self, "عنصر موجود",
                    f"يوجد عنصر مشترك باسم «{name}» بالفعل.\n"
                    "هل تريد استخدامه بدلاً من إنشاء نسخة جديدة؟",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    shared_id = ex["id"]
                    self._link_companies(shared_id)
                    bus.data_changed.emit()
                    QMessageBox.information(
                        self, "تم",
                        f"✅ تم ربط الشركات المختارة بالعنصر «{name}»"
                    )
                    self.accept()
                    return
                break

        shared_id = insert_shared_item(self._conn, name, t, data)
        self._link_companies(shared_id)
        bus.data_changed.emit()
        QMessageBox.information(
            self, "تم",
            f"✅ تم نشر «{name}» كعنصر مشترك وربطه بالشركات المختارة.\n"
            "سيظهر الآن في قوائم الشركات المشتركة فيه."
        )
        self.accept()

    def _link_companies(self, shared_id: int):
        for i in range(self.lst_companies.count()):
            item = self.lst_companies.item(i)
            if item.checkState() == Qt.Checked:
                co_id = item.data(Qt.UserRole)
                link_company(self._conn, shared_id, co_id)
