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

from services.design import get_dimension_set_service
from ui.font import get_font_size, fs
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.theme import _C
from ui.constants import (
    DIM_SETS_LIST_CARD_MIN_H, DIM_SETS_LIST_CARD_BORDER_W, DIM_SETS_LIST_CARD_SELECTED_BORDER_W,
    DIM_SETS_LIST_CARD_RADIUS, DIM_SETS_LIST_CARD_MARGIN_H, DIM_SETS_LIST_CARD_MARGIN_V,
    DIM_SETS_LIST_CARD_SPACING, DIM_SETS_LIST_ICON_LBL_W, DIM_SETS_LIST_TEXT_COL_SPACING,
    DIM_SETS_LIST_BADGE_W, DIM_SETS_LIST_BADGE_H, DIM_SETS_LIST_BADGE_RADIUS,
    DIM_SETS_LIST_HDR_PAD_V, DIM_SETS_LIST_HDR_PAD_H, DIM_SETS_LIST_HAIRLINE_W,
    DIM_SETS_LIST_SEARCH_FRAME_MARGIN_H, DIM_SETS_LIST_SEARCH_FRAME_MARGIN_V,
    DIM_SETS_LIST_SEARCH_SPACING, DIM_SETS_LIST_SEARCH_FIELD_H, DIM_SETS_LIST_CMB_CAT_MAX_W,
    DIM_SETS_LIST_INP_BORDER_W, DIM_SETS_LIST_INP_RADIUS, DIM_SETS_LIST_INP_PAD_V,
    DIM_SETS_LIST_INP_PAD_H, DIM_SETS_LIST_CMB_PAD_H, DIM_SETS_LIST_SCROLL_W,
    DIM_SETS_LIST_SCROLL_RADIUS, DIM_SETS_LIST_SCROLL_MIN_H, DIM_SETS_LIST_CARDS_SPACING,
    DIM_SETS_LIST_CARDS_MARGIN, DIM_SETS_LIST_COUNT_PAD,
)

_BLUE       = _C["acc_type_asset"]
_BLUE_LIGHT = _C["accent_light"]
_BLUE_MID   = _C["accent_mid"]
_GRAY_BG    = _C["bg_surface"]
_BORDER     = _C["border"]
_TEXT       = _C["text_primary"]
_TEXT_MUTED = _C["text_muted"]

_CARD_NORMAL = f"""
    QFrame {{
        background: {_C["bg_input"]};
        border: {DIM_SETS_LIST_CARD_BORDER_W}px solid {_C["border"]};
        border-radius: {DIM_SETS_LIST_CARD_RADIUS}px;
    }}
    QFrame:hover {{
        border-color: {_C["accent_mid"]};
        background: {_C["accent_light"]};
    }}
"""

