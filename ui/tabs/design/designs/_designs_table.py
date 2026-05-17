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
    QPushButton, QLabel, QLineEdit,
    QFrame, QComboBox,
    QScrollArea
)
from PyQt5.QtCore  import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QTimer


from db.designs.dimension_sets_repo import fetch_all_dimension_sets
from ._xcf_thumbnail import get_watcher, clear_cache
from ._design_detail_panel import _DesignDetailPanel

from .designs_table._design_card import _fetch_designs_filtered, _DesignCard, _ThumbWorker

import os

# ── Palette ──────────────────────────────────────────────
_BG          = "#FFFFFF"
_BG_SURFACE  = "#F8F9FB"
_BORDER      = "#E5E9F0"
_BORDER_MED  = "#CDD3E0"
_TEXT_PRI    = "#1A2035"
_TEXT_SEC    = "#5A6680"
_TEXT_MUT    = "#9BA5BE"

_ACCENT      = "#4F6EF7"
_CARD_W      = 172
_CARD_THUMB  = 128
_RADIUS_SM   = "6px"


def _btn_ss(bg, fg, bdr, hover_bg, radius=_RADIUS_SM, height=32):
    return (
        f"QPushButton{{"
        f"  background:{bg}; color:{fg};"
        f"  border:1px solid {bdr}; border-radius:{radius};"
        f"  padding:0 14px; font-size:12px; min-height:{height}px;"
        f"}}"
        f"QPushButton:hover{{background:{hover_bg};}}"
        f"QPushButton:pressed{{opacity:0.85;}}"
    )



# ════════════════════════════════════════════════════════
# Panel الرئيسي
# ════════════════════════════════════════════════════════

