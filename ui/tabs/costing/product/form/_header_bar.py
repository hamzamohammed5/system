"""
ui/tabs/costing/product/form/_header_bar.py
============================================
_FormHeaderBar — شريط الهيدر العلوي للفورم (اسم المنتج + التصنيف + الأزرار).

مسؤوليته:
  - حقل الاسم
  - combo التصنيف
  - أزرار (+ مكون، حفظ، إلغاء)
  - label الوضع
  - لوحة السيناريوهات
  - صف عناوين الأعمدة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel,
    QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal

from ui.helpers import success_button
from ui.widgets.shared.category_manager import CategoryCombo
from ui.widgets.shared.scrollable_form  import wrap_in_scroll
from ui.tabs.costing.shared.bom_scenarios_panel import _BomScenariosPanel


class _FormHeaderBar(QWidget):
    """
    الشريط العلوي للفورم:
      - label الوضع + حقل الاسم + التصنيف + الأزرار
      - لوحة السيناريوهات
      - صف عناوين الأعمدة

    Signals:
      add_row_clicked     — المستخدم ضغط "مكون+"
      save_clicked        — المستخدم ضغط "حفظ"
      cancel_clicked      — المستخدم ضغط "إلغاء"
      scenario_changed(int) — تغيير السيناريو الحالي
    """

    add_row_clicked   = pyqtSignal()
    save_clicked      = pyqtSignal()
    cancel_clicked    = pyqtSignal()
    scenario_changed  = pyqtSignal(int)

    def __init__(self, conn, scope: str, parent=None):
        super().__init__(parent)
        self._scope = scope
        self._conn  = conn
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── inner container جوا scroll ──
        header_inner = QWidget()
        header_inner.setMinimumWidth(400)
        header_inner.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)

        header_scroll = wrap_in_scroll(header_inner)
        header_scroll.setFixedHeight(150)

        header_lay = QVBoxLayout(header_inner)
        header_lay.setContentsMargins(12, 8, 12, 8)
        header_lay.setSpacing(6)

        # ── صف الأزرار والحقول ──
        top = QHBoxLayout()
        top.setSpacing(8)

        self.lbl_mode = QLabel("─── منتج جديد ───")
        self.lbl_mode.setStyleSheet(
            "font-weight:bold; color:#1565c0; font-size:12px;"
        )
        self.lbl_mode.setMinimumWidth(160)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم المنتج...")
        self.inp_name.setMinimumHeight(32)

        self.cmb_category = CategoryCombo(self._conn, scope=self._scope)
        self.cmb_category.setMinimumHeight(32)
        self.cmb_category.setFixedWidth(160)

        self.btn_add_row = QPushButton("+ مكون")
        self.btn_add_row.setMinimumHeight(32)
        self.btn_add_row.clicked.connect(self.add_row_clicked.emit)

        self.btn_save   = success_button("حفظ")
        self.btn_cancel = QPushButton("X الغاء")
        self.btn_save.setMinimumHeight(32)
        self.btn_cancel.setMinimumHeight(32)
        self.btn_save.clicked.connect(self.save_clicked.emit)
        self.btn_cancel.clicked.connect(self.cancel_clicked.emit)
        self.btn_cancel.setVisible(False)

        top.addWidget(self.lbl_mode)
        top.addWidget(self.inp_name, stretch=3)
        top.addSpacing(4)
        top.addWidget(QLabel("التصنيف:"))
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
        hlay = QHBoxLayout(headers)
        hlay.setContentsMargins(0, 0, 0, 0)
        hlay.setSpacing(6)

        def _hdr(text, w=None, stretch=0):
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "font-size:11px; font-weight:bold; color:#555;"
                "border-bottom:1px solid #ccc; padding-bottom:2px;"
            )
            if w:
                lbl.setFixedWidth(w)
            hlay.addWidget(lbl, stretch=stretch)

        _hdr("النوع",          150)
        _hdr("العنصر",         stretch=3)
        _hdr("الصف / Variant", 160)
        _hdr("تكلفة/قطعة",    80)
        _hdr("الكمية",         80)
        _hdr("الهادر %",       90)
        _hdr("",               32)
        header_lay.addWidget(headers)

        outer.addWidget(header_scroll)

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

    def exit_edit_mode(self, label: str = "منتج جديد"):
        self.lbl_mode.setText(label)
        self.btn_cancel.setVisible(False)

    def reset(self):
        self.inp_name.clear()
        self.cmb_category.setCurrentIndex(0)
        self._scenarios_panel.clear()
        self.exit_edit_mode()