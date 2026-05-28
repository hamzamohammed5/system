"""
ui/widgets/utils/searchable_combo.py
=====================================
SearchableCombo — QComboBox مع حقل بحث مدمج.

التحسينات:
  - [تحسين 13] debounce داخلي للبحث (120ms).
    القديم: كل ضغطة تعيد بناء الـ combo كاملاً.
    الجديد: QTimer واحد يجمع الضغطات ثم يبني مرة واحدة.
    أي مستدعي ينسى الـ debounce محمي تلقائياً.
    قوائم > 200 عنصر لن تعاني من performance مرئي.

  - [محفوظ] pending_sep pattern — يمنع الـ separators الفارغة
    بدون _remove_empty_seps (كانت O(n²)).
"""
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QComboBox, QLineEdit, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui  import QColor, QFont

from ui.app_settings import _C, fs, get_font_size

_SEP = ("__sep__", None)


def build_grouped_items(items: list) -> list:
    """
    تحوّل قائمة (id, name, cat_id, cat_name) إلى
    قائمة مجمّعة جاهزة لـ SearchableCombo.populate().
    """
    groups: dict = {}
    NO_CAT = "__no_category__"

    for entry in items:
        item_id  = entry[0]
        name     = entry[1]
        cat_name = entry[3] if len(entry) > 3 and entry[3] else NO_CAT
        groups.setdefault(cat_name, []).append((item_id, name))

    result = []
    for cat_name, members in groups.items():
        if cat_name == NO_CAT:
            continue
        result.append((f"─── {cat_name} ───", _SEP, True))
        for item_id, name in members:
            result.append((f"{item_id} — {name}", (None, item_id), False))

    if NO_CAT in groups:
        if result:
            result.append(("─── بدون تصنيف ───", _SEP, True))
        for item_id, name in groups[NO_CAT]:
            result.append((f"{item_id} — {name}", (None, item_id), False))

    return result


