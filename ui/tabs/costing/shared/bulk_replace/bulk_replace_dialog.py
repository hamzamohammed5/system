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

[Refactor] استخدام BulkReplaceService بدل repos مباشرة:
  من: db.shared.items_repo.fetch_item / replace_bom / fetch_bom
  إلى: services.costing.bulk_replace_service.BulkReplaceService

[Fix i18n] كل النصوص المكتوبة مباشرة (عنوان النافذة، رسائل التأكيد
  والأخطاء، أزرار الإجراء) انتقلت إلى مفاتيح ترجمة في ar.py/en.py.
[Fix colors] كل الألوان الست عشرية المباشرة استُبدلت بمفاتيح _C
  من ui/theme_manager.py (المصدر الوحيد للألوان).

الاستخدام:
    dlg = BulkReplaceDialog(conn, child_type, child_id, child_name, parent)
    dlg.exec_()
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QMessageBox,
)
from PyQt5.QtCore import Qt

from services.costing.bulk_replace_service import BulkReplaceService
from ui.widgets.core.events import bus, emit_company_data_changed
from ui.theme import _C
from ui.widgets.core.i18n import tr


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
        # ✅ [Refactor] استخدام get_element_name من helpers (لا تغيير هنا)
        self.child_name = child_name or get_element_name(conn, child_type, child_id)

        self.setWindowTitle(tr("bulk_replace_window_title"))
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
        body.setStyleSheet(f"background: {_C['bg_page']};")
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
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {_C['blue']}, stop:1 {_C['blue_hover']});
                border-bottom: 2px solid {_C['blue_strong']};
            }}
        """)
        header.setFixedHeight(70)

        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)

        lbl_icon = QLabel("🔄")
        lbl_icon.setStyleSheet("font-size:28px; background:transparent; border:none;")

        lbl_title = QLabel(
            tr("bulk_replace_header_title").format(
                name=f"<span style='color:{_C['blue_border']};'>{self.child_name}</span>"
            )
        )
        lbl_title.setStyleSheet(
            f"font-size:15px; font-weight:bold; color:{_C['btn_primary_text']};"
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

        self._btn_apply = QPushButton(f"🚀  {tr('apply_to_selected')}")
        self._btn_apply.setMinimumHeight(38)
        self._btn_apply.setStyleSheet(f"""
            QPushButton {{
                background: {_C['blue']}; color: {_C['btn_primary_text']};
                font-weight: bold; font-size: 13px;
                border-radius: 6px; padding: 0 20px;
            }}
            QPushButton:hover {{ background: {_C['blue_hover']}; }}
            QPushButton:disabled {{ background: {_C['text_disabled']}; }}
        """)
        self._btn_apply.clicked.connect(self._apply)

        btn_cancel = QPushButton(f"✖  {tr('close')}")
        btn_cancel.setMinimumHeight(38)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface']}; color: {_C['text_neutral']};
                border: 1px solid {_C['border']}; border-radius: 6px;
                padding: 0 16px; font-size: 12px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        btn_cancel.clicked.connect(self.reject)

        row.addStretch()
        row.addWidget(btn_cancel)
        row.addWidget(self._btn_apply)
        return row

    # ── تحميل البيانات ────────────────────────────────────

    def _load_candidates(self):
        """يملأ قسم العملية بالعناصر البديلة."""
        # ✅ استخدام fetch_candidates من helpers (يبقى كما هو للتوافق)
        candidates = fetch_candidates(self.conn, self.child_type, self.child_id)
        self._op_section.load_candidates(candidates)

    def _update_apply_btn_state(self):
        self._btn_apply.setEnabled(self._products_panel.has_products())

    # ── تطبيق التعديل ─────────────────────────────────────

    def _apply(self):
        selected_rows = self._products_panel.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, tr("warning"), tr("select_at_least_one_product"))
            return

        do_replace   = self._op_section.do_replace
        do_qty       = self._op_section.do_qty
        new_child_id = self._op_section.new_child_id
        uniform_qty  = self._op_section.uniform_qty

        # التحقق من وجود بديل لو العملية تستلزمه
        if do_replace and new_child_id is None:
            QMessageBox.warning(
                self, tr("warning"), tr("select_replacement_first")
            )
            return

        # رسالة التأكيد
        op_desc = []
        if do_replace:
            # ✅ [Refactor] BulkReplaceService.get_element_name
            try:
                svc      = BulkReplaceService(self.conn)
                new_name = svc.get_element_name(self.child_type, new_child_id)
            except Exception:
                new_name = get_element_name(self.conn, self.child_type, new_child_id)
            op_desc.append(
                tr("bulk_replace_desc_line").format(old=self.child_name, new=new_name)
            )
        if do_qty:
            if uniform_qty is not None:
                op_desc.append(tr("bulk_set_qty_desc_line").format(qty=f"{uniform_qty:.4f}"))
            else:
                op_desc.append(tr("bulk_keep_qty_desc_line"))

        msg = tr("bulk_apply_confirm_msg").format(
            count=len(selected_rows), ops="\n".join(op_desc)
        )
        if QMessageBox.question(
            self, tr("confirm_apply_title"), msg,
            QMessageBox.Yes | QMessageBox.No
        ) != QMessageBox.Yes:
            return

        # ✅ [Refactor] استخدام BulkReplaceService.apply بدل حلقة يدوية
        try:
            svc = BulkReplaceService(self.conn)

            # بناء product_rows: [(product_id, qty), ...]
            product_rows = [
                (r.product_id, r.new_qty)
                for r in selected_rows
            ]

            updated, errors = svc.apply(
                child_type=self.child_type,
                old_child_id=self.child_id,
                new_child_id=new_child_id if do_replace else None,
                product_rows=product_rows,
                uniform_qty=uniform_qty,
                do_replace=do_replace,
                do_qty=do_qty,
            )

        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))
            return

        emit_company_data_changed()

        if errors:
            QMessageBox.warning(
                self, tr("bulk_completed_with_errors_title"),
                tr("bulk_completed_with_errors_msg").format(
                    updated=updated, failed=len(errors), errors="\n".join(errors)
                )
            )
        else:
            QMessageBox.information(
                self, tr("done"),
                tr("bulk_completed_success_msg").format(count=updated)
            )

        if do_replace:
            self.accept()
        else:
            self._products_panel.reload()
