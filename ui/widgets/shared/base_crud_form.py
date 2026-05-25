"""
ui/widgets/shared/base_crud_form.py
=====================================
BaseCrudForm — قاعدة مشتركة لكل نماذج الإضافة/التعديل/الإلغاء.

[تحديث v3]:
  - NotificationBar بدل msg_warning المنبثقة
  - FormValidationMixin مدمجة
  - _collect_and_validate() hook موحد
  - set_conn() لتحديث الـ connection
  - FORM_TITLE_ICON لإضافة أيقونة للعنوان
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QPushButton, QHBoxLayout,
)
from PyQt5.QtCore import pyqtSignal

from ui.helpers import EditModeMixin
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.panels import (
    FormGroup,
    build_inner_scroll,
    ModeLabel,
    NotificationBar,
    _make_btn,
)
from ui.widgets.shared.shared_ui_mixins import FormValidationMixin
from ui.events import bus

logger = logging.getLogger(__name__)


def _buttons_row(*btns) -> QHBoxLayout:
    lay = QHBoxLayout()
    lay.setSpacing(6)
    for btn in btns:
        lay.addWidget(btn)
    lay.addStretch()
    return lay


class BaseCrudForm(QWidget, EditModeMixin, LiveConnMixin, FormValidationMixin):
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
      _after_insert(new_id) → بعد الإضافة
      _after_save()         → بعد الحفظ
      _build_extra(root)    → widgets إضافية تحت الأزرار
      _validate()           → تحقق إضافي قبل الحفظ، يرجع str أو None
    """

    # signals
    item_added   = pyqtSignal(int)   # new_id
    item_updated = pyqtSignal(int)   # item_id

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
        self.init_edit_mode(
            self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode
        )
        self._post_init()

    # ── override hooks ─────────────────────────────────────

    def _build_fields(self, grp: FormGroup) -> None:
        raise NotImplementedError

    def _collect(self) -> dict | None:
        raise NotImplementedError

    def _do_insert(self, data: dict) -> int:
        raise NotImplementedError

    def _do_update(self, item_id: int, data: dict) -> None:
        raise NotImplementedError

    def _do_load(self, item_id: int) -> dict | None:
        raise NotImplementedError

    def _fill_fields(self, data: dict) -> None:
        raise NotImplementedError

    def _reset_fields(self) -> None:
        raise NotImplementedError

    # ── اختياري ───────────────────────────────────────────

    def _after_insert(self, new_id: int) -> None:
        pass

    def _after_save(self) -> None:
        pass

    def _build_extra(self, root) -> None:
        pass

    def _post_init(self) -> None:
        pass

    def _validate(self) -> str | None:
        """
        تحقق إضافي قبل الحفظ.
        يرجع str (رسالة خطأ) أو None (كل شيء صحيح).
        """
        return None

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self):
        _outer, _inner, root = build_inner_scroll(self, min_width=self.MIN_WIDTH)

        # Notification bar
        self._notif = NotificationBar(show_dismiss=True)
        root.addWidget(self._notif)

        # عنوان الفورم
        title = f"{self.FORM_TITLE_ICON}  {self.FORM_TITLE}" \
                if self.FORM_TITLE_ICON else self.FORM_TITLE
        grp = FormGroup(title)

        # ModeLabel
        self.lbl_mode = ModeLabel(
            add_text=self.ADD_TEXT.lstrip("➕  "),
        )
        grp.add_label_row(self.lbl_mode)

        self._build_fields(grp)
        root.addWidget(grp)

        # أزرار
        self.btn_add    = _make_btn(self.ADD_TEXT,    "primary")
        self.btn_save   = _make_btn(self.SAVE_TEXT,   "success")
        self.btn_cancel = _make_btn(self.CANCEL_TEXT, "ghost")
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(30)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self._on_cancel)
        root.addLayout(_buttons_row(self.btn_add, self.btn_save, self.btn_cancel))

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

    # ── مساعدات ───────────────────────────────────────────

    def _reset(self):
        self._reset_fields()
        add_label = self.ADD_TEXT.lstrip("➕  ")
        self.exit_edit_mode(f"─── {add_label} جديد ───")

    def set_conn(self, conn):
        """يحدّث الـ connection (مفيد عند تغيير الشركة)."""
        self.conn = conn

    # alias للتوافق
    def _warn(self, msg: str) -> None:
        self._notif.show(msg, "warning")