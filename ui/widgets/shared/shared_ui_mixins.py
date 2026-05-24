"""
ui/widgets/shared/shared_ui_mixins.py
=======================================
Mixins لأنماط UI المتكررة عبر التطبيق.

الناقص الذي يحل هذا الملف:
  - RefreshableMixin    : لأي widget يحتاج refresh بعد تغيير البيانات
  - BusConnectedMixin   : ربط تلقائي بـ bus.data_changed و company_data_changed
  - SelectionMixin      : منطق موحد لتحديد عنصر من جدول
  - FormValidationMixin : تحقق موحد من حقول الفورم قبل الحفظ

الاستخدام:
    class MyListPanel(QWidget, BusConnectedMixin):
        def __init__(self, conn):
            super().__init__()
            self.conn = conn
            self._connect_bus(data=True, company=True)

        def _on_data_changed(self):
            self.refresh()

        def _on_company_changed(self, company_id):
            self.refresh()

    class MyForm(QWidget, FormValidationMixin):
        def _save(self):
            if not self.validate_fields([
                (self.inp_name, "الاسم"),
                (self.inp_code, "الكود"),
            ]):
                return
            # continue saving...
"""

from PyQt5.QtWidgets import QWidget, QTableWidget, QMessageBox
from PyQt5.QtCore import Qt


# ══════════════════════════════════════════════════════════
# RefreshableMixin — widget قابل للتحديث
# ══════════════════════════════════════════════════════════

class RefreshableMixin:
    """
    Mixin لأي widget يحتاج refresh.
    يفصل منطق التحميل عن الاستجابة للأحداث.

    Override:
        _load_data() → يجلب البيانات من DB
        _fill_ui(data) → يملأ الـ UI بالبيانات

    الاستخدام:
        class MyPanel(QWidget, RefreshableMixin):
            def _load_data(self):
                return fetch_items(self.conn)

            def _fill_ui(self, data):
                self.table.setRowCount(0)
                for row in data:
                    ...
    """

    def refresh(self):
        """يعيد تحميل البيانات وتحديث الـ UI."""
        try:
            data = self._load_data()
            self._fill_ui(data)
        except Exception as e:
            self._on_refresh_error(e)

    def _load_data(self):
        """Override: يجلب البيانات."""
        return []

    def _fill_ui(self, data):
        """Override: يملأ الـ UI."""
        pass

    def _on_refresh_error(self, error: Exception):
        """Override: يتعامل مع أخطاء التحميل."""
        print(f"[{self.__class__.__name__}] refresh error: {error}")


# ══════════════════════════════════════════════════════════
# BusConnectedMixin — ربط تلقائي بـ event bus
# ══════════════════════════════════════════════════════════

class BusConnectedMixin:
    """
    Mixin يوفر ربطاً موحداً بـ event bus.

    يحل التكرار في الربط اليدوي بـ bus.data_changed و bus.company_data_changed.

    الاستخدام:
        class MyWidget(QWidget, BusConnectedMixin):
            def __init__(self):
                super().__init__()
                self._connect_bus(data=True, company=True)

            def _on_data_changed(self):
                self._load()

            def _on_company_changed(self, company_id: int):
                self._rebuild()
    """

    def _connect_bus(self, data: bool = True, company: bool = False):
        """يربط بـ event bus حسب الاحتياج."""
        from ui.events import bus
        if data:
            bus.data_changed.connect(self._on_data_changed)
        if company:
            bus.company_data_changed.connect(self._on_company_changed)

    def _on_data_changed(self):
        """Override: الاستجابة لتغيير البيانات."""
        pass

    def _on_company_changed(self, company_id: int):
        """Override: الاستجابة لتغيير الشركة."""
        pass


# ══════════════════════════════════════════════════════════
# SelectionMixin — منطق تحديد العناصر
# ══════════════════════════════════════════════════════════

