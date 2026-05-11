"""
ui/widgets/searchable_combo.py
===============================
_SearchableCombo  — QComboBox مع حقل بحث نصي مدمج.
_build_grouped_items — دالة مساعدة تجمّع العناصر بالتصنيف.

الاستخدام:
    from ui.widgets.searchable_combo import _SearchableCombo, _build_grouped_items

    combo = _SearchableCombo()
    combo.item_selected.connect(my_handler)

    items = [(id, name, cat_id, cat_name), ...]
    grouped = _build_grouped_items(items)
    combo.populate(grouped)

    # جلب الاختيار الحالي
    data = combo.current_data()   # → (None, item_id) أو None
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton,
    QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui  import QColor, QFont

# ── بيانات خاصة للسيباريتور ──
_SEPARATOR_DATA = ("__sep__", None)


# ══════════════════════════════════════════════════════════
# دالة مساعدة — تجميع العناصر بالتصنيف
# ══════════════════════════════════════════════════════════

def _build_grouped_items(items: list[tuple]) -> list[tuple]:
    """
    تحوّل قايمة عناصر (id, name, cat_id, cat_name) إلى
    قايمة مجمّعة بالتصنيف جاهزة لـ _SearchableCombo.populate().

    كل عنصر في النتيجة:
      (display_text, user_data, is_separator)
    """
    groups: dict[str, list[tuple]] = {}
    NO_CAT = "__no_category__"

    for entry in items:
        item_id  = entry[0]
        name     = entry[1]
        cat_name = entry[3] if len(entry) > 3 and entry[3] else NO_CAT
        if cat_name not in groups:
            groups[cat_name] = []
        groups[cat_name].append((item_id, name))

    result = []

    # التصنيفات المسمّاة أولاً
    for cat_name, members in groups.items():
        if cat_name == NO_CAT:
            continue
        result.append((f"─── {cat_name} ───", _SEPARATOR_DATA, True))
        for item_id, name in members:
            result.append((f"{item_id} — {name}", (None, item_id), False))

    # بدون تصنيف في الآخر
    if NO_CAT in groups:
        if result:
            result.append(("─── بدون تصنيف ───", _SEPARATOR_DATA, True))
        for item_id, name in groups[NO_CAT]:
            result.append((f"{item_id} — {name}", (None, item_id), False))

    return result


# ══════════════════════════════════════════════════════════
# _SearchableCombo
# ══════════════════════════════════════════════════════════

class _SearchableCombo(QWidget):
    """
    Combo مع حقل بحث نصي:
      [🔍 بحث...] [✖]  [القايمة ▼]

    Signals:
      item_selected(data) — يُطلق عند اختيار عنصر حقيقي (مش سيباريتور)
    """

    item_selected = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_items: list[tuple] = []
        self._build()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        # حقل البحث
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(90)
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 4px;
                padding: 2px 6px;
                font-size: 11px;
            }
            QLineEdit:focus { border-color: #1565c0; background: white; }
        """)
        self.inp_search.textChanged.connect(self._on_search)

        # زر مسح البحث
        self.btn_clear = QPushButton("✖")
        self.btn_clear.setFixedSize(20, 20)
        self.btn_clear.setStyleSheet(
            "QPushButton { background:transparent; border:none; color:#aaa; font-size:10px; }"
            "QPushButton:hover { color:#e53935; }"
        )
        self.btn_clear.clicked.connect(self._clear_search)
        self.btn_clear.setVisible(False)

        # الـ ComboBox
        self.cmb = QComboBox()
        self.cmb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb.setMinimumWidth(150)
        self.cmb.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmb.currentIndexChanged.connect(self._on_combo_changed)

        lay.addWidget(self.inp_search)
        lay.addWidget(self.btn_clear)
        lay.addWidget(self.cmb, stretch=1)

    # ══════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════

    def _on_search(self, text: str):
        self.btn_clear.setVisible(bool(text))
        self._rebuild_combo(filter_text=text.strip().lower())

    def _clear_search(self):
        self.inp_search.blockSignals(True)
        self.inp_search.clear()
        self.inp_search.blockSignals(False)
        self.btn_clear.setVisible(False)
        self._rebuild_combo(filter_text="")

    def _on_combo_changed(self, idx: int):
        data = self.cmb.itemData(idx)
        if data and data != _SEPARATOR_DATA and data[0] not in ("__sep__", "__orphan__"):
            self.item_selected.emit(data)

    # ══════════════════════════════════════════════════════
    # ملء وإعادة بناء القايمة
    # ══════════════════════════════════════════════════════

    def populate(self, items: list[tuple]):
        """
        items: list of (display_text, user_data, is_separator)
        ناتج _build_grouped_items عادةً.
        """
        self._all_items = items
        self._rebuild_combo(filter_text=self.inp_search.text().strip().lower())

    def _rebuild_combo(self, filter_text: str = ""):
        prev_data = self.cmb.currentData()
        self.cmb.blockSignals(True)
        self.cmb.clear()

        for display_text, user_data, is_separator in self._all_items:
            # فلترة — السيباريتورات تمر دائماً (هتتحذف لاحقاً لو فاضية)
            if filter_text and not is_separator:
                name_part = (
                    display_text.split("—", 1)[-1].strip().lower()
                    if "—" in display_text
                    else display_text.lower()
                )
                if filter_text not in name_part and filter_text not in display_text.lower():
                    continue

            self.cmb.addItem(display_text, userData=user_data)
            idx = self.cmb.count() - 1

            if is_separator:
                self._style_separator(idx)
            elif user_data and user_data[0] == "__orphan__":
                self.cmb.setItemData(idx, QColor("#e53935"), Qt.ForegroundRole)

        self._remove_empty_separators()
        self.cmb.blockSignals(False)
        self._restore_selection(prev_data)

    def _style_separator(self, idx: int):
        """يطبّق ستايل السيباريتور ويعطّله."""
        self.cmb.setItemData(idx, QColor("#78909c"), Qt.ForegroundRole)
        font = QFont()
        font.setBold(True)
        font.setPointSize(font.pointSize() - 1)
        self.cmb.setItemData(idx, font, Qt.FontRole)
        model = self.cmb.model()
        item  = model.item(idx)
        if item:
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)

    def _remove_empty_separators(self):
        """يحذف السيباريتورات الفاضية (آخر القايمة أو متتالية)."""
        changed = True
        while changed:
            changed = False
            count = self.cmb.count()
            for i in range(count - 1, -1, -1):
                d = self.cmb.itemData(i)
                if not self._is_sep(d):
                    continue
                # آخر عنصر؟
                if i == count - 1:
                    self.cmb.removeItem(i)
                    changed = True
                    break
                # التالي سيباريتور كمان؟
                if self._is_sep(self.cmb.itemData(i + 1)):
                    self.cmb.removeItem(i)
                    changed = True
                    break

    @staticmethod
    def _is_sep(data) -> bool:
        return data == _SEPARATOR_DATA or (
            data and isinstance(data, tuple) and data[0] == "__sep__"
        )

    def _restore_selection(self, prev_data):
        if prev_data is None:
            self._select_first_real()
            return
        for i in range(self.cmb.count()):
            if self.cmb.itemData(i) == prev_data:
                self.cmb.setCurrentIndex(i)
                return
        self._select_first_real()

    def _select_first_real(self):
        """يختار أول عنصر حقيقي (مش سيباريتور ومش orphan)."""
        for i in range(self.cmb.count()):
            d = self.cmb.itemData(i)
            if d and d != _SEPARATOR_DATA and isinstance(d, tuple) \
                    and d[0] not in ("__sep__", "__orphan__"):
                self.cmb.setCurrentIndex(i)
                return

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def current_data(self):
        return self.cmb.currentData()

    def set_selection(self, user_data):
        for i in range(self.cmb.count()):
            if self.cmb.itemData(i) == user_data:
                self.cmb.setCurrentIndex(i)
                return

    def block_signals(self, val: bool):
        self.cmb.blockSignals(val)

    def count(self) -> int:
        return self.cmb.count()

    def item_data(self, idx: int):
        return self.cmb.itemData(idx)

    def set_item_text(self, idx: int, text: str):
        self.cmb.setItemText(idx, text)

    def add_item_at_start(self, text: str, data):
        self.cmb.insertItem(0, text, data)
        self.cmb.setItemData(0, QColor("#e53935"), Qt.ForegroundRole)