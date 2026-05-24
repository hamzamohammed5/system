"""
ui/widgets/shared/panles_helper/detail_section.py
==================================================
DetailSection — قسم تفاصيل موحد يعرض أزواج (عنوان: قيمة) بشكل منظم.

يحل التكرار في عشرات الملفات اللي بتبني صفوف تفاصيل يدوياً
بـ QLabel + QLabel في كل مرة.

المتوفر:
  DetailSection   — QFrame لعرض تفاصيل منظمة
  DetailRow       — صف تفاصيل واحد (عنوان + قيمة)
  make_detail_row — دالة سريعة لبناء صف تفاصيل

الاستخدام:
    sec = DetailSection("بيانات المنتج")
    sec.add_row("الاسم:", "منتج A")
    sec.add_row("الكود:", "P001", color="#1565c0")
    sec.add_row("التاريخ:", "2025-01-15")
    layout.addWidget(sec)

    # تحديث قيمة:
    lbl = sec.add_row("الحالة:", "نشط")
    lbl.setText("موقوف")

    # أو باستخدام dict:
    sec.set_data({
        "الاسم:":   "منتج A",
        "الكود:":   "P001",
        "التاريخ:": "2025-01-15",
    })
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget,
    QGridLayout, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from .colors_and_base import _base
from .section_header import SectionHeader


class DetailSection(QFrame):
    """
    قسم تفاصيل موحد — يعرض أزواج (عنوان: قيمة) في grid منظم.

    المعاملات:
        title    : عنوان القسم (يظهر في SectionHeader)
        cols     : عدد الأعمدة (1 = عمود واحد، 2 = عمودان)
        compact  : تباعد أقل بين الصفوف
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
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: 10px;
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
        v_pad = 4 if self._compact else 6
        h_pad = 12
        self._grid.setContentsMargins(h_pad, v_pad, h_pad, v_pad)
        self._grid.setHorizontalSpacing(16)
        self._grid.setVerticalSpacing(6 if self._compact else 10)

        # أعمدة الـ labels التسميات بحجم ثابت، القيم بحجم متمدد
        for c in range(self._cols):
            self._grid.setColumnStretch(c * 2, 0)      # label
            self._grid.setColumnStretch(c * 2 + 1, 1)  # value

        root.addLayout(self._grid)

    # ── إضافة صفوف ────────────────────────────────────────

    def add_row(self, label: str, value: str = "─",
                color: str = None,
                bold: bool = False,
                icon: str = "") -> QLabel:
        """
        يضيف صف تفاصيل ويرجع الـ QLabel للقيمة للتحديث لاحقاً.

        label : عنوان الحقل
        value : قيمة الحقل
        color : لون القيمة (None = افتراضي)
        bold  : هل القيمة بخط عريض
        icon  : أيقونة قبل القيمة
        """
        base = _base()

        # Label العنوان
        lbl_key = QLabel(label)
        lbl_key.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
            "background:transparent; border:none; font-weight:500;"
        )
        lbl_key.setAlignment(Qt.AlignRight | Qt.AlignTop)
        lbl_key.setMinimumWidth(80)

        # Label القيمة
        display = f"{icon} {value}" if icon else value
        lbl_val = QLabel(display)
        lbl_val.setWordWrap(True)
        val_color = color or _C['text_primary']
        weight = "bold" if bold else "500"
        lbl_val.setStyleSheet(
            f"color:{val_color}; font-size:{fs(base,0)}pt; font-weight:{weight};"
            "background:transparent; border:none;"
        )
        lbl_val.setAlignment(Qt.AlignRight | Qt.AlignTop)

        # حساب موقع الصف والعمود
        row   = self._count // self._cols
        col   = self._count % self._cols
        g_col = col * 2  # كل عمود يأخذ خانتين (label + value)

        self._grid.addWidget(lbl_key, row, g_col,     Qt.AlignRight | Qt.AlignTop)
        self._grid.addWidget(lbl_val, row, g_col + 1, Qt.AlignRight | Qt.AlignTop)

        self._rows.append((lbl_key, lbl_val))
        self._count += 1
        return lbl_val

    def add_separator(self):
        """يضيف فاصل أفقي."""
        from PyQt5.QtWidgets import QFrame as _F
        sep = _F()
        sep.setFrameShape(_F.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_C['border']}; border:none;")
        row = (self._count + self._cols - 1) // self._cols
        self._grid.addWidget(sep, row, 0, 1, self._cols * 2)

    def set_data(self, data: dict):
        """
        يضبط كل الصفوف من dict.
        {label: value, ...}

        لو الصف موجود بالفعل → يحدّث القيمة فقط.
        لو مش موجود → يضيف صف جديد.
        """
        existing_labels = {
            lbl_key.text(): lbl_val
            for lbl_key, lbl_val in self._rows
        }
        for label, value in data.items():
            if label in existing_labels:
                existing_labels[label].setText(str(value) if value else "─")
            else:
                self.add_row(label, str(value) if value else "─")

    def clear_rows(self):
        """يمسح كل الصفوف."""
        for lbl_key, lbl_val in self._rows:
            self._grid.removeWidget(lbl_key)
            self._grid.removeWidget(lbl_val)
            lbl_key.deleteLater()
            lbl_val.deleteLater()
        self._rows.clear()
        self._count = 0

    def update_value(self, index: int, value: str, color: str = None):
        """يحدّث قيمة صف بالـ index."""
        if 0 <= index < len(self._rows):
            _, lbl_val = self._rows[index]
            lbl_val.setText(value)
            if color:
                base = _base()
                lbl_val.setStyleSheet(
                    f"color:{color}; font-size:{fs(base,0)}pt; font-weight:500;"
                    "background:transparent; border:none;"
                )

    def value_label(self, index: int) -> QLabel | None:
        """يرجع QLabel القيمة للتحديث المباشر."""
        if 0 <= index < len(self._rows):
            return self._rows[index][1]
        return None

    def reset_values(self):
        """يعيد كل القيم لـ '─'."""
        for _, lbl_val in self._rows:
            lbl_val.setText("─")


