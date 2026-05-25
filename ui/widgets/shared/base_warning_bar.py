"""
ui/widgets/shared/base_warning_bar.py
======================================
BaseWarningBar — شريط تحذير موحد قابل لإعادة الاستخدام.

[إصلاح v2]:
  - الأزرار تستخدم _make_btn من make_btn.py بدل hardcoded styles
  - ألوان من _C و STATUS_COLORS بدل hardcoded hex

يحل محل _WarningBar المكررة في:
  - ui/tabs/costing/product/product_table.py

الاستخدام:
    from ui.widgets.shared.base_warning_bar import BaseWarningBar

    self._warning = BaseWarningBar(
        on_fix=self._fix_orphans,
        on_edit=self._edit_selected,
    )
    layout.addWidget(self._warning)

    # إظهار تحذير
    self._warning.show_message(
        message="«منتج ما» — 3 مكوّنات محذوفة",
        fix_text="🗑️ حذف الناقص",
        edit_text="✏️ تعديل",
    )

    # إخفاء
    self._warning.setVisible(False)
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.shared.panles_helper.make_btn        import _make_btn
from ui.widgets.shared.panles_helper.theme           import STATUS_COLORS


class BaseWarningBar(QFrame):
    """
    شريط تحذير أفقي موحد.

    Signals:
        fix_clicked   — المستخدم ضغط زر الإصلاح
        edit_clicked  — المستخدم ضغط زر التعديل
        dismissed     — المستخدم ضغط ✖
    """

    fix_clicked  = pyqtSignal()
    edit_clicked = pyqtSignal()
    dismissed    = pyqtSignal()

    def __init__(self,
                 on_fix=None,
                 on_edit=None,
                 fix_text: str = "🗑️ حذف الناقص",
                 edit_text: str = "✏️ تعديل",
                 show_dismiss: bool = True,
                 parent=None):
        super().__init__(parent)
        self._fix_text  = fix_text
        self._edit_text = edit_text
        self._build(show_dismiss)
        self.setVisible(False)

        if on_fix:
            self.fix_clicked.connect(on_fix)
        if on_edit:
            self.edit_clicked.connect(on_edit)

    # ── بناء الواجهة ──────────────────────────────────────

    def _build(self, show_dismiss: bool):
        s = STATUS_COLORS["warning"]
        self.setObjectName("warningBar")
        self.setStyleSheet(f"""
            #warningBar {{
                background: {s['bg']};
                border: 1px solid {s['border']};
                border-radius: 6px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)

        self._icon = QLabel("⚠️")
        self._icon.setStyleSheet(
            "font-size:16px; background:transparent; border:none;"
        )
        lay.addWidget(self._icon)

        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setStyleSheet(
            f"color:{s['fg']}; font-weight:bold; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl, stretch=1)

        self._btn_fix = _make_btn(self._fix_text, "danger")
        self._btn_fix.clicked.connect(self.fix_clicked.emit)
        lay.addWidget(self._btn_fix)

        self._btn_edit = _make_btn(self._edit_text, "primary")
        self._btn_edit.clicked.connect(self.edit_clicked.emit)
        lay.addWidget(self._btn_edit)

        if show_dismiss:
            btn_dismiss = _make_btn("✖", "ghost")
            btn_dismiss.clicked.connect(self._on_dismiss)
            lay.addWidget(btn_dismiss)

    # ── API خارجي ─────────────────────────────────────────

    def show_message(self, message: str,
                     fix_text: str = None,
                     edit_text: str = None):
        """
        يعرض رسالة التحذير ويظهر الشريط.

        message  : نص الرسالة
        fix_text : نص زر الإصلاح (اختياري — يستخدم القيمة المبدئية لو None)
        edit_text: نص زر التعديل (اختياري)
        """
        self._lbl.setText(message)
        if fix_text:
            self._btn_fix.setText(fix_text)
        if edit_text:
            self._btn_edit.setText(edit_text)
        self.setVisible(True)

    def show_orphans(self, orphans: list, product_name: str,
                     type_labels: dict = None):
        """
        يعرض قائمة المكونات الناقصة (Orphans) بشكل موحد.

        orphans      : list of dicts من fetch_orphan_bom_rows
        product_name : اسم المنتج
        type_labels  : dict لترجمة أنواع المكونات (اختياري)
        """
        if not orphans:
            self.setVisible(False)
            return

        _default_labels = {
            "raw":        "خامة",
            "semi":       "نصف مصنع",
            "labor_op":   "عملية عمالة",
            "machine_op": "عملية تشغيل",
        }
        labels = type_labels or _default_labels

        lines = []
        for o in orphans:
            type_ar  = labels.get(o["child_type"], o["child_type"])
            display  = o.get("child_name") or f"ID: {o['child_id']}"
            lines.append(f"• {type_ar}: «{display}»")

        msg = (
            f"«{product_name}» — {len(orphans)} مكوّن محذوف:\n"
            + "  ".join(lines)
        )
        self.show_message(msg)

    def hide_warning(self):
        """يخفي الشريط."""
        self.setVisible(False)

    def set_fix_visible(self, visible: bool):
        """يظهر/يخفي زر الإصلاح."""
        self._btn_fix.setVisible(visible)

    def set_edit_visible(self, visible: bool):
        """يظهر/يخفي زر التعديل."""
        self._btn_edit.setVisible(visible)

    # ── signal handlers ───────────────────────────────────

    def _on_dismiss(self):
        self.setVisible(False)
        self.dismissed.emit()