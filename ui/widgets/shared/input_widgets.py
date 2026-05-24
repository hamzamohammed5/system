"""
ui/widgets/shared/input_widgets.py
====================================
مكونات Input موحدة — تكمل form_utils.py للأنماط المتكررة.

الناقص في الـ widgets الحالية:
  - SearchLineEdit     : QLineEdit بحث موحد مع أيقونة ومسح
  - LabeledInput       : حقل مع label في سطر أفقي
  - RequiredLineEdit   : QLineEdit مع تحقق من الفراغ
  - AmountSpinBox      : QDoubleSpinBox للمبالغ المالية بستايل موحد
  - DateField          : QDateEdit موحد
  - ComboWithLabel     : QComboBox مع label

الاستخدام:
    from ui.widgets.shared.input_widgets import (
        SearchLineEdit, LabeledInput, AmountSpinBox, DateField
    )

    search = SearchLineEdit("🔍 بحث في المنتجات...")
    search.text_changed.connect(self._filter)

    amount = AmountSpinBox(max_=999999)
    form.addRow("المبلغ:", amount)

    date = DateField()
    form.addRow("التاريخ:", date)
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLineEdit, QLabel, QPushButton,
    QDoubleSpinBox, QSpinBox, QDateEdit,
    QComboBox, QSizePolicy,
)
from PyQt5.QtCore import Qt, QDate, QTimer, pyqtSignal
from PyQt5.QtGui  import QFont

from ui.app_settings import _C, fs
from ui.widgets.shared.panles_helper.colors_and_base import _base


# ══════════════════════════════════════════════════════════
# SearchLineEdit — حقل بحث موحد
# ══════════════════════════════════════════════════════════

class SearchLineEdit(QWidget):
    """
    حقل بحث موحد مع:
      - أيقونة بحث
      - زر مسح (يظهر عند الكتابة)
      - delay قبل إطلاق الـ signal

    Signals:
        text_changed(str) — يُطلق بعد توقف الكتابة

    الاستخدام:
        s = SearchLineEdit("🔍 ابحث في المنتجات...")
        s.text_changed.connect(self._on_search)
        layout.addWidget(s)
        query = s.text()
    """

    text_changed = pyqtSignal(str)

    def __init__(self, placeholder: str = "🔍  بحث...",
                 delay_ms: int = 250,
                 height: int = 34,
                 parent=None):
        super().__init__(parent)
        self._delay = delay_ms
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._emit)
        self._build(placeholder, height)

    def _build(self, placeholder: str, height: int):
        base = _base()
        lay  = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self._inp = QLineEdit()
        self._inp.setPlaceholderText(placeholder)
        self._inp.setFixedHeight(height)
        self._inp.setClearButtonEnabled(True)
        self._inp.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self._inp.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 0 10px;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {_C['accent']};
                background: white;
            }}
        """)
        self._inp.textChanged.connect(self._on_change)
        lay.addWidget(self._inp)

    def _on_change(self):
        if self._delay > 0:
            self._timer.start()
        else:
            self._emit()

    def _emit(self):
        self.text_changed.emit(self._inp.text().strip().lower())

    def text(self) -> str:
        return self._inp.text().strip().lower()

    def clear(self):
        self._inp.clear()

    def set_placeholder(self, text: str):
        self._inp.setPlaceholderText(text)

    @property
    def line_edit(self) -> QLineEdit:
        return self._inp


# ══════════════════════════════════════════════════════════
# AmountSpinBox — QDoubleSpinBox للمبالغ المالية
# ══════════════════════════════════════════════════════════

