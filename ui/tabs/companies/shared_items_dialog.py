"""
ui/tabs/companies/shared_items_dialog.py
==========================================
نافذة إدارة العناصر المشتركة بين الشركات.

من هنا يمكن:
  - نشر عنصر (خامة / ماكينة / عملية) كعنصر مشترك
  - ربط عناصر مشتركة بالشركة الحالية
  - مزامنة التغييرات من الشركة المصدر
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QComboBox, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox,
    QWidget, QFrame, QTabWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.companies.companies_schema import get_central_connection, create_central_tables
from db.companies.companies_repo   import (
    fetch_all_companies,
    fetch_all_shared_items,
    fetch_shared_items_for_company,
    publish_item_as_shared,
    link_shared_item_to_company,
    unlink_shared_item,
    sync_shared_item,
)
from db.companies.company_state import company_state
from ui.app_settings            import _C

_TYPE_AR = {
    "raw":        "خامة",
    "machine":    "ماكينة",
    "labor_op":   "عملية عمالة",
    "machine_op": "عملية تشغيل",
}


class SharedItemsDialog(QDialog):
    """نافذة إدارة العناصر المشتركة."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._central = get_central_connection()
        create_central_tables(self._central)

        self.setWindowTitle("🔗  العناصر المشتركة بين الشركات")
        self.setMinimumSize(920, 620)
        self.setModal(True)
        self._build()
        self._load_all()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel("🔗  العناصر المشتركة")
        title.setStyleSheet(f"font-size: 14pt; font-weight: bold; color: {_C['accent']};")
        root.addWidget(title)

        hint = QLabel(
            "💡  يمكنك نشر عنصر من شركتك كعنصر مشترك، ثم ربطه بشركات أخرى.\n"
            "    عند المزامنة، تنتقل التغييرات من الشركة المصدر إلى كل الشركات المرتبطة."
        )
        hint.setStyleSheet(f"""
            background: {_C['info_bg']}; color: {_C['info']};
            border: 1px solid {_C['info_border']};
            border-radius: 6px; padding: 8px 12px; font-size: 10pt;
        """)
        hint.setWordWrap(True)
        root.addWidget(hint)

        tabs = QTabWidget()
        tabs.addTab(self._build_published_tab(),  "📤  العناصر المنشورة")
        tabs.addTab(self._build_my_links_tab(),   "🔗  المرتبطة بشركتي")
        tabs.addTab(self._build_publish_tab(),    "➕  نشر عنصر جديد")
        root.addWidget(tabs)

        close_btn = QPushButton("✖  إغلاق")
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 4px 18px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    # ══ تبويب: العناصر المنشورة ══════════════════════════

    def _build_published_tab(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(6)

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("كل العناصر المنشورة للمشاركة بين الشركات:"))
        toolbar.addStretch()
        refresh_btn = QPushButton("🔄  تحديث")
        refresh_btn.setFixedHeight(30)
        refresh_btn.clicked.connect(self._load_published)
        toolbar.addWidget(refresh_btn)
        lay.addLayout(toolbar)

        self._published_table = self._make_table(
            ["العنصر", "النوع", "الشركة المصدر", ""]
        )
        lay.addWidget(self._published_table)
        return w

    def _build_my_links_tab(self) -> QWidget:
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(6)

        if not company_state.is_ready:
            lay.addWidget(QLabel("⚠️  اختر شركة نشطة أولاً"))
            return w

        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel(f"العناصر المشتركة المرتبطة بـ: {company_state.company_name}"))
        toolbar.addStretch()
        add_btn = QPushButton("➕  ربط عنصر مشترك")
        add_btn.setFixedHeight(30)
        add_btn.setStyleSheet(self._btn_style(_C['accent'], _C['accent_hover']))
        add_btn.clicked.connect(self._link_item_dialog)
        toolbar.addWidget(add_btn)
        lay.addLayout(toolbar)

        self._links_table = self._make_table(
            ["العنصر", "النوع", "الشركة المصدر", "آخر مزامنة", ""]
        )
        lay.addWidget(self._links_table)
        return w

    def _build_publish_tab(self) -> QWidget:
        """تبويب نشر عنصر جديد من الشركة الحالية."""
        w   = QWidget()
        lay = QVBoxLayout(w)
        lay.setSpacing(10)
        lay.setContentsMargins(16, 16, 16, 16)

        if not company_state.is_ready:
            lay.addWidget(QLabel("⚠️  اختر شركة نشطة أولاً"))
            return w

        lay.addWidget(QLabel(f"نشر عنصر من شركة: {company_state.company_name}"))

        def _lbl(t):
            l = QLabel(t)
            l.setStyleSheet(f"font-size: 10pt; color: {_C['text_sec']};")
            return l

        lay.addWidget(_lbl("نوع العنصر:"))
        self._pub_type_combo = QComboBox()
        self._pub_type_combo.setFixedHeight(32)
        for key, ar in _TYPE_AR.items():
            self._pub_type_combo.addItem(ar, userData=key)
        self._pub_type_combo.currentIndexChanged.connect(self._on_pub_type_changed)
        lay.addWidget(self._pub_type_combo)

        lay.addWidget(_lbl("اختر العنصر:"))
        self._pub_item_combo = QComboBox()
        self._pub_item_combo.setFixedHeight(32)
        lay.addWidget(self._pub_item_combo)

        lay.addStretch()

        pub_btn = QPushButton("📤  نشر هذا العنصر كمشترك")
        pub_btn.setFixedHeight(38)
        pub_btn.setStyleSheet(self._btn_style(_C['accent'], _C['accent_hover']))
        pub_btn.clicked.connect(self._publish_item)
        lay.addWidget(pub_btn)

        # تحميل أول نوع
        self._on_pub_type_changed(0)
        return w

    # ══ تحميل البيانات ═══════════════════════════════════

    def _load_all(self):
        self._load_published()
        self._load_my_links()

    def _load_published(self):
        items = fetch_all_shared_items(self._central)
        t = self._published_table
        t.setRowCount(0)
        for item in items:
            ri = t.rowCount()
            t.insertRow(ri)
            t.setItem(ri, 0, QTableWidgetItem(item["name"]))
            t.setItem(ri, 1, QTableWidgetItem(_TYPE_AR.get(item["shared_type"], item["shared_type"])))
            t.setItem(ri, 2, QTableWidgetItem(item["source_company_name"] or ""))

            btns = self._make_action_btns(
                item["id"],
                item["source_company_name"],
                is_published_view=True
            )
            t.setCellWidget(ri, 3, btns)
            t.setRowHeight(ri, 36)

    def _load_my_links(self):
        if not company_state.is_ready:
            return
        if not hasattr(self, "_links_table"):
            return
        items = fetch_shared_items_for_company(self._central, company_state.company_id)
        t = self._links_table
        t.setRowCount(0)
        for item in items:
            ri = t.rowCount()
            t.insertRow(ri)
            t.setItem(ri, 0, QTableWidgetItem(item["name"]))
            t.setItem(ri, 1, QTableWidgetItem(_TYPE_AR.get(item["shared_type"], item["shared_type"])))
            t.setItem(ri, 2, QTableWidgetItem(item["source_company_name"] or ""))

            synced = item["is_synced"]
            sync_item = QTableWidgetItem("✅ محدّث" if synced else "⚠️ يحتاج مزامنة")
            sync_item.setForeground(QColor("#2e7d52" if synced else "#e65100"))
            t.setItem(ri, 3, sync_item)

            btns = self._make_action_btns(
                item["shared_item_id"],
                item["source_company_name"],
                is_published_view=False,
                link_id=item["link_id"]
            )
            t.setCellWidget(ri, 4, btns)
            t.setRowHeight(ri, 36)

    def _on_pub_type_changed(self, idx: int):
        """تحميل عناصر النوع المختار من erp.db الشركة النشطة."""
        if not company_state.is_ready:
            return
        self._pub_item_combo.clear()
        shared_type = self._pub_type_combo.currentData()
        if not shared_type:
            return
        try:
            erp = company_state.get_erp_conn()
            if shared_type == "raw":
                rows = erp.execute(
                    "SELECT id, name FROM items WHERE type='raw' ORDER BY name"
                ).fetchall()
            elif shared_type == "machine":
                rows = erp.execute("SELECT id, name FROM machines ORDER BY name").fetchall()
            elif shared_type == "labor_op":
                rows = erp.execute("SELECT id, name FROM labor_ops ORDER BY name").fetchall()
            elif shared_type == "machine_op":
                rows = erp.execute("SELECT id, name FROM machine_ops ORDER BY name").fetchall()
            else:
                rows = []
            for r in rows:
                self._pub_item_combo.addItem(r["name"], userData=r["id"])
        except Exception as e:
            print(f"[SharedItemsDialog] _on_pub_type_changed: {e}")

    def _publish_item(self):
        if not company_state.is_ready:
            QMessageBox.warning(self, "تنبيه", "اختر شركة نشطة أولاً")
            return
        item_id = self._pub_item_combo.currentData()
        name    = self._pub_item_combo.currentText()
        stype   = self._pub_type_combo.currentData()

        if not item_id:
            QMessageBox.warning(self, "تنبيه", "اختر عنصراً أولاً")
            return

        try:
            shared_id = publish_item_as_shared(
                self._central,
                source_company_id=company_state.company_id,
                source_item_id=item_id,
                shared_type=stype,
                name=name,
            )
            QMessageBox.information(
                self, "تم",
                f"تم نشر «{name}» كعنصر مشترك.\n"
                "يمكن للشركات الأخرى الآن ربطه واستخدامه."
            )
            self._load_all()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _link_item_dialog(self):
        """ربط عنصر مشترك بالشركة الحالية."""
        items = fetch_all_shared_items(self._central)
        # استثنِ المرتبطة مسبقاً
        linked = {
            r["shared_item_id"]
            for r in fetch_shared_items_for_company(self._central, company_state.company_id)
        }
        available = [i for i in items if i["id"] not in linked]

        if not available:
            QMessageBox.information(self, "تنبيه", "لا توجد عناصر مشتركة متاحة للربط")
            return

        from ui.tabs.companies._link_item_picker import LinkItemPicker
        dlg = LinkItemPicker(available, parent=self)
        if dlg.exec_() == QDialog.Accepted and dlg.selected_id:
            self._do_link(dlg.selected_id)

    def _do_link(self, shared_item_id: int):
        try:
            # جلب بيانات العنصر
            shared = self._central.execute(
                "SELECT * FROM shared_items WHERE id=?", (shared_item_id,)
            ).fetchone()
            if not shared:
                return

            import sqlite3
            from db.companies.companies_schema import get_company_db_path
            src_path = get_company_db_path(shared["source_company_id"], "erp")
            src_erp  = sqlite3.connect(src_path)
            src_erp.row_factory     = sqlite3.Row
            src_erp.isolation_level = None

            try:
                local_id = link_shared_item_to_company(
                    self._central, src_erp,
                    shared_item_id,
                    company_state.company_id
                )
            finally:
                src_erp.close()

            # أعد فتح erp connection عشان يظهر العنصر الجديد
            company_state.refresh_connections()

            QMessageBox.information(
                self, "تم",
                f"تم ربط «{shared['name']}» بشركتك بنجاح.\n"
                f"يمكنك الآن استخدامه في BOM وحسابات التكلفة."
            )
            self._load_all()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _sync_item(self, shared_item_id: int):
        """مزامنة عنصر مشترك."""
        try:
            shared = self._central.execute(
                "SELECT * FROM shared_items WHERE id=?", (shared_item_id,)
            ).fetchone()
            if not shared:
                return

            import sqlite3
            from db.companies.companies_schema import get_company_db_path
            src_path = get_company_db_path(shared["source_company_id"], "erp")
            src_erp  = sqlite3.connect(src_path)
            src_erp.row_factory     = sqlite3.Row
            src_erp.isolation_level = None
            try:
                sync_shared_item(self._central, src_erp, shared_item_id)
            finally:
                src_erp.close()

            company_state.refresh_connections()
            QMessageBox.information(self, "تم", "تمت المزامنة بنجاح")
            self._load_all()
        except Exception as e:
            QMessageBox.critical(self, "خطأ", str(e))

    def _unlink_item(self, shared_item_id: int):
        if QMessageBox.question(
            self, "تأكيد", "إلغاء ربط هذا العنصر من شركتك؟\n(لن يُحذف العنصر المحلي)",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            unlink_shared_item(self._central, shared_item_id, company_state.company_id)
            self._load_my_links()

    # ══ مساعدات ══════════════════════════════════════════

    def _make_table(self, headers: list) -> QTableWidget:
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.setEditTriggers(QTableWidget.NoEditTriggers)
        t.setAlternatingRowColors(True)
        t.verticalHeader().setVisible(False)
        hh = t.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, len(headers)):
            hh.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        t.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {_C['border']};
                border-radius: 6px; background: white;
            }}
            QHeaderView::section {{
                background: {_C['bg_surface_2']};
                padding: 6px 8px; border: none;
                border-bottom: 2px solid {_C['border_med']};
                font-weight: 600;
            }}
        """)
        return t

    def _make_action_btns(self, shared_item_id: int, source_name: str,
                           is_published_view: bool, link_id: int = None) -> QWidget:
        w   = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(4)

        if is_published_view:
            # زر ربط بالشركة الحالية
            if company_state.is_ready:
                link_btn = QPushButton("🔗 ربط بشركتي")
                link_btn.setFixedHeight(26)
                link_btn.setStyleSheet("""
                    QPushButton { background: #e3f2fd; border: none;
                        border-radius: 4px; padding: 2px 8px; font-size: 9pt; }
                    QPushButton:hover { background: #bbdefb; }
                """)
                link_btn.clicked.connect(lambda _, sid=shared_item_id: self._do_link(sid))
                lay.addWidget(link_btn)
        else:
            # زر مزامنة + فك ربط
            sync_btn = QPushButton("🔄 مزامنة")
            sync_btn.setFixedHeight(26)
            sync_btn.setStyleSheet("""
                QPushButton { background: #e8f5e9; border: none;
                    border-radius: 4px; padding: 2px 8px; font-size: 9pt; }
                QPushButton:hover { background: #c8e6c9; }
            """)
            sync_btn.clicked.connect(lambda _, sid=shared_item_id: self._sync_item(sid))
            lay.addWidget(sync_btn)

            unlink_btn = QPushButton("✖ فك الربط")
            unlink_btn.setFixedHeight(26)
            unlink_btn.setStyleSheet("""
                QPushButton { background: #fdecea; border: none;
                    border-radius: 4px; padding: 2px 8px; font-size: 9pt; }
                QPushButton:hover { background: #ffcdd2; }
            """)
            unlink_btn.clicked.connect(lambda _, sid=shared_item_id: self._unlink_item(sid))
            lay.addWidget(unlink_btn)

        return w

    def _btn_style(self, bg, hover):
        return f"""
            QPushButton {{
                background: {bg}; color: white; font-weight: 600;
                border: none; border-radius: 5px; padding: 4px 14px;
            }}
            QPushButton:hover {{ background: {hover}; }}
        """

    def closeEvent(self, event):
        try:
            self._central.close()
        except Exception:
            pass
        super().closeEvent(event)