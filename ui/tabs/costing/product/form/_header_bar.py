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

from ui.app_settings               import _C
from ui.widgets.core.i18n          import tr
from ui.widgets.components.button  import make_btn
from ui.widgets.combo.category     import CategoryCombo
from ui.widgets.theme.styles       import wrap_in_scroll
from ui.events                     import bus
from ui.tabs.costing.shared.bom_scenarios_panel import _BomScenariosPanel


class _FormHeaderBar(QWidget):
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
        self._build()
        bus.theme_changed.connect(self._apply_theme)

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header_inner = QWidget()
        header_inner.setMinimumWidth(400)
        header_inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        self._header_inner = header_inner

        header_scroll = wrap_in_scroll(header_inner)
        header_scroll.setFixedHeight(150)

        header_lay = QVBoxLayout(header_inner)
        header_lay.setContentsMargins(12, 8, 12, 8)
        header_lay.setSpacing(6)

        # ── صف الأزرار والحقول ──
        top = QHBoxLayout()
        top.setSpacing(8)

        self.lbl_mode = QLabel(f"─── {tr('new_product')} ───")
        self.lbl_mode.setMinimumWidth(160)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("product_name_placeholder"))
        self.inp_name.setMinimumHeight(32)

        self.cmb_category = CategoryCombo(self._conn, scope=self._scope)
        self.cmb_category.setMinimumHeight(32)
        self.cmb_category.setFixedWidth(160)

        self.btn_add_row = QPushButton(f"+ {tr('add_component')}")
        self.btn_add_row.setMinimumHeight(32)
        self.btn_add_row.clicked.connect(self.add_row_clicked.emit)

        self.btn_save   = make_btn(tr("save"), style="success")
        self.btn_cancel = QPushButton(f"✖ {tr('cancel')}")
        self.btn_save.setMinimumHeight(32)
        self.btn_cancel.setMinimumHeight(32)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)
        self.btn_cancel.setVisible(False)

        top.addWidget(self.lbl_mode)
        top.addWidget(self.inp_name, stretch=3)
        top.addSpacing(4)
        top.addWidget(QLabel(f"{tr('category')}:"))
        top.addWidget(self.cmb_category)
        top.addSpacing(8)
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

    def _apply_theme(self, _=None):
        """يُطبق الـ stylesheet الحالي عند تغيير الثيم."""
        if hasattr(self, "_header_inner"):
            self._header_inner.setStyleSheet(
                f"background:{_C['bg_surface']};"
            )
        if hasattr(self, "lbl_mode"):
            self.lbl_mode.setStyleSheet(
                f"font-weight:bold; color:{_C['accent']}; font-size:12px;"
            )
        if hasattr(self, "inp_name"):
            self.inp_name.setStyleSheet(
                f"background:{_C['bg_input']}; border:1px solid {_C['border']};"
                f"border-radius:4px; padding:2px 8px; color:{_C['text_primary']};"
            )
        if hasattr(self, "_headers_widget"):
            for lbl in self._headers_widget.findChildren(QLabel):
                lbl.setStyleSheet(
                    f"font-size:11px; font-weight:bold; color:{_C['text_sec']};"
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
        self.lbl_mode.setText(label or tr("new_product"))
        self.btn_cancel.setVisible(False)

    def reset(self):
        self.inp_name.clear()
        self.cmb_category.setCurrentIndex(0)
        self._scenarios_panel.clear()
        self.exit_edit_mode()