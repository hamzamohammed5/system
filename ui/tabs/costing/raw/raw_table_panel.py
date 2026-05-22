"""
ui/tabs/costing/raw/raw_table_panel.py
=======================================
_TablePanel — جدول الخامات مع:
  - العناصر المشتركة تظهر بـ badge أخضر 🔗
  - تعديل مشترك → SharedItemsDialog (نافذة مباشرة للعنصر الواحد)
  - نشر خامة محلية كمشتركة → PublishAsSharedDialog
  - bus.data_changed يحدّث الجدول فوراً بعد أي تعديل
  - IDs المشتركة = "shared:{n}" (string) متوافق مع items_repo.py
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QTableWidgetItem,
    QMessageBox, QLabel,
)
from PyQt5.QtGui import QColor

from db.shared.items_repo import fetch_items_by_type, delete_item
from models.costing import raw_unit_price
from ui.helpers import (
    make_table, buttons_row, section_label, confirm_delete, danger_button,
)
from ui.widgets.costing.bulk_replace.bulk_replace_dialog import BulkReplaceDialog
from ui.widgets.shared.filter_bar import FilterBar
from ui.tabs.companies.shared_items_mixin import (
    get_shared_raws, is_shared_id, extract_shared_id,
)
from ui.events import bus

_SHARED_COLOR = "#2e7d52"
_SHARED_BG    = "#e8f5e9"


def _to_dict(row) -> dict:
    if isinstance(row, dict):
        return row
    try:
        return dict(row)
    except Exception:
        return {}


class _TablePanel(QWidget):
    def __init__(self, conn, input_panel, parent=None):
        super().__init__(parent)
        self.conn         = conn
        self._input_panel = input_panel
        self._all_rows    = []
        self._build()
        self._load()
        bus.data_changed.connect(self._load)

    def _live_conn(self):
        if self.conn is not None:
            try:
                self.conn.execute("SELECT 1")
                return self.conn
            except Exception:
                pass
        from db.companies.company_state import company_state
        return company_state.get_erp_conn()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(6)
        root.setContentsMargins(12, 8, 12, 12)

        root.addWidget(section_label("─── الخامات المحفوظة ───"))

        legend = QLabel("🔗 أخضر = خامة مشتركة بين الشركات — تعديلها يتعكس فوراً على الكل")
        legend.setStyleSheet(
            f"color:{_SHARED_COLOR}; background:{_SHARED_BG};"
            "border-radius:4px; padding:3px 8px; font-size:9pt;"
        )
        root.addWidget(legend)

        self._filter = FilterBar(self._live_conn(), scope="raw")
        self._filter.filter_changed.connect(self._apply_filter)
        root.addWidget(self._filter)

        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "السعر الكلي", "الكمية الكلية", "سعر الوحدة"],
            stretch_col=1,
        )
        self.table.setColumnWidth(0, 45)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 90)
        self.table.setColumnWidth(5, 95)
        root.addWidget(self.table)

        btn_edit        = QPushButton("✏️  تعديل المحدد")
        btn_del         = danger_button("🗑️  حذف المحدد")
        btn_replace     = QPushButton("🔄  استبدال شامل")
        btn_edit_shared = QPushButton("🔗  تعديل المشترك")
        btn_publish     = QPushButton("📤  نشر كمشترك")

        btn_replace.setStyleSheet(
            "QPushButton { background:#e65100; color:white; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#bf360c; }"
        )
        btn_edit_shared.setStyleSheet(
            f"QPushButton {{ background:{_SHARED_BG}; color:{_SHARED_COLOR};"
            "border:1px solid #a5d6a7; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            f"QPushButton:hover {{ background:#c8e6c9; }}"
        )
        btn_publish.setStyleSheet(
            "QPushButton { background:#e3f2fd; color:#1565c0;"
            "border:1px solid #90caf9; border-radius:4px;"
            "padding:4px 10px; font-weight:bold; }"
            "QPushButton:hover { background:#bbdefb; }"
        )
        for btn in (btn_edit, btn_del, btn_replace, btn_edit_shared, btn_publish):
            btn.setMinimumHeight(30)

        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_replace.clicked.connect(self._bulk_replace)
        btn_edit_shared.clicked.connect(self._edit_shared)
        btn_publish.clicked.connect(self._publish_as_shared)
        root.addLayout(buttons_row(btn_edit, btn_del, btn_replace,
                                    btn_edit_shared, btn_publish))

    # ══════════════════════════════════════════════════════
    # مساعدات التحديد
    # ══════════════════════════════════════════════════════

    def _selected_row_data(self):
        row = self.table.currentRow()
        if row == -1:
            return None, None
        item_id   = self.table.item(row, 0).data(0x0100)
        item_name = self.table.item(row, 1).text()
        return item_id, item_name

    def _selected_raw_dict(self):
        """يرجع dict كامل للصف المحدد (للنشر)."""
        row = self.table.currentRow()
        if row == -1:
            return None
        item_id = self.table.item(row, 0).data(0x0100)
        for r in self._all_rows:
            if str(r.get("id")) == str(item_id):
                return r
        return None

    # ══════════════════════════════════════════════════════
    # أحداث الأزرار
    # ══════════════════════════════════════════════════════

    def _edit(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر خامة من الجدول أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.information(
                self, "عنصر مشترك",
                "هذه خامة مشتركة — استخدم زر «🔗 تعديل المشترك» لتعديلها\n"
                "التعديل سيُطبق فوراً على كل الشركات المشتركة فيها."
            )
            return
        self._input_panel.load_for_edit(int(item_id))

    def _edit_shared(self):
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر خامة من الجدول أولاً")
            return
        if not is_shared_id(item_id):
            QMessageBox.information(
                self, "تنبيه",
                "هذه خامة عادية — استخدم زر «✏️ تعديل المحدد» لتعديلها."
            )
            return
        shared_id = extract_shared_id(item_id)
        if shared_id is not None:
            self._open_shared_editor(shared_id)

    def _open_shared_editor(self, shared_id: int):
        from db.companies.companies_schema import (
            get_central_connection, create_central_tables
        )
        from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
        central = get_central_connection()
        create_central_tables(central)
        dlg = SharedItemsDialog(central, shared_id, parent=self)
        dlg.exec_()
        central.close()

    def _delete(self):
        item_id, item_name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر خامة أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.warning(
                self, "عنصر مشترك",
                "لا يمكن حذف خامة مشتركة من هنا.\n"
                "استخدم نافذة «العناصر المشتركة» لحذفها أو فك الربط."
            )
            return
        item_id_int = int(item_id)
        if self._input_panel.is_editing and self._input_panel._editing_id == item_id_int:
            self._input_panel._reset()
        if confirm_delete(self, item_name):
            try:
                delete_item(self._live_conn(), item_id_int)
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))
                return
            bus.data_changed.emit()

    def _bulk_replace(self):
        item_id, item_name = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر خامة من الجدول أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.information(self, "تنبيه",
                                    "الاستبدال الشامل غير متاح للعناصر المشتركة.")
            return
        dlg = BulkReplaceDialog(
            conn=self._live_conn(), child_type="raw",
            child_id=int(item_id), child_name=item_name, parent=self,
        )
        dlg.exec_()

    def _publish_as_shared(self):
        """نشر خامة محلية كمشتركة بين الشركات."""
        item_id, _ = self._selected_row_data()
        if item_id is None:
            QMessageBox.information(self, "تنبيه", "اختر خامة من الجدول أولاً")
            return
        if is_shared_id(item_id):
            QMessageBox.information(
                self, "مشترك بالفعل",
                "هذه الخامة مشتركة بالفعل.\n"
                "استخدم «🔗 تعديل المشترك» لتعديل الربط."
            )
            return

        row = self._selected_raw_dict()
        if not row:
            return

        item_data = {
            "price":     float(row.get("price", 0.0)),
            "total_qty": row.get("total_qty"),
        }

        try:
            from db.companies.companies_schema import (
                get_central_connection, create_central_tables
            )
            from db.companies.shared_items_repo import create_shared_items_tables
            from ui.tabs.companies.shared_items_manager_helper._add_sharedItem_dialog import (
                PublishAsSharedDialog
            )
            central = get_central_connection()
            create_central_tables(central)
            create_shared_items_tables(central)

            dlg = PublishAsSharedDialog(
                central_conn = central,
                shared_type  = "raw",
                item_name    = row.get("name", ""),
                item_data    = item_data,
                parent       = self,
            )
            dlg.exec_()
            central.close()
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load(self):
        try:
            conn       = self._live_conn()
            local_rows = [_to_dict(r) for r in fetch_items_by_type(conn, "raw")]
        except Exception:
            local_rows = []

        shared_rows = get_shared_raws()
        self._all_rows = local_rows + shared_rows
        self._apply_filter()

    def _apply_filter(self):
        self.table.setRowCount(0)
        shown = 0

        for row in self._all_rows:
            if not self._filter.match(row.get("name", ""), row.get("category_id")):
                continue

            is_shared = row.get("is_shared", False)
            tq        = row.get("total_qty")
            price     = row.get("price", 0.0)

            if is_shared:
                unit = (price / float(tq)) if (tq and float(tq) > 0) else price
            else:
                unit = raw_unit_price(row)

            r = self.table.rowCount()
            self.table.insertRow(r)

            id_item = QTableWidgetItem("🔗" if is_shared else str(row.get("id", "")))
            id_item.setData(0x0100, row.get("id"))
            self.table.setItem(r, 0, id_item)

            self.table.setItem(r, 1, QTableWidgetItem(
                ("🔗 " if is_shared else "") + row.get("name", "")
            ))
            self.table.setItem(r, 2, QTableWidgetItem(row.get("category_name") or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(f"{price:.2f}"))
            self.table.setItem(r, 4, QTableWidgetItem(str(tq) if tq is not None else "—"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{unit:.4f}"))

            if is_shared:
                for col in range(self.table.columnCount()):
                    itm = self.table.item(r, col)
                    if itm:
                        itm.setBackground(QColor(_SHARED_BG))
                        itm.setForeground(QColor(_SHARED_COLOR))

            shown += 1

        self._filter.set_count(shown, len(self._all_rows))