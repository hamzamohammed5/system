"""
ui/tabs/costing/shared/bulk_replace/bulk_replace_dialog.py
===========================================================
نافذة "الاستبدال الشامل" — تُفتح من تبويبات الخامات / العمالة / التشغيل.

الوظيفة:
  - تعرض كل المنتجات التي تحتوي على العنصر المحدد
  - تتيح: ① إحلال العنصر بآخر  ② تعديل الكمية  ③ الاثنين معاً

التقسيم الداخلي:
  bulk_replace_helpers.py         → ProductRow + دوال مساعدة
  bulk_replace_products_panel.py  → _ProductsPanel
  _operation_section.py           → _OperationSection
  bulk_replace_dialog.py          → BulkReplaceDialog (هذا الملف)

الاستخدام:
    dlg = BulkReplaceDialog(conn, child_type, child_id, child_name, parent)
    dlg.exec_()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt

from db.shared.items_repo import fetch_item, replace_bom, fetch_bom
from ui.events import bus
from ui.widgets.shared.panels import _make_btn  # noqa — للتوافق

from .bulk_replace_helpers        import get_element_name, fetch_candidates
from .bulk_replace_products_panel import _ProductsPanel
from ._operation_section          import _OperationSection


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

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._build_header())

        body = QFrame()
        body.setStyleSheet("background: #f5f7fa;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 14, 16, 14)
        body_lay.setSpacing(12)

        # قسم العملية (مُستخرج في ملف منفصل)
        self._op_section = _OperationSection(self.child_type)
        body_lay.addWidget(self._op_section)

        # لوحة المنتجات المتأثرة
        self._products_panel = _ProductsPanel(
            self.conn, self.child_type, self.child_id
        )
        body_lay.addWidget(self._products_panel, stretch=1)

        # أزرار الإجراء
        body_lay.addLayout(self._build_action_buttons())
        root.addWidget(body, stretch=1)

        self._update_apply_btn_state()

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
            f"استبدال شامل  —  "
            f"<span style='color:#90caf9;'>{self.child_name}</span>"
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

    def _build_action_buttons(self) -> QHBoxLayout:
        row = QHBoxLayout()

        self._btn_apply = QPushButton("🚀  تطبيق على المحدد")
        self._btn_apply.setMinimumHeight(38)
        self._btn_apply.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                font-weight: bold; font-size: 13px;
                border-radius: 6px; padding: 0 20px;
            }
            QPushButton:hover { background: #1976d2; }
            QPushButton:disabled { background: #90a4ae; }
        """)
        self._btn_apply.clicked.connect(self._apply)

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
        row.addWidget(self._btn_apply)
        return row

    # ── تحميل البيانات ────────────────────────────────────

    def _load_candidates(self):
        """يملأ قسم العملية بالعناصر البديلة."""
        candidates = fetch_candidates(self.conn, self.child_type, self.child_id)
        self._op_section.load_candidates(candidates)

    def _update_apply_btn_state(self):
        self._btn_apply.setEnabled(self._products_panel.has_products())

    # ── تطبيق التعديل ─────────────────────────────────────

    def _apply(self):
        selected_rows = self._products_panel.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "تنبيه", "اختر منتجاً واحداً على الأقل")
            return

        do_replace   = self._op_section.do_replace
        do_qty       = self._op_section.do_qty
        new_child_id = self._op_section.new_child_id
        uniform_qty  = self._op_section.uniform_qty

        # التحقق من وجود بديل لو العملية تستلزمه
        if do_replace and new_child_id is None:
            QMessageBox.warning(
                self, "تنبيه",
                "اختر العنصر البديل أولاً\n"
                "أو اختر «تعديل الكمية فقط» لو لا تريد الاستبدال."
            )
            return

        # رسالة التأكيد
        op_desc = []
        if do_replace:
            new_name = get_element_name(self.conn, self.child_type, new_child_id)
            op_desc.append(f"• استبدال  «{self.child_name}»  بـ  «{new_name}»")
        if do_qty:
            if uniform_qty is not None:
                op_desc.append(f"• تعيين الكمية = {uniform_qty:.4f}")
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

        # التطبيق الفعلي
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
                        if uniform_qty is not None:
                            final_qty = uniform_qty
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
                self, "تم",
                f"✅ تم تحديث {updated} منتج بنجاح"
            )

        if do_replace:
            self.accept()
        else:
            self._products_panel.reload()