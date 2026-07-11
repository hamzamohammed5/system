"""
ui/tabs/costing/shared/bulk_replace/bulk_replace_helpers.py
====================================
ProductRow — عنصر واجهة (widget) لنافذة الاستبدال الشامل.

[إصلاح هيكلي] هذا الملف كان يحتوي أيضاً على منطق أعمال واستعلامات DB
(get_element_name / fetch_candidates / fetch_affected_products) —
وهو كسر للهيكلة لأن ui/ يجب أن يستدعي services/ فقط، لا db/ مباشرة،
ولا يجوز أن يُعرّف منطق أعمال يُستدعى لاحقاً من services/ (دائرة استيراد).

الدوال الثلاث انتقلت إلى:
    services/costing/bulk_replace_service.py
واللي بيستخدمها الآن هو BulkReplaceDialog عبر:
    from services.costing.bulk_replace_service import BulkReplaceService
    svc = BulkReplaceService(conn)
    svc.get_element_name(...) / svc.fetch_candidates(...) / svc.fetch_affected_products(...)
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QCheckBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.widgets.core.i18n       import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    PRODUCT_ROW_MARGIN_H, PRODUCT_ROW_MARGIN_V, PRODUCT_ROW_SPACING,
    PRODUCT_ROW_CHK_W, PRODUCT_ROW_TYPE_ICON_W,
    PRODUCT_ROW_SP_W, PRODUCT_ROW_SP_MIN_H, PRODUCT_ROW_RADIUS,
    SPACING_MD,
)
from ui.font import FS_BASE, FS_SM, FS_XS


# ══════════════════════════════════════════════════════════
# ProductRow — صف منتج واحد في اللوحة
# ══════════════════════════════════════════════════════════

class ProductRow(QFrame, WidgetMixin):
    """
    صف يعرض معلومات منتج واحد مع:
      - checkbox للاختيار
      - حقل الكمية الحالية (قابل للتعديل)
      - بيانات المنتج (اسم، نوع، تصنيف، تكلفة)
    """

    def __init__(self, product: dict, parent=None):
        super().__init__(parent)
        self._product = product
        self._init_widget_mixin(data=False)
        self._build()

    def _build(self):
        self.setFrameShape(QFrame.StyledPanel)
        self._apply_style(checked=True)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(PRODUCT_ROW_MARGIN_H, PRODUCT_ROW_MARGIN_V,
                               PRODUCT_ROW_MARGIN_H, PRODUCT_ROW_MARGIN_V)
        lay.setSpacing(PRODUCT_ROW_SPACING)

        # ── checkbox ──
        self.chk = QCheckBox()
        self.chk.setChecked(True)
        self.chk.setFixedWidth(PRODUCT_ROW_CHK_W)
        self.chk.toggled.connect(self._on_toggle)
        lay.addWidget(self.chk)

        # ── نوع المنتج ──
        type_icon = "🔧" if self._product["type"] == "semi" else "🏭"
        lbl_type = QLabel(type_icon)
        lbl_type.setFixedWidth(PRODUCT_ROW_TYPE_ICON_W)
        lbl_type.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl_type)

        # ── الاسم والتصنيف ──
        from PyQt5.QtWidgets import QVBoxLayout as VL
        info = VL()
        info.setSpacing(SPACING_MD // 4)
        self.lbl_name = QLabel(self._product["name"])
        self.lbl_name.setStyleSheet(
            f"font-weight:bold; font-size:{FS_BASE}px; color:{_C['text_primary']};"
        )
        lbl_cat = QLabel(
            f"🏷 {self._product['category_name']}  "
            f"│  💰 {self._product['cost']:.2f} {tr('currency_abbr')}"
        )
        lbl_cat.setStyleSheet(f"color:{_C['text_sec']}; font-size:{FS_XS}px;")
        info.addWidget(self.lbl_name)
        info.addWidget(lbl_cat)
        lay.addLayout(info, stretch=1)

        # ── الكمية الحالية ──
        lay.addWidget(QLabel(f"{tr('qty')}:"))
        self.sp_qty = QDoubleSpinBox()
        self.sp_qty.setRange(0.0001, 999999)
        self.sp_qty.setDecimals(4)
        self.sp_qty.setValue(self._product["qty"])
        self.sp_qty.setFixedWidth(PRODUCT_ROW_SP_W)
        self.sp_qty.setMinimumHeight(PRODUCT_ROW_SP_MIN_H)
        self.sp_qty.setToolTip(
            f"{tr('qty')} — {tr('element')}"
        )
        lay.addWidget(self.sp_qty)

    def _refresh_style(self, *_):
        checked = self.chk.isChecked() if hasattr(self, 'chk') else True
        self._apply_style(checked=checked)
        if hasattr(self, 'lbl_name'):
            color = _C['text_primary'] if checked else _C['text_disabled']
            self.lbl_name.setStyleSheet(
                f"font-weight:bold; font-size:{FS_BASE}px; color:{color};"
            )

    def _apply_style(self, checked: bool):
        if checked:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_C['bg_input']};
                    border: 1px solid {_C['border']};
                    border-radius: {PRODUCT_ROW_RADIUS}px;
                    margin: 1px 0;
                }}
                QFrame:hover {{
                    border-color: {_C['border_focus']};
                    background: {_C['accent_light']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_C['bg_surface']};
                    border: 1px solid {_C['border']};
                    border-radius: {PRODUCT_ROW_RADIUS}px;
                    margin: 1px 0;
                }}
            """)

    def _on_toggle(self, checked: bool):
        self.sp_qty.setEnabled(checked)
        self._apply_style(checked)
        if hasattr(self, 'lbl_name'):
            color = _C['text_primary'] if checked else _C['text_disabled']
            self.lbl_name.setStyleSheet(
                f"font-weight:bold; font-size:{FS_BASE}px; color:{color};"
            )

    @property
    def is_selected(self) -> bool:
        return self.chk.isChecked()

    @property
    def product_id(self) -> int:
        return self._product["id"]

    @property
    def new_qty(self) -> float:
        return self.sp_qty.value()

    def set_selected(self, val: bool):
        self.chk.setChecked(val)
