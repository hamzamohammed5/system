"""
ui/widgets/mixins/select.py
=====================================
SelectionMixin — منطق موحد لتحديد عناصر الجدول.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMessageBox


class SelectionMixin:
    """
    Mixin يوفر منطق التحديد الموحد لأي widget يحتوي جدول.

    يُستخدم في: DataTableWidget, BaseListPanel, وأي widget آخر.

    الاستخدام:
        class MyPanel(QWidget, SelectionMixin):
            def _edit(self):
                item_id = self._require_selection()
                if item_id is None:
                    return

            def _on_select(self):
                self._emit_selected(self.table, self.row_selected)
    """

    _id_col:  int = 0
    _id_role: int = Qt.UserRole

    # ── قراءة الـ ID المحدد ───────────────────────────────

    def _selected_id(self, table=None):
        """يرجع ID العنصر المحدد أو None."""
        tbl = table or getattr(self, "table", None)
        if tbl is None:
            return None

        row = tbl.currentRow()
        if row < 0:
            return None

        item = tbl.item(row, self._id_col)
        if item is None:
            return None

        data = item.data(self._id_role)
        if data is not None:
            try:
                return int(data)
            except (ValueError, TypeError):
                return data

        try:
            return int(item.text())
        except (ValueError, TypeError):
            return None

    def _selected_row(self, table=None) -> int:
        tbl = table or getattr(self, "table", None)
        return tbl.currentRow() if tbl else -1

    # ── emit موحد — يُستدعى من itemSelectionChanged ────────

    def _emit_selected(self, table, signal):
        """
        يقرأ الـ ID من الصف المحدد ويطلق الـ signal.

        الاستخدام:
            self.table.itemSelectionChanged.connect(
                lambda: self._emit_selected(self.table, self.row_selected)
            )
        """
        row = table.currentRow()
        if row < 0:
            return
        item = table.item(row, self._id_col)
        if item:
            data = item.data(self._id_role)
            if data is not None:
                signal.emit(int(data))

    # ── تحديد صف بالـ ID ──────────────────────────────────

    def select_row_by_id(self, item_id: int, table=None):
        """يحدد الصف الذي يحمل item_id في العمود 0."""
        tbl = table or getattr(self, "table", None)
        if tbl is None:
            return
        for r in range(tbl.rowCount()):
            item = tbl.item(r, self._id_col)
            if item and item.data(self._id_role) == item_id:
                tbl.selectRow(r)
                return

    # ── تحقق من وجود تحديد ───────────────────────────────

    def _warn_no_selection(self, msg: str = "اختر عنصراً أولاً"):
        QMessageBox.information(self, "تنبيه", msg)

    def _require_selection(self, msg: str = "اختر عنصراً أولاً") -> "int | None":
        item_id = self._selected_id()
        if item_id is None:
            self._warn_no_selection(msg)
        return item_id