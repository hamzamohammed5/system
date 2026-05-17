"""
ui/tabs/design/dimension_sets/values_panel/_sets_list_panel.py
=====================================
مع دعم تغيير حجم الخط ديناميكياً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit,
    QScrollArea, QFrame, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets,
    fetch_all_design_categories, build_category_tree,
)
from ui.app_settings import get_font_size, fs

_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GRAY_BG    = "#f8f9fc"
_BORDER     = "#e0e7f3"
_TEXT       = "#1a2340"
_TEXT_MUTED = "#7a869a"

_CARD_NORMAL = f"""
    QFrame {{
        background: white;
        border: 1.5px solid {_BORDER};
        border-radius: 10px;
    }}
    QFrame:hover {{
        border-color: {_BLUE_MID};
        background: #f5f8ff;
    }}
"""

_CARD_SELECTED = f"""
    QFrame {{
        background: {_BLUE_LIGHT};
        border: 2px solid {_BLUE};
        border-radius: 10px;
    }}
"""


# ══════════════════════════════════════════════════════════
# بطاقة مجموعة مقاسات
# ══════════════════════════════════════════════════════════

class _SetCard(QFrame):
    clicked = pyqtSignal(int)

    def __init__(self, set_id: int, name: str,
                 category: str, unit: str, fields_cnt: int,
                 instances_cnt: int, parent=None):
        super().__init__(parent)
        self.set_id    = set_id
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(_CARD_NORMAL)
        self.setMinimumHeight(72)
        self._build(name, category, unit, fields_cnt, instances_cnt)

    def _build(self, name, category, unit, fields_cnt, instances_cnt):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)

        base = get_font_size()

        icon_lbl = QLabel("📐")
        icon_lbl.setStyleSheet(f"font-size: {fs(base,+4)}pt; background: transparent; border: none;")
        icon_lbl.setFixedWidth(34)
        icon_lbl.setAlignment(Qt.AlignCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        self._name_lbl = QLabel(name)
        self._name_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_TEXT};
            background: transparent;
            border: none;
        """)

        self._meta_lbl = QLabel(
            f"{category or '—'}  ·  {unit}  ·  {fields_cnt} حقل"
        )
        self._meta_lbl.setStyleSheet(f"""
            font-size: {fs(base,-1)}pt;
            color: {_TEXT_MUTED};
            background: transparent;
            border: none;
        """)

        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._meta_lbl)

        self._badge = QLabel(f"{instances_cnt} قيمة")
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setFixedSize(58, 22)
        self._badge.setStyleSheet(f"""
            background: {_BLUE_LIGHT};
            color: {_BLUE};
            border-radius: 11px;
            font-size: {fs(base,-1)}pt;
            font-weight: bold;
            border: none;
        """)

        lay.addWidget(icon_lbl)
        lay.addLayout(text_col, stretch=1)
        lay.addWidget(self._badge)

    def refresh_font(self):
        """يُستدعى عند تغيير حجم الخط."""
        base = get_font_size()
        self._name_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_TEXT};
            background: transparent;
            border: none;
        """)
        self._meta_lbl.setStyleSheet(f"""
            font-size: {fs(base,-1)}pt;
            color: {_TEXT_MUTED};
            background: transparent;
            border: none;
        """)
        self._badge.setStyleSheet(f"""
            background: {_BLUE_LIGHT};
            color: {_BLUE};
            border-radius: 11px;
            font-size: {fs(base,-1)}pt;
            font-weight: bold;
            border: none;
        """)

    def set_selected(self, sel: bool):
        self._selected = sel
        self.setStyleSheet(_CARD_SELECTED if sel else _CARD_NORMAL)

    def mousePressEvent(self, event):
        self.clicked.emit(self.set_id)
        super().mousePressEvent(event)


# ══════════════════════════════════════════════════════════
# قائمة مجموعات المقاسات
# ══════════════════════════════════════════════════════════

class _SetsListPanel(QWidget):
    set_selected = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._cards     = {}
        self._active_id = None
        self._all_rows  = []
        self._build()
        self._load()

    def _on_font_changed(self, size: int):
        """يُستدعى من _ValuesPanel عند تغيير حجم الخط."""
        base = size
        # تحديث الـ header
        self._hdr_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_BLUE};
            background: {_BLUE_LIGHT};
            padding: 10px 16px;
            border-bottom: 1px solid {_BORDER};
        """)
        # تحديث حقل البحث
        self._search_inp.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {_BORDER};
                border-radius: 8px;
                padding: 3px 10px;
                font-size: {fs(base,0)}pt;
                background: {_GRAY_BG};
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: white; }}
        """)
        # تحديث عداد النتائج
        self._count_lbl.setStyleSheet(f"""
            color: {_TEXT_MUTED};
            font-size: {fs(base,-1)}pt;
            padding: 6px;
            background: white;
            border-top: 1px solid {_BORDER};
        """)
        # تحديث كل الكروت
        for card in self._cards.values():
            card.refresh_font()

    def _build(self):
        base = get_font_size()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._hdr_lbl = QLabel("📐  مجموعات المقاسات")
        self._hdr_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_BLUE};
            background: {_BLUE_LIGHT};
            padding: 10px 16px;
            border-bottom: 1px solid {_BORDER};
        """)
        root.addWidget(self._hdr_lbl)

        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        s_lay = QHBoxLayout(search_frame)
        s_lay.setContentsMargins(10, 8, 10, 8)
        s_lay.setSpacing(6)

        self._search_inp = QLineEdit()
        self._search_inp.setPlaceholderText("🔍  بحث...")
        self._search_inp.setMinimumHeight(32)
        self._search_inp.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {_BORDER};
                border-radius: 8px;
                padding: 3px 10px;
                font-size: {fs(base,0)}pt;
                background: {_GRAY_BG};
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: white; }}
        """)
        self._search_inp.textChanged.connect(self._apply_filter)

        self._cmb_cat = QComboBox()
        self._cmb_cat.setMinimumHeight(32)
        self._cmb_cat.setMaximumWidth(130)
        self._cmb_cat.setStyleSheet(f"""
            QComboBox {{
                border: 1.5px solid {_BORDER};
                border-radius: 8px;
                padding: 3px 8px;
                font-size: {fs(base,-1)}pt;
                background: {_GRAY_BG};
            }}
            QComboBox:focus {{ border-color: {_BLUE}; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self._cmb_cat.currentIndexChanged.connect(self._apply_filter)

        s_lay.addWidget(self._search_inp, stretch=1)
        s_lay.addWidget(self._cmb_cat)
        root.addWidget(search_frame)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {_GRAY_BG}; }}
            QScrollBar:vertical {{
                background: #f0f0f0; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: #c5cae9; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet(f"background: {_GRAY_BG};")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(10, 10, 10, 10)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_widget)
        root.addWidget(scroll, stretch=1)

        self._count_lbl = QLabel("")
        self._count_lbl.setAlignment(Qt.AlignCenter)
        self._count_lbl.setStyleSheet(f"""
            color: {_TEXT_MUTED};
            font-size: {fs(base,-1)}pt;
            padding: 6px;
            background: white;
            border-top: 1px solid {_BORDER};
        """)
        root.addWidget(self._count_lbl)

    def _reload_cat_filter(self):
        prev = self._cmb_cat.currentData()
        self._cmb_cat.blockSignals(True)
        self._cmb_cat.clear()
        self._cmb_cat.addItem("كل التصنيفات", None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_cat_nodes(tree, 0)
        for i in range(self._cmb_cat.count()):
            if self._cmb_cat.itemData(i) == prev:
                self._cmb_cat.setCurrentIndex(i)
                break
        self._cmb_cat.blockSignals(False)

    def _add_cat_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self._cmb_cat.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    def _load(self):
        self._all_rows = list(fetch_all_dimension_sets(self.conn))
        self._reload_cat_filter()
        self._apply_filter()

    def _apply_filter(self):
        q      = self._search_inp.text().strip().lower()
        cat_id = self._cmb_cat.currentData()

        for card in self._cards.values():
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        self._cards = {}

        shown = 0
        for ds in self._all_rows:
            if q and q not in ds["name"].lower():
                continue
            if cat_id is not None and ds["category_id"] != cat_id:
                continue

            fields_cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?",
                (ds["id"],)
            ).fetchone()["c"]

            instances_cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_set_instances WHERE set_id=?",
                (ds["id"],)
            ).fetchone()["c"]

            card = _SetCard(
                ds["id"], ds["name"],
                ds["category_name"] or "",
                ds["default_unit"] or "cm",
                fields_cnt, instances_cnt
            )
            card.clicked.connect(self._on_card_click)
            if ds["id"] == self._active_id:
                card.set_selected(True)

            self._cards_layout.insertWidget(
                self._cards_layout.count() - 1, card
            )
            self._cards[ds["id"]] = card
            shown += 1

        total = len(self._all_rows)
        self._count_lbl.setText(
            f"{shown} مجموعة" if shown == total
            else f"{shown} من {total} مجموعة"
        )

    def _on_card_click(self, set_id: int):
        if self._active_id and self._active_id in self._cards:
            self._cards[self._active_id].set_selected(False)
        self._active_id = set_id
        if set_id in self._cards:
            self._cards[set_id].set_selected(True)
        self.set_selected.emit(set_id)

    def refresh(self):
        self._load()
        if self._active_id:
            self.set_selected.emit(self._active_id)

    def refresh_card(self, set_id: int):
        self._load()