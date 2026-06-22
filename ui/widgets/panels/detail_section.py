"""
ui/widgets/panels/detail_section.py
===============================================
DetailSection  — قسم تفاصيل موحد (عنوان: قيمة) في grid.
TwoColDetails  — عرض في عمودين.
make_detail_row — دالة سريعة.

[إصلاح 2.3] from ..components.headers import SectionHeader
         → from ..components.headers_page import SectionHeader
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QGridLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.font  import fs, get_font_size
from ui.theme import _C
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    DETAIL_SECTION_RADIUS, DETAIL_SECTION_MARGIN_B, DETAIL_SECTION_HDR_MARGIN_H,
    DETAIL_GRID_MARGIN_H, DETAIL_GRID_H_SPACING,
    DETAIL_GRID_V_SPACING, DETAIL_GRID_V_SPACING_C,
    DETAIL_GRID_PAD_COMPACT, DETAIL_GRID_PAD_NORMAL,
    DETAIL_LABEL_MIN_W, TWO_COL_H_SPACING, TWO_COL_V_SPACING,
)
from ..components.headers_page import SectionHeader   # [إصلاح 2.3]


class DetailSection(QFrame, WidgetMixin):
    """قسم تفاصيل موحد — يعرض أزواج (عنوان: قيمة) في grid منظم."""

    def __init__(self, title: str = "",
                 cols: int = 1,
                 compact: bool = False,
                 parent=None):
        super().__init__(parent)
        self._cols    = max(1, cols)
        self._compact = compact
        self._rows: list[tuple[QLabel, QLabel]] = []
        self._count   = 0
        self._init_widget_mixin(theme=True, font=True, lang=False, data=False)
        self._build(title)

    def _refresh_style(self, *_):
        self.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface']};
                border:1px solid {_C['border']};
                border-radius:{DETAIL_SECTION_RADIUS}px;
            }}
        """)

    def _build(self, title: str):
        self._refresh_style()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, DETAIL_SECTION_MARGIN_B)
        root.setSpacing(0)

        if title:
            hdr = SectionHeader(title)
            hdr.setContentsMargins(DETAIL_SECTION_HDR_MARGIN_H, 0,
                                   DETAIL_SECTION_HDR_MARGIN_H, 0)
            root.addWidget(hdr)

        self._grid = QGridLayout()
        v_pad      = DETAIL_GRID_PAD_COMPACT if self._compact else DETAIL_GRID_PAD_NORMAL
        self._grid.setContentsMargins(DETAIL_GRID_MARGIN_H, v_pad,
                                      DETAIL_GRID_MARGIN_H, v_pad)
        self._grid.setHorizontalSpacing(DETAIL_GRID_H_SPACING)
        self._grid.setVerticalSpacing(DETAIL_GRID_V_SPACING_C if self._compact
                                      else DETAIL_GRID_V_SPACING)

        for c in range(self._cols):
            self._grid.setColumnStretch(c * 2, 0)
            self._grid.setColumnStretch(c * 2 + 1, 1)

        root.addLayout(self._grid)

    # ── إضافة صفوف ────────────────────────────────────────

    def add_row(self, label: str, value: str = None,
                color: str = None, bold: bool = False,
                icon: str = "") -> QLabel:
        from ui.widgets.core.i18n import tr
        if value is None:
            value = tr('amount_dash_placeholder')
        base = get_font_size()

        lbl_key = QLabel(label)
        lbl_key.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none; font-weight:500;"
        )
        lbl_key.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lbl_key.setMinimumWidth(DETAIL_LABEL_MIN_W)

        display = f"{icon} {value}" if icon else value
        lbl_val = QLabel(display)
        lbl_val.setWordWrap(True)
        val_color = color or _C['text_primary']
        weight    = "bold" if bold else "500"
        lbl_val.setStyleSheet(
            f"color:{val_color}; font-size:{fs(base,0)}pt; font-weight:{weight};"
            "background:transparent; border:none;"
        )
        lbl_val.setAlignment(Qt.AlignRight | Qt.AlignTop)

        row   = self._count // self._cols
        col   = self._count % self._cols
        g_col = col * 2

        self._grid.addWidget(lbl_key, row, g_col,     Qt.AlignRight | Qt.AlignTop)
        self._grid.addWidget(lbl_val, row, g_col + 1, Qt.AlignRight | Qt.AlignTop)

        self._rows.append((lbl_key, lbl_val))
        self._count += 1
        return lbl_val

    def add_separator(self):
        from PyQt5.QtWidgets import QFrame as _F
        from ui.constants import SEPARATOR_LINE_H
        sep = _F()
        sep.setFrameShape(_F.HLine)
        sep.setFixedHeight(SEPARATOR_LINE_H)
        sep.setStyleSheet(f"background:{_C['border']}; border:none;")
        row = (self._count + self._cols - 1) // self._cols
        self._grid.addWidget(sep, row, 0, 1, self._cols * 2)

    def set_data(self, data: dict,
                 clear_missing: bool = False) -> "dict[str, QLabel]":
        result   = {}
        existing = {lk.text(): (lk, lv) for lk, lv in self._rows}

        if clear_missing:
            new_keys = set(data.keys())
            for key, (lk, lv) in existing.items():
                if key not in new_keys:
                    lk.setVisible(False)
                    lv.setVisible(False)

        for label, value in data.items():
            from ui.widgets.core.i18n import tr
            str_val = str(value) if value is not None else tr('amount_dash_placeholder')
            if label in existing:
                lk, lv = existing[label]
                lv.setText(str_val)
                lk.setVisible(True)
                lv.setVisible(True)
                result[label] = lv
            else:
                lbl = self.add_row(label, str_val)
                result[label] = lbl

        return result

    def clear_rows(self):
        for lbl_key, lbl_val in self._rows:
            self._grid.removeWidget(lbl_key)
            self._grid.removeWidget(lbl_val)
            lbl_key.deleteLater()
            lbl_val.deleteLater()
        self._rows.clear()
        self._count = 0

    def update_value(self, index: int, value: str, color: str = None):
        if 0 <= index < len(self._rows):
            _, lbl_val = self._rows[index]
            lbl_val.setText(value)
            if color:
                base = get_font_size()
                lbl_val.setStyleSheet(
                    f"color:{color}; font-size:{fs(base,0)}pt; font-weight:500;"
                    "background:transparent; border:none;"
                )

    def value_label(self, index: int) -> "QLabel | None":
        if 0 <= index < len(self._rows):
            return self._rows[index][1]
        return None

    def reset_values(self):
        from ui.widgets.core.i18n import tr
        _dash = tr('amount_dash_placeholder')
        for _, lbl_val in self._rows:
            lbl_val.setText(_dash)

    def show_all_rows(self):
        for lbl_key, lbl_val in self._rows:
            lbl_key.setVisible(True)
            lbl_val.setVisible(True)


