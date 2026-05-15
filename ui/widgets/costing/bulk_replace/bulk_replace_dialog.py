"""
ui/widgets/costing/bulk_replace/bulk_replace_dialog.py
==================================
نافذة "الاستبدال الشامل" — تُفتح من تبويبات الخامات / العمالة / التشغيل.

الوظيفة:
  - تعرض كل المنتجات التي تحتوي على العنصر المحدد
  - تتيح: ① إحلال العنصر بآخر  ② تعديل الكمية  ③ الاثنين معاً

التقسيم الداخلي:
  bulk_replace_helpers.py        → ProductRow + دوال مساعدة
  bulk_replace_products_panel.py → _ProductsPanel (لوحة المنتجات)
  bulk_replace_dialog.py         → BulkReplaceDialog (الـ Dialog)

الاستخدام:
    from ui.widgets.bulk_replace_dialog import BulkReplaceDialog
    dlg = BulkReplaceDialog(conn, child_type, child_id, child_name, parent)
    dlg.exec_()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QDoubleSpinBox, QPushButton,
    QCheckBox, QFrame, QMessageBox,
    QRadioButton, QGroupBox,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor, QFont

from db.shared.items_repo  import fetch_item, replace_bom, fetch_bom
from ui.events      import bus

from .bulk_replace_helpers       import get_element_name, fetch_candidates
from .bulk_replace_products_panel import _ProductsPanel


class BulkReplaceDialog(QDialog):
    """نافذة الاستبدال الشامل لعنصر BOM في عدة منتجات دفعة واحدة."""

    def __init__(self, conn, child_type: str, child_id: int,
                 child_name: str = None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self.child_type = child_type
        self.child_id   = child_id
        self.child_name = child_name or get_element_name(conn, child_type, child_id)

        self.setWindowTitle("🔄  استبدال / تعديل شامل")
        self.setMinimumSize(750, 620)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()
        self._load_candidates()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._build_header())

        body = QWidget()
        body.setStyleSheet("background: #f5f7fa;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 14, 16, 14)
        body_lay.setSpacing(12)

        body_lay.addWidget(self._build_operation_section())

        # ── لوحة المنتجات ──
        self._products_panel = _ProductsPanel(
            self.conn, self.child_type, self.child_id
        )
        body_lay.addWidget(self._products_panel, stretch=1)

        # تحديث زر التطبيق حسب وجود منتجات
        self._update_apply_btn_state()

        body_lay.addLayout(self._build_action_buttons())
        root.addWidget(body, stretch=1)

    def _build_header(self) -> QFrame:
        header = QFrame()
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #1976d2);
                border-bottom: 2px solid #0d47a1;
            }
        """)
        header.setFixedHeight(70)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)

        lbl_icon = QLabel("🔄")
        lbl_icon.setStyleSheet("font-size:28px; background:transparent; border:none;")

        lbl_title = QLabel(
            f"استبدال شامل  —  <span style='color:#90caf9;'>{self.child_name}</span>"
        )
        lbl_title.setStyleSheet(
            "font-size:15px; font-weight:bold; color:white;"
            "background:transparent; border:none;"
        )
        lbl_title.setTextFormat(Qt.RichText)

        h_lay.addWidget(lbl_icon)
        h_lay.addSpacing(10)
        h_lay.addWidget(lbl_title)
        h_lay.addStretch()
        return header

    def _build_operation_section(self) -> QGroupBox:
        grp = QGroupBox("⚙️  العملية المطلوبة")
        grp.setStyleSheet("""
            QGroupBox {
                background: white; border: 1px solid #e0e0e0;
                border-radius: 8px; font-weight: bold;
                color: #1565c0; padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top right;
                padding: 0 8px;
            }
        """)
        lay = QVBoxLayout(grp)
        lay.setSpacing(10)

        # خيارات العملية
        ops_row = QHBoxLayout()
        self._rdo_replace = QRadioButton("🔀  استبدال العنصر")
        self._rdo_qty     = QRadioButton("🔢  تعديل الكمية فقط")
        self._rdo_both    = QRadioButton("✅  الاثنين معاً")
        self._rdo_both.setChecked(True)
        for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
            rdo.setStyleSheet("font-size:12px;")
            ops_row.addWidget(rdo)
        ops_row.addStretch()
        lay.addLayout(ops_row)

        # حقول البديل والكمية
        self._replace_frame = QFrame()
        self._replace_frame.setStyleSheet(
            "QFrame { background:#f8fbff; border:1px solid #bbdefb;"
            "border-radius:6px; padding:4px; }"
        )
        from PyQt5.QtWidgets import QFormLayout
        rf_lay = QFormLayout(self._replace_frame)
        rf_lay.setSpacing(8)
        rf_lay.setLabelAlignment(Qt.AlignRight)

        self.cmb_replacement = QComboBox()
        self.cmb_replacement.setMinimumHeight(32)
        self.cmb_replacement.setMinimumWidth(280)

        lbl_new_type = {
            "raw":        "🧱  الخامة البديلة :",
            "labor_op":   "👷  العملية البديلة :",
            "machine_op": "⚙️  العملية البديلة :",
        }.get(self.child_type, "البديل :")
        rf_lay.addRow(lbl_new_type, self.cmb_replacement)

        qty_row = QHBoxLayout()
        self.chk_uniform_qty = QCheckBox("تطبيق كمية موحدة على المنتجات المختارة:")
        self.chk_uniform_qty.setStyleSheet("font-size:11px;")
        self.sp_uniform_qty = QDoubleSpinBox()
        self.sp_uniform_qty.setRange(0.0001, 999999)
        self.sp_uniform_qty.setDecimals(4)
        self.sp_uniform_qty.setValue(1.0)
        self.sp_uniform_qty.setFixedWidth(100)
        self.sp_uniform_qty.setEnabled(False)
        self.chk_uniform_qty.toggled.connect(self.sp_uniform_qty.setEnabled)
        qty_row.addWidget(self.chk_uniform_qty)
        qty_row.addWidget(self.sp_uniform_qty)
        qty_row.addStretch()
        rf_lay.addRow("", qty_row)
        lay.addWidget(self._replace_frame)

        # ربط الـ radio buttons
        for rdo in (self._rdo_replace, self._rdo_qty, self._rdo_both):
            rdo.toggled.connect(self._update_op_ui)
        self._update_op_ui()
        return grp

    def _build_action_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self.btn_apply = QPushButton("🚀  تطبيق على المحدد")
        self.btn_apply.setMinimumHeight(38)
        self.btn_apply.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                font-weight: bold; font-size: 13px;
                border-radius: 6px; padding: 0 20px;
            }
            QPushButton:hover { background: #1976d2; }
            QPushButton:disabled { background: #90a4ae; }
        """)
        self.btn_apply.clicked.connect(self._apply)

        btn_cancel = QPushButton("✖  إغلاق")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet("""
            QPushButton {
                background: #f5f5f5; color: #555;
                border: 1px solid #ddd; border-radius: 6px;
                padding: 0 16px; font-size: 12px;
            }
            QPushButton:hover { background: #eeeeee; }
        """)
        btn_cancel.clicked.connect(self.reject)

        row.addStretch()
        row.addWidget(btn_cancel)
        row.addWidget(self.btn_apply)
        return row

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load_candidates(self):
        """يملأ combo الاستبدال بالعناصر البديلة مجمّعة بالتصنيف."""
        candidates = fetch_candidates(self.conn, self.child_type, self.child_id)
        self.cmb_replacement.clear()
        self.cmb_replacement.addItem("— اختر البديل —", None)

        last_cat = object()
        for cid, cname, cat_name in candidates:
            if cat_name != last_cat:
                sep_text = f"─── {cat_name or 'بدون تصنيف'} ───"
                self.cmb_replacement.addItem(sep_text, "__sep__")
                idx   = self.cmb_replacement.count() - 1
                model = self.cmb_replacement.model()
                item  = model.item(idx)
                if item:
                    from PyQt5.QtCore import Qt as _Qt
                    item.setFlags(
                        item.flags() & ~_Qt.ItemIsEnabled & ~_Qt.ItemIsSelectable
                    )
                    item.setForeground(QColor("#78909c"))
                    f = QFont(); f.setBold(True)
                    f.setPointSize(f.pointSize() - 1)
                    item.setFont(f)
                last_cat = cat_name

            self.cmb_replacement.addItem(f"{cid} — {cname}", cid)

        if self.cmb_replacement.count() == 1:
            self.cmb_replacement.addItem("لا توجد عناصر بديلة", "__empty__")
            self.cmb_replacement.setEnabled(False)
            self._rdo_qty.setChecked(True)
            self._rdo_replace.setEnabled(False)
            self._rdo_both.setEnabled(False)

    # ══════════════════════════════════════════════════════
    # منطق UI
    # ══════════════════════════════════════════════════════

    def _update_op_ui(self):
        show_replace = self._rdo_replace.isChecked() or self._rdo_both.isChecked()
        self.cmb_replacement.setEnabled(show_replace)
        if self._rdo_qty.isChecked():
            self._replace_frame.setStyleSheet(
                "QFrame { background:#f5f5f5; border:1px solid #e0e0e0;"
                "border-radius:6px; padding:4px; }"
            )
        else:
            self._replace_frame.setStyleSheet(
                "QFrame { background:#f8fbff; border:1px solid #bbdefb;"
                "border-radius:6px; padding:4px; }"
            )

    def _update_apply_btn_state(self):
        self.btn_apply.setEnabled(self._products_panel.has_products())

    # ══════════════════════════════════════════════════════
    # تطبيق التعديل
    # ══════════════════════════════════════════════════════

    def _apply(self):
        selected_rows = self._products_panel.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "اختر منتجاً واحداً على الأقل")
            return

        do_replace = self._rdo_replace.isChecked() or self._rdo_both.isChecked()
        do_qty     = self._rdo_qty.isChecked()     or self._rdo_both.isChecked()

        new_child_id = None
        if do_replace:
            new_child_id = self.cmb_replacement.currentData()
            if not new_child_id or new_child_id in (None, "__sep__", "__empty__"):
                QMessageBox.warning(
                    self, "تنبيه",
                    "اختر العنصر البديل أولاً\n"
                    "أو اختر «تعديل الكمية فقط» لو لا تريد الاستبدال."
                )
                return

        # تأكيد
        op_desc = []
        if do_replace:
            new_name = get_element_name(self.conn, self.child_type, new_child_id)
            op_desc.append(f"• استبدال  «{self.child_name}»  بـ  «{new_name}»")
        if do_qty:
            if self.chk_uniform_qty.isChecked():
                op_desc.append(
                    f"• تعيين الكمية = {self.sp_uniform_qty.value():.4f}"
                )
            else:
                op_desc.append("• الاحتفاظ بالكمية المعدَّلة لكل منتج")

        msg = (
            f"سيتم تطبيق التالي على {len(selected_rows)} منتج:\n\n"
            + "\n".join(op_desc) + "\n\nهل تريد المتابعة؟"
        )
        if QMessageBox.question(
            self, "تأكيد التطبيق", msg,
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        errors  = []
        updated = 0

        for prod_row in selected_rows:
            pid = prod_row.product_id
            try:
                bom     = fetch_bom(self.conn, pid)
                new_bom = []
                for child_type, child_id, qty, waste_pct in bom:
                    if child_type == self.child_type and child_id == self.child_id:
                        final_cid = new_child_id if do_replace else child_id
                        if do_qty and self.chk_uniform_qty.isChecked():
                            final_qty = self.sp_uniform_qty.value()
                        elif do_qty:
                            final_qty = prod_row.new_qty
                        else:
                            final_qty = qty
                        new_bom.append((child_type, final_cid, final_qty, waste_pct))
                    else:
                        new_bom.append((child_type, child_id, qty, waste_pct))

                replace_bom(self.conn, pid, new_bom)
                updated += 1
            except Exception as e:
                item = fetch_item(self.conn, pid)
                name = item["name"] if item else f"ID:{pid}"
                errors.append(f"• {name}: {e}")

        bus.data_changed.emit()

        if errors:
            QMessageBox.warning(
                self, "اكتمل مع أخطاء",
                f"✅ تم تحديث {updated} منتج بنجاح\n\n"
                f"⚠️ فشل {len(errors)} منتج:\n" + "\n".join(errors)
            )
        else:
            QMessageBox.information(
                self, "تم", f"✅ تم تحديث {updated} منتج بنجاح"
            )

        if do_replace:
            self.accept()
        else:
            self._products_panel.reload()