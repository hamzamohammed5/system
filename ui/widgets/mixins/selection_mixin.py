"""
ui/widgets/mixins/selection_mixin.py
======================================
SelectionMixin — منطق اختيار الصفوف في الجداول.

مستخرج من mixins/data_mixins.py.
"""

from PyQt5.QtCore import Qt


class SelectionMixin:
    """
    Mixin يوفر _selected_id() و _require_selection() لأي widget يحتوي جدول.

    الاستخدام:
        class MyPanel(QWidget, SelectionMixin):
            def _edit(self):
                item_id = self._require_selection()
                if item_id is None:
                    return
    """

    _id_col: int  = 0
    _id_role: int = Qt.UserRole

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

    def _warn_no_selection(self, msg: str = ""):
        from ..dialogs.message import msg_info
        from ..core.i18n import tr
        _msg = msg or tr("select_item_first")
        msg_info(self, tr("warning"), _msg)

    def _require_selection(self, msg: str = "") -> "int | None":
        item_id = self._selected_id()
        if item_id is None:
            self._warn_no_selection(msg)
        return item_id