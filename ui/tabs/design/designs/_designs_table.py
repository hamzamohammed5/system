"""
ui/tabs/design/designs/_designs_table.py
==============================
جدول التصميمات مع فلتر بالاسم + التصنيف + مجموعة المقاسات.
لما تتغير مجموعة المقاسات في الفلتر، signal set_filter_changed بيتبعت
للوحة التفاصيل عشان تفلتر بطاقات المقاسات.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidgetItem,
    QPushButton, QLabel, QLineEdit,
    QMessageBox, QFrame, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

from db.designs.designs_repo import (
    fetch_design, delete_design,
)
from db.designs.designs_sizes_repo import (
    fetch_all_designs_summary,
)
from db.designs.dimension_sets_repo import (
    fetch_all_design_categories, build_category_tree,
    fetch_all_dimension_sets, fetch_category_descendants,
)
from ui.helpers import make_table, danger_button, confirm_delete, buttons_row

from ._design_detail_panel import _DesignDetailPanel

_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GREEN      = "#2e7d32"
_ORANGE     = "#e65100"


def _fetch_designs_filtered(conn, name_q="", category_id=None, set_id=None):
    sql = """
        SELECT d.id, d.name, d.category_id, d.notes,
               d.created_at, d.updated_at,
               dc.name                                    AS category_name,
               COUNT(DISTINCT ds.id)                      AS sizes_count,
               SUM(CASE WHEN ds.xcf_path IS NOT NULL
                             AND ds.xcf_path != ''
                        THEN 1 ELSE 0 END)                AS files_count
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


