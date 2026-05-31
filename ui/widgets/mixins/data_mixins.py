"""
ui/widgets/mixins/data_mixins.py
=================================
دمج ثلاثة mixins ليها علاقة بتحميل وعرض البيانات:
  - RefreshableMixin  (كان في refresh.py)
  - RebuildMixin      (كان في rebuild.py)
  - SelectionMixin    (كان في select.py)

الملفات المحذوفة: refresh.py, rebuild.py, select.py
"""

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QWidget

from ..core.i18n import tr


# ══════════════════════════════════════════════════════════
# RefreshableMixin
# ══════════════════════════════════════════════════════════

class RefreshableMixin:
    """
    Mixin لأي widget يحتاج تحديث دوري.

    Override:
        _load_data() → يجلب البيانات
        _fill_ui(data) → يملأ الـ UI
    """

    def refresh(self):
        try:
            data = self._load_data()
            self._fill_ui(data)
        except Exception as e:
            self._on_refresh_error(e)

    def _load_data(self):
        return []

    def _fill_ui(self, data):
        pass

    def _on_refresh_error(self, error: Exception):
        print(f"[{self.__class__.__name__}] refresh error: {error}")


# ══════════════════════════════════════════════════════════
# RebuildMixin
# ══════════════════════════════════════════════════════════

class RebuildMixin:
    """
    Mixin يوفر _replace_widget() لإعادة بناء محتوى الـ tab.

    يفترض: self._root_layout (QVBoxLayout)
    """

    def _replace_widget(self, new_widget: QWidget):
        root = getattr(self, "_root_layout", None)
        if root is None:
            return

        old = getattr(self, "_current_widget", None)
        if old is not None:
            root.removeWidget(old)
            old.hide()
            old.deleteLater()

        self._current_widget = new_widget
        if new_widget is not None:
            root.addWidget(new_widget)

    def _schedule_rebuild(self, delay_ms: int = 0):
        QTimer.singleShot(delay_ms, self._rebuild)

    def _rebuild(self):
        pass


# ══════════════════════════════════════════════════════════
# SelectionMixin
# ══════════════════════════════════════════════════════════

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
        _msg = msg or tr("select_item_first")
        msg_info(self, tr("warning"), _msg)

    def _require_selection(self, msg: str = "") -> "int | None":
        item_id = self._selected_id()
        if item_id is None:
            self._warn_no_selection(msg)
        return item_id