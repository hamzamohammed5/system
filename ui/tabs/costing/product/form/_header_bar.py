"""
ui/tabs/costing/product/form/_header_bar.py
============================================
_FormHeaderBar — شريط الهيدر العلوي للفورم (اسم المنتج + التصنيف + الأزرار).

[Refactor] المسارات الموثقة في files_reference:
  - make_btn(style="success") → ui.widgets.components.button
  - CategoryCombo             → ui.widgets.combo.category
  - wrap_in_scroll            → ui.widgets.theme.styles
[Refactor] ربط bus.theme_changed لتحديث stylesheet ديناميكياً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal

from ui.widgets.core.widget_mixin  import WidgetMixin
from ui.widgets.core.i18n          import tr
from ui.widgets.components.button  import make_btn
from ui.widgets.combo.category     import CategoryCombo
from ui.widgets.theme.builders     import wrap_in_scroll
from ui.font                       import FS_BASE, FS_SM
from ui.constants import (
    PRODUCT_FORM_HEADER_MIN_W, PRODUCT_FORM_HEADER_H,
    PRODUCT_FORM_HEADER_MARGIN, PRODUCT_FORM_HEADER_SPACING,
    PRODUCT_FORM_TOP_SPACING, PRODUCT_FORM_MODE_MIN_W,
    PRODUCT_FORM_INP_MIN_H, PRODUCT_FORM_CAT_W,
    PRODUCT_FORM_TOP_INNER_SPACING, PRODUCT_FORM_TOP_BTN_SPACING,
    SPACING_ZERO, MARGIN_ZERO,
)

from ui.tabs.costing.shared.bom_scenarios_panel import _BomScenariosPanel


class _FormHeaderBar(QWidget, WidgetMixin):
    """
    الشريط العلوي للفورم.

    Signals:
      add_row_clicked       — المستخدم ضغط "+ مكون"
      save_clicked          — المستخدم ضغط "حفظ"
      cancel_clicked        — المستخدم ضغط "إلغاء"
      scenario_changed(int) — تغيير السيناريو الحالي
    """

    add_row_clicked  = pyqtSignal()
    save_clicked     = pyqtSignal()
    cancel_clicked   = pyqtSignal()
    scenario_changed = pyqtSignal(int)

    def __init__(self, conn, scope: str, parent=None):
        super().__init__(parent)
        self._scope = scope
        self._conn  = conn
        self._init_widget_mixin(lang=False, data=False)
        self._build()
        self._refresh_style()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(*MARGIN_ZERO)
        outer.setSpacing(SPACING_ZERO)

        header_inner = QWidget()
        header_inner.setMinimumWidth(PRODUCT_FORM_HEADER_MIN_W)
        header_inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self._header_inner = header_inner

        header_scroll = wrap_in_scroll(header_inner)
        header_scroll.setFixedHeight(PRODUCT_FORM_HEADER_H)

        header_lay = QVBoxLayout(header_inner)
        header_lay.setContentsMargins(*PRODUCT_FORM_HEADER_MARGIN)
        header_lay.setSpacing(PRODUCT_FORM_HEADER_SPACING)

        # ── صف الأزرار والحقول ──
        top = QHBoxLayout()
        top.setSpacing(PRODUCT_FORM_TOP_SPACING)

        self.lbl_mode = QLabel(tr("mode_label_wrap").format(content=tr("new_product")))
        self.lbl_mode.setMinimumWidth(PRODUCT_FORM_MODE_MIN_W)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("product_name_placeholder"))
        self.inp_name.setMinimumHeight(PRODUCT_FORM_INP_MIN_H)

        self.cmb_category = CategoryCombo(self._conn, scope=self._scope)
        self.cmb_category.setMinimumHeight(PRODUCT_FORM_INP_MIN_H)
        self.cmb_category.setFixedWidth(PRODUCT_FORM_CAT_W)

        self.btn_add_row = QPushButton(tr("btn_add_component"))
        self.btn_add_row.setMinimumHeight(PRODUCT_FORM_INP_MIN_H)
        self.btn_add_row.clicked.connect(self.add_row_clicked.emit)

        self.btn_save   = make_btn(tr("save"), style="success")
        self.btn_cancel = QPushButton(tr("btn_cancel"))
        self.btn_save.setMinimumHeight(PRODUCT_FORM_INP_MIN_H)
        self.btn_cancel.setMinimumHeight(PRODUCT_FORM_INP_MIN_H)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)
        self.btn_cancel.setVisible(False)

        top.addWidget(self.lbl_mode)
        top.addWidget(self.inp_name, stretch=3)
        top.addSpacing(PRODUCT_FORM_TOP_INNER_SPACING)
        top.addWidget(QLabel(f"{tr('category')}:"))
        top.addWidget(self.cmb_category)
        top.addSpacing(PRODUCT_FORM_TOP_BTN_SPACING)
        top.addWidget(self.btn_add_row)
        top.addWidget(self.btn_save)
        top.addWidget(self.btn_cancel)
        header_lay.addLayout(top)

        # ── لوحة السيناريوهات ──
        self._scenarios_panel = _BomScenariosPanel(self._conn)
        self._scenarios_panel.scenario_changed.connect(self.scenario_changed.emit)
        header_lay.addWidget(self._scenarios_panel)

        # ── صف عناوين الأعمدة ──
        headers = QWidget()
        self._headers_widget = headers
        hlay = QHBoxLayout(headers)
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(6)

        def _hdr(text, w=None, stretch=0):
            lbl = QLabel(text)
            if w:
                lbl.setFixedWidth(w)
            hlay.addWidget(lbl, stretch=stretch)

        _hdr(tr("type"),           150)
        _hdr(tr("element"),        stretch=3)
        _hdr(tr("row_or_variant"), 160)
        _hdr(tr("cost_per_unit"),  80)
        _hdr(tr("qty"),            80)
        _hdr(tr("waste_pct_col"),  90)
        _hdr("",                   32)
        header_lay.addWidget(headers)

        outer.addWidget(header_scroll)
        self._apply_theme()

    def _refresh_style(self, _=None):
        """يُطبق الـ stylesheet الحالي عند تغيير الثيم."""
        from ui.theme import _C
        if hasattr(self, "_header_inner"):
            self._header_inner.setStyleSheet(
                f"background:{_C['bg_surface']};"
            )
        if hasattr(self, "lbl_mode"):
            self.lbl_mode.setStyleSheet(
                f"font-weight:bold; color:{_C['accent']}; font-size:{FS_BASE}px;"
            )
        if hasattr(self, "inp_name"):
            self.inp_name.setStyleSheet(
                f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
                f"border-radius:4px; padding:2px 8px; color:{_C['text_primary']};"
            )
        if hasattr(self, "_headers_widget"):
            for lbl in self._headers_widget.findChildren(QLabel):
                lbl.setStyleSheet(
                    f"font-size:{FS_SM}px; font-weight:bold; color:{_C['text_sec']};"
                    f"border-bottom:1px solid {_C['border']}; padding-bottom:2px;"
                )

    # ── API خارجي ─────────────────────────────────────────

    @property
    def scenarios_panel(self) -> _BomScenariosPanel:
        return self._scenarios_panel

    @property
    def product_name(self) -> str:
        return self.inp_name.text().strip()

    @product_name.setter
    def product_name(self, value: str):
        self.inp_name.setText(value)

    @property
    def category_id(self):
        return self.cmb_category.get_category()

    def set_category(self, cat_id):
        self.cmb_category.set_category(cat_id)

    def set_mode(self, text: str):
        self.lbl_mode.setText(text)

    def enter_edit_mode(self, label: str = ""):
        if label:
            self.lbl_mode.setText(label)
        self.btn_cancel.setVisible(True)

    def exit_edit_mode(self, label: str = ""):
        self.lbl_mode.setText(label or tr("mode_label_wrap").format(content=tr("new_product")))
        self.btn_cancel.setVisible(False)

    def reset(self):
        self.inp_name.clear()
        self.cmb_category.setCurrentIndex(0)
        self._scenarios_panel.clear()
        self.exit_edit_mode()