class _DesignsTable(QWidget):
    """
    Signals:
      design_selected(int)       — اختيار تصميم
      design_deleted()           — بعد حذف
      set_filter_changed(object) — تغيير فلتر المجموعة (int | None)
    """

    design_selected    = pyqtSignal(int)
    design_deleted     = pyqtSignal()
    set_filter_changed = pyqtSignal(object)

    def __init__(self, conn, detail_panel, parent=None):
        super().__init__(parent)
        self.conn   = conn
        self._panel = detail_panel
        self._build()
        self._load()

    # ──────────────────────────────────────────────────────
    # بناء الواجهة
    # ──────────────────────────────────────────────────────

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── شريط الفلتر ──
        ff = QFrame()
        ff.setStyleSheet(f"""
            QFrame {{
                background: {_BLUE_LIGHT};
                border: 1px solid {_BLUE_MID};
                border-radius: 6px;
            }}
        """)
        fl = QVBoxLayout(ff)
        fl.setContentsMargins(8, 8, 8, 8)
        fl.setSpacing(6)

        # صف 1: بحث + زر جديد
        r1 = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث بالاسم...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            f"color:{_BLUE};font-size:10px;font-weight:bold;"
            "background:transparent;border:none;"
        )

        btn_new = QPushButton("➕  تصميم جديد")
        btn_new.setMinimumHeight(28)
        btn_new.setStyleSheet(f"""
            QPushButton {{
                background:{_BLUE}; color:white; border:none;
                border-radius:4px; padding:2px 10px;
                font-weight:bold; font-size:11px;
            }}
            QPushButton:hover {{ background:#0d47a1; }}
        """)
        btn_new.clicked.connect(self._new_design)
        r1.addWidget(self.inp_search, stretch=1)
        r1.addWidget(self.lbl_count)
        r1.addWidget(btn_new)
        fl.addLayout(r1)

        # صف 2: فلتر تصنيف + فلتر مجموعة + ريست
        r2 = QHBoxLayout()
        r2.setSpacing(6)

        for icon in ("📁", "📐"):
            lbl = QLabel(icon)
            lbl.setFixedWidth(18)
            lbl.setStyleSheet("background:transparent;border:none;font-size:13px;")
            r2.addWidget(lbl)
            if icon == "📁":
                self.cmb_category = QComboBox()
                self.cmb_category.setMinimumHeight(28)
                self.cmb_category.setMinimumWidth(130)
                self.cmb_category.setStyleSheet(self._combo_ss())
                self.cmb_category.currentIndexChanged.connect(self._apply_filter)
                r2.addWidget(self.cmb_category, stretch=1)
            else:
                self.cmb_set = QComboBox()
                self.cmb_set.setMinimumHeight(28)
                self.cmb_set.setMinimumWidth(130)
                self.cmb_set.setStyleSheet(self._combo_ss())
                self.cmb_set.currentIndexChanged.connect(self._on_set_changed)
                r2.addWidget(self.cmb_set, stretch=1)

        btn_rst = QPushButton("↺")
        btn_rst.setFixedSize(28, 28)
        btn_rst.setToolTip("مسح الفلاتر")
        btn_rst.setStyleSheet(f"""
            QPushButton {{
                background:white; color:{_BLUE};
                border:1px solid {_BLUE_MID}; border-radius:4px; font-size:14px;
            }}
            QPushButton:hover {{ background:{_BLUE_MID}; }}
        """)
        btn_rst.clicked.connect(self._reset_filters)
        r2.addWidget(btn_rst)
        fl.addLayout(r2)

        root.addWidget(ff)

        # ── جدول ──
        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "المقاسات", "الملفات"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 110)
        self.table.setColumnWidth(3, 65)
        self.table.setColumnWidth(4, 65)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(self._on_select)
        root.addWidget(self.table)

        btn_del = danger_button("🗑️  حذف")
        btn_del.setMinimumHeight(28)
        btn_del.clicked.connect(self._delete)
        root.addLayout(buttons_row(btn_del))

        self._reload_category_combo()
        self._reload_set_combo()

    @staticmethod
    def _combo_ss():
        return f"""
            QComboBox {{
                background:white; border:1px solid {_BLUE_MID};
                border-radius:4px; padding:2px 6px; font-size:11px;
            }}
            QComboBox:focus {{ border-color:{_BLUE}; }}
            QComboBox::drop-down {{ border:none; }}
        """

    # ──────────────────────────────────────────────────────
    # Combo loaders
    # ──────────────────────────────────────────────────────

    def _reload_category_combo(self):
        prev = self.cmb_category.currentData()
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("— كل التصنيفات —", None)
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
        self.cmb_set.addItem("— كل المجموعات —", None)
        for ds in fetch_all_dimension_sets(self.conn):
            self.cmb_set.addItem(ds["name"], ds["id"])
        for i in range(self.cmb_set.count()):
            if self.cmb_set.itemData(i) == prev:
                self.cmb_set.setCurrentIndex(i)
                break
        self.cmb_set.blockSignals(False)

    # ──────────────────────────────────────────────────────
    # فلترة
    # ──────────────────────────────────────────────────────

    def _load(self):
        self._reload_category_combo()
        self._reload_set_combo()
        self._apply_filter()

    def _on_set_changed(self):
        """تغيير فلتر المجموعة — فلتر الجدول + إبلاغ لوحة التفاصيل."""
        self._apply_filter()
        self.set_filter_changed.emit(self.cmb_set.currentData())

    def _apply_filter(self):
        name_q  = self.inp_search.text().strip()
        cat_id  = self.cmb_category.currentData()
        set_id  = self.cmb_set.currentData()
        prev_id = self._selected_id()

        rows = _fetch_designs_filtered(self.conn, name_q, cat_id, set_id)

        self.table.setRowCount(0)
        for d in rows:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(d["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(d["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(d["category_name"] or "—"))

            sz = d["sizes_count"] or 0
            fl = d["files_count"] or 0

            i_sz = QTableWidgetItem(str(sz))
            i_sz.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(r, 3, i_sz)

            i_fl = QTableWidgetItem(str(fl))
            i_fl.setTextAlignment(Qt.AlignCenter)
            if fl == sz and sz > 0:
                i_fl.setForeground(QColor(_GREEN))
            elif fl > 0:
                i_fl.setForeground(QColor(_ORANGE))
            self.table.setItem(r, 4, i_fl)

            self.table.item(r, 0).setData(Qt.UserRole, d["id"])

        shown = self.table.rowCount()
        if name_q or cat_id or set_id:
            total = len(fetch_all_designs_summary(self.conn))
            self.lbl_count.setText(f"({shown}/{total})")
        else:
            self.lbl_count.setText(f"({shown})")

        if prev_id:
            for r in range(self.table.rowCount()):
                if self.table.item(r, 0).data(Qt.UserRole) == prev_id:
                    self.table.selectRow(r)
                    return

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

    # ──────────────────────────────────────────────────────
    # تفاعل الجدول
    # ──────────────────────────────────────────────────────

    def _selected_id(self):
        row  = self.table.currentRow()
        item = self.table.item(row, 0) if row >= 0 else None
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