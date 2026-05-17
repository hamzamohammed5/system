"""
ui/tabs/design/designs/_designs_categories_panel.py
====================================================
Sidebar تصنيفات التصميمات — مع دعم كامل لتغيير حجم الخط ديناميكياً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QMessageBox, QFrame,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.designs.design_item_categories_repo import (
    fetch_all_item_categories,
    fetch_item_category,
    delete_item_category,
    build_item_category_tree,
    fetch_item_category_descendants,
    count_designs_per_category,
)
from ui.events import bus
from ui.tabs.design.design_styles import get_styles

_SIDEBAR_W = 230

# ── Palette ──────────────────────────────────────────────
_BG          = "#FFFFFF"
_BG_SURFACE  = "#F8F9FB"
_BG_HOVER    = "#F1F4F9"
_BG_SELECTED = "#EEF2FF"
_BORDER      = "#E5E9F0"
_BORDER_MED  = "#CDD3E0"
_TEXT_PRI    = "#1A2035"
_TEXT_SEC    = "#5A6680"
_TEXT_MUT    = "#9BA5BE"
_ACCENT      = "#4F6EF7"
_DANGER      = "#DC2626"
_DANGER_LT   = "#FEF2F2"
_DANGER_BDR  = "#FECACA"
_RADIUS_SM   = "5px"

from .designs_categories._row_and_form import _btn_ss, _CatForm, _CatRow


class DesignsCategoriesPanel(QWidget):
    category_changed = pyqtSignal(object)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._active_id = "ALL"
        self._items     = []
        self._build()
        self._load()
        bus.font_changed.connect(self._on_font_changed)

    def _on_font_changed(self, size: int):
        self._apply_dynamic_styles()

    def _apply_dynamic_styles(self):
        s = get_styles()

        # header
        self._lbl_header.setStyleSheet(
            f"font-size:{s.large}pt; font-weight:700; color:{_TEXT_PRI};"
            "background:transparent; border:none;"
        )
        self._btn_add.setStyleSheet(
            f"QPushButton{{"
            f"  background:{_ACCENT}; color:#fff;"
            f"  border:none; border-radius:{s.normal + 2}px;"
            f"  font-size:{s.large}pt; font-weight:700;"
            f"}}"
            f"QPushButton:hover{{background:#3D5BEF;}}"
        )
        self._inp_search.setStyleSheet(s.input_search())

        self.btn_edit.setStyleSheet(
            s.btn(_BG, _TEXT_SEC, _BORDER_MED, _BG_HOVER)
        )
        self.btn_del.setStyleSheet(
            s.btn(_DANGER_LT, _DANGER, _DANGER_BDR, "#FEE2E2")
        )

    def _build(self):
        s = get_styles()
        self.setFixedWidth(_SIDEBAR_W)
        self.setStyleSheet(
            f"QWidget{{ background:{_BG}; border-left:1px solid {_BORDER}; }}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──────────────────────────────────────
        hdr = QFrame()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet(
            f"QFrame{{ background:{_BG}; border-bottom:1px solid {_BORDER}; }}"
        )
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(14, 0, 10, 0)
        hdr_lay.setSpacing(8)

        self._lbl_header = QLabel("التصنيفات")
        self._lbl_header.setStyleSheet(
            f"font-size:{s.large}pt; font-weight:700; color:{_TEXT_PRI};"
            "background:transparent; border:none;"
        )

        self._btn_add = QPushButton("+")
        self._btn_add.setFixedSize(26, 26)
        self._btn_add.setToolTip("تصنيف جديد")
        self._btn_add.setStyleSheet(
            f"QPushButton{{"
            f"  background:{_ACCENT}; color:#fff;"
            f"  border:none; border-radius:13px;"
            f"  font-size:{s.large}pt; font-weight:700;"
            f"}}"
            f"QPushButton:hover{{background:#3D5BEF;}}"
        )
        self._btn_add.clicked.connect(self._show_add_form)

        hdr_lay.addWidget(self._lbl_header, stretch=1)
        hdr_lay.addWidget(self._btn_add)
        root.addWidget(hdr)

        # ── شريط البحث ──────────────────────────────
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame{{ background:{_BG}; border-bottom:1px solid {_BORDER}; padding:8px 12px; }}"
        )
        sf_lay = QHBoxLayout(search_frame)
        sf_lay.setContentsMargins(0, 6, 0, 6)
        sf_lay.setSpacing(6)

        self._inp_search = QLineEdit()
        self._inp_search.setPlaceholderText("بحث في التصنيفات...")
        self._inp_search.setMinimumHeight(30)
        self._inp_search.setStyleSheet(s.input_search())
        self._inp_search.textChanged.connect(self._on_search)

        self._btn_clear_search = QPushButton("✕")
        self._btn_clear_search.setFixedSize(22, 22)
        self._btn_clear_search.setVisible(False)
        self._btn_clear_search.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;"
            f"color:{_TEXT_MUT};}}"
            f"QPushButton:hover{{color:{_DANGER};}}"
        )
        self._btn_clear_search.clicked.connect(self._clear_search)
        self._inp_search.textChanged.connect(
            lambda t: self._btn_clear_search.setVisible(bool(t))
        )

        sf_lay.addWidget(self._inp_search, stretch=1)
        sf_lay.addWidget(self._btn_clear_search)
        root.addWidget(search_frame)

        # ── قائمة التصنيفات ──────────────────────────
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea{{border:none; background:{_BG};}}"
            "QScrollBar:vertical{"
            f"  background:{_BG_SURFACE}; width:4px; border-radius:2px;"
            "}"
            "QScrollBar::handle:vertical{"
            f"  background:{_BORDER_MED}; border-radius:2px; min-height:20px;"
            "}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{height:0;}"
        )

        self._list_w = QWidget()
        self._list_w.setStyleSheet(f"background:{_BG};")
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, 6, 0, 6)
        self._list_lay.setSpacing(1)
        self._list_lay.addStretch()

        scroll.setWidget(self._list_w)
        root.addWidget(scroll, stretch=1)

        # ── شريط الإجراءات ──────────────────────────
        act = QFrame()
        act.setStyleSheet(
            f"QFrame{{ background:{_BG_SURFACE}; border-top:1px solid {_BORDER}; }}"
        )
        ab = QHBoxLayout(act)
        ab.setContentsMargins(10, 8, 10, 8)
        ab.setSpacing(6)

        self.btn_edit = QPushButton("تعديل")
        self.btn_edit.setMinimumHeight(28)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setStyleSheet(s.btn(_BG, _TEXT_SEC, _BORDER_MED, _BG_HOVER))
        self.btn_edit.clicked.connect(self._show_edit_form)

        self.btn_del = QPushButton("حذف")
        self.btn_del.setMinimumHeight(28)
        self.btn_del.setEnabled(False)
        self.btn_del.setStyleSheet(s.btn(_DANGER_LT, _DANGER, _DANGER_BDR, "#FEE2E2"))
        self.btn_del.clicked.connect(self._delete)

        ab.addWidget(self.btn_edit, stretch=1)
        ab.addWidget(self.btn_del)
        root.addWidget(act)

        # ── فورم مدمج ────────────────────────────────
        self._form = _CatForm(self.conn)
        self._form.setVisible(False)
        self._form.saved.connect(self._on_form_saved)
        self._form.canceled.connect(lambda: self._form.setVisible(False))
        root.addWidget(self._form)

    # ── تحميل التصنيفات ───────────────────────────────────

    def _load(self, query=""):
        for item in self._items:
            self._list_lay.removeWidget(item)
            item.deleteLater()
        self._items = []

        all_row = _CatRow(None, "كل التصميمات", _ACCENT, depth=0)
        all_row.clicked.connect(self._on_clicked)
        all_row.set_selected(self._active_id == "ALL")
        self._list_lay.insertWidget(self._list_lay.count() - 1, all_row)
        self._items.append(all_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_BORDER}; margin:3px 12px;")
        self._list_lay.insertWidget(self._list_lay.count() - 1, sep)

        rows   = fetch_all_item_categories(self.conn)
        tree   = build_item_category_tree(rows)
        counts = count_designs_per_category(self.conn)
        self._add_tree(tree, 0, counts, query.lower())

        has_selection = self._active_id not in ("ALL", None)
        self.btn_edit.setEnabled(has_selection)
        self.btn_del.setEnabled(has_selection)

    def _add_tree(self, nodes, depth, counts, query):
        for node in nodes:
            name_lower = node["name"].lower()
            if query and query not in name_lower and not node["children"]:
                continue

            desc = fetch_item_category_descendants(self.conn, node["id"])
            cnt  = sum(counts.get(d, 0) for d in desc)

            row = _CatRow(node["id"], node["name"], node["color"],
                          count=cnt, depth=depth)
            row.clicked.connect(self._on_clicked)
            row.set_selected(self._active_id == node["id"])
            self._list_lay.insertWidget(self._list_lay.count() - 1, row)
            self._items.append(row)

            if node["children"]:
                self._add_tree(node["children"], depth + 1, counts, query)

    # ── Signal Handlers ────────────────────────────────────

    def _on_search(self, text):
        self._load(query=text.strip())

    def _clear_search(self):
        self._inp_search.clear()

    def _on_clicked(self, cat_id):
        self._active_id = "ALL" if cat_id is None else cat_id
        for item in self._items:
            item.set_selected(item.cat_id == cat_id)
        has = self._active_id not in ("ALL", None)
        self.btn_edit.setEnabled(has)
        self.btn_del.setEnabled(has)
        self.category_changed.emit(cat_id)

    def _show_add_form(self):
        self._form.load_new()
        self._form.setVisible(True)
        self._form.inp_name.setFocus()

    def _show_edit_form(self):
        if self._active_id in ("ALL", None):
            return
        self._form.load_edit(self._active_id)
        self._form.setVisible(True)
        self._form.inp_name.setFocus()

    def _on_form_saved(self):
        self._form.setVisible(False)
        self._load()
        self.category_changed.emit(
            None if self._active_id == "ALL" else self._active_id
        )

    def _delete(self):
        if self._active_id in ("ALL", None):
            return
        cat = fetch_item_category(self.conn, self._active_id)
        if not cat:
            return

        desc   = fetch_item_category_descendants(self.conn, self._active_id)
        counts = count_designs_per_category(self.conn)
        total  = sum(counts.get(d, 0) for d in desc)

        msg = f"حذف تصنيف «{cat['name']}»؟"
        cc  = len(desc) - 1
        if cc:
            msg += f"\n⚠️ {cc} تصنيف فرعي سيُحذف."
        if total:
            msg += f"\n⚠️ {total} تصميم سيفقد تصنيفه."

        if QMessageBox.question(
            self, "تأكيد", msg, QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            for d in sorted(desc, reverse=True):
                delete_item_category(self.conn, d)
            self._active_id = "ALL"
            self._load()
            self.category_changed.emit(None)

    def refresh(self):
        self._load(query=self._inp_search.text().strip())

    def current_category_id(self):
        return None if self._active_id == "ALL" else self._active_id