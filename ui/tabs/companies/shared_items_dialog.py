"""
ui/tabs/companies/shared_items_dialog.py
=========================================
SharedItemsDialog — نافذة تعديل عنصر مشترك واحد.
تُفتح من أزرار "تعديل المشترك" في الجداول المحلية.

المبدأ:
  - التعديل يكتب مباشرة في companies.db
  - التعكس فوري على كل الشركات المشتركة (بدون sync يدوي)
  - bus.data_changed يُطلق بعد الحفظ لتحديث كل الجداول

التحديثات:
  - إضافة زر "فك الربط" للشركة الحالية
  - الشركات المشتركة تظهر مع إمكانية الإضافة/الإزالة
"""

import json

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QDoubleSpinBox,
    QComboBox, QGroupBox, QFormLayout,
    QWidget, QCheckBox, QScrollArea, QMessageBox,
    QFrame,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from db.companies.shared_items_repo import (
    fetch_shared_item, update_shared_item,
    fetch_linked_companies, set_linked_companies,
    unlink_company,
)
from db.companies.companies_repo import fetch_all_companies
from db.companies.company_state  import company_state
from ui.events import bus

_TYPE_LABELS = {
    "raw":        "🧱 خامة",
    "machine":    "🖥️ ماكينة",
    "labor_op":   "👷 عملية عمالة",
    "machine_op": "⚙️ عملية تشغيل",
}

_ACCENT = "#1565c0"
_GREEN  = "#2e7d32"
_BORDER = "#e0e0e0"


def _spin(max_=9_999_999, dec=2) -> QDoubleSpinBox:
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(32)
    s.setStyleSheet("""
        QDoubleSpinBox {
            background: white; border: 1px solid #ddd;
            border-radius: 5px; padding: 3px 8px;
        }
        QDoubleSpinBox:focus { border-color: #1565c0; }
    """)
    return s


def _decode(data_str):
    try:
        return json.loads(data_str) if data_str else {}
    except Exception:
        return {}


