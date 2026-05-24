"""
ui/widgets/shared/base_crud_form.py
=====================================
BaseCrudForm — قاعدة مشتركة لكل نماذج الإضافة/التعديل/الإلغاء.

تحل محل الكود المتكرر في:
  machine_form.py, labor_op_form.py, machine_op_form.py,
  raw_input_panel.py, category_form.py

توفر:
  - build_inner_scroll تلقائي
  - EditModeMixin جاهز
  - أزرار إضافة/حفظ/إلغاء موحدة
  - منطق CRUD مجرد (abstract methods)

الاستخدام:
    class _MachineForm(BaseCrudForm):
        def _build_fields(self, grp: FormGroup) -> None:
            self.inp_name = QLineEdit()
            grp.add_row("الاسم:", self.inp_name)

        def _collect(self) -> dict | None:
            name = self.inp_name.text().strip()
            if not name:
                self._warn("أدخل الاسم")
                return None
            return {"name": name}

        def _do_insert(self, data: dict) -> int:
            return insert_machine(self._live_conn(), **data)

        def _do_update(self, item_id: int, data: dict) -> None:
            update_machine(self._live_conn(), item_id, **data)

        def _do_load(self, item_id: int) -> dict | None:
            return dict(fetch_machine(self._live_conn(), item_id) or {})

        def _fill_fields(self, data: dict) -> None:
            self.inp_name.setText(data.get("name", ""))

        def _reset_fields(self) -> None:
            self.inp_name.clear()
"""

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QLabel, QMessageBox,
)
from PyQt5.QtCore import pyqtSignal

from ui.helpers import EditModeMixin, buttons_row
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.form_utils import (
    FormGroup, build_inner_scroll,
)
from ui.events import bus


class BaseCrudForm(QWidget, EditModeMixin, LiveConnMixin):
    """
    قاعدة موحدة لكل نماذج CRUD.

    للاستخدام override المطلوب:
      _build_fields(grp)   → يضيف حقول الفورم في FormGroup
      _collect()           → يجمع البيانات ويرجع dict أو None
      _do_insert(data)     → يضيف في DB ويرجع ID
      _do_update(id, data) → يحدّث في DB
      _do_load(id)         → يجلب بيانات للتعديل ويرجع dict
      _fill_fields(data)   → يملأ الحقول بالبيانات
      _reset_fields()      → يمسح الحقول

    اختياري:
      _after_insert(new_id)  → بعد الإضافة (مثلاً تحميل صفوف)
      _after_save()          → بعد الحفظ
      _build_extra(root)     → widgets إضافية تحت الأزرار
    """

    # اسم النموذج للعرض (يُستخدم في label الوضع)
    FORM_TITLE : str = "بيانات"
    ADD_TEXT   : str = "➕  إضافة"
    SAVE_TEXT  : str = "💾  حفظ التعديل"
    CANCEL_TEXT: str = "✖  إلغاء"
    MIN_WIDTH  : int = 260

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(
            self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode
        )
        self._post_init()

    # ── override hooks ─────────────────────────────────────

    def _build_fields(self, grp: FormGroup) -> None:
        """يضيف حقول الفورم في grp.add_row(...)."""
        raise NotImplementedError

    def _collect(self) -> dict | None:
        """يجمع البيانات من الحقول ويرجع dict أو None لو فيه خطأ."""
        raise NotImplementedError

    def _do_insert(self, data: dict) -> int:
        """يضيف سجل في DB ويرجع ID الجديد."""
        raise NotImplementedError

    def _do_update(self, item_id: int, data: dict) -> None:
        """يحدّث سجل في DB."""
        raise NotImplementedError

    def _do_load(self, item_id: int) -> dict | None:
        """يجلب بيانات سجل للتعديل ويرجع dict أو None."""
        raise NotImplementedError

    def _fill_fields(self, data: dict) -> None:
        """يملأ الحقول بالبيانات للتعديل."""
        raise NotImplementedError

    def _reset_fields(self) -> None:
        """يمسح الحقول بعد الحفظ أو الإلغاء."""
        raise NotImplementedError

    # ── اختياري ───────────────────────────────────────────

    def _after_insert(self, new_id: int) -> None:
        """يُستدعى بعد الإضافة الناجحة."""
        pass

    def _after_save(self) -> None:
        """يُستدعى بعد الحفظ الناجح."""
        pass

    def _build_extra(self, root) -> None:
        """يضيف widgets إضافية تحت الأزرار (مثل _OpRowsEditor)."""
        pass

    def _post_init(self) -> None:
        """يُستدعى بعد الـ init — للاشتراك في signals مثلاً."""
        pass

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        _outer, _inner, root = build_inner_scroll(self, min_width=self.MIN_WIDTH)

        grp = FormGroup(self.FORM_TITLE)

        self.lbl_mode = QLabel(f"─── {self.ADD_TEXT.lstrip('➕  ')} جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        grp.add_label_row(self.lbl_mode)

        self._build_fields(grp)
        root.addWidget(grp)

        self.btn_add    = QPushButton(self.ADD_TEXT)
        self.btn_save   = QPushButton(self.SAVE_TEXT)
        self.btn_cancel = QPushButton(self.CANCEL_TEXT)
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self._on_cancel)
        root.addLayout(buttons_row(self.btn_add, self.btn_save, self.btn_cancel))

        self._build_extra(root)
        root.addStretch()

    # ── منطق الحفظ ────────────────────────────────────────

    def _on_add(self):
        data = self._collect()
        if data is None:
            return
        try:
            new_id = self._do_insert(data)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        bus.data_changed.emit()
        self._after_insert(new_id)
        self._reset()

    def _on_save(self):
        data = self._collect()
        if data is None:
            return
        try:
            self._do_update(self._editing_id, data)
        except Exception as e:
            QMessageBox.warning(self, "خطأ", str(e))
            return
        self._reset()
        bus.data_changed.emit()
        self._after_save()

    def _on_cancel(self):
        self._reset()

    # ── تحميل للتعديل ─────────────────────────────────────

    def load_for_edit(self, item_id: int):
        """يحمل بيانات سجل ويدخل وضع التعديل."""
        try:
            data = self._do_load(item_id)
        except Exception:
            return
        if not data:
            return
        self._fill_fields(data)
        label = data.get("name", f"ID:{item_id}")
        self.enter_edit_mode(item_id, f"─── تعديل: {label} ───")

    # ── مساعدات ───────────────────────────────────────────

    def _reset(self):
        """يمسح الحقول ويخرج من وضع التعديل."""
        self._reset_fields()
        self.exit_edit_mode(f"─── {self.ADD_TEXT.lstrip('➕  ')} جديد ───")

    def _warn(self, msg: str) -> None:
        """يعرض رسالة تحذير."""
        QMessageBox.warning(self, "تنبيه", msg)