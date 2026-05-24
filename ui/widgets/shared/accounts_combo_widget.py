"""
ui/widgets/shared/accounts_combo_widget.py
==========================================
AccountsComboWidget — combo box موحد لاختيار الحسابات المحاسبية.

يوحّد الكود المكرر في:
  - trial_balance_tab.py
  - income_statement_tab.py
  - balance_sheet_tab.py
  - owners_equity_tab.py
  - أي تبويب يحتاج فلترة بالنوع

الاستخدام:
    from ui.widgets.shared.accounts_combo_widget import AccountTypeFilter

    filt = AccountTypeFilter(TYPE_AR)
    filt.type_changed.connect(self._on_type_filter)
    layout.addWidget(filt)
    current = filt.current_type()   # → "asset" | None
"""

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox
from PyQt5.QtCore import pyqtSignal

from ui.app_settings import _C


class AccountTypeFilter(QWidget):
    """
    شريط فلتر النوع للحسابات المحاسبية.

    يعرض: [أيقونة] [نوع الحساب ▼]

    Signals:
        type_changed(str | None) — يُطلق عند تغيير النوع
    """

    type_changed = pyqtSignal(object)

    def __init__(self, type_map: dict, include_all: bool = True, parent=None):
        """
        type_map : dict من {key: label} مثل TYPE_AR
        include_all : هل يضيف خيار "كل الأنواع"
        """
        super().__init__(parent)
        self._type_map   = type_map
        self._build(include_all)

    def _build(self, include_all: bool):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lbl = QLabel("🏷")
        lbl.setStyleSheet("background:transparent; border:none;")
        lbl.setFixedWidth(20)
        lay.addWidget(lbl)

        self._cmb = QComboBox()
        self._cmb.setMinimumHeight(28)
        self._cmb.setStyleSheet(f"""
            QComboBox {{
                background: white;
                border: 1px solid {_C.get('border_med', '#c5cae9')};
                border-radius: 5px;
                padding: 2px 8px;
                font-size: 11px;
                color: {_C.get('text_primary', '#333')};
            }}
            QComboBox::drop-down {{ border: none; }}
        """)
        if include_all:
            self._cmb.addItem("── كل الأنواع ──", None)
        for key, label in self._type_map.items():
            self._cmb.addItem(label, key)
        self._cmb.currentIndexChanged.connect(
            lambda _: self.type_changed.emit(self._cmb.currentData())
        )
        lay.addWidget(self._cmb, stretch=1)

    def current_type(self):
        return self._cmb.currentData()

    def set_type(self, key: str):
        for i in range(self._cmb.count()):
            if self._cmb.itemData(i) == key:
                self._cmb.setCurrentIndex(i)
                return

    def block_signals(self, val: bool):
        self._cmb.blockSignals(val)