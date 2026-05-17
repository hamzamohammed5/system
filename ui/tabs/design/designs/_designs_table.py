"""
ui/tabs/design/designs/_designs_table.py
==========================================
جدول التصميمات — تصميم Modern/Flat محسّن.

التحسينات:
  - شريط فلاتر نظيف في صف واحد
  - جدول بـ row height مريحة وحدود خفيفة
  - thumbnail أوضح مع placeholder مناسب
  - عداد النتائج واضح
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QPushButton, QLabel, QLineEdit,
    QMessageBox, QFrame, QComboBox,
    QAbstractItemView,
)
from PyQt5.QtCore  import Qt, pyqtSignal, QThread, pyqtSignal as Signal
from PyQt5.QtGui   import QPixmap, QColor, QFont

from db.designs.designs_repo import fetch_design, delete_design
from db.designs.designs_sizes_repo import fetch_all_designs_summary
from db.designs.dimension_sets_repo import (
    fetch_all_design_categories, build_category_tree,
    fetch_all_dimension_sets, fetch_category_descendants,
)
from ui.helpers import danger_button, confirm_delete, buttons_row
from ._xcf_thumbnail import get_xcf_thumbnail, get_watcher
from ._design_detail_panel import _DesignDetailPanel

# ── ألوان النظام ──
_BG         = "#ffffff"
_BG_SUBTLE  = "#f8fafc"
_BORDER     = "#e2e8f0"
_BORDER_MED = "#cbd5e1"
_TEXT       = "#0f172a"
_TEXT_MED   = "#475569"
_TEXT_MUTED = "#94a3b8"
_BLUE       = "#3b82f6"
_BLUE_LT    = "#eff6ff"
_BLUE_MED   = "#bfdbfe"
_GREEN      = "#16a34a"
_ORANGE     = "#ea580c"
_RED        = "#dc2626"
_RED_LT     = "#fef2f2"

_TABLE_THUMB = 52


# ════════════════════════════════════════════════════════
# Worker — تحميل الـ thumbnail في الخلفية
# ════════════════════════════════════════════════════════

class _RowThumbWorker(QThread):
    done = Signal(int, object)

    def __init__(self, row: int, xcf_path: str, size: int = _TABLE_THUMB):
        super().__init__()
        self._row  = row
        self._path = xcf_path
        self._size = size

    def run(self):
        try:
            px = get_xcf_thumbnail(self._path, self._size)
        except Exception:
            px = None
        self.done.emit(self._row, px)


# ════════════════════════════════════════════════════════
# جلب التصميمات المفلترة
# ════════════════════════════════════════════════════════

def _fetch_designs_filtered(conn, name_q="", category_id=None, set_id=None):
    sql = """
        SELECT d.id, d.name, d.category_id, d.notes,
               d.created_at, d.updated_at,
               dc.name                                    AS category_name,
               COUNT(DISTINCT ds.id)                      AS sizes_count,
               SUM(CASE WHEN ds.xcf_path IS NOT NULL
                             AND ds.xcf_path != ''
                        THEN 1 ELSE 0 END)                AS files_count,
               (SELECT ds2.xcf_path
                FROM   design_sizes ds2
                WHERE  ds2.design_id = d.id
                  AND  ds2.xcf_path IS NOT NULL
                  AND  ds2.xcf_path != ''
                ORDER  BY ds2.sort_order, ds2.id
                LIMIT  1)                                 AS first_xcf
        FROM   designs d
        LEFT JOIN design_categories dc ON dc.id = d.category_id
        LEFT JOIN design_sizes ds      ON ds.design_id = d.id
    """
    conditions, params = [], []

    if name_q:
        conditions.append("d.name LIKE ?")
        params.append(f"%{name_q}%")

    if category_id is not None:
        desc = fetch_category_descendants(conn, category_id)
        ph   = ",".join("?" * len(desc))
        conditions.append(f"d.category_id IN ({ph})")
        params.extend(desc)

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
# أعمدة الجدول
# ════════════════════════════════════════════════════════

_COL_THUMB    = 0
_COL_ID       = 1
_COL_NAME     = 2
_COL_CATEGORY = 3
_COL_SIZES    = 4
_COL_FILES    = 5
_COLS         = ["", "ID", "الاسم", "التصنيف", "مقاسات", "ملفات"]


# ════════════════════════════════════════════════════════
# جدول التصميمات
# ════════════════════════════════════════════════════════

class _DesignsTable(QWidget):

    design_selected    = pyqtSignal(int)
    design_deleted     = pyqtSignal()
    set_filter_changed = pyqtSignal(object)

    def __init__(self, conn, detail_panel: "_DesignDetailPanel", parent=None):
        super().__init__(parent)
        self.conn   = conn
        self._panel = detail_panel
        self._thumb_workers: list[_RowThumbWorker] = []
        self._xcf_row_map: dict[str, int] = {}

        get_watcher().file_changed.connect(self._on_xcf_changed)

        self._build()
        self._load()

    # ── بناء الواجهة ──────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── شريط الفلاتر ──
        filter_bar = QFrame()
        filter_bar.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        fb_lay = QVBoxLayout(filter_bar)
        fb_lay.setContentsMargins(12, 10, 12, 10)
        fb_lay.setSpacing(8)

        # صف 1: بحث + زر جديد
        row1 = QHBoxLayout()
        row1.setSpacing(8)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث بالاسم...")
        self.inp_search.setStyleSheet(self._input_ss())
        self.inp_search.setMinimumHeight(32)
        self.inp_search.textChanged.connect(self._apply_filter)

        btn_new = QPushButton("➕  جديد")
        btn_new.setMinimumHeight(32)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background:{_BLUE}; color:#fff; border:none;
                border-radius:6px; padding:0 14px;
                font-size:12px; font-weight:500;
            }}
            QPushButton:hover {{ background:#2563eb; }}
        """)
        btn_new.clicked.connect(self._new_design)

        row1.addWidget(self.inp_search, stretch=1)
        row1.addWidget(btn_new)
        fb_lay.addLayout(row1)

        # صف 2: فلاتر + عداد + ريست
        row2 = QHBoxLayout()
        row2.setSpacing(6)

        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(28)
        self.cmb_category.setStyleSheet(self._combo_ss())
        self.cmb_category.currentIndexChanged.connect(self._apply_filter)

        self.cmb_set = QComboBox()
        self.cmb_set.setMinimumHeight(28)
        self.cmb_set.setStyleSheet(self._combo_ss())
        self.cmb_set.currentIndexChanged.connect(self._on_set_changed)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"color:{_TEXT_MUTED}; font-size:11px; background:transparent;"
        )

        btn_rst = QPushButton("↺")
        btn_rst.setFixedSize(28, 28)
        btn_rst.setToolTip("مسح الفلاتر")
        btn_rst.setStyleSheet(f"""
            QPushButton {{
                background:{_BG_SUBTLE}; color:{_TEXT_MED};
                border:1px solid {_BORDER_MED}; border-radius:6px; font-size:14px;
            }}
            QPushButton:hover {{ background:{_BG}; color:{_BLUE}; border-color:{_BLUE_MED}; }}
        """)
        btn_rst.clicked.connect(self._reset_filters)

        row2.addWidget(QLabel("📁"))
        row2.addWidget(self.cmb_category, stretch=1)
        row2.addWidget(QLabel("📐"))
        row2.addWidget(self.cmb_set, stretch=1)
        row2.addWidget(self.lbl_count)
        row2.addWidget(btn_rst)
        fb_lay.addLayout(row2)

        # تلوين labels الفلاتر
        for lbl in filter_bar.findChildren(QLabel):
            if lbl.text() in ("📁", "📐"):
                lbl.setStyleSheet(
                    f"font-size:14px; background:transparent; color:{_TEXT_MUTED};"
                )

        root.addWidget(filter_bar)

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setColumnCount(len(_COLS))
        self.table.setHorizontalHeaderLabels(_COLS)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: {_BG};
                outline: none;
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 6px 10px;
                border-bottom: 1px solid {_BORDER};
                color: {_TEXT};
            }}
            QTableWidget::item:selected {{
                background: {_BLUE_LT};
                color: {_BLUE};
            }}
            QHeaderView::section {{
                background: {_BG_SUBTLE};
                color: {_TEXT_MUTED};
                font-size: 11px;
                font-weight: 500;
                padding: 6px 10px;
                border: none;
                border-bottom: 1px solid {_BORDER_MED};
                border-left: 1px solid {_BORDER};
            }}
            QHeaderView::section:first {{
                border-left: none;
            }}
        """)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(_COL_THUMB,    QHeaderView.Fixed)
        self.table.setColumnWidth(_COL_THUMB,   _TABLE_THUMB + 12)
        hh.setSectionResizeMode(_COL_ID,        QHeaderView.Fixed)
        self.table.setColumnWidth(_COL_ID,       36)
        hh.setSectionResizeMode(_COL_NAME,      QHeaderView.Stretch)
        hh.setSectionResizeMode(_COL_CATEGORY,  QHeaderView.Interactive)
        self.table.setColumnWidth(_COL_CATEGORY, 100)
        hh.setSectionResizeMode(_COL_SIZES,     QHeaderView.Fixed)
        self.table.setColumnWidth(_COL_SIZES,    54)
        hh.setSectionResizeMode(_COL_FILES,     QHeaderView.Fixed)
        self.table.setColumnWidth(_COL_FILES,    54)

        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(self._on_select)
        root.addWidget(self.table, stretch=1)

        # ── زر الحذف ──
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border-top: 1px solid {_BORDER};
            }}
        """)
        bb_lay = QHBoxLayout(bottom_bar)
        bb_lay.setContentsMargins(12, 6, 12, 6)

        btn_del = QPushButton("🗑️  حذف التصميم")
        btn_del.setMinimumHeight(30)
        btn_del.setStyleSheet(f"""
            QPushButton {{
                background:{_BG}; color:{_RED};
                border:1px solid #fca5a5; border-radius:6px;
                padding:0 14px; font-size:11px;
            }}
            QPushButton:hover {{ background:{_RED_LT}; }}
        """)
        btn_del.clicked.connect(self._delete)
        bb_lay.addWidget(btn_del)
        bb_lay.addStretch()
        root.addWidget(bottom_bar)

        self._reload_category_combo()
        self._reload_set_combo()

    @staticmethod
    def _input_ss():
        return f"""
            QLineEdit {{
                background:{_BG_SUBTLE}; border:1px solid {_BORDER_MED};
                border-radius:6px; padding:0 10px;
                font-size:12px; color:{_TEXT};
            }}
            QLineEdit:focus {{
                border-color:{_BLUE}; background:{_BG};
            }}
        """

    @staticmethod
    def _combo_ss():
        return f"""
            QComboBox {{
                background:{_BG_SUBTLE}; border:1px solid {_BORDER_MED};
                border-radius:6px; padding:0 8px;
                font-size:11px; color:{_TEXT_MED};
            }}
            QComboBox:focus {{ border-color:{_BLUE}; }}
            QComboBox::drop-down {{ border:none; width:18px; }}
        """

    # ── Combo loaders ──────────────────────────────────

    def _reload_category_combo(self):
        prev = self.cmb_category.currentData()
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("📁  كل التصنيفات", None)
        tree = build_category_tree(fetch_all_design_categories(self.conn))
        self._add_cat_nodes(tree, 0)
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == prev:
                self.cmb_category.setCurrentIndex(i)
                break
        self.cmb_category.blockSignals(False)

    def _add_cat_nodes(self, nodes, depth):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_category.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

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

    # ── تحميل وفلترة ───────────────────────────────────

    def _load(self):
        self._reload_category_combo()
        self._reload_set_combo()
        self._apply_filter()

    def _on_set_changed(self):
        self._apply_filter()
        self.set_filter_changed.emit(self.cmb_set.currentData())

    def _apply_filter(self):
        for w in self._thumb_workers:
            w.quit()
        self._thumb_workers.clear()

        watcher = get_watcher()
        for path in list(self._xcf_row_map.keys()):
            watcher.unwatch(path)
        self._xcf_row_map.clear()

        name_q  = self.inp_search.text().strip()
        cat_id  = self.cmb_category.currentData()
        set_id  = self.cmb_set.currentData()
        prev_id = self._selected_id()

        rows = _fetch_designs_filtered(self.conn, name_q, cat_id, set_id)
        self.table.setRowCount(0)

        import os
        for d in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, _TABLE_THUMB + 12)

            # ── Thumbnail ──
            thumb_lbl = QLabel()
            thumb_lbl.setFixedSize(_TABLE_THUMB + 4, _TABLE_THUMB + 4)
            thumb_lbl.setAlignment(Qt.AlignCenter)
            thumb_lbl.setStyleSheet(f"""
                background: {_BG_SUBTLE};
                border: 1px solid {_BORDER};
                border-radius: 8px;
                margin: 4px;
                font-size: 20px;
                color: {_TEXT_MUTED};
            """)
            thumb_lbl.setText("🎨")
            self.table.setCellWidget(r, _COL_THUMB, thumb_lbl)

            xcf = d["first_xcf"]
            if xcf and os.path.exists(xcf):
                watcher.watch(xcf)
                self._xcf_row_map[os.path.normpath(xcf)] = r
                worker = _RowThumbWorker(r, xcf, _TABLE_THUMB)
                worker.done.connect(self._on_row_thumb_ready)
                worker.start()
                self._thumb_workers.append(worker)

            # ── ID ──
            id_item = QTableWidgetItem(str(d["id"]))
            id_item.setData(Qt.UserRole, d["id"])
            id_item.setTextAlignment(Qt.AlignCenter)
            id_item.setForeground(QColor(_TEXT_MUTED))
            self.table.setItem(r, _COL_ID, id_item)

            # ── الاسم ──
            name_item = QTableWidgetItem(d["name"])
            name_item.setData(Qt.UserRole, d["id"])
            f = QFont()
            f.setWeight(QFont.Medium)
            name_item.setFont(f)
            self.table.setItem(r, _COL_NAME, name_item)

            # ── التصنيف ──
            cat_item = QTableWidgetItem(d["category_name"] or "—")
            cat_item.setForeground(QColor(_TEXT_MED))
            self.table.setItem(r, _COL_CATEGORY, cat_item)

            # ── عدد المقاسات ──
            sz    = d["sizes_count"] or 0
            fl_cnt = d["files_count"] or 0

            i_sz = QTableWidgetItem(str(sz))
            i_sz.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, _COL_SIZES, i_sz)

            # ── عدد الملفات ──
            i_fl = QTableWidgetItem(str(fl_cnt))
            i_fl.setTextAlignment(Qt.AlignCenter)
            if fl_cnt > 0 and fl_cnt == sz:
                i_fl.setForeground(QColor(_GREEN))
            elif fl_cnt > 0:
                i_fl.setForeground(QColor(_ORANGE))
            else:
                i_fl.setForeground(QColor(_TEXT_MUTED))
            self.table.setItem(r, _COL_FILES, i_fl)

        shown = self.table.rowCount()
        total = len(fetch_all_designs_summary(self.conn))
        if name_q or cat_id or set_id:
            self.lbl_count.setText(f"{shown} / {total}")
        else:
            self.lbl_count.setText(f"{shown} تصميم")

        if prev_id:
            for r in range(self.table.rowCount()):
                item = self.table.item(r, _COL_ID)
                if item and item.data(Qt.UserRole) == prev_id:
                    self.table.selectRow(r)
                    return

    # ── Thumbnail handlers ──────────────────────────────

    def _on_row_thumb_ready(self, row: int, pixmap):
        self._set_row_thumb(row, pixmap)

    def _on_xcf_changed(self, path: str):
        import os
        norm = os.path.normpath(path)
        row  = self._xcf_row_map.get(norm)
        if row is None or row >= self.table.rowCount():
            return
        worker = _RowThumbWorker(row, path, _TABLE_THUMB)
        worker.done.connect(self._on_row_thumb_ready)
        worker.start()
        self._thumb_workers.append(worker)

    def _set_row_thumb(self, row: int, pixmap):
        if row >= self.table.rowCount():
            return
        widget = self.table.cellWidget(row, _COL_THUMB)
        if not isinstance(widget, QLabel):
            return

        if pixmap and not pixmap.isNull():
            widget.setText("")
            widget.setPixmap(pixmap)
            widget.setStyleSheet(f"""
                background: #1e1b4b;
                border: 1px solid {_BLUE_MED};
                border-radius: 8px;
                margin: 4px;
            """)
        else:
            widget.setText("🎨")

    # ── مساعدات ────────────────────────────────────────

    def _reset_filters(self):
        for w in (self.inp_search, self.cmb_category, self.cmb_set):
            w.blockSignals(True)
        self.inp_search.clear()
        self.cmb_category.setCurrentIndex(0)
        self.cmb_set.setCurrentIndex(0)
        for w in (self.inp_search, self.cmb_category, self.cmb_set):
            w.blockSignals(False)
        self._apply_filter()
        self.set_filter_changed.emit(None)

    def _selected_id(self):
        row  = self.table.currentRow()
        item = self.table.item(row, _COL_ID) if row >= 0 else None
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        did = self._selected_id()
        if did:
            self._panel.load_design(did)
            self.design_selected.emit(did)

    def _new_design(self):
        self.table.clearSelection()
        self._panel.reset()

    def _delete(self):
        did = self._selected_id()
        if did is None:
            QMessageBox.information(self, "تنبيه", "اختر تصميماً أولاً")
            return
        d = fetch_design(self.conn, did)
        if not d:
            return
        if confirm_delete(self, d["name"]):
            delete_design(self.conn, did)
            self._panel.reset()
            self._load()
            self.design_deleted.emit()

    def refresh(self):
        self._load()