# ══════════════════════════════════════════════════════════
# دوال مساعدة سريعة
# ══════════════════════════════════════════════════════════

def make_detail_row(label: str, value: str = "─",
                    color: str = None,
                    bold: bool = False) -> tuple[QLabel, QLabel]:
    """
    يبني صف تفاصيل واحد خارج DetailSection.
    يرجع (label_widget, value_widget).

    الاستخدام:
        lbl_key, lbl_val = make_detail_row("الاسم:", "منتج A")
        form_layout.addRow(lbl_key, lbl_val)
    """
    base = _base()

    lbl_key = QLabel(label)
    lbl_key.setStyleSheet(
        f"color:{_C['text_muted']}; font-size:{fs(base,-1)}pt;"
        "background:transparent; border:none; font-weight:500;"
    )
    lbl_key.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    lbl_val = QLabel(value)
    val_color = color or _C['text_primary']
    weight = "bold" if bold else "500"
    lbl_val.setStyleSheet(
        f"color:{val_color}; font-size:{fs(base,0)}pt; font-weight:{weight};"
        "background:transparent; border:none;"
    )
    lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    lbl_val.setWordWrap(True)

    return lbl_key, lbl_val


class TwoColDetails(QWidget):
    """
    عرض تفاصيل في عمودين (مثل بطاقات المعلومات في صفحة التفاصيل).

    الاستخدام:
        details = TwoColDetails()
        details.add("الاسم:", "منتج A")
        details.add("الكود:", "P001", color="#1565c0")
        details.add("التاريخ:", "2025-01-15")
        details.add("الحالة:", "نشط", bold=True)
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
        """يضيف عنصر ويرجع label القيمة."""
        base = _base()
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
        col = (self._count % 2) * 2  # 0 أو 2

        self._grid.addWidget(lbl_key, row, col,     Qt.AlignRight)
        self._grid.addWidget(lbl_val, row, col + 1, Qt.AlignRight)

        self._vals.append(lbl_val)
        self._count += 1
        return lbl_val

    def reset(self):
        """يعيد كل القيم لـ '─'."""
        for lbl in self._vals:
            lbl.setText("─")