class SelectionMixin:
    """
    Mixin يوفر منطقاً موحداً للحصول على العنصر المحدد في الجدول.

    يحل التكرار في:
        row = self.table.currentRow()
        if row == -1: return None
        item = self.table.item(row, 0)
        return int(item.text()) if item else None

    الاستخدام:
        class MyTable(QWidget, SelectionMixin):
            def _edit(self):
                item_id = self._selected_id()
                if item_id is None:
                    self._warn_no_selection()
                    return
                ...

        # مع UserRole:
        class MyTable(QWidget, SelectionMixin):
            _id_col = 0
            _id_role = Qt.UserRole
    """

    _id_col: int = 0
    _id_role: int = Qt.UserRole
    _id_as_text: bool = False  # True لو الـ ID موجود كنص في الخلية

    def _selected_id(self, table: QTableWidget = None):
        """
        يرجع ID العنصر المحدد أو None.

        table: الجدول (افتراضياً self.table)
        """
        tbl = table or getattr(self, 'table', None)
        if tbl is None:
            return None

        row = tbl.currentRow()
        if row < 0:
            return None

        item = tbl.item(row, self._id_col)
        if item is None:
            return None

        if self._id_as_text:
            try:
                return int(item.text())
            except (ValueError, TypeError):
                return None
        else:
            data = item.data(self._id_role)
            if data is not None:
                try:
                    return int(data)
                except (ValueError, TypeError):
                    return data
            # fallback للنص
            try:
                return int(item.text())
            except (ValueError, TypeError):
                return None

    def _selected_row(self, table: QTableWidget = None) -> int:
        """يرجع رقم الصف المحدد أو -1."""
        tbl = table or getattr(self, 'table', None)
        if tbl is None:
            return -1
        return tbl.currentRow()

    def _warn_no_selection(self, parent=None, msg: str = "اختر عنصراً أولاً"):
        """يُظهر تحذير لو لم يتم التحديد."""
        p = parent or self
        QMessageBox.information(p, "تنبيه", msg)

    def _require_selection(self, parent=None,
                            msg: str = "اختر عنصراً أولاً") -> int | None:
        """
        يرجع ID المحدد أو يُظهر تحذير ويرجع None.

        الاستخدام:
            def _edit(self):
                item_id = self._require_selection()
                if item_id is None:
                    return
                ...
        """
        item_id = self._selected_id()
        if item_id is None:
            self._warn_no_selection(parent, msg)
        return item_id


# ══════════════════════════════════════════════════════════
# FormValidationMixin — تحقق موحد من الفورم
# ══════════════════════════════════════════════════════════

class FormValidationMixin:
    """
    Mixin يوفر تحققاً موحداً من حقول الفورم.

    الاستخدام:
        class MyForm(QWidget, FormValidationMixin):
            def _save(self):
                if not self.validate_required([
                    (self.inp_name, "الاسم"),
                    (self.inp_code, "الكود"),
                ]):
                    return

                if not self.validate_amount(self.sp_amount, "المبلغ"):
                    return

                # proceed with save...
    """

    def validate_required(self, fields: list,
                           parent=None) -> bool:
        """
        يتحقق من أن كل الحقول المطلوبة غير فارغة.

        fields: list of (widget, label_text)
        يرجع True لو كل الحقول مملوءة.
        """
        from PyQt5.QtWidgets import QLineEdit, QComboBox
        p = parent or self

        for widget, label in fields:
            if isinstance(widget, QLineEdit):
                if not widget.text().strip():
                    QMessageBox.warning(p, "تنبيه", f"أدخل {label}")
                    widget.setFocus()
                    return False
            elif isinstance(widget, QComboBox):
                if widget.currentData() is None:
                    QMessageBox.warning(p, "تنبيه", f"اختر {label}")
                    return False

        return True

    def validate_amount(self, spinbox, label: str = "المبلغ",
                        min_val: float = 0.01,
                        parent=None) -> bool:
        """
        يتحقق من أن المبلغ أكبر من الحد الأدنى.
        يرجع True لو صالح.
        """
        p = parent or self
        if spinbox.value() < min_val:
            QMessageBox.warning(p, "تنبيه", f"أدخل {label} أكبر من صفر")
            spinbox.setFocus()
            return False
        return True

    def validate_positive(self, value: float,
                           label: str = "القيمة",
                           parent=None) -> bool:
        """يتحقق من أن القيمة موجبة."""
        p = parent or self
        if value <= 0:
            QMessageBox.warning(p, "تنبيه", f"{label} يجب أن يكون أكبر من صفر")
            return False
        return True