class AmountSpinBox(QDoubleSpinBox):
    """
    QDoubleSpinBox للمبالغ المالية بستايل موحد.

    يحل محل _spin() و spin_field() في الأماكن اللي محتاجة
    ستايل خاص بالمبالغ (أخضر عند موجب، وخلفية مميزة).

    الاستخدام:
        sp = AmountSpinBox(max_=999999)
        form.addRow("المبلغ:", sp)
        amount = sp.value()
    """

    def __init__(self, max_: float = 999_999_999,
                 dec: int = 2,
                 min_: float = 0,
                 height: int = 32,
                 currency: str = "",
                 parent=None):
        super().__init__(parent)
        self.setRange(min_, max_)
        self.setDecimals(dec)
        self.setMinimumHeight(height)
        if currency:
            self.setSuffix(f"  {currency}")
        self._apply_style()
        self.valueChanged.connect(self._on_value_changed)

    def _apply_style(self, positive: bool = False):
        base = _base()
        if positive:
            bg, border, color = "#f0fdf4", "#86efac", "#15803d"
        else:
            bg = _C['bg_input']
            border = _C['border_med']
            color = _C['text_primary']

        self.setStyleSheet(f"""
            QDoubleSpinBox {{
                background: {bg};
                border: 1.5px solid {border};
                border-radius: 6px;
                padding: 0 8px;
                font-size: {fs(base, 0)}pt;
                color: {color};
                font-weight: {'bold' if positive else 'normal'};
            }}
            QDoubleSpinBox:focus {{
                border-color: {_C['accent']};
                background: white;
            }}
            QDoubleSpinBox:disabled {{
                background: {_C['bg_surface_2']};
                color: {_C['text_disabled']};
            }}
        """)

    def _on_value_changed(self, val: float):
        self._apply_style(positive=val > 0)


# ══════════════════════════════════════════════════════════
# DateField — QDateEdit موحد
# ══════════════════════════════════════════════════════════

class DateField(QDateEdit):
    """
    QDateEdit موحد مع:
      - popup تقويم
      - تنسيق yyyy-MM-dd
      - ستايل موحد

    الاستخدام:
        dt = DateField()
        form.addRow("التاريخ:", dt)
        date_str = dt.date_str()   # → "2025-01-15"
    """

    def __init__(self, date: QDate = None,
                 height: int = 32,
                 width: int = None,
                 parent=None):
        super().__init__(date or QDate.currentDate(), parent)
        self.setCalendarPopup(True)
        self.setDisplayFormat("yyyy-MM-dd")
        self.setMinimumHeight(height)
        if width:
            self.setFixedWidth(width)
        base = _base()
        self.setStyleSheet(f"""
            QDateEdit {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 0 8px;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_primary']};
            }}
            QDateEdit:focus {{
                border-color: {_C['accent']};
            }}
            QDateEdit::drop-down {{
                border: none;
                width: 24px;
            }}
        """)

    def date_str(self) -> str:
        """يرجع التاريخ كـ string بتنسيق yyyy-MM-dd."""
        return self.date().toString("yyyy-MM-dd")

    def set_date_str(self, date_str: str):
        """يضبط التاريخ من string بتنسيق yyyy-MM-dd."""
        if date_str:
            d = QDate.fromString(date_str, "yyyy-MM-dd")
            if d.isValid():
                self.setDate(d)


# ══════════════════════════════════════════════════════════
# LabeledInput — حقل مع label أفقي
# ══════════════════════════════════════════════════════════

class LabeledInput(QWidget):
    """
    حقل مع label على اليمين في سطر أفقي.
    مفيد لأي input خارج QFormLayout.

    الاستخدام:
        field = LabeledInput("الكمية:", QDoubleSpinBox())
        layout.addWidget(field)

        # مع وحدة قياس:
        field = LabeledInput("السعر:", sp_price, unit="جنيه")
        layout.addWidget(field)
    """

    def __init__(self, label: str, widget: QWidget,
                 unit: str = "",
                 spacing: int = 8,
                 label_width: int = None,
                 parent=None):
        super().__init__(parent)
        self._widget = widget
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(spacing)

        base = _base()
        lbl = QLabel(label)
        lbl.setStyleSheet(
            f"color: {_C['text_sec']}; font-size: {fs(base, 0)}pt; font-weight: 600;"
            "background: transparent; border: none;"
        )
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        if label_width:
            lbl.setFixedWidth(label_width)

        lay.addWidget(lbl)
        lay.addWidget(widget, stretch=1)

        if unit:
            lbl_unit = QLabel(unit)
            lbl_unit.setStyleSheet(
                f"color: {_C['text_muted']}; font-size: {fs(base, -1)}pt;"
                "background: transparent; border: none;"
            )
            lay.addWidget(lbl_unit)

    @property
    def widget(self) -> QWidget:
        return self._widget


