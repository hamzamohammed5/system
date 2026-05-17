"""
ui/tabs/design/designs/_designs_table.py  — v3
===============================================
قائمة التصميمات — Grid Cards محسّن.

التحسينات:
  - Cards أوضح مع معلومات منظّمة
  - Toolbar أنظف مع فلتر أذكى
  - ألوان متناسقة
  - Placeholder أجمل للـ thumbnails
  - selected state أوضح
  - حالة فارغة مع call-to-action
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit,
    QMessageBox, QFrame, QComboBox,
    QScrollArea, QSizePolicy,
)
from PyQt5.QtCore  import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QTimer
from PyQt5.QtGui   import QPixmap, QColor, QFont

from db.designs.designs_repo import fetch_design, delete_design
from db.designs.designs_sizes_repo import fetch_all_designs_summary
from db.designs.design_item_categories_repo import (
    fetch_item_category_descendants,
)
from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets,
)
from ui.helpers import confirm_delete
from ._xcf_thumbnail import get_xcf_thumbnail, get_watcher
from ._design_detail_panel import _DesignDetailPanel

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
_ACCENT_LT   = "#EEF2FF"
_ACCENT_BDR  = "#C7D2FE"

_SUCCESS     = "#16A34A"
_SUCCESS_LT  = "#F0FDF4"
_WARNING     = "#D97706"
_WARNING_LT  = "#FFFBEB"
_DANGER      = "#DC2626"
_DANGER_LT   = "#FEF2F2"

_CARD_W      = 172
_CARD_THUMB  = 128
_RADIUS      = "10px"
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
# Worker — تحميل الـ thumbnail
# ════════════════════════════════════════════════════════

class _ThumbWorker(QThread):
    done = Signal(str, object)

    def __init__(self, xcf_path: str, size: int = _CARD_THUMB):
        super().__init__()
        self._path = xcf_path
        self._size = size

    def run(self):
        try:
            px = get_xcf_thumbnail(self._path, self._size)
        except Exception:
            px = None
        self.done.emit(self._path, px)


# ════════════════════════════════════════════════════════
# بطاقة تصميم واحد — محسّنة
# ════════════════════════════════════════════════════════

class _DesignCard(QFrame):
    selected = pyqtSignal(int)
    deleted  = pyqtSignal(int)

    def __init__(self, conn, design_data, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._data     = dict(design_data)
        self._did      = self._data["id"]
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(_CARD_W)
        self._build()

    def _build(self):
        self._update_style()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── منطقة الـ Thumbnail ──
        thumb_frame = QFrame()
        thumb_frame.setFixedSize(_CARD_W, _CARD_THUMB)
        thumb_frame.setStyleSheet(f"""
            QFrame {{
                background: #1E1B4B;
                border-radius: {_RADIUS} {_RADIUS} 0 0;
            }}
        """)

        self._thumb_lbl = QLabel(thumb_frame)
        self._thumb_lbl.setFixedSize(_CARD_W, _CARD_THUMB)
        self._thumb_lbl.setAlignment(Qt.AlignCenter)
        self._thumb_lbl.setStyleSheet(
            "background:transparent; font-size:28px; color:#6366F1;"
        )
        self._thumb_lbl.setText("🎨")

        # badge عدد المقاسات
        sz_cnt = self._data.get("sizes_count") or 0
        if sz_cnt:
            badge = QLabel(f"{sz_cnt}", thumb_frame)
            badge.setGeometry(_CARD_W - 30, 8, 22, 18)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                "background:rgba(0,0,0,0.55); color:#fff;"
                f"border-radius:9px; font-size:9px; font-weight:700;"
                "border:1px solid rgba(255,255,255,0.2);"
            )

        root.addWidget(thumb_frame)

        # ── معلومات التصميم ──
        info = QFrame()
        info.setStyleSheet(
            f"QFrame{{background:transparent; border:none;}}"
        )
        info_lay = QVBoxLayout(info)
        info_lay.setContentsMargins(10, 8, 10, 10)
        info_lay.setSpacing(3)

        # اسم التصميم
        name = self._data.get("name", "")
        lbl_name = QLabel(name)
        lbl_name.setWordWrap(True)
        font_n = QFont()
        font_n.setPointSize(10)
        font_n.setWeight(QFont.Medium)
        lbl_name.setFont(font_n)
        lbl_name.setStyleSheet(
            f"color:{_TEXT_PRI}; background:transparent; border:none;"
        )
        info_lay.addWidget(lbl_name)

        # التصنيف
        cat = self._data.get("category_name") or ""
        if cat:
            lbl_cat = QLabel(cat)
            font_c = QFont()
            font_c.setPointSize(8)
            lbl_cat.setFont(font_c)
            lbl_cat.setStyleSheet(
                f"color:{_TEXT_MUT}; background:transparent; border:none;"
            )
            info_lay.addWidget(lbl_cat)

        # حالة الملفات
        fl_cnt = self._data.get("files_count") or 0
        if sz_cnt:
            if fl_cnt == sz_cnt:
                status_col  = _SUCCESS
                status_text = f"✓  {fl_cnt}/{sz_cnt} ملف"
            elif fl_cnt > 0:
                status_col  = _WARNING
                status_text = f"⚡  {fl_cnt}/{sz_cnt} ملف"
            else:
                status_col  = _TEXT_MUT
                status_text = f"○  {sz_cnt} مقاس — بدون ملفات"

            lbl_status = QLabel(status_text)
            font_s = QFont()
            font_s.setPointSize(8)
            lbl_status.setFont(font_s)
            lbl_status.setStyleSheet(
                f"color:{status_col}; background:transparent; border:none;"
            )
            info_lay.addWidget(lbl_status)

        root.addWidget(info)

    def set_selected(self, sel: bool):
        self._selected = sel
        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_ACCENT_LT};
                    border: 2px solid {_ACCENT};
                    border-radius: {_RADIUS};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_BG};
                    border: 1px solid {_BORDER};
                    border-radius: {_RADIUS};
                }}
                QFrame:hover {{
                    border-color: {_ACCENT_BDR};
                    background: {_ACCENT_LT};
                }}
            """)

    def set_thumbnail(self, pixmap):
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                _CARD_W, _CARD_THUMB,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self._thumb_lbl.setPixmap(scaled)
            self._thumb_lbl.setText("")
        else:
            self._thumb_lbl.setText("🎨")

    def mousePressEvent(self, event):
        self.selected.emit(self._did)
        super().mousePressEvent(event)


