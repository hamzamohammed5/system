"""
ui/tabs/companies/shared_items_manager.py
==========================================
SharedItemsManagerDialog — نافذة إدارة كل العناصر المشتركة.

تُفتح من زر «🔗 العناصر المشتركة» في الـ sidebar.

الوظائف:
  - عرض كل العناصر المشتركة مجمّعة بالنوع
  - إضافة عنصر مشترك جديد
  - تعديل عنصر موجود (يفتح SharedItemsDialog)
  - حذف عنصر مشترك
  - إدارة ربط الشركات من خلال SharedItemsDialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QWidget, QMessageBox, QFrame,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QFont, QBrush

from db.companies.shared_items_repo import (
    fetch_all_shared_items, delete_shared_item,
    fetch_linked_companies,
)
from ui.events import bus

_TYPE_AR = {
    "raw":        "🧱  الخامات",
    "machine":    "🖥️  الماكينات",
    "labor_op":   "👷  عمليات العمالة",
    "machine_op": "⚙️  عمليات التشغيل",
}

_TYPE_COLORS = {
    "raw":        "#1565c0",
    "machine":    "#6a1b9a",
    "labor_op":   "#2e7d32",
    "machine_op": "#e65100",
}


class SharedItemsManagerDialog(QDialog):
    """
    نافذة إدارة العناصر المشتركة بين الشركات.

    الاستخدام:
        central = get_central_connection()
        dlg = SharedItemsManagerDialog(central, parent=self)
        dlg.items_changed.connect(lambda: bus.data_changed.emit())
        dlg.exec_()
        central.close()
    """

    items_changed = pyqtSignal()

    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self._conn = central_conn
        self.setWindowTitle("🔗  إدارة العناصر المشتركة بين الشركات")
        self.setMinimumSize(820, 600)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()
        self._load()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        body = QWidget()
        body.setStyleSheet("background:#f5f7fa;")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(16, 14, 16, 14)
        body_lay.setSpacing(10)

        # ── شرح ──
        lbl_hint = QLabel(
            "💡  العناصر المشتركة مخزنة مركزياً — أي تعديل على السعر أو البيانات يتعكس فوراً "
            "على كل الشركات المشتركة فيها. لا توجد نسخ محلية."
        )
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet(
            "background:#e8f5e9; border:1px solid #a5d6a7; border-radius:6px;"
            "padding:8px 12px; color:#1b5e20; font-size:11px;"
        )
        body_lay.addWidget(lbl_hint)

        # ── أزرار ──
        btn_row = QHBoxLayout()

        self.btn_add = QPushButton("➕  إضافة عنصر مشترك")
        self.btn_add.setMinimumHeight(32)
        self.btn_add.setStyleSheet(
            "background:#1565c0; color:white; font-weight:bold;"
            "border-radius:6px; padding:0 14px;"
        )
        self.btn_add.clicked.connect(self._add_item)

        self.btn_edit = QPushButton("✏️  تعديل المحدد")
        self.btn_edit.setMinimumHeight(32)
        self.btn_edit.clicked.connect(self._edit_item)

        self.btn_delete = QPushButton("🗑️  حذف المحدد")
        self.btn_delete.setMinimumHeight(32)
        self.btn_delete.setStyleSheet(
            "background:#fdecea; color:#c62828; border:1px solid #ef9a9a;"
            "border-radius:4px; padding:0 12px; font-weight:bold;"
        )
        self.btn_delete.clicked.connect(self._delete_item)

        self.btn_refresh = QPushButton("🔄  تحديث")
        self.btn_refresh.setMinimumHeight(32)
        self.btn_refresh.clicked.connect(self._load)

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_refresh)
        body_lay.addLayout(btn_row)

        # ── الشجرة ──
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels([
            "اسم العنصر", "النوع", "البيانات الرئيسية",
            "الشركات المشتركة", "آخر تحديث"
        ])
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setStyleSheet("""
            QTreeWidget {
                border:1px solid #e0e0e0; border-radius:8px;
                background:white;
            }
            QTreeWidget::item { padding:5px 8px; }
            QTreeWidget::item:selected {
                background:#e3f2fd; color:#1565c0;
            }
        """)

        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        hh.setSectionResizeMode(4, QHeaderView.Interactive)
        self.tree.setColumnWidth(1, 110)
        self.tree.setColumnWidth(2, 180)
        self.tree.setColumnWidth(3, 160)
        self.tree.setColumnWidth(4, 130)

        body_lay.addWidget(self.tree, stretch=1)

        btn_close = QPushButton("✖  إغلاق")
        btn_close.setMinimumHeight(34)
        btn_close.clicked.connect(self.accept)
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_row.addWidget(btn_close)
        body_lay.addLayout(close_row)

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
        header.setFixedHeight(60)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(20, 0, 20, 0)
        lbl = QLabel("🔗  إدارة العناصر المشتركة بين الشركات")
        lbl.setStyleSheet(
            "font-size:14px; font-weight:bold; color:white;"
            "background:transparent; border:none;"
        )
        h_lay.addWidget(lbl)
        h_lay.addStretch()
        return header

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load(self):
        self.tree.clear()
        items = fetch_all_shared_items(self._conn)

        # تجميع بالنوع
        by_type: dict = {}
        for item in items:
            t = item["shared_type"]
            by_type.setdefault(t, []).append(item)

        for shared_type, type_items in sorted(by_type.items()):
            # نود النوع
            type_label = _TYPE_AR.get(shared_type, shared_type)
            type_node  = QTreeWidgetItem([
                f"{type_label}  ({len(type_items)})", "", "", "", ""
            ])
            font = QFont()
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            type_node.setFont(0, font)
            color = QColor(_TYPE_COLORS.get(shared_type, "#333"))
            type_node.setForeground(0, color)
            type_node.setBackground(0, QBrush(QColor("#f5f5f5")))
            type_node.setData(0, Qt.UserRole, ("__type__", shared_type))

            for item in type_items:
                linked_cos = fetch_linked_companies(self._conn, item["id"])
                co_names   = ", ".join(c["name"] for c in linked_cos) or "─ لا يوجد"

                try:
                    import json
                    data = json.loads(item["data"]) if item["data"] else {}
                except Exception:
                    data = {}

                data_summary = self._data_summary(shared_type, data)

                child = QTreeWidgetItem([
                    item["name"],
                    _TYPE_AR.get(shared_type, shared_type).split("  ")[1] if "  " in _TYPE_AR.get(shared_type, "") else shared_type,
                    data_summary,
                    f"🏢 {co_names}  ({len(linked_cos)} شركة)",
                    item["updated_at"][:16] if item["updated_at"] else "─",
                ])
                child.setData(0, Qt.UserRole, ("item", item["id"]))
                child.setToolTip(0, item["name"])
                child.setToolTip(3, co_names)
                type_node.addChild(child)

            self.tree.addTopLevelItem(type_node)
            type_node.setExpanded(True)

    def _data_summary(self, shared_type: str, data: dict) -> str:
        """ملخص قصير لبيانات العنصر."""
        if shared_type == "raw":
            price = data.get("price", 0)
            tq    = data.get("total_qty")
            if tq:
                return f"السعر: {price:.2f} ج  │  الكمية: {tq}"
            return f"السعر: {price:.2f} جنيه/وحدة"
        elif shared_type == "machine":
            rh = data.get("rate_per_hour", 0)
            ru = data.get("rate_per_unit", 0)
            return f"{rh:.2f} ج/ساعة  │  {ru:.2f} ج/وحدة"
        elif shared_type == "labor_op":
            m = data.get("minutes", 0)
            return f"{m:.2f} دقيقة"
        elif shared_type == "machine_op":
            v = data.get("value", 0)
            m = data.get("mode", "time")
            return f"{'وقت' if m=='time' else 'وحدة'}: {v:.4g}"
        return "─"

    # ══════════════════════════════════════════════════════
    # أحداث
    # ══════════════════════════════════════════════════════

    def _selected_item_id(self) -> int | None:
        item = self.tree.currentItem()
        if not item:
            return None
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "item":
            return data[1]
        return None

    def _on_double_click(self, item, col):
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "item":
            self._open_edit_dialog(data[1])

    def _add_item(self):
        """إضافة عنصر مشترك جديد."""
        try:
            from ui.tabs.companies.shared_items_manager_helper._add_shared_item_dialog import (
                PublishAsSharedDialog
            )
        except ImportError:
            # fallback بسيط لو الملف مش موجود
            self._add_item_simple()
            return

        # نفتح نافذة الإضافة مع نوع = raw افتراضياً
        dlg = PublishAsSharedDialog(
            central_conn=self._conn,
            shared_type="raw",
            item_name="",
            item_data={},
            parent=self,
        )
        if dlg.exec_():
            self._load()
            self.items_changed.emit()
            bus.data_changed.emit()

    def _add_item_simple(self):
        """إضافة بسيطة بدون نافذة خاصة — يُستخدم كـ fallback."""
        from PyQt5.QtWidgets import QInputDialog, QComboBox
        types = ["raw", "machine", "labor_op", "machine_op"]
        type_ar = ["خامة", "ماكينة", "عملية عمالة", "عملية تشغيل"]
        t, ok = QInputDialog.getItem(
            self, "نوع العنصر", "اختر نوع العنصر:",
            type_ar, 0, False
        )
        if not ok:
            return
        shared_type = types[type_ar.index(t)]

        name, ok = QInputDialog.getText(self, "اسم العنصر", "اسم العنصر:")
        if not ok or not name.strip():
            return

        from db.companies.shared_items_repo import insert_shared_item
        new_id = insert_shared_item(self._conn, name.strip(), shared_type)
        self._load()
        bus.data_changed.emit()
        self._open_edit_dialog(new_id)

    def _edit_item(self):
        item_id = self._selected_item_id()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عنصراً أولاً")
            return
        self._open_edit_dialog(item_id)

    def _open_edit_dialog(self, item_id: int):
        from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
        dlg = SharedItemsDialog(self._conn, item_id, parent=self)
        dlg.item_updated.connect(self._load)
        dlg.item_updated.connect(self.items_changed.emit)
        dlg.exec_()

    def _delete_item(self):
        item_id = self._selected_item_id()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر عنصراً أولاً")
            return

        # تحقق من وجود شركات مرتبطة
        linked = fetch_linked_companies(self._conn, item_id)
        if linked:
            co_names = ", ".join(c["name"] for c in linked)
            reply = QMessageBox.question(
                self, "تأكيد الحذف",
                f"هذا العنصر مرتبط بـ {len(linked)} شركة:\n{co_names}\n\n"
                "حذفه سيفك الربط تلقائياً. هل تريد المتابعة؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        else:
            reply = QMessageBox.question(
                self, "تأكيد الحذف", "حذف هذا العنصر المشترك؟",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        delete_shared_item(self._conn, item_id)
        self._load()
        self.items_changed.emit()
        bus.data_changed.emit()
        QMessageBox.information(self, "تم", "✅ تم حذف العنصر المشترك")