class _DesignsTable(QWidget):
    design_selected    = pyqtSignal(int)
    design_deleted     = pyqtSignal()
    set_filter_changed = pyqtSignal(object)

    def __init__(self, conn, detail_panel: _DesignDetailPanel, parent=None):
        super().__init__(parent)
        self.conn          = conn
        self._panel        = detail_panel
        self._cards        = {}           # did → _DesignCard
        self._workers      = []
        self._xcf_card_map = {}           # norm_path → did
        self._active_did   = None
        self._cat_filter   = None
        self._set_filter   = None
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(280)
        self._search_timer.timeout.connect(self._apply_filter)

        get_watcher().file_changed.connect(self._on_xcf_changed)

        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Toolbar ──────────────────────────────────────
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        tb_lay = QVBoxLayout(toolbar)
        tb_lay.setContentsMargins(14, 10, 14, 10)
        tb_lay.setSpacing(8)

        # صف 1: بحث + زر جديد
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG_SURFACE};
                border: 1px solid {_BORDER};
                border-radius: {_RADIUS_SM};
                padding: 0 12px;
                font-size: 12px;
                color: {_TEXT_PRI};
            }}
            QLineEdit:focus {{
                border-color: {_ACCENT};
                background: {_BG};
            }}
        """)
        self.inp_search.textChanged.connect(lambda: self._search_timer.start())

        self.btn_new = QPushButton("  تصميم جديد  +")
        self.btn_new.setMinimumHeight(34)
        self.btn_new.setStyleSheet(
            _btn_ss(_ACCENT, "#fff", _ACCENT, "#3D5BEF", height=34)
        )
        self.btn_new.clicked.connect(self._new_design)

        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(self.btn_new)
        tb_lay.addLayout(row1)

        # صف 2: فلتر مجموعة المقاسات + عداد + reset
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_set = QLabel("المجموعة:")
        lbl_set.setStyleSheet(
            f"font-size:11px; color:{_TEXT_SEC}; background:transparent;"
        )

        self.cmb_set = QComboBox()
        self.cmb_set.setMinimumHeight(28)
        self.cmb_set.setStyleSheet(f"""
            QComboBox {{
                background: {_BG_SURFACE};
                border: 1px solid {_BORDER};
                border-radius: {_RADIUS_SM};
                padding: 0 8px;
                font-size: 11px;
                color: {_TEXT_PRI};
            }}
            QComboBox:focus {{ border-color: {_ACCENT}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
        """)
        self.cmb_set.currentIndexChanged.connect(self._on_set_changed)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"font-size:11px; color:{_TEXT_MUT}; background:transparent;"
        )

        btn_rst = QPushButton("↺  مسح")
        btn_rst.setMinimumHeight(28)
        btn_rst.setStyleSheet(
            _btn_ss(_BG_SURFACE, _TEXT_SEC, _BORDER, _BG, height=28)
        )
        btn_rst.clicked.connect(self._reset_filters)

        row2.addWidget(lbl_set)
        row2.addWidget(self.cmb_set, stretch=1)
        row2.addWidget(self.lbl_count)
        row2.addWidget(btn_rst)
        tb_lay.addLayout(row2)

        root.addWidget(toolbar)

        # ── منطقة الكروت ──────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {_BG_SURFACE}; }}
            QScrollBar:vertical {{
                background: {_BG_SURFACE}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {_BORDER_MED}; border-radius: 3px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet(f"background:{_BG_SURFACE};")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(14, 14, 14, 14)
        self._grid_layout.setSpacing(12)
        self._grid_layout.setAlignment(Qt.AlignTop | Qt.AlignRight)

        self._scroll.setWidget(self._grid_widget)
        root.addWidget(self._scroll, stretch=1)

        # ── حالة فارغة ────────────────────────────────────
        self._empty_frame = QFrame()
        self._empty_frame.setStyleSheet(f"background:{_BG_SURFACE}; border:none;")
        ef_lay = QVBoxLayout(self._empty_frame)
        ef_lay.setAlignment(Qt.AlignCenter)
        ef_lay.setSpacing(12)

        ef_icon = QLabel("🎨")
        ef_icon.setAlignment(Qt.AlignCenter)
        ef_icon.setStyleSheet("font-size:48px; background:transparent;")

        self._empty_msg = QLabel("لا توجد تصميمات")
        self._empty_msg.setAlignment(Qt.AlignCenter)
        self._empty_msg.setStyleSheet(
            f"color:{_TEXT_SEC}; font-size:14px; font-weight:600; background:transparent;"
        )
        self._empty_sub = QLabel("اضغط «تصميم جديد» للبدء")
        self._empty_sub.setAlignment(Qt.AlignCenter)
        self._empty_sub.setStyleSheet(
            f"color:{_TEXT_MUT}; font-size:12px; background:transparent;"
        )

        ef_lay.addWidget(ef_icon)
        ef_lay.addWidget(self._empty_msg)
        ef_lay.addWidget(self._empty_sub)
        root.addWidget(self._empty_frame)
        self._empty_frame.setVisible(False)

        self._reload_set_combo()

    # ── تحميل combo المجموعات ──────────────────────────────

    def _reload_set_combo(self):
        prev = self.cmb_set.currentData()
        self.cmb_set.blockSignals(True)
        self.cmb_set.clear()
        self.cmb_set.addItem("كل المجموعات", None)
        for ds in fetch_all_dimension_sets(self.conn):
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
        rows   = _fetch_designs_filtered(
            self.conn, name_q, self._cat_filter, self._set_filter
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
                self._empty_msg.setText("لا توجد نتائج")
                self._empty_sub.setText("جرّب تغيير معايير البحث")
            else:
                self._empty_msg.setText("لا توجد تصميمات")
                self._empty_sub.setText("اضغط «تصميم جديد +» للبدء")
            self.lbl_count.setText("")
            return

        self._empty_frame.setVisible(False)
        self._scroll.setVisible(True)

        cols = max(2, (self.width() - 28) // (_CARD_W + 12))

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
                worker = _ThumbWorker(norm, _CARD_THUMB)
                worker.done.connect(self._on_thumb_ready)
                worker.start()
                self._workers.append(worker)
            else:
                card.set_thumbnail(None)

        total = len(rows)
        self.lbl_count.setText(f"{total} تصميم")

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
            worker = _ThumbWorker(path, _CARD_THUMB)
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
        QTimer.singleShot(60, self._reflow_grid)

    def _reflow_grid(self):
        if not self._cards:
            return
        cols = max(2, (self.width() - 28) // (_CARD_W + 12))
        cards_list = list(self._cards.items())
        for idx, (did, card) in enumerate(cards_list):
            self._grid_layout.removeWidget(card)
            self._grid_layout.addWidget(card, idx // cols, idx % cols, Qt.AlignTop)

    def refresh(self):
        self._load()

    def selected_id(self):
        return self._active_did