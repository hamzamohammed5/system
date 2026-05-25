"""
widgets/base/crud_form.py
==========================
BaseCrudForm — قاعدة مشتركة لكل نماذج الإضافة/التعديل.

التغييرات عن النسخة القديمة:
  - NotificationBar بدل QMessageBox المنبثقة
  - _collect_and_validate() hook موحد
  - EditModeMixin مدمجة هنا مباشرة
  - set_conn() لتحديث الـ connection
  - build_inner_scroll من utils/scroll
"""

import logging
from PyQt5.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QScrollArea, QSizePolicy
from PyQt5.QtCore    import pyqtSignal, Qt

from ui.app_settings import _C
from ..panels.form_parts import FormGroup, ModeLabel
from ..panels.notify     import NotificationBar
from ..panels._btn       import make_btn
from ..mixins.edit       import EditModeMixin
from ..mixins.validate   import FormValidationMixin
from ..utils.scroll      import wrap_in_scroll
from ui.events import bus

logger = logging.getLogger(__name__)


class BaseCrudForm(QWidget, EditModeMixin, FormValidationMixin):
    """
    قاعدة موحدة لكل نماذج CRUD.

    Override المطلوب:
        _build_fields(group)    → يضيف حقول الفورم
        _collect()              → يجمع البيانات ويرجع dict أو None
        _do_insert(data)        → يضيف في DB ويرجع ID
        _do_update(id, data)    → يحدّث في DB
        _do_load(id)            → يجلب بيانات للتعديل ويرجع dict
        _fill_fields(data)      → يملأ الحقول
        _reset_fields()         → يمسح الحقول

    Override الاختياري:
        _after_insert(new_id)
        _after_save()
        _build_extra(root)      → widgets إضافية تحت الأزرار
        _validate()             → تحقق إضافي، يرجع str أو None
        _post_init()
    """

    item_added   = pyqtSignal(int)
    item_updated = pyqtSignal(int)

    FORM_TITLE      : str = "بيانات"
    FORM_TITLE_ICON : str = ""
    ADD_TEXT        : str = "➕  إضافة"
    SAVE_TEXT       : str = "💾  حفظ التعديل"
    CANCEL_TEXT     : str = "✖  إلغاء"
    MIN_WIDTH       : int = 260

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode)
        self._post_init()

    # ── override hooks ────────────────────────────────────

    def _build_fields(self, group: FormGroup):
        raise NotImplementedError

    def _collect(self) -> "dict | None":
        raise NotImplementedError

    def _do_insert(self, data: dict) -> int:
        raise NotImplementedError

    def _do_update(self, item_id: int, data: dict):
        raise NotImplementedError

    def _do_load(self, item_id: int) -> "dict | None":
        raise NotImplementedError

    def _fill_fields(self, data: dict):
        raise NotImplementedError

    def _reset_fields(self):
        raise NotImplementedError

    # ── اختياري ───────────────────────────────────────────

    def _after_insert(self, new_id: int):
        pass

    def _after_save(self):
        pass

    def _build_extra(self, root: QVBoxLayout):
        pass

    def _post_init(self):
        pass

    def _validate(self) -> "str | None":
        return None

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        inner = QWidget()
        inner.setMinimumWidth(self.MIN_WIDTH)
        inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        scroll = wrap_in_scroll(inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        outer.addWidget(scroll)

        root = QVBoxLayout(inner)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        self._notif = NotificationBar(show_dismiss=True)
        root.addWidget(self._notif)

        title = f"{self.FORM_TITLE_ICON}  {self.FORM_TITLE}" \
                if self.FORM_TITLE_ICON else self.FORM_TITLE
        grp = FormGroup(title)

        self.lbl_mode = ModeLabel(add_text=self.ADD_TEXT.lstrip("➕  "))
        grp.add_label_row(self.lbl_mode)

        self._build_fields(grp)
        root.addWidget(grp)

        self.btn_add    = make_btn(self.ADD_TEXT,    "primary")
        self.btn_save   = make_btn(self.SAVE_TEXT,   "success")
        self.btn_cancel = make_btn(self.CANCEL_TEXT, "ghost")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self._on_cancel)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        root.addLayout(btn_row)

        self._build_extra(root)
        root.addStretch()

    # ── منطق الحفظ ────────────────────────────────────────

    def _on_add(self):
        self._notif.hide_bar()
        data = self._collect()
        if data is None:
            return
        err = self._validate()
        if err:
            self._notif.show(err, "warning")
            return
        try:
            new_id = self._do_insert(data)
        except Exception as e:
            logger.warning("%s._on_add failed: %s", type(self).__name__, e)
            self._notif.show(str(e), "danger")
            return
        bus.data_changed.emit()
        self.item_added.emit(new_id)
        self._after_insert(new_id)
        self._reset()
        self._notif.show("تم الإضافة بنجاح", "success", auto_hide=2500)

    def _on_save(self):
        self._notif.hide_bar()
        data = self._collect()
        if data is None:
            return
        err = self._validate()
        if err:
            self._notif.show(err, "warning")
            return
        try:
            self._do_update(self._editing_id, data)
        except Exception as e:
            logger.warning("%s._on_save failed: %s", type(self).__name__, e)
            self._notif.show(str(e), "danger")
            return
        self._reset()
        bus.data_changed.emit()
        self.item_updated.emit(self._editing_id)
        self._after_save()

    def _on_cancel(self):
        self._notif.hide_bar()
        self._reset()

    # ── تحميل للتعديل ─────────────────────────────────────

    def load_for_edit(self, item_id: int):
        self._notif.hide_bar()
        try:
            data = self._do_load(item_id)
        except Exception as e:
            logger.warning("%s.load_for_edit failed: %s", type(self).__name__, e)
            self._notif.show(f"خطأ في تحميل البيانات: {e}", "danger")
            return
        if not data:
            return
        self._fill_fields(data)
        label = data.get("name", f"ID:{item_id}")
        self.enter_edit_mode(item_id, f"─── تعديل: {label} ───")

    # ── helpers ───────────────────────────────────────────

    def _reset(self):
        self._reset_fields()
        add_label = self.ADD_TEXT.lstrip("➕  ")
        self.exit_edit_mode(f"─── {add_label} جديد ───")

    def set_conn(self, conn):
        self.conn = conn

    # alias
    def _warn(self, msg: str):
        self._notif.show(msg, "warning")