# ══════════════════════════════════════════════════════════
# make_detail_row
# ══════════════════════════════════════════════════════════

def make_detail_row(label: str, value: str = None,
                    color: str = None,
                    bold: bool = False) -> "tuple[QLabel, QLabel]":
    from ui.widgets.core.i18n import tr
    if value is None:
        value = tr('amount_dash_placeholder')
    base = get_font_size()

    lbl_key = QLabel(label)
    lbl_key.setStyleSheet(
        f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
        "background:transparent; border:none; font-weight:500;"
    )
    lbl_key.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    lbl_val = QLabel(value)
    val_color = color or _C['text_primary']
    weight    = "bold" if bold else "500"
    lbl_val.setStyleSheet(
        f"color:{val_color}; font-size:{fs(base,0)}pt; font-weight:{weight};"
        "background:transparent; border:none;"
    )
    lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    lbl_val.setWordWrap(True)

    return lbl_key, lbl_val


# ══════════════════════════════════════════════════════════
# TwoColDetails
# ══════════════════════════════════════════════════════════

class TwoColDetails(QWidget, WidgetMixin):
    """عرض تفاصيل في عمودين."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(TWO_COL_H_SPACING)
        self._grid.setVerticalSpacing(TWO_COL_V_SPACING)
        self._grid.setColumnStretch(1, 1)
        self._grid.setColumnStretch(3, 1)
        self._count = 0
        self._vals: list[QLabel] = []
        self._init_widget_mixin(theme=True, font=True, lang=False, data=False)

    def add(self, label: str, value: str = None,
            color: str = None, bold: bool = False) -> QLabel:
        from ui.widgets.core.i18n import tr
        if value is None:
            value = tr('amount_dash_placeholder')
        base = get_font_size()

        lbl_key = QLabel(label)
        lbl_key.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none;"
        )
        lbl_key.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        lbl_val = QLabel(value)
        c = color or _C['text_primary']
        w = "bold" if bold else "500"
        lbl_val.setStyleSheet(
            f"color:{c}; font-size:{fs(base,0)}pt; font-weight:{w};"
            "background:transparent; border:none;"
        )
        lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_val.setWordWrap(True)

        row = self._count // 2
        col = (self._count % 2) * 2

        self._grid.addWidget(lbl_key, row, col,     Qt.AlignRight)
        self._grid.addWidget(lbl_val, row, col + 1, Qt.AlignRight)

        self._vals.append(lbl_val)
        self._count += 1
        return lbl_val

    def reset(self):
        from ui.widgets.core.i18n import tr
        _dash = tr('amount_dash_placeholder')
        for lbl in self._vals:
            lbl.setText(_dash)