"""
ui/widgets/base/crud_form.py
=============================
BaseCrudForm — قاعدة مشتركة لكل فورمات CRUD.

[إصلاح 2.4] from ui.widgets.mixins.edit import EditModeMixin
         → from ui.widgets.mixins.form_mixins import EditModeMixin
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.mixins.form_mixins import EditModeMixin   # [إصلاح 2.4]
from ui.widgets.core.conn          import LiveConnMixin
from ui.widgets.panels.form_group  import FormGroup
from ui.widgets.theme.builders     import wrap_in_scroll
from ui.events                     import bus


class BaseCrudForm(QWidget, EditModeMixin, LiveConnMixin):
    """
    قاعدة مشتركة لكل فورمات CRUD.
    راجع docstring الملف للتفاصيل الكاملة.
    """

    # ── إعدادات الـ subclass ──────────────────────────────
    FORM_TITLE : str = "بيانات العنصر"
    ADD_TEXT   : str = "➕  إضافة"
    SAVE_TEXT  : str = "💾  حفظ التعديل"

    # signal يُطلق بعد نجاح الإضافة أو التعديل — يحمل ID العنصر
    saved = pyqtSignal(int)

    def __init__(self, conn=None, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()
        self.init_edit_mode(
            self.btn_add, self.btn_save, self.btn_cancel, self.lbl_mode
        )

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        inner = QWidget()
        inner.setMinimumWidth(260)
        root = QVBoxLayout(inner)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        outer.addWidget(wrap_in_scroll(inner))

        # ── FormGroup ──
        grp = FormGroup(self.FORM_TITLE)

        self.lbl_mode = QLabel()
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0;")
        grp.add_label_row(self.lbl_mode)

        # hook الـ subclass لإضافة الحقول
        self._build_fields(grp)
        root.addWidget(grp)

        # hook اختياري لإضافة widgets إضافية بعد الـ FormGroup
        self._build_extra(root)

        # ── أزرار ──
        self.btn_add    = QPushButton(self.ADD_TEXT)
        self.btn_save   = QPushButton(self.SAVE_TEXT)
        self.btn_cancel = QPushButton("✖  إلغاء")
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
        root.addStretch()

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
            QMessageBox.warning(self, "خطأ", str(e))
            return
        self._reset()
        bus.data_changed.emit()
        self.saved.emit(new_id)

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
        self.enter_edit_mode(item_id, f"─── تعديل: {name} ───")

    def _reset(self):
        self._reset_fields()
        self.exit_edit_mode(f"─── {self.FORM_TITLE} ───")