class SearchableCombo(QWidget):
    """
    Combo مع حقل بحث: [🔍] [✖] [القائمة ▼]

    Signals:
        item_selected(data) — عند اختيار عنصر حقيقي
    """

    item_selected = pyqtSignal(object)

    # [تحسين 13] delay البحث الداخلي بالـ ms
    SEARCH_DELAY_MS: int = 120

    def __init__(self, parent=None):
        super().__init__(parent)
        self._all_items: list = []
        self._pending_filter  = ""

        # [تحسين 13] QTimer داخلي للـ debounce
        self._rebuild_timer = QTimer(self)
        self._rebuild_timer.setSingleShot(True)
        self._rebuild_timer.setInterval(self.SEARCH_DELAY_MS)
        self._rebuild_timer.timeout.connect(self._do_rebuild)

        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        base = get_font_size()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث...")
        self.inp_search.setFixedWidth(90)
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background:{_C['bg_surface_2']}; border:1px solid {_C['border_med']};
                border-radius:4px; padding:2px 6px; font-size:{fs(base, -1)}pt;
                color:{_C['text_primary']};
            }}
            QLineEdit:focus {{ border-color:{_C['accent']}; background:{_C['bg_input']}; }}
        """)
        self.inp_search.textChanged.connect(self._on_search)

        self.btn_clear = QPushButton("✖")
        self.btn_clear.setFixedSize(20, 20)
        self.btn_clear.setStyleSheet(f"""
            QPushButton {{
                background:transparent; border:none;
                color:{_C['text_disabled']}; font-size:{fs(base, -2)}pt;
            }}
            QPushButton:hover {{ color:{_C['danger']}; }}
        """)
        self.btn_clear.clicked.connect(self._clear_search)
        self.btn_clear.setVisible(False)

        self.cmb = QComboBox()
        self.cmb.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.cmb.setMinimumWidth(150)
        self.cmb.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.cmb.currentIndexChanged.connect(self._on_combo_changed)

        lay.addWidget(self.inp_search)
        lay.addWidget(self.btn_clear)
        lay.addWidget(self.cmb, stretch=1)

    # ── handlers ──────────────────────────────────────────

    def _on_search(self, text: str):
        """
        [تحسين 13] بدل ما نبني مباشرة، نحفظ الـ filter ونطلق الـ timer.
        الـ timer يجمع الضغطات السريعة ويبني مرة واحدة.
        """
        self.btn_clear.setVisible(bool(text))
        self._pending_filter = text.strip().lower()
        self._rebuild_timer.start()

    def _do_rebuild(self):
        """[تحسين 13] يُستدعى من الـ timer — بناء الـ combo بالفلتر المعلق."""
        self._rebuild(filter_text=self._pending_filter)

    def _clear_search(self):
        self.inp_search.blockSignals(True)
        self.inp_search.clear()
        self.inp_search.blockSignals(False)
        self.btn_clear.setVisible(False)
        # إلغاء الـ timer المعلق وإعادة البناء فوراً
        self._rebuild_timer.stop()
        self._pending_filter = ""
        self._rebuild(filter_text="")

    def _on_combo_changed(self, idx: int):
        data = self.cmb.itemData(idx)
        if data and data != _SEP and data[0] not in ("__sep__", "__orphan__"):
            self.item_selected.emit(data)

    # ── ملء القائمة ───────────────────────────────────────

    def populate(self, items: list):
        """items: list of (display_text, user_data, is_separator)"""
        self._all_items = items
        # [تحسين 13] نستخدم الـ pending_filter الحالي (لو فيه بحث نشط)
        self._rebuild_timer.stop()
        self._rebuild(filter_text=self._pending_filter)

    def clear_items(self):
        self._all_items = []
        self._pending_filter = ""
        self._rebuild_timer.stop()
        self.cmb.clear()
        self.inp_search.clear()
        self.btn_clear.setVisible(False)

    def _rebuild(self, filter_text: str = ""):
        """
        يبني القائمة مع فلترة الـ separators الفارغة أثناء البناء.

        pending_sep pattern:
          - نأخر إضافة الـ separator حتى يجي عنصر حقيقي بعده
          - لو الـ separator في النهاية أو يليه separator آخر → يُتجاهل
        """
        prev = self.cmb.currentData()
        self.cmb.blockSignals(True)
        self.cmb.clear()

        pending_sep = None

        for display, user_data, is_sep in self._all_items:
            if filter_text and not is_sep:
                name_part = (display.split("—", 1)[-1].strip().lower()
                             if "—" in display else display.lower())
                if filter_text not in name_part and filter_text not in display.lower():
                    continue

            if is_sep:
                pending_sep = (display, user_data)
            else:
                if pending_sep is not None:
                    self.cmb.addItem(pending_sep[0], userData=pending_sep[1])
                    self._style_sep(self.cmb.count() - 1)
                    pending_sep = None

                self.cmb.addItem(display, userData=user_data)
                idx = self.cmb.count() - 1
                if user_data and user_data[0] == "__orphan__":
                    self.cmb.setItemData(idx, QColor(_C['danger']), Qt.ForegroundRole)

        self.cmb.blockSignals(False)
        self._restore(prev)

    def _style_sep(self, idx: int):
        self.cmb.setItemData(idx, QColor(_C['text_muted']), Qt.ForegroundRole)
        f = QFont()
        f.setBold(True)
        f.setPointSize(f.pointSize() - 1)
        self.cmb.setItemData(idx, f, Qt.FontRole)
        item = self.cmb.model().item(idx)
        if item:
            item.setFlags(item.flags() & ~Qt.ItemIsEnabled & ~Qt.ItemIsSelectable)

    def _restore(self, prev):
        if prev is None:
            self._select_first_real()
            return
        for i in range(self.cmb.count()):
            if self.cmb.itemData(i) == prev:
                self.cmb.setCurrentIndex(i)
                return
        self._select_first_real()

    @staticmethod
    def _is_sep(data) -> bool:
        return data == _SEP or (
            data and isinstance(data, tuple) and data[0] == "__sep__"
        )

    def _select_first_real(self):
        for i in range(self.cmb.count()):
            d = self.cmb.itemData(i)
            if (d and d != _SEP and isinstance(d, tuple)
                    and d[0] not in ("__sep__", "__orphan__")):
                self.cmb.setCurrentIndex(i)
                return

    # ── API ───────────────────────────────────────────────

    def current_data(self):
        return self.cmb.currentData()

    def get_selected_id(self):
        data = self.cmb.currentData()
        if data and data != _SEP and isinstance(data, tuple):
            if data[0] not in ("__sep__", "__orphan__"):
                return data[1]
        return None

    def set_selection(self, user_data):
        for i in range(self.cmb.count()):
            if self.cmb.itemData(i) == user_data:
                self.cmb.setCurrentIndex(i)
                return

    def set_placeholder(self, text: str):
        self.inp_search.setPlaceholderText(text)

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
        self.cmb.setItemData(0, QColor(_C['danger']), Qt.ForegroundRole)