"""
ui/tabs/design/designs/_designs_table.py  — v2
===============================================
قائمة التصميمات — تصميم Grid Cards بدل الجدول.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QPushButton, QLabel, QLineEdit,
    QMessageBox, QFrame, QComboBox,
    QScrollArea, QAbstractItemView, QSizePolicy,
)
from PyQt5.QtCore  import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QTimer
from PyQt5.QtGui   import QPixmap, QColor, QFont, QPainter, QLinearGradient

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

# ── ألوان ──
_BG          = "#ffffff"
_BG_SUBTLE   = "#f8fafc"
_BG_CARD     = "#ffffff"
_BORDER      = "#e2e8f0"
_BORDER_MED  = "#cbd5e1"
_TEXT        = "#0f172a"
_TEXT_MED    = "#475569"
_TEXT_MUTED  = "#94a3b8"
_BLUE        = "#3b82f6"
_BLUE_LT     = "#eff6ff"
_BLUE_MED    = "#bfdbfe"
_GREEN       = "#16a34a"
_GREEN_LT    = "#f0fdf4"
_ORANGE      = "#ea580c"
_RED         = "#dc2626"
_RED_LT      = "#fef2f2"

_CARD_W      = 180
_CARD_THUMB  = 140


# ════════════════════════════════════════════════════════
# Worker — تحميل الـ thumbnail
# ════════════════════════════════════════════════════════

class _ThumbWorker(QThread):
    done = Signal(str, object)  # xcf_path, QPixmap|None

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
# بطاقة تصميم واحد
# ════════════════════════════════════════════════════════

class _DesignCard(QFrame):
    selected  = pyqtSignal(int)
    deleted   = pyqtSignal(int)

    def __init__(self, conn, design_data, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._data     = dict(design_data)   # ← تحويل sqlite3.Row لـ dict
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

        # ── Thumbnail ──
        self._thumb_lbl = QLabel()
        self._thumb_lbl.setFixedSize(_CARD_W, _CARD_THUMB)
        self._thumb_lbl.setAlignment(Qt.AlignCenter)
        self._thumb_lbl.setStyleSheet(f"""
            QLabel {{
                background: #1e1b4b;
                border-radius: 10px 10px 0 0;
                font-size: 32px;
                color: #4c1d95;
            }}
        """)
        self._thumb_lbl.setText("🎨")
        root.addWidget(self._thumb_lbl)

        # ── معلومات ──
        info = QFrame()
        info.setStyleSheet("QFrame { background: transparent; border: none; }")
        info_lay = QVBoxLayout(info)
        info_lay.setContentsMargins(10, 8, 10, 10)
        info_lay.setSpacing(3)

        name = self._data["name"]
        lbl_name = QLabel(name)
        lbl_name.setWordWrap(True)
        lbl_name.setStyleSheet(
            f"font-size:12px; font-weight:600; color:{_TEXT};"
            " background:transparent; border:none;"
        )
        lbl_name.setFixedWidth(_CARD_W - 20)
        info_lay.addWidget(lbl_name)

        cat = self._data.get("category_name") or ""
        if cat:
            lbl_cat = QLabel(cat)
            lbl_cat.setStyleSheet(
                f"font-size:10px; color:{_TEXT_MUTED}; background:transparent; border:none;"
            )
            info_lay.addWidget(lbl_cat)

        sz_cnt = self._data.get("sizes_count") or 0
        fl_cnt = self._data.get("files_count") or 0
        if sz_cnt:
            fl_color = _GREEN if fl_cnt == sz_cnt else (_ORANGE if fl_cnt else _TEXT_MUTED)
            stats = QLabel(f"📐 {sz_cnt}  📁 {fl_cnt}")
            stats.setStyleSheet(
                f"font-size:10px; color:{fl_color}; background:transparent; border:none;"
            )
            info_lay.addWidget(stats)

        root.addWidget(info)

    def set_selected(self, sel: bool):
        self._selected = sel
        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_BLUE_LT};
                    border: 2px solid {_BLUE};
                    border-radius: 10px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_BG_CARD};
                    border: 1px solid {_BORDER};
                    border-radius: 10px;
                }}
                QFrame:hover {{
                    border-color: {_BLUE_MED};
                    background: {_BLUE_LT};
                }}
            """)

    def set_thumbnail(self, pixmap):
        if pixmap and not pixmap.isNull():
            self._thumb_lbl.setPixmap(
                pixmap.scaled(_CARD_W, _CARD_THUMB,
                              Qt.KeepAspectRatioByExpanding,
                              Qt.SmoothTransformation)
            )
            self._thumb_lbl.setStyleSheet("""
                QLabel {
                    background: #0f0e17;
                    border-radius: 10px 10px 0 0;
                }
            """)
        else:
            self._thumb_lbl.setText("🎨")

    def mousePressEvent(self, event):
        self.selected.emit(self._did)
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event):
        self.selected.emit(self._did)
        super().mouseDoubleClickEvent(event)