# ════════════════════════════════════════════════════════
# جلب التصميمات مع فلترة
# ════════════════════════════════════════════════════════

def _fetch_designs_filtered(conn, name_q="", category_id=None, set_id=None):
    sql = """
        SELECT d.id, d.name, d.item_category_id, d.notes,
               d.created_at, d.updated_at,
               ic.name                              AS category_name,
               ic.color                             AS category_color,
               COUNT(DISTINCT ds.id)                AS sizes_count,
               SUM(CASE WHEN ds.xcf_path IS NOT NULL
                             AND ds.xcf_path != ''
                        THEN 1 ELSE 0 END)          AS files_count,
               (SELECT ds2.xcf_path
                FROM   design_sizes ds2
                WHERE  ds2.design_id = d.id
                  AND  ds2.xcf_path IS NOT NULL
                  AND  ds2.xcf_path != ''
                ORDER  BY ds2.sort_order, ds2.id
                LIMIT  1)                           AS first_xcf
        FROM   designs d
        LEFT JOIN design_item_categories ic ON ic.id = d.item_category_id
        LEFT JOIN design_sizes ds           ON ds.design_id = d.id
    """
    conditions, params = [], []

    if name_q:
        conditions.append("d.name LIKE ?")
        params.append(f"%{name_q}%")

    if category_id is not None:
        try:
            desc = fetch_item_category_descendants(conn, category_id)
            ph   = ",".join("?" * len(desc))
            conditions.append(f"d.item_category_id IN ({ph})")
            params.extend(desc)
        except Exception:
            conditions.append("d.item_category_id = ?")
            params.append(category_id)

    if set_id is not None:
        conditions.append(
            "EXISTS (SELECT 1 FROM design_sizes ds2 "
            "WHERE ds2.design_id = d.id AND ds2.set_id = ?)"
        )
        params.append(set_id)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " GROUP BY d.id ORDER BY d.updated_at DESC, d.name"
    return conn.execute(sql, params).fetchall()


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
        self._cards        = {}
        self._workers      = []
        self._xcf_card_map = {}
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

        # ── Toolbar ──────────────────────────────
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

        # ── منطقة الكروت ──────────────────────────
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

        # ── حالة فارغة ────────────────────────────
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

    def _on_set_changed(self):
        self._set_filter = self.cmb_set.currentData()
        self._apply_filter()
        self.set_filter_changed.emit(self._set_filter)

    def filter_by_category(self, cat_id):
        self._cat_filter = cat_id
        self._apply_filter()

    def _apply_filter(self):
        for w in self._workers:
            w.quit()
        self._workers.clear()

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

            card = _DesignCard(self.conn, d)
            card.selected.connect(self._on_card_selected)
            if d["id"] == self._active_did:
                card.set_selected(True)

            self._grid_layout.addWidget(card, row_i, col_i, Qt.AlignTop)
            self._cards[d["id"]] = card

            xcf = d["first_xcf"]
            if xcf and os.path.exists(xcf):
                norm = os.path.normpath(xcf)
                watcher.watch(norm)
                self._xcf_card_map[norm] = d["id"]
                worker = _ThumbWorker(norm, _CARD_THUMB)
                worker.done.connect(self._on_thumb_ready)
                worker.start()
                self._workers.append(worker)

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
            from ._xcf_thumbnail import clear_cache
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