# ══════════════════════════════════════════════════════════
# RequiredLineEdit — QLineEdit مع تحقق بصري
# ══════════════════════════════════════════════════════════

class RequiredLineEdit(QLineEdit):
    """
    QLineEdit مع تحقق بصري من الفراغ.
    يُظهر حدوداً حمراء لو الحقل فارغ وتم التحقق.

    الاستخدام:
        inp = RequiredLineEdit("أدخل الاسم...")
        form.addRow("الاسم:", inp)

        if not inp.validate():   # يُظهر error state
            return
        name = inp.text_stripped()
    """

    def __init__(self, placeholder: str = "",
                 height: int = 32,
                 parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(height)
        self._error = False
        self._apply_style(False)
        self.textChanged.connect(self._on_change)

    def _apply_style(self, error: bool):
        base = _base()
        if error:
            bg, border = "#fef2f2", "#f87171"
        else:
            bg, border = _C['bg_input'], _C['border_med']

        self.setStyleSheet(f"""
            QLineEdit {{
                background: {bg};
                border: 1.5px solid {border};
                border-radius: 6px;
                padding: 0 8px;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {'#f87171' if error else _C['accent']};
                background: white;
            }}
        """)

    def _on_change(self):
        if self._error and self.text().strip():
            self._error = False
            self._apply_style(False)

    def validate(self) -> bool:
        """يتحقق ويُظهر error state لو فارغ. يرجع True لو صالح."""
        if not self.text().strip():
            self._error = True
            self._apply_style(True)
            self.setFocus()
            return False
        return True

    def text_stripped(self) -> str:
        return self.text().strip()

    def clear_error(self):
        self._error = False
        self._apply_style(False)


# ══════════════════════════════════════════════════════════
# StyledComboBox — QComboBox بستايل موحد
# ══════════════════════════════════════════════════════════

class StyledComboBox(QComboBox):
    """
    QComboBox بستايل موحد مع الـ theme.
    يحل محل الـ QComboBox العادي في الفورم.

    الاستخدام:
        cmb = StyledComboBox()
        cmb.addItem("الخيار الأول", "value1")
        form.addRow("النوع:", cmb)
    """

    def __init__(self, height: int = 32, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(height)
        base = _base()
        self.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border_med']};
                border-radius: 6px;
                padding: 0 8px;
                font-size: {fs(base, 0)}pt;
                color: {_C['text_primary']};
                min-height: {height}px;
            }}
            QComboBox:focus {{
                border-color: {_C['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 24px;
            }}
            QComboBox:disabled {{
                background: {_C['bg_surface_2']};
                color: {_C['text_disabled']};
            }}
        """)


# ══════════════════════════════════════════════════════════
# NotesLineEdit — حقل ملاحظات موحد
# ══════════════════════════════════════════════════════════

class NotesLineEdit(QLineEdit):
    """
    QLineEdit للملاحظات بستايل مخصص (خلفية أفتح).

    الاستخدام:
        notes = NotesLineEdit()
        form.addRow("ملاحظات:", notes)
    """

    def __init__(self, placeholder: str = "ملاحظات اختيارية...",
                 height: int = 30,
                 parent=None):
        super().__init__(parent)
        self.setPlaceholderText(placeholder)
        self.setMinimumHeight(height)
        base = _base()
        self.setStyleSheet(f"""
            QLineEdit {{
                background: #fafafa;
                border: 1px solid {_C['border']};
                border-radius: 6px;
                padding: 0 8px;
                font-size: {fs(base, -1)}pt;
                color: {_C['text_sec']};
                font-style: italic;
            }}
            QLineEdit:focus {{
                border-color: {_C['border_med']};
                background: white;
                font-style: normal;
                color: {_C['text_primary']};
            }}
        """)