class SharedItemsDialog(QDialog):
    """
    نافذة تعديل عنصر مشترك واحد + ربط الشركات + فك الربط.
    """

    saved = pyqtSignal()

    def __init__(self, central_conn, shared_id: int, parent=None):
        super().__init__(parent)
        self._central     = central_conn
        self._shared_id   = shared_id
        self._fields      = {}
        self._shared_type = None

        self.setModal(True)
        self.setMinimumWidth(520)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("QDialog { background: #f5f7fa; }")
        self._build()
        self._load()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header ──
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {_ACCENT}, stop:1 #1976d2);
                border-bottom: 2px solid #0d47a1;
            }}
        """)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)

        self._lbl_title = QLabel("تعديل عنصر مشترك")
        self._lbl_title.setStyleSheet(
            "font-weight:bold; font-size:14px; color:white;"
            "background:transparent; border:none;"
        )
        lbl_sub = QLabel("التعديل يتعكس فوراً على كل الشركات المشتركة")
        lbl_sub.setStyleSheet(
            "font-size:10px; color:#90caf9; background:transparent; border:none;"
        )
        txt_col = QVBoxLayout()
        txt_col.setSpacing(2)
        txt_col.addWidget(self._lbl_title)
        txt_col.addWidget(lbl_sub)
        h_lay.addLayout(txt_col)
        h_lay.addStretch()
        root.addWidget(header)

        # ── Body ──
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 8, 16, 8)
        body_lay.setSpacing(12)

        # ── اسم العنصر ──
        name_grp = QGroupBox("الاسم")
        name_grp.setStyleSheet(self._grp_style())
        name_lay = QVBoxLayout(name_grp)
        self._inp_name = QLineEdit()
        self._inp_name.setMinimumHeight(34)
        self._inp_name.setStyleSheet("""
            QLineEdit {
                background: white; border: 1px solid #ddd;
                border-radius: 5px; padding: 4px 10px; font-size: 13px;
            }
            QLineEdit:focus { border-color: #1565c0; }
        """)
        name_lay.addWidget(self._inp_name)
        body_lay.addWidget(name_grp)

        # ── بيانات العنصر (ديناميكي) ──
        self._data_grp = QGroupBox("البيانات")
        self._data_grp.setStyleSheet(self._grp_style())
        self._data_lay = QFormLayout(self._data_grp)
        self._data_lay.setSpacing(10)
        self._data_lay.setLabelAlignment(Qt.AlignRight)
        body_lay.addWidget(self._data_grp)

        # ── الشركات المشتركة ──
        comp_grp = QGroupBox("🏢  الشركات المشتركة في هذا العنصر")
        comp_grp.setStyleSheet(self._grp_style())
        comp_lay = QVBoxLayout(comp_grp)

        hint = QLabel("✅ ضع علامة على الشركات التي تريد مشاركة العنصر معها")
        hint.setStyleSheet(
            "color:#555; font-size:10px; background:#e8f5e9;"
            "border-radius:4px; padding:4px 8px; border: none;"
        )
        hint.setWordWrap(True)
        comp_lay.addWidget(hint)

        self._comp_scroll_widget = QWidget()
        self._comp_layout = QVBoxLayout(self._comp_scroll_widget)
        self._comp_layout.setSpacing(4)
        self._comp_layout.setContentsMargins(4, 4, 4, 4)

        comp_scroll = QScrollArea()
        comp_scroll.setWidgetResizable(True)
        comp_scroll.setMaximumHeight(160)
        comp_scroll.setStyleSheet("QScrollArea { border: none; background: white; }")
        comp_scroll.setWidget(self._comp_scroll_widget)

        comp_lay.addWidget(comp_scroll)

        # زر فك ربط الشركة الحالية
        self._btn_unlink = QPushButton("🔓  فك ربط شركتي من هذا العنصر")
        self._btn_unlink.setMinimumHeight(32)
        self._btn_unlink.setStyleSheet("""
            QPushButton {
                background: #fff3e0; color: #e65100;
                border: 1px solid #ffcc80; border-radius: 5px;
                font-size: 11px; font-weight: bold; padding: 0 12px;
            }
            QPushButton:hover { background: #ffe0b2; }
        """)
        self._btn_unlink.clicked.connect(self._unlink_current_company)
        comp_lay.addWidget(self._btn_unlink)

        body_lay.addWidget(comp_grp)

        # ── تحذير التأثير ──
        warn = QLabel(
            "⚠️  أي تعديل على البيانات أعلاه يُطبَّق فوراً على كل الشركات "
            "المشتركة في هذا العنصر دون الحاجة لأي خطوة إضافية."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet(
            "color:#e65100; font-size:10px; background:#fff3e0;"
            "border:1px solid #ffcc80; border-radius:4px; padding:6px 10px;"
        )
        body_lay.addWidget(warn)

        root.addWidget(body)

        # ── أزرار ──
        footer = QFrame()
        footer.setStyleSheet(f"QFrame {{ background: white; border-top: 1px solid {_BORDER}; }}")
        btn_row = QHBoxLayout(footer)
        btn_row.setContentsMargins(16, 10, 16, 10)
        btn_row.setSpacing(8)

        btn_save = QPushButton("💾  حفظ التغييرات")
        btn_save.setMinimumHeight(38)
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {_GREEN}; color: white;
                border: none; border-radius: 6px;
                font-weight: bold; font-size: 13px; padding: 0 20px;
            }}
            QPushButton:hover {{ background: #1b5e38; }}
        """)
        btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: #f5f5f5; color: #555;
                border: 1px solid {_BORDER}; border-radius: 6px;
                padding: 0 16px;
            }}
            QPushButton:hover {{ background: #eeeeee; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        btn_row.addWidget(btn_save)
        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        root.addWidget(footer)

        self._checkboxes: dict[int, QCheckBox] = {}

    def _grp_style(self):
        return f"""
            QGroupBox {{
                background: white; border: 1px solid {_BORDER};
                border-radius: 8px; font-weight: bold; color: {_ACCENT};
                padding-top: 12px; margin-top: 4px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
            }}
        """

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
        type_label = _TYPE_LABELS.get(self._shared_type, self._shared_type)

        self.setWindowTitle(f"تعديل {type_label} — مشترك")
        self._lbl_title.setText(f"تعديل {type_label}  —  مشترك بين الشركات")
        self._data_grp.setTitle(f"📊  بيانات {type_label}")

        self._inp_name.setText(row["name"])

        data = _decode(row["data"])
        self._build_data_fields(self._shared_type, data)
        self._load_companies()

        # لو الشركة الحالية مش مربوطة، نخفي زر فك الربط
        current_id = company_state.company_id
        linked_ids = {r["id"] for r in fetch_linked_companies(self._central, self._shared_id)}
        self._btn_unlink.setVisible(current_id in linked_ids)

    def _build_data_fields(self, shared_type: str, data: dict):
        while self._data_lay.rowCount():
            self._data_lay.removeRow(0)
        self._fields.clear()

        lbl_ss = "font-weight: bold; color: #555;"

        if shared_type == "raw":
            sp_price = _spin()
            sp_price.setValue(data.get("price", 0.0))
            sp_qty = _spin()
            sp_qty.setSpecialValueText("—")
            tq = data.get("total_qty")
            sp_qty.setValue(float(tq) if tq else 0.0)

            lbl1 = QLabel("السعر الكلي (جنيه):"); lbl1.setStyleSheet(lbl_ss)
            lbl2 = QLabel("الكمية الكلية (0 = بدون):"); lbl2.setStyleSheet(lbl_ss)

            self._data_lay.addRow(lbl1, sp_price)
            self._data_lay.addRow(lbl2, sp_qty)
            self._fields["price"]     = sp_price
            self._fields["total_qty"] = sp_qty

            self._lbl_unit_preview = QLabel("─")
            self._lbl_unit_preview.setStyleSheet(
                "color: #1565c0; font-weight: bold;"
                "background: #e3f2fd; border-radius: 4px; padding: 4px 8px;"
            )
            sp_price.valueChanged.connect(self._update_raw_preview)
            sp_qty.valueChanged.connect(self._update_raw_preview)
            self._data_lay.addRow(QLabel("سعر الوحدة:"), self._lbl_unit_preview)
            self._update_raw_preview()

        elif shared_type == "machine":
            sp_h = _spin(); sp_h.setValue(data.get("rate_per_hour", 0.0))
            sp_u = _spin(); sp_u.setValue(data.get("rate_per_unit", 0.0))
            lbl1 = QLabel("معدل / ساعة (جنيه):"); lbl1.setStyleSheet(lbl_ss)
            lbl2 = QLabel("معدل / وحدة (جنيه):"); lbl2.setStyleSheet(lbl_ss)
            self._data_lay.addRow(lbl1, sp_h)
            self._data_lay.addRow(lbl2, sp_u)
            self._fields["rate_per_hour"] = sp_h
            self._fields["rate_per_unit"] = sp_u

        elif shared_type == "labor_op":
            sp_m = _spin(99_999, 2); sp_m.setValue(data.get("minutes", 0.0))
            lbl1 = QLabel("الوقت (دقيقة):"); lbl1.setStyleSheet(lbl_ss)
            self._data_lay.addRow(lbl1, sp_m)
            self._fields["minutes"] = sp_m

        elif shared_type == "machine_op":
            inp_machine = QLineEdit()
            inp_machine.setText(data.get("machine_name", ""))
            inp_machine.setMinimumHeight(32)
            inp_machine.setStyleSheet("""
                QLineEdit {
                    background: white; border: 1px solid #ddd;
                    border-radius: 5px; padding: 3px 8px;
                }
                QLineEdit:focus { border-color: #1565c0; }
            """)

            cmb_mode = QComboBox(); cmb_mode.setMinimumHeight(32)
            cmb_mode.addItem("⏱  بالوقت (time)", "time")
            cmb_mode.addItem("📦  بالوحدة (unit)", "unit")
            cmb_mode.setCurrentIndex(0 if data.get("mode", "time") == "time" else 1)

            sp_val = _spin(); sp_val.setValue(data.get("value", 0.0))
            sp_rh  = _spin(); sp_rh.setValue(data.get("rate_per_hour", 0.0))
            sp_ru  = _spin(); sp_ru.setValue(data.get("rate_per_unit", 0.0))

            def _lbl(t):
                l = QLabel(t); l.setStyleSheet(lbl_ss); return l

            self._data_lay.addRow(_lbl("اسم الماكينة:"),     inp_machine)
            self._data_lay.addRow(_lbl("وضع الحساب:"),       cmb_mode)
            self._data_lay.addRow(_lbl("القيمة:"),            sp_val)
            self._data_lay.addRow(_lbl("معدل / ساعة (جنيه):"), sp_rh)
            self._data_lay.addRow(_lbl("معدل / وحدة (جنيه):"), sp_ru)

            self._fields["machine_name"]  = inp_machine
            self._fields["mode"]          = cmb_mode
            self._fields["value"]         = sp_val
            self._fields["rate_per_hour"] = sp_rh
            self._fields["rate_per_unit"] = sp_ru

    def _update_raw_preview(self):
        try:
            price = self._fields["price"].value()
            tq    = self._fields["total_qty"].value()
            if tq > 0 and price > 0:
                unit = price / tq
                self._lbl_unit_preview.setText(
                    f"{price:.2f} ÷ {tq:.4g} = {unit:.4f} جنيه/وحدة"
                )
            elif price > 0:
                self._lbl_unit_preview.setText(f"{price:.2f} جنيه/وحدة (بدون تقسيم)")
            else:
                self._lbl_unit_preview.setText("─")
        except Exception:
            pass

    def _load_companies(self):
        for i in reversed(range(self._comp_layout.count())):
            item = self._comp_layout.takeAt(i)
            if item and item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()

        try:
            all_companies = fetch_all_companies(self._central)
            linked_ids = {
                r["id"] for r in fetch_linked_companies(self._central, self._shared_id)
            }
        except Exception:
            all_companies = []
            linked_ids = set()

        current_id = company_state.company_id

        for company in all_companies:
            cb = QCheckBox(f"  {company['name']}")
            cb.setChecked(company["id"] in linked_ids)
            color = company["color"] or _ACCENT

            # الشركة الحالية دايماً محددة ومقفولة
            if company["id"] == current_id:
                cb.setEnabled(False)
                cb.setToolTip("شركتك الحالية — لا يمكن إلغاء ربطها من هنا\nاستخدم «فك الربط» أدناه")

            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {color}; font-size: 12px; padding: 4px 8px;
                    border-radius: 4px;
                }}
                QCheckBox:hover {{ background: #f5f5f5; }}
                QCheckBox::indicator {{
                    width: 18px; height: 18px;
                    border: 2px solid #ccc; border-radius: 4px;
                    background: white;
                }}
                QCheckBox::indicator:checked {{
                    background: {color}; border-color: {color};
                }}
                QCheckBox::indicator:disabled {{
                    background: {color}; border-color: {color};
                }}
            """)

            def _on_toggle(checked, cb=cb):
                f = cb.font(); f.setBold(checked); cb.setFont(f)
            cb.toggled.connect(_on_toggle)
            # تطبيق bold على المحدد حالاً
            f = cb.font(); f.setBold(company["id"] in linked_ids); cb.setFont(f)

            self._checkboxes[company["id"]] = cb
            self._comp_layout.addWidget(cb)

        self._comp_layout.addStretch()

    # ══════════════════════════════════════════════════════
    # فك ربط الشركة الحالية
    # ══════════════════════════════════════════════════════

    def _unlink_current_company(self):
        current_id = company_state.company_id
        if not current_id:
            return
        row = fetch_shared_item(self._central, self._shared_id)
        name = row["name"] if row else f"ID:{self._shared_id}"

        if QMessageBox.question(
            self, "تأكيد فك الربط",
            f"فك ربط شركتك من العنصر المشترك «{name}»؟\n\n"
            "لن يُحذف العنصر من الشركات الأخرى، لكنه سيختفي من شركتك.",
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        try:
            unlink_company(self._central, self._shared_id, current_id)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return

        bus.data_changed.emit()
        self.saved.emit()
        self.accept()

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
        # تأكد إن الشركة الحالية دايماً في القائمة
        current_id = company_state.company_id
        if current_id and current_id not in selected_company_ids:
            selected_company_ids.append(current_id)

        try:
            update_shared_item(self._central, self._shared_id, name, data)
            set_linked_companies(self._central, self._shared_id, selected_company_ids)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return

        try:
            bus.data_changed.emit()
        except Exception:
            pass

        self.saved.emit()
        self.accept()