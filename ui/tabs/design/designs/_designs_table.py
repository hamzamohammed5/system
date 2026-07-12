"""
ui/tabs/design/designs/_designs_table.py  — v3
===============================================
قائمة التصميمات — Grid Cards محسّن.

التغييرات عن v2:
  - _fetch_designs_filtered: الـ first_xcf بيتحدد حسب set_id المفلتر
    (أول ملف من المجموعة المطلوبة، وإلا fallback لأول ملف عموماً)
  - _DesignCard: يستقبل set_id ويدعم update_set_filter لتحديث الـ thumbnail
  - _DesignsTable._on_set_changed: يعمل apply_filter كامل عند تغيير المجموعة
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel,
    QFrame,
    QScrollArea
)
from PyQt5.QtCore  import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QTimer
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedComboBox


from services.design import get_design_size_service, get_design_service
from ._xcf_thumbnail import get_watcher, clear_cache
from ._design_detail_panel import _DesignDetailPanel

from .designs_table._design_card import _DesignCard, _ThumbWorker

from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import get_font_size, fs
from ui.constants import (
    INPUT_BORDER_W,
    INPUT_BORDER_RADIUS,
    INPUT_PAD_H,
    BTN_PAD_H,
    INPUT_HEIGHT,
    DESIGN_CARD_W,
    DESIGN_CARD_THUMB,
    DESIGNS_TABLE_TB_MARGIN_H,
    DESIGNS_TABLE_TB_MARGIN_V,
    DESIGNS_TABLE_TB_SPACING,
    DESIGNS_TABLE_ROW_SPACING,
    DESIGNS_TABLE_INP_MIN_H,
    DESIGNS_TABLE_CMB_MIN_H,
    DESIGNS_TABLE_CMB_DROP_W,
    DESIGNS_TABLE_GRID_MARGIN,
    DESIGNS_TABLE_GRID_SPACING,
    DESIGNS_TABLE_SCROLL_W,
    DESIGNS_TABLE_SCROLL_RADIUS,
    DESIGNS_TABLE_SCROLL_MIN_H,
    DESIGNS_TABLE_INP_PAD_H,
    DESIGNS_TABLE_REFLOW_DELAY,
    DESIGNS_TABLE_SEARCH_DELAY,
    DESIGNS_TABLE_COLS_SIDE_PAD,
    DESIGNS_TABLE_MIN_COLS,
    DESIGNS_TABLE_EMPTY_SPACING,
)

import os

_RADIUS_SM = f"{INPUT_BORDER_RADIUS}px"


def _btn_ss(bg, fg, bdr, hover_bg, radius=_RADIUS_SM, height=INPUT_HEIGHT):
    from ui.theme import _C
    base = get_font_size()
    return (
        f"QPushButton{{"
        f"  background:{bg}; color:{fg};"
        f"  border:{INPUT_BORDER_W}px solid {bdr}; border-radius:{radius};"
        f"  padding:0 {BTN_PAD_H}px; font-size:{fs(base,0)}pt; min-height:{height}px;"
        f"}}"
        f"QPushButton:hover{{background:{hover_bg};}}"
        f"QPushButton:pressed{{opacity:0.85;}}"
    )



# ════════════════════════════════════════════════════════
# Panel الرئيسي
# ════════════════════════════════════════════════════════

class _DesignsTable(QWidget, WidgetMixin):
    design_selected    = pyqtSignal(int)
    design_deleted     = pyqtSignal()
    set_filter_changed = pyqtSignal(object)

    def __init__(self, conn, detail_panel: _DesignDetailPanel, parent=None):
        super().__init__(parent)
        self.conn          = conn
        self._size_svc     = get_design_size_service(conn)
        self._design_svc   = get_design_service(conn)
        self._panel        = detail_panel
        self._cards        = {}           # did → _DesignCard
        self._workers      = []
        self._xcf_card_map = {}           # norm_path → did
        self._active_did   = None
        self._cat_filter   = None
        self._set_filter   = None
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(DESIGNS_TABLE_SEARCH_DELAY)
        self._search_timer.timeout.connect(self._apply_filter)

        get_watcher().file_changed.connect(self._on_xcf_changed)

        self._build()
        self._load()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        base = get_font_size()

        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_C['bg_surface']};
                border: {INPUT_BORDER_W}px solid {_C['border']};
                border-radius: {_RADIUS_SM};
                padding: 0 {DESIGNS_TABLE_INP_PAD_H}px;
                font-size: {fs(base,0)}pt;
                color: {_C['text_primary']};
            }}
            QLineEdit:focus {{
                border-color: {_C['accent']};
                background: {_C['bg_input']};
            }}
        """)

        self.btn_new.setStyleSheet(
            _btn_ss(_C["accent"], _C["accent_text"], _C["accent"], _C["accent_hover"], height=DESIGNS_TABLE_INP_MIN_H)
        )

        self._lbl_set.setStyleSheet(
            f"font-size:{fs(base,-1)}pt; color:{_C['text_sec']}; background:transparent;"
        )

        self.cmb_set.setStyleSheet(f"""
            QComboBox {{
                background: {_C['bg_surface']};
                border: {INPUT_BORDER_W}px solid {_C['border']};
                border-radius: {_RADIUS_SM};
                padding: 0 {INPUT_PAD_H}px;
                font-size: {fs(base,-1)}pt;
                color: {_C['text_primary']};
            }}
            QComboBox:focus {{ border-color: {_C['accent']}; }}
            QComboBox::drop-down {{ border: none; width: {DESIGNS_TABLE_CMB_DROP_W}px; }}
        """)

        self.lbl_count.setStyleSheet(
            f"font-size:{fs(base,-1)}pt; color:{_C['text_muted']}; background:transparent;"
        )

        self._btn_rst.setStyleSheet(
            _btn_ss(_C["bg_surface"], _C["text_sec"], _C["border"], _C["bg_input"], height=DESIGNS_TABLE_CMB_MIN_H)
        )

        self._ef_icon.setStyleSheet(f"font-size:{fs(base,+18)}pt; background:transparent;")
        self._empty_msg.setStyleSheet(
            f"color:{_C['text_sec']}; font-size:{fs(base,+2)}pt; font-weight:600; background:transparent;"
        )
        self._empty_sub.setStyleSheet(
            f"color:{_C['text_muted']}; font-size:{fs(base,0)}pt; background:transparent;"
        )

    def _build(self):
        from ui.theme import _C
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border-bottom: {INPUT_BORDER_W}px solid {_C['border']};
            }}
        """)
        tb_lay = QVBoxLayout(toolbar)
        tb_lay.setContentsMargins(DESIGNS_TABLE_TB_MARGIN_H, DESIGNS_TABLE_TB_MARGIN_V,
                                  DESIGNS_TABLE_TB_MARGIN_H, DESIGNS_TABLE_TB_MARGIN_V)
        tb_lay.setSpacing(DESIGNS_TABLE_TB_SPACING)

        # صف 1: بحث + زر جديد
        row1 = QHBoxLayout()
        row1.setSpacing(DESIGNS_TABLE_ROW_SPACING)

        self.inp_search = ThemedLineEdit()
        self.inp_search.setPlaceholderText(tr("design_table_search_placeholder"))
        self.inp_search.setMinimumHeight(DESIGNS_TABLE_INP_MIN_H)
        self.inp_search.textChanged.connect(lambda: self._search_timer.start())

        self.btn_new = QPushButton(f"  {tr('design_table_new_btn')}")
        self.btn_new.setMinimumHeight(DESIGNS_TABLE_INP_MIN_H)
        self.btn_new.clicked.connect(self._new_design)

        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(self.btn_new)
        tb_lay.addLayout(row1)

        # صف 2: فلتر مجموعة المقاسات + عداد + reset
        row2 = QHBoxLayout()
        row2.setSpacing(DESIGNS_TABLE_ROW_SPACING)

        self._lbl_set = QLabel(tr("design_table_set_filter_label"))

        self.cmb_set = ThemedComboBox()
        self.cmb_set.setMinimumHeight(DESIGNS_TABLE_CMB_MIN_H)
        self.cmb_set.currentIndexChanged.connect(self._on_set_changed)

        self.lbl_count = QLabel("")

        self._btn_rst = QPushButton(tr("design_table_reset_filters_btn"))
        self._btn_rst.setMinimumHeight(DESIGNS_TABLE_CMB_MIN_H)
        self._btn_rst.clicked.connect(self._reset_filters)

        row2.addWidget(self._lbl_set)
        row2.addWidget(self.cmb_set, stretch=1)
        row2.addWidget(self.lbl_count)
        row2.addWidget(self._btn_rst)
        tb_lay.addLayout(row2)

        root.addWidget(toolbar)

        # ── منطقة الكروت ──────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {_C['bg_surface']}; }}
            QScrollBar:vertical {{
                background: {_C['bg_surface']}; width: {DESIGNS_TABLE_SCROLL_W}px; border-radius: {DESIGNS_TABLE_SCROLL_RADIUS}px;
            }}
            QScrollBar::handle:vertical {{
                background: {_C['border_med']}; border-radius: {DESIGNS_TABLE_SCROLL_RADIUS}px; min-height: {DESIGNS_TABLE_SCROLL_MIN_H}px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet(f"background:{_C['bg_surface']};")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(DESIGNS_TABLE_GRID_MARGIN, DESIGNS_TABLE_GRID_MARGIN,
                                             DESIGNS_TABLE_GRID_MARGIN, DESIGNS_TABLE_GRID_MARGIN)
        self._grid_layout.setSpacing(DESIGNS_TABLE_GRID_SPACING)
        self._grid_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)

        self._scroll.setWidget(self._grid_widget)
        root.addWidget(self._scroll, stretch=1)

        # ── حالة فارغة ────────────────────────────────────
        self._empty_frame = QFrame()
        self._empty_frame.setStyleSheet(f"background:{_C['bg_surface']}; border:none;")
        ef_lay = QVBoxLayout(self._empty_frame)
        ef_lay.setAlignment(Qt.AlignCenter)
        ef_lay.setSpacing(DESIGNS_TABLE_EMPTY_SPACING)

        self._ef_icon = QLabel(tr("design_table_empty_icon"))
        self._ef_icon.setAlignment(Qt.AlignCenter)

        self._empty_msg = QLabel(tr("design_table_empty_no_designs"))
        self._empty_msg.setAlignment(Qt.AlignCenter)
        self._empty_sub = QLabel(tr("design_table_empty_start"))
        self._empty_sub.setAlignment(Qt.AlignCenter)

        ef_lay.addWidget(self._ef_icon)
        ef_lay.addWidget(self._empty_msg)
        ef_lay.addWidget(self._empty_sub)
        root.addWidget(self._empty_frame)
        self._empty_frame.setVisible(False)

        self._refresh_style()
        self._reload_set_combo()

    # ── تحميل combo المجموعات ──────────────────────────────

    def _reload_set_combo(self):
        prev = self.cmb_set.currentData()
        self.cmb_set.blockSignals(True)
        self.cmb_set.clear()
        self.cmb_set.addItem(tr("design_table_all_sets"), None)
        for ds in self._size_svc.list_all_sets():
            self.cmb_set.addItem(ds["name"], ds["id"])
        for i in range(self.cmb_set.count()):
            if self.cmb_set.itemData(i) == prev:
                self.cmb_set.setCurrentIndex(i)
                break
        self.cmb_set.blockSignals(False)

    def _load(self):
        self._reload_set_combo()
        self._apply_filter()

    # ── Signal handlers ────────────────────────────────────

    def _on_set_changed(self):
        """
        لما يتغير فلتر المجموعة:
          - يحدّث _set_filter
          - يعمل apply_filter كامل عشان الـ first_xcf يتحسب من جديد في الـ SQL
          - يبعت set_filter_changed للـ detail panel
        """
        self._set_filter = self.cmb_set.currentData()
        self._apply_filter()
        self.set_filter_changed.emit(self._set_filter)

    def filter_by_category(self, cat_id):
        """يُستدعى من DesignsCategoriesPanel."""
        self._cat_filter = cat_id
        self._apply_filter()

    # ── الفلترة وبناء الكروت ──────────────────────────────

    def _apply_filter(self):
        # إيقاف workers القديمة
        for w in self._workers:
            w.quit()
        self._workers.clear()

        # إيقاف مراقبة الملفات القديمة
        watcher = get_watcher()
        for path in list(self._xcf_card_map.keys()):
            watcher.unwatch(path)
        self._xcf_card_map.clear()

        name_q = self.inp_search.text().strip()
        rows   = self._design_svc.list_designs_filtered(
            name_q, self._cat_filter, self._set_filter
        )

        # حذف الكروت القديمة
        for card in self._cards.values():
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards = {}

        if not rows:
            self._scroll.setVisible(False)
            self._empty_frame.setVisible(True)
            if name_q or self._cat_filter or self._set_filter:
                self._empty_msg.setText(tr("design_table_empty_no_results"))
                self._empty_sub.setText(tr("design_table_empty_change_criteria"))
            else:
                self._empty_msg.setText(tr("design_table_empty_no_designs"))
                self._empty_sub.setText(tr("design_table_empty_start"))
            self.lbl_count.setText("")
            return

        self._empty_frame.setVisible(False)
        self._scroll.setVisible(True)

        cols = max(DESIGNS_TABLE_MIN_COLS, (self.width() - DESIGNS_TABLE_COLS_SIDE_PAD) // (DESIGN_CARD_W + DESIGNS_TABLE_GRID_SPACING))

        for idx, d in enumerate(rows):
            row_i = idx // cols
            col_i = idx % cols

            # إنشاء الـ card مع تمرير set_id الحالي
            card = _DesignCard(self.conn, d, set_id=self._set_filter)
            card.selected.connect(self._on_card_selected)
            if d["id"] == self._active_did:
                card.set_selected(True)

            self._grid_layout.addWidget(card, row_i, col_i, Qt.AlignTop)
            self._cards[d["id"]] = card

            # الـ first_xcf جاي من الـ SQL المعدَّل — يراعي set_id تلقائياً
            xcf = d["first_xcf"]
            if xcf and os.path.exists(xcf):
                norm = os.path.normpath(xcf)
                watcher.watch(norm)
                self._xcf_card_map[norm] = d["id"]
                worker = _ThumbWorker(norm, DESIGN_CARD_THUMB)
                worker.done.connect(self._on_thumb_ready)
                worker.start()
                self._workers.append(worker)
            else:
                card.set_thumbnail(None)

        total = len(rows)
        self.lbl_count.setText(tr("design_table_count").format(count=total))

    def _on_thumb_ready(self, xcf_path: str, pixmap):
        norm = os.path.normpath(xcf_path)
        did  = self._xcf_card_map.get(norm)
        if did and did in self._cards:
            self._cards[did].set_thumbnail(pixmap)

    def _on_xcf_changed(self, path: str):
        norm = os.path.normpath(path)
        did  = self._xcf_card_map.get(norm)
        if did and did in self._cards:
            clear_cache(path)
            worker = _ThumbWorker(path, DESIGN_CARD_THUMB)
            worker.done.connect(self._on_thumb_ready)
            worker.start()
            self._workers.append(worker)

    def _on_card_selected(self, did: int):
        if self._active_did and self._active_did in self._cards:
            self._cards[self._active_did].set_selected(False)
        self._active_did = did
        if did in self._cards:
            self._cards[did].set_selected(True)
        self._panel.load_design(did)
        self.design_selected.emit(did)

    def _new_design(self):
        if self._active_did and self._active_did in self._cards:
            self._cards[self._active_did].set_selected(False)
        self._active_did = None
        self._panel.reset()

    def _reset_filters(self):
        self.inp_search.blockSignals(True)
        self.cmb_set.blockSignals(True)
        self.inp_search.clear()
        self.cmb_set.setCurrentIndex(0)
        self.inp_search.blockSignals(False)
        self.cmb_set.blockSignals(False)
        self._set_filter = None
        self._apply_filter()
        self.set_filter_changed.emit(None)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        QTimer.singleShot(DESIGNS_TABLE_REFLOW_DELAY, self._reflow_grid)

    def _reflow_grid(self):
        if not self._cards:
            return
        cols = max(DESIGNS_TABLE_MIN_COLS, (self.width() - DESIGNS_TABLE_COLS_SIDE_PAD) // (DESIGN_CARD_W + DESIGNS_TABLE_GRID_SPACING))
        cards_list = list(self._cards.items())
        for idx, (did, card) in enumerate(cards_list):
            self._grid_layout.removeWidget(card)
            self._grid_layout.addWidget(card, idx // cols, idx % cols, Qt.AlignTop)

    def refresh(self):
        self._load()

    def selected_id(self):
        return self._active_did