# ════════════════════════════════════════════════════════
# جلب التصميمات مع فلترة — محدّث لـ item_category_id
# ════════════════════════════════════════════════════════

def _fetch_designs_filtered(conn, name_q="", category_id=None, set_id=None):
    """
    جلب التصميمات مع فلترة.
    category_id هنا = item_category_id (تصنيف التصميم المستقل).
    """
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
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self._apply_filter)

        get_watcher().file_changed.connect(self._on_xcf_changed)

        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── شريط الأدوات ──
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        tb_lay = QVBoxLayout(toolbar)
        tb_lay.setContentsMargins(12, 10, 12, 10)
        tb_lay.setSpacing(8)

        # صف 1: بحث + زر جديد
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث بالاسم...")
        self.inp_search.setMinimumHeight(34)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                background:{_BG_SUBTLE}; border:1px solid {_BORDER_MED};
                border-radius:8px; padding:0 12px;
                font-size:12px; color:{_TEXT};
            }}
            QLineEdit:focus {{ border-color:{_BLUE}; background:{_BG}; }}
        """)
        self.inp_search.textChanged.connect(lambda: self._search_timer.start())

        self.btn_new = QPushButton("➕  تصميم جديد")
        self.btn_new.setMinimumHeight(34)
        self.btn_new.setStyleSheet(f"""
            QPushButton {{
                background:{_BLUE}; color:#fff; border:none;
                border-radius:8px; padding:0 16px;
                font-size:12px; font-weight:500;
            }}
            QPushButton:hover {{ background:#2563eb; }}
        """)
        self.btn_new.clicked.connect(self._new_design)

        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(self.btn_new)
        tb_lay.addLayout(row1)

        # صف 2: فلتر مجموعات + عداد
        row2 = QHBoxLayout()
        row2.setSpacing(8)

        lbl_set = QLabel("📐")
        lbl_set.setStyleSheet(
            f"font-size:14px; background:transparent; color:{_TEXT_MUTED};"
        )

        self.cmb_set = QComboBox()
        self.cmb_set.setMinimumHeight(28)
        self.cmb_set.setStyleSheet(f"""
            QComboBox {{
                background:{_BG_SUBTLE}; border:1px solid {_BORDER_MED};
                border-radius:6px; padding:0 8px;
                font-size:11px; color:{_TEXT_MED};
            }}
            QComboBox:focus {{ border-color:{_BLUE}; }}
            QComboBox::drop-down {{ border:none; width:16px; }}
        """)
        self.cmb_set.currentIndexChanged.connect(self._on_set_changed)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"color:{_TEXT_MUTED}; font-size:11px; background:transparent;"
        )

        btn_rst = QPushButton("↺")
        btn_rst.setFixedSize(28, 28)
        btn_rst.setToolTip("مسح البحث")
        btn_rst.setStyleSheet(f"""
            QPushButton {{
                background:{_BG_SUBTLE}; color:{_TEXT_MED};
                border:1px solid {_BORDER_MED}; border-radius:6px; font-size:14px;
            }}
            QPushButton:hover {{ color:{_BLUE}; border-color:{_BLUE_MED}; }}
        """)
        btn_rst.clicked.connect(self._reset_filters)

        row2.addWidget(lbl_set)
        row2.addWidget(self.cmb_set, stretch=1)
        row2.addWidget(self.lbl_count)
        row2.addWidget(btn_rst)
        tb_lay.addLayout(row2)

        root.addWidget(toolbar)

        # ── منطقة الكروت ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{_BG_SUBTLE}; }}
            QScrollBar:vertical {{
                background:#f0f0f0; width:6px; border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
                background:#c5cae9; border-radius:3px; min-height:20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        self._grid_widget = QWidget()
        self._grid_widget.setStyleSheet(f"background:{_BG_SUBTLE};")
        self._grid_layout = QGridLayout(self._grid_widget)
        self._grid_layout.setContentsMargins(12, 12, 12, 12)
        self._grid_layout.setSpacing(12)

        scroll.setWidget(self._grid_widget)
        root.addWidget(scroll, stretch=1)

        # ── حالة فارغة ──
        self._empty_frame = QFrame()
        self._empty_frame.setStyleSheet(f"background:{_BG_SUBTLE}; border:none;")
        ef_lay = QVBoxLayout(self._empty_frame)
        ef_lay.setAlignment(Qt.AlignCenter)
        ef_icon = QLabel("🎨")
        ef_icon.setAlignment(Qt.AlignCenter)
        ef_icon.setStyleSheet("font-size:52px; background:transparent;")
        self._empty_msg = QLabel("لا توجد تصميمات بعد")
        self._empty_msg.setAlignment(Qt.AlignCenter)
        self._empty_msg.setStyleSheet(
            f"color:{_TEXT_MUTED}; font-size:13px; background:transparent;"
        )
        ef_lay.addWidget(ef_icon)
        ef_lay.addSpacing(12)
        ef_lay.addWidget(self._empty_msg)
        root.addWidget(self._empty_frame)
        self._empty_frame.setVisible(False)

        self._reload_set_combo()

    def _reload_set_combo(self):
        prev = self.cmb_set.currentData()
        self.cmb_set.blockSignals(True)
        self.cmb_set.clear()
        self.cmb_set.addItem("📐  كل المجموعات", None)
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
        """يُستدعى من DesignsCategoriesPanel."""
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

        for card in self._cards.values():
            self._grid_layout.removeWidget(card)
            card.deleteLater()
        self._cards = {}

        if not rows:
            self._empty_frame.setVisible(True)
            if name_q or self._cat_filter or self._set_filter:
                self._empty_msg.setText("لا توجد نتائج للبحث الحالي")
            else:
                self._empty_msg.setText("لا توجد تصميمات بعد\nاضغط «تصميم جديد» للبدء")
            self.lbl_count.setText("لا شيء")
            return

        self._empty_frame.setVisible(False)

        cols = max(2, (self.width() - 240) // (_CARD_W + 12))

        for idx, d in enumerate(rows):
            row_i = idx // cols
            col_i = idx % cols

            card = _DesignCard(self.conn, d)
            card.selected.connect(self._on_card_selected)
            if d["id"] == self._active_did:
                card.set_selected(True)

            self._grid_layout.addWidget(card, row_i, col_i)
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

        self.lbl_count.setText(f"{len(rows)} تصميم")

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
        QTimer.singleShot(50, self._reflow_grid)

    def _reflow_grid(self):
        if not self._cards:
            return
        cols = max(2, (self.width() - 240) // (_CARD_W + 12))
        for idx, (did, card) in enumerate(self._cards.items()):
            self._grid_layout.removeWidget(card)
            self._grid_layout.addWidget(card, idx // cols, idx % cols)

    def refresh(self):
        self._load()

    def selected_id(self):
        return self._active_did