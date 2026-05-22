"""
ui/tabs/companies/shared_items_manager_helper/_add_sharedItem_dialog.py
=========================================================================
PublishAsSharedDialog — نافذة "نشر عنصر محلي كمشترك بين الشركات".

تُفتح من:
  - raw_table_panel.py   (زر "🔗 نشر كمشترك")
  - machine_table.py     (زر "🔗 نشر كمشترك")
  - labor_op_table.py    (زر "🔗 نشر كمشترك")

المنطق:
  1. يعرض بيانات العنصر المحلي المختار (اسم + بيانات)
  2. يتيح اختيار الشركات اللي هتشارك فيه
  3. عند التأكيد:
     - يُضاف العنصر لـ shared_items في companies.db
     - تُربط الشركات المختارة + الشركة الحالية تلقائياً
  4. بعد النشر، الشركات المشتركة تشوف العنصر بـ 🔗

ملاحظة:
  - لو العنصر منشور بالفعل، يُعرض مع خيار تحديث الربط فقط
"""

import json
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QCheckBox, QScrollArea, QWidget,
    QFrame, QGroupBox, QMessageBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.companies.shared_items_repo import (
    insert_shared_item, fetch_all_shared_items,
    link_company, set_linked_companies, fetch_linked_companies,
    fetch_shared_item,
)
from db.companies.companies_repo import fetch_all_companies
from db.companies.company_state  import company_state
from ui.events import bus

_ACCENT = "#1565c0"
_GREEN  = "#2e7d32"
_BORDER = "#e0e0e0"

_TYPE_LABELS = {
    "raw":        ("🧱", "خامة"),
    "machine":    ("⚙️", "ماكينة"),
    "labor_op":   ("👷", "عملية عمالة"),
    "machine_op": ("🔩", "عملية تشغيل"),
}


