"""
ui/widgets/shared/panles_helper/divider_utils.py
=================================================
دوال مساعدة للفواصل الموحدة.

كانت كل ملف بيعمل QFrame فاصل بنفس الطريقة — ده تكرار واضح.
هذا الملف يوحدهم في مكان واحد.

مُصدَّر في panels.py ومن theme.py مباشرة.

الاستخدام:
    from ui.widgets.shared.panles_helper.divider_utils import (
        make_h_divider, make_v_divider
    )
    layout.addWidget(make_h_divider())
    toolbar_lay.addWidget(make_v_divider())

ملاحظة: make_divider() و make_vline_sep() موجودان في theme.py أيضاً
كـ aliases — استخدم أيٍّ منهما.
"""

from PyQt5.QtWidgets import QFrame
from ui.app_settings import _C


def make_h_divider(color: str = None, height: int = 1) -> QFrame:
    """
    فاصل أفقي موحد (HLine).

    الاستخدام:
        root.addWidget(make_h_divider())
        root.addWidget(make_h_divider(color="#e0e0e0"))
    """
    c = color or _C.get('border', '#e0e0e0')
    div = QFrame()
    div.setFrameShape(QFrame.HLine)
    div.setFixedHeight(height)
    div.setStyleSheet(f"background:{c}; border:none;")
    return div


# alias للتوافق مع theme.make_divider
make_divider = make_h_divider


def make_v_divider(color: str = None, width: int = 1,
                   margin_v: int = 4) -> QFrame:
    """
    فاصل عمودي موحد (VLine) — للـ toolbars والـ rows.

    الاستخدام:
        toolbar_lay.addWidget(make_v_divider())
    """
    c = color or _C.get('border_med', '#bdbdbd')
    sep = QFrame()
    sep.setFrameShape(QFrame.VLine)
    sep.setFixedWidth(width)
    sep.setStyleSheet(
        f"background:{c}; border:none; margin:{margin_v}px 2px;"
    )
    return sep


# alias للتوافق مع theme.make_vline_sep
make_vline_sep = make_v_divider