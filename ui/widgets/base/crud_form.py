"""
ui/widgets/base/crud_form.py
=============================
BaseCrudForm — قاعدة مشتركة لكل فورمات CRUD.

[إصلاح 2.4] from ui.widgets.mixins.edit import EditModeMixin
         → from ui.widgets.mixins.form_mixins import EditModeMixin

[FIX] استبدال bus.data_changed.emit() بـ emit_company_data_changed()
      لتجنب تحديث كل الـ widgets في كل الشركات عند حفظ بيانات شركة واحدة.

[i18n] استبدال كل النصوص الثابتة (FORM_TITLE الافتراضي، نصوص الأزرار،
       عنوان رسالة الخطأ، وصيغ وضع التعديل/العرض) بمفاتيح tr() من ar.py/en.py.
       lang=True أُضيفت لـ WidgetMixin عشان تتحدث النصوص تلقائياً عند تغيير اللغة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.mixins.form_mixins  import EditModeMixin   # [إصلاح 2.4]
from ui.widgets.core.conn           import LiveConnMixin
from ui.widgets.panels.form_group   import FormGroup
from ui.widgets.theme.builders      import wrap_in_scroll
from ui.widgets.core.events         import emit_company_data_changed
from ui.widgets.core.widget_mixin   import WidgetMixin
from ui.constants                   import (
    FORM_MIN_W, MARGIN_FORM, SPACING_MD, SPACING_SM, BTN_MIN_HEIGHT,
)


def _tr_safe(key: str, **kwargs) -> str:
    try:
        from ui.widgets.core.i18n import tr
        text = tr(key)
        return text.format(**kwargs) if kwargs else text
    except Exception:
        return key


class BaseCrudForm(QWidget, EditModeMixin, LiveConnMixin, WidgetMixin):
    """
    قاعدة مشتركة لكل فورمات CRUD.
    راجع docstring الملف للتفاصيل الكاملة.
    """

    # ── إعدادات الـ subclass ──────────────────────────────
    # [i18n] القيم دي fallback افتراضي بس — الـ subclass المفروض يعمل override
    # بمفتاح tr() مناسب لسياقه. لو الـ subclass سابها زي ما هي، بتترجم
    # تلقائياً عبر المفاتيح العامة دي.
    FORM_TITLE : str = "shared_item_data_section"
    ADD_TEXT   : str = "btn_add"
    SAVE_TEXT  : str = "btn_save"

    # signal يُطلق بعد نجاح الإضافة أو التعديل — يحمل ID العنصر
    saved = pyqtSignal(int)

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._editing_name: "str | None" = None
        self._build()
        self.init_edit_mode(
            self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode
        )
        self._init_widget_mixin(theme=True, font=False, lang=True)
        self._refresh_style()
        self._refresh_lang()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        inner = QWidget()
        inner.setMinimumWidth(FORM_MIN_W)
        root = QVBoxLayout(inner)
        root.setContentsMargins(*MARGIN_FORM)
        root.setSpacing(SPACING_MD)

        outer.addWidget(wrap_in_scroll(inner))

        # ── FormGroup ──
        self._grp = FormGroup(_tr_safe(self.FORM_TITLE))

        self.lbl_mode = QLabel()
        self._grp.add_label_row(self.lbl_mode)

        # hook الـ subclass لإضافة الحقول
        self._build_fields(self._grp)
        root.addWidget(self._grp)

        # hook اختياري لإضافة widgets إضافية بعد الـ FormGroup
        self._build_extra(root)

        # ── أزرار ──
        self.btn_add    = QPushButton(_tr_safe(self.ADD_TEXT))
        self.btn_save   = QPushButton(_tr_safe(self.SAVE_TEXT))
        self.btn_cancel = QPushButton(_tr_safe("btn_cancel"))
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn.setMinimumHeight(BTN_MIN_HEIGHT)

        self.btn_add.clicked.connect(self._on_add)
        self.btn_save.clicked.connect(self._on_save)
        self.btn_cancel.clicked.connect(self._on_cancel)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(SPACING_SM)
        for btn in (self.btn_add, self.btn_save, self.btn_cancel):
            btn_row.addWidget(btn)
        btn_row.addStretch()
        root.addLayout(btn_row)
        root.addStretch()

    # ── [i18n/themes] Theme handler ───────────────────────

    def _refresh_style(self, *_):
        from ui.theme import _C
        self.lbl_mode.setStyleSheet(f"font-weight:bold; color:{_C['blue']};")

    # ── [i18n] Language handler ────────────────────────────

    def _refresh_lang(self, *_):
        self._grp.setTitle(_tr_safe(self.FORM_TITLE))
        self.btn_add.setText(_tr_safe(self.ADD_TEXT))
        self.btn_save.setText(_tr_safe(self.SAVE_TEXT))
        self.btn_cancel.setText(_tr_safe("btn_cancel"))
        # إعادة رسم نص وضع التعديل/العرض الحالي بترجمة محدثة
        if getattr(self, "_editing_id", None) and self._editing_name is not None:
            self.enter_edit_mode(self._editing_id, _tr_safe("edit_mode_fmt", name=self._editing_name))
        else:
            self.exit_edit_mode(_tr_safe("form_title_wrapped_fmt", title=_tr_safe(self.FORM_TITLE)))

    # ══════════════════════════════════════════════════════
    # Hooks — المطلوب override في الـ subclass
    # ══════════════════════════════════════════════════════

    def _build_fields(self, group: FormGroup):
        raise NotImplementedError

    def _build_extra(self, root_layout: QVBoxLayout):
        pass

    def _collect(self) -> "dict | None":
        raise NotImplementedError

    def _do_insert(self, data: dict) -> int:
        raise NotImplementedError

    def _do_update(self, item_id: int, data: dict) -> None:
        raise NotImplementedError

    def _do_load(self, item_id: int) -> "dict | None":
        raise NotImplementedError

    def _fill_fields(self, data: dict) -> None:
        raise NotImplementedError

    def _reset_fields(self) -> None:
        raise NotImplementedError

    # ══════════════════════════════════════════════════════
    # منطق الأزرار
    # ══════════════════════════════════════════════════════

    def _on_add(self):
        data = self._collect()
        if data is None:
            return
        try:
            new_id = self._do_insert(data)
        except Exception as e:
            QMessageBox.warning(self, _tr_safe("error"), str(e))
            return
        self._reset()
        # [FIX] emit_company_data_changed بدل bus.data_changed.emit()
        # يضمن تحديث widgets الشركة النشطة فقط بدل كل الشركات
        emit_company_data_changed()
        self.saved.emit(new_id)

    def _on_save(self):
        data = self._collect()
        if data is None:
            return
        try:
            self._do_update(self._editing_id, data)
        except Exception as e:
            QMessageBox.warning(self, _tr_safe("error"), str(e))
            return
        self._reset()
        # [FIX] emit_company_data_changed بدل bus.data_changed.emit()
        emit_company_data_changed()
        self.saved.emit(self._editing_id)

    def _on_cancel(self):
        self._reset()

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_for_edit(self, item_id: int):
        try:
            data = self._do_load(item_id)
        except Exception:
            return
        if not data:
            return
        self._fill_fields(data)
        name = data.get("name", f"ID:{item_id}")
        self._editing_name = name
        self.enter_edit_mode(item_id, _tr_safe("edit_mode_fmt", name=name))

    def _reset(self):
        self._editing_name = None
        self._reset_fields()
        self.exit_edit_mode(_tr_safe("form_title_wrapped_fmt", title=_tr_safe(self.FORM_TITLE)))