_CARD_SELECTED = f"""
    QFrame {{
        background: {_C["accent_light"]};
        border: {DIM_SETS_LIST_CARD_SELECTED_BORDER_W}px solid {_C["accent"]};
        border-radius: {DIM_SETS_LIST_CARD_RADIUS}px;
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
        self.setMinimumHeight(DIM_SETS_LIST_CARD_MIN_H)
        self._build(name, category, unit, fields_cnt, instances_cnt)

    def _build(self, name, category, unit, fields_cnt, instances_cnt):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(DIM_SETS_LIST_CARD_MARGIN_H, DIM_SETS_LIST_CARD_MARGIN_V,
                                DIM_SETS_LIST_CARD_MARGIN_H, DIM_SETS_LIST_CARD_MARGIN_V)
        lay.setSpacing(DIM_SETS_LIST_CARD_SPACING)

        base = get_font_size()

        icon_lbl = QLabel(tr("dim_sets_set_icon"))
        icon_lbl.setStyleSheet(f"font-size: {fs(base,+4)}pt; background: transparent; border: none;")
        icon_lbl.setFixedWidth(DIM_SETS_LIST_ICON_LBL_W)
        icon_lbl.setAlignment(Qt.AlignCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(DIM_SETS_LIST_TEXT_COL_SPACING)

        self._name_lbl = QLabel(name)
        self._name_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_TEXT};
            background: transparent;
            border: none;
        """)

        sep = tr("dim_sets_meta_separator")
        self._meta_lbl = QLabel(
            f"{category or tr('dim_sets_card_no_category')}{sep}{unit}{sep}"
            + tr("dim_sets_card_field_suffix").format(count=fields_cnt)
        )
        self._meta_lbl.setStyleSheet(f"""
            font-size: {fs(base,-1)}pt;
            color: {_TEXT_MUTED};
            background: transparent;
            border: none;
        """)

        text_col.addWidget(self._name_lbl)
        text_col.addWidget(self._meta_lbl)

        self._badge = QLabel(tr("dim_sets_badge_values").format(count=instances_cnt))
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setFixedSize(DIM_SETS_LIST_BADGE_W, DIM_SETS_LIST_BADGE_H)
        self._badge.setStyleSheet(f"""
            background: {_BLUE_LIGHT};
            color: {_BLUE};
            border-radius: {DIM_SETS_LIST_BADGE_RADIUS}px;
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
            border-radius: {DIM_SETS_LIST_BADGE_RADIUS}px;
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

class _SetsListPanel(QWidget, WidgetMixin):
    set_selected = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._svc       = get_dimension_set_service(conn)
        self._cards     = {}
        self._active_id = None
        self._all_rows  = []
        self._build()
        self._load()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        base = get_font_size()
        # تحديث الـ header
        self._hdr_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_C['accent']};
            background: {_C['accent_light']};
            padding: {DIM_SETS_LIST_HDR_PAD_V}px {DIM_SETS_LIST_HDR_PAD_H}px;
            border-bottom: {DIM_SETS_LIST_HAIRLINE_W}px solid {_BORDER};
        """)
        # تحديث حقل البحث
        self._search_inp.setStyleSheet(f"""
            QLineEdit {{
                border: {DIM_SETS_LIST_INP_BORDER_W}px solid {_BORDER};
                border-radius: {DIM_SETS_LIST_INP_RADIUS}px;
                padding: {DIM_SETS_LIST_INP_PAD_V}px {DIM_SETS_LIST_INP_PAD_H}px;
                font-size: {fs(base,0)}pt;
                background: {_GRAY_BG};
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_input']}; }}
        """)
        # تحديث عداد النتائج
        self._count_lbl.setStyleSheet(f"""
            color: {_TEXT_MUTED};
            font-size: {fs(base,-1)}pt;
            padding: {DIM_SETS_LIST_COUNT_PAD}px;
            background: {_C['bg_input']};
            border-top: {DIM_SETS_LIST_HAIRLINE_W}px solid {_BORDER};
        """)
        # تحديث كل الكروت
        for card in self._cards.values():
            card.refresh_font()

    def _on_font_changed(self, size: int = None):
        """يُبقيها متوافقة مع أي نداء خارجي قديم من _ValuesPanel."""
        self._refresh_style()

    def _build(self):
        base = get_font_size()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._hdr_lbl = QLabel(tr("dim_sets_list_title"))
        self._hdr_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: {fs(base,+1)}pt;
            color: {_C['accent']};
            background: {_C['accent_light']};
            padding: {DIM_SETS_LIST_HDR_PAD_V}px {DIM_SETS_LIST_HDR_PAD_H}px;
            border-bottom: {DIM_SETS_LIST_HAIRLINE_W}px solid {_BORDER};
        """)
        root.addWidget(self._hdr_lbl)

        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border-bottom: {DIM_SETS_LIST_HAIRLINE_W}px solid {_BORDER};
            }}
        """)
        s_lay = QHBoxLayout(search_frame)
        s_lay.setContentsMargins(DIM_SETS_LIST_SEARCH_FRAME_MARGIN_H, DIM_SETS_LIST_SEARCH_FRAME_MARGIN_V,
                                  DIM_SETS_LIST_SEARCH_FRAME_MARGIN_H, DIM_SETS_LIST_SEARCH_FRAME_MARGIN_V)
        s_lay.setSpacing(DIM_SETS_LIST_SEARCH_SPACING)

        self._search_inp = QLineEdit()
        self._search_inp.setPlaceholderText(tr("dim_sets_list_search"))
        self._search_inp.setMinimumHeight(DIM_SETS_LIST_SEARCH_FIELD_H)
        self._search_inp.setStyleSheet(f"""
            QLineEdit {{
                border: {DIM_SETS_LIST_INP_BORDER_W}px solid {_BORDER};
                border-radius: {DIM_SETS_LIST_INP_RADIUS}px;
                padding: {DIM_SETS_LIST_INP_PAD_V}px {DIM_SETS_LIST_INP_PAD_H}px;
                font-size: {fs(base,0)}pt;
                background: {_GRAY_BG};
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; background: {_C['bg_input']}; }}
        """)
        self._search_inp.textChanged.connect(self._apply_filter)

        self._cmb_cat = QComboBox()
        self._cmb_cat.setMinimumHeight(DIM_SETS_LIST_SEARCH_FIELD_H)
        self._cmb_cat.setMaximumWidth(DIM_SETS_LIST_CMB_CAT_MAX_W)
        self._cmb_cat.setStyleSheet(f"""
            QComboBox {{
                border: {DIM_SETS_LIST_INP_BORDER_W}px solid {_BORDER};
                border-radius: {DIM_SETS_LIST_INP_RADIUS}px;
                padding: {DIM_SETS_LIST_INP_PAD_V}px {DIM_SETS_LIST_CMB_PAD_H}px;
                font-size: {fs(base,-1)}pt;
                background: {_GRAY_BG};
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
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
                background: {_C['bg_surface']}; width: {DIM_SETS_LIST_SCROLL_W}px; border-radius: {DIM_SETS_LIST_SCROLL_RADIUS}px;
            }}
            QScrollBar::handle:vertical {{
                background: {_C['border_med']}; border-radius: {DIM_SETS_LIST_SCROLL_RADIUS}px; min-height: {DIM_SETS_LIST_SCROLL_MIN_H}px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet(f"background: {_GRAY_BG};")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(DIM_SETS_LIST_CARDS_SPACING)
        self._cards_layout.setContentsMargins(DIM_SETS_LIST_CARDS_MARGIN, DIM_SETS_LIST_CARDS_MARGIN,
                                               DIM_SETS_LIST_CARDS_MARGIN, DIM_SETS_LIST_CARDS_MARGIN)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_widget)
        root.addWidget(scroll, stretch=1)

        self._count_lbl = QLabel("")
        self._count_lbl.setAlignment(Qt.AlignCenter)
        self._count_lbl.setStyleSheet(f"""
            color: {_TEXT_MUTED};
            font-size: {fs(base,-1)}pt;
            padding: {DIM_SETS_LIST_COUNT_PAD}px;
            background: {_C['bg_input']};
            border-top: {DIM_SETS_LIST_HAIRLINE_W}px solid {_BORDER};
        """)
        root.addWidget(self._count_lbl)

    def _reload_cat_filter(self):
        prev = self._cmb_cat.currentData()
        self._cmb_cat.blockSignals(True)
        self._cmb_cat.clear()
        self._cmb_cat.addItem(tr("dim_sets_list_all_cats"), None)
        rows = self._svc.list_categories()
        tree = self._svc.build_tree(rows)
        self._add_cat_nodes(tree, 0)
        for i in range(self._cmb_cat.count()):
            if self._cmb_cat.itemData(i) == prev:
                self._cmb_cat.setCurrentIndex(i)
                break
        self._cmb_cat.blockSignals(False)

    def _add_cat_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = tr("category_tree_arrow") if depth > 0 else ""
        for node in nodes:
            self._cmb_cat.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    def _load(self):
        self._all_rows = list(self._svc.list_sets())
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

            fields_cnt = self._svc.count_fields_for_set(ds["id"])

            instances_cnt = self._svc.count_instances_for_set(ds["id"])

            card = _SetCard(
                ds["id"], ds["name"],
                ds["category_name"] or "",
                ds["default_unit"] or tr("dim_sets_list_default_unit"),
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
            tr("dim_sets_list_count_all").format(count=shown) if shown == total
            else tr("dim_sets_list_count_filtered").format(shown=shown, total=total)
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