def _encode(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


class PublishAsSharedDialog(QDialog):
    """
    نافذة نشر عنصر محلي كمشترك بين الشركات.

    الاستخدام:
        dlg = PublishAsSharedDialog(
            central_conn = central_conn,
            shared_type  = "raw",          # نوع العنصر
            item_name    = "قطن أبيض",     # اسم العنصر
            item_data    = {"price": 100, "total_qty": 50},  # بيانات العنصر
            parent       = self
        )
        if dlg.exec_() == QDialog.Accepted:
            bus.data_changed.emit()
    """

    def __init__(self, central_conn, shared_type: str,
                 item_name: str, item_data: dict, parent=None):
        super().__init__(parent)
        self._central     = central_conn
        self._shared_type = shared_type
        self._item_name   = item_name
        self._item_data   = item_data or {}
        self._existing_id = None   # لو العنصر منشور بالفعل

        icon, type_label = _TYPE_LABELS.get(shared_type, ("🔗", "عنصر"))
        self.setWindowTitle(f"🔗  نشر {type_label} كمشترك بين الشركات")
        self.setMinimumWidth(480)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self.setStyleSheet("QDialog { background: #f5f7fa; }")

        self._build(icon, type_label)
        self._check_existing()
        self._load_companies()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self, icon: str, type_label: str):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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

        lbl_icon = QLabel(f"{icon}")
        lbl_icon.setStyleSheet("font-size:20px; background:transparent; border:none;")

        lbl_title = QLabel(f"نشر {type_label} كمشترك")
        lbl_title.setStyleSheet(
            "font-weight:bold; font-size:14px; color:white;"
            "background:transparent; border:none;"
        )
        lbl_sub = QLabel("ستظهر في كل الشركات المشتركة بأيقونة 🔗")
        lbl_sub.setStyleSheet(
            "font-size:10px; color:#90caf9; background:transparent; border:none;"
        )
        txt = QVBoxLayout(); txt.setSpacing(1)
        txt.addWidget(lbl_title); txt.addWidget(lbl_sub)
        h_lay.addWidget(lbl_icon)
        h_lay.addSpacing(8)
        h_lay.addLayout(txt)
        h_lay.addStretch()
        root.addWidget(header)

        # ── Body ──
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 12, 16, 12)
        body_lay.setSpacing(12)

        # ── معلومات العنصر ──
        info_grp = QGroupBox(f"بيانات {type_label}")
        info_grp.setStyleSheet(self._grp_style())
        info_lay = QVBoxLayout(info_grp)

        self._lbl_item_info = QLabel()
        self._lbl_item_info.setWordWrap(True)
        self._lbl_item_info.setStyleSheet(
            "font-size:12px; color:#333; background:transparent; border:none;"
        )
        self._lbl_item_info.setText(self._build_item_info_text())
        info_lay.addWidget(self._lbl_item_info)

        self._lbl_existing_warning = QLabel(
            "⚠️  هذا العنصر منشور بالفعل — ستقوم بتحديث الربط فقط"
        )
        self._lbl_existing_warning.setStyleSheet(
            "color:#e65100; font-size:11px; background:#fff3e0;"
            "border:1px solid #ffcc80; border-radius:4px; padding:5px 8px;"
        )
        self._lbl_existing_warning.setWordWrap(True)
        self._lbl_existing_warning.setVisible(False)
        info_lay.addWidget(self._lbl_existing_warning)
        body_lay.addWidget(info_grp)

        # ── اختيار الشركات ──
        comp_grp = QGroupBox("🏢  اختر الشركات المشاركة")
        comp_grp.setStyleSheet(self._grp_style())
        comp_lay = QVBoxLayout(comp_grp)

        hint = QLabel("✅ اختر الشركات التي ستشارك في هذا العنصر.\n"
                       "الشركة الحالية مربوطة تلقائياً ولا يمكن إلغاؤها.")
        hint.setWordWrap(True)
        hint.setStyleSheet(
            "font-size:10px; color:#555; background:#e8f5e9;"
            "border-radius:4px; padding:5px 8px; border:none;"
        )
        comp_lay.addWidget(hint)

        scroll_widget = QWidget()
        self._comp_layout = QVBoxLayout(scroll_widget)
        self._comp_layout.setSpacing(3)
        self._comp_layout.setContentsMargins(4, 4, 4, 4)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(180)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #e0e0e0; background: white; }")
        scroll.setWidget(scroll_widget)
        comp_lay.addWidget(scroll)

        body_lay.addWidget(comp_grp)

        # ── تحذير التأثير ──
        warn = QLabel(
            "🔗  بعد النشر، أي تعديل على هذا العنصر من أي شركة مشتركة\n"
            "يُطبَّق فوراً على الكل بدون أي خطوة إضافية."
        )
        warn.setWordWrap(True)
        warn.setStyleSheet(
            "color:#1565c0; font-size:10px; background:#e3f2fd;"
            "border:1px solid #90caf9; border-radius:4px; padding:6px 10px;"
        )
        body_lay.addWidget(warn)

        root.addWidget(body)

        # ── Footer ──
        footer = QFrame()
        footer.setStyleSheet(f"QFrame {{ background:white; border-top:1px solid {_BORDER}; }}")
        f_lay = QHBoxLayout(footer)
        f_lay.setContentsMargins(16, 10, 16, 10)
        f_lay.setSpacing(8)

        self._btn_publish = QPushButton("🔗  نشر كمشترك")
        self._btn_publish.setMinimumHeight(38)
        self._btn_publish.setStyleSheet(f"""
            QPushButton {{
                background: {_GREEN}; color: white; font-weight: bold;
                border: none; border-radius: 6px; font-size: 13px; padding: 0 20px;
            }}
            QPushButton:hover {{ background: #1b5e38; }}
        """)
        self._btn_publish.clicked.connect(self._publish)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: #f5f5f5; color: #555;
                border: 1px solid {_BORDER}; border-radius: 6px; padding: 0 16px;
            }}
            QPushButton:hover {{ background: #eeeeee; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        f_lay.addWidget(self._btn_publish)
        f_lay.addStretch()
        f_lay.addWidget(btn_cancel)
        root.addWidget(footer)

        self._checkboxes: dict[int, QCheckBox] = {}

    def _grp_style(self) -> str:
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

    def _build_item_info_text(self) -> str:
        lines = [f"<b>الاسم:</b> {self._item_name}"]
        st = self._shared_type
        d  = self._item_data
        if st == "raw":
            lines.append(f"<b>السعر:</b> {d.get('price', 0):.2f} جنيه")
            tq = d.get("total_qty")
            if tq:
                lines.append(f"<b>الكمية الكلية:</b> {tq}")
                lines.append(f"<b>سعر الوحدة:</b> {float(d.get('price',0))/float(tq):.4f} جنيه")
        elif st == "machine":
            lines.append(f"<b>معدل الساعة:</b> {d.get('rate_per_hour', 0):.2f} جنيه/ساعة")
            lines.append(f"<b>معدل الوحدة:</b> {d.get('rate_per_unit', 0):.2f} جنيه/وحدة")
        elif st == "labor_op":
            lines.append(f"<b>الوقت:</b> {d.get('minutes', 0):.2f} دقيقة")
        elif st == "machine_op":
            mode = "بالوقت" if d.get("mode") == "time" else "بالوحدة"
            lines.append(f"<b>وضع الحساب:</b> {mode}")
            lines.append(f"<b>القيمة:</b> {d.get('value', 0):.4f}")
        return "  |  ".join(lines)

    # ══════════════════════════════════════════════════════
    # تحقق من وجود مسبق
    # ══════════════════════════════════════════════════════

    def _check_existing(self):
        """هل هذا العنصر منشور بالفعل بنفس الاسم والنوع؟"""
        try:
            rows = fetch_all_shared_items(self._central, self._shared_type)
            for r in rows:
                if r["name"].strip() == self._item_name.strip():
                    self._existing_id = r["id"]
                    self._lbl_existing_warning.setVisible(True)
                    self._btn_publish.setText("🔄  تحديث الربط")
                    break
        except Exception:
            pass

    # ══════════════════════════════════════════════════════
    # تحميل الشركات
    # ══════════════════════════════════════════════════════

    def _load_companies(self):
        current_id = company_state.company_id

        # الشركات المرتبطة بالفعل لو منشور
        linked_ids: set[int] = {current_id} if current_id else set()
        if self._existing_id:
            try:
                for r in fetch_linked_companies(self._central, self._existing_id):
                    linked_ids.add(r["id"])
            except Exception:
                pass

        try:
            companies = fetch_all_companies(self._central, active_only=True)
        except Exception:
            companies = []

        # حذف checkboxes القديمة
        while self._comp_layout.count():
            item = self._comp_layout.takeAt(0)
            if item and item.widget():
                item.widget().deleteLater()
        self._checkboxes.clear()

        for comp in companies:
            cid = comp["id"]
            cb  = QCheckBox(f"  {comp['name']}")
            cb.setChecked(cid in linked_ids)

            # الشركة الحالية مقفولة دايماً
            if cid == current_id:
                cb.setEnabled(False)
                cb.setToolTip("الشركة الحالية — مربوطة دايماً")

            color = comp.get("color") or _ACCENT
            cb.setStyleSheet(f"""
                QCheckBox {{
                    color: {color}; font-size: 12px; padding: 4px 8px;
                    border-radius: 4px;
                }}
                QCheckBox:hover {{ background: #f5f5f5; }}
                QCheckBox::indicator {{
                    width: 17px; height: 17px;
                    border: 2px solid #ccc; border-radius: 3px;
                    background: white;
                }}
                QCheckBox::indicator:checked {{
                    background: {color}; border-color: {color};
                }}
                QCheckBox::indicator:disabled {{
                    background: {color}; border-color: {color}; opacity: 0.6;
                }}
            """)
            self._checkboxes[cid] = cb
            self._comp_layout.addWidget(cb)

        self._comp_layout.addStretch()

    # ══════════════════════════════════════════════════════
    # النشر
    # ══════════════════════════════════════════════════════

    def _publish(self):
        selected_ids = [cid for cid, cb in self._checkboxes.items() if cb.isChecked()]
        if not selected_ids:
            QMessageBox.warning(self, "تنبيه", "اختر شركة واحدة على الأقل")
            return

        try:
            if self._existing_id:
                # تحديث الربط فقط
                set_linked_companies(self._central, self._existing_id, selected_ids)
            else:
                # إنشاء عنصر مشترك جديد
                shared_id = insert_shared_item(
                    self._central,
                    name        = self._item_name,
                    shared_type = self._shared_type,
                    data        = self._item_data,
                )
                set_linked_companies(self._central, shared_id, selected_ids)

        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return

        bus.data_changed.emit()
        self.accept()


# ══════════════════════════════════════════════════════════
# دالة مساعدة سريعة — تُستخدم من الجداول
# ══════════════════════════════════════════════════════════

def publish_item_dialog(central_conn, shared_type: str,
                         item_name: str, item_data: dict,
                         parent=None) -> bool:
    """
    يفتح نافذة النشر ويرجع True لو تم النشر بنجاح.

    مثال الاستخدام من raw_table_panel:
        from ui.tabs.companies.shared_items_manager_helper._add_sharedItem_dialog import publish_item_dialog
        if publish_item_dialog(central, "raw", row["name"],
                               {"price": row["price"], "total_qty": row["total_qty"]},
                               parent=self):
            bus.data_changed.emit()
    """
    dlg = PublishAsSharedDialog(
        central_conn = central_conn,
        shared_type  = shared_type,
        item_name    = item_name,
        item_data    = item_data,
        parent       = parent,
    )
    return dlg.exec_() == QDialog.Accepted