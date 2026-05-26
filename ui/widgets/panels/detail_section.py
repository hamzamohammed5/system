"""
ui/widgets/panels/detail_section.py
===============================================
DetailSection  — قسم تفاصيل موحد (عنوان: قيمة) في grid.
TwoColDetails  — عرض في عمودين.
make_detail_row — دالة سريعة.
"""
from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QGridLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt

from ui.app_settings import _C, fs
from ui.app_settings import get_font_size
from ..components.headers         import SectionHeader


class DetailSection(QFrame):
    """
    قسم تفاصيل موحد — يعرض أزواج (عنوان: قيمة) في grid منظم.

    الاستخدام:
        sec = DetailSection("بيانات المنتج", cols=2)
        sec.add_row("الاسم:", "منتج A")
        sec.add_row("الكود:", "P001", color="#1565c0")
        lbl = sec.add_row("الحالة:", "نشط")
        lbl.setText("موقوف")          # تحديث مباشر
        layout.addWidget(sec)
    """

    def __init__(self, title: str = "",
                 cols: int = 1,
                 compact: bool = False,
                 parent=None):
        super().__init__(parent)
        self._cols    = max(1, cols)
        self._compact = compact
        self._rows: list[tuple[QLabel, QLabel]] = []
        self._count   = 0
        self._build(title)

    def _build(self, title: str):
        self.setStyleSheet(f"""
            QFrame {{
                background:{_C['bg_surface']};
                border:1px solid {_C['border']};
                border-radius:10px;
            }}
        """)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 12)
        root.setSpacing(0)

        if title:
            hdr = SectionHeader(title)
            hdr.setContentsMargins(12, 0, 12, 0)
            root.addWidget(hdr)

        self._grid = QGridLayout()
        v_pad      = 4 if self._compact else 6
        self._grid.setContentsMargins(12, v_pad, 12, v_pad)
        self._grid.setHorizontalSpacing(16)
        self._grid.setVerticalSpacing(6 if self._compact else 10)

        for c in range(self._cols):
            self._grid.setColumnStretch(c * 2, 0)      # label
            self._grid.setColumnStretch(c * 2 + 1, 1)  # value

        root.addLayout(self._grid)

    # ── إضافة صفوف ────────────────────────────────────────

    def add_row(self, label: str, value: str = "─",
                color: str = None, bold: bool = False,
                icon: str = "") -> QLabel:
        base = get_font_size()

        lbl_key = QLabel(label)
        lbl_key.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none; font-weight:500;"
        )
        lbl_key.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lbl_key.setMinimumWidth(80)

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
        sep = _F()
        sep.setFrameShape(_F.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_C['border']}; border:none;")
        row = (self._count + self._cols - 1) // self._cols
        self._grid.addWidget(sep, row, 0, 1, self._cols * 2)

    def set_data(self, data: dict):
        existing = {lk.text(): lv for lk, lv in self._rows}
        for label, value in data.items():
            if label in existing:
                existing[label].setText(str(value) if value else "─")
            else:
                self.add_row(label, str(value) if value else "─")

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
        for _, lbl_val in self._rows:
            lbl_val.setText("─")


# ══════════════════════════════════════════════════════════
# make_detail_row
# ══════════════════════════════════════════════════════════

def make_detail_row(label: str, value: str = "─",
                    color: str = None,
                    bold: bool = False) -> "tuple[QLabel, QLabel]":
    """يبني صف تفاصيل واحد خارج DetailSection."""
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

class TwoColDetails(QWidget):
    """
    عرض تفاصيل في عمودين.

    الاستخدام:
        details = TwoColDetails()
        details.add("الاسم:", "منتج A")
        details.add("الكود:", "P001", color="#1565c0")
        layout.addWidget(details)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background:transparent;")
        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(24)
        self._grid.setVerticalSpacing(8)
        self._grid.setColumnStretch(1, 1)
        self._grid.setColumnStretch(3, 1)
        self._count = 0
        self._vals: list[QLabel] = []

    def add(self, label: str, value: str = "─",
            color: str = None, bold: bool = False) -> QLabel:
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
        col = (self._count % 2) * 2   # 0 أو 2

        self._grid.addWidget(lbl_key, row, col,     Qt.AlignRight)
        self._grid.addWidget(lbl_val, row, col + 1, Qt.AlignRight)

        self._vals.append(lbl_val)
        self._count += 1
        return lbl_val

    def reset(self):
        for lbl in self._vals:
            lbl.setText("─")