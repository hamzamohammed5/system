"""
ui/tabs/design/designs/_designs_categories_panel.py
====================================================
Sidebar تصنيفات التصميمات — تصميم محسّن v3.

التحسينات:
  - ألوان متناسقة وأكثر هدوءاً
  - Typography أوضح مع hierarchy أحسن
  - أيقونات Tabler بدل الإيموجي
  - شريط بحث أنظف
  - Hover/selected states أجمل
  - فورم مدمج inline بشكل أسلس
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QColorDialog, QMessageBox, QFrame,
    QScrollArea, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from db.designs.design_item_categories_repo import (
    fetch_all_item_categories,
    fetch_item_category,
    insert_item_category,
    update_item_category,
    delete_item_category,
    build_item_category_tree,
    fetch_item_category_descendants,
    count_designs_per_category,
)

_SIDEBAR_W = 230

# ── Palette — هادئ ومتناسق ──
_BG          = "#FFFFFF"
_BG_SURFACE  = "#F8F9FB"
_BG_HOVER    = "#F1F4F9"
_BG_SELECTED = "#EEF2FF"
_BORDER      = "#E5E9F0"
_BORDER_MED  = "#CDD3E0"

_TEXT_PRI    = "#1A2035"
_TEXT_SEC    = "#5A6680"
_TEXT_MUT    = "#9BA5BE"

_ACCENT      = "#4F6EF7"           # أزرق بنفسجي
_ACCENT_LT   = "#EEF2FF"
_ACCENT_BDR  = "#C7D2FE"

_SUCCESS     = "#16A34A"
_DANGER      = "#DC2626"
_DANGER_LT   = "#FEF2F2"
_DANGER_BDR  = "#FECACA"

_RADIUS      = "8px"
_RADIUS_SM   = "5px"


def _btn_ss(bg, fg, bdr, hover_bg, height=28):
    return (
        f"QPushButton{{"
        f"  background:{bg}; color:{fg};"
        f"  border:1px solid {bdr}; border-radius:{_RADIUS_SM};"
        f"  padding:0 12px; font-size:12px; min-height:{height}px;"
        f"}}"
        f"QPushButton:hover{{background:{hover_bg};}}"
        f"QPushButton:pressed{{opacity:0.85;}}"
    )


# ══════════════════════════════════════════════════════════
# عنصر تصنيف واحد
# ══════════════════════════════════════════════════════════

class _CatRow(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self, cat_id, name, color, count=0, depth=0, parent=None):
        super().__init__(parent)
        self.cat_id    = cat_id
        self._selected = False
        self._color    = color or _ACCENT
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(12 + depth * 16, 0, 10, 0)
        lay.setSpacing(8)

        # خط ربط للعناصر الفرعية
        if depth > 0:
            indent_line = QFrame()
            indent_line.setFixedWidth(2)
            indent_line.setFixedHeight(16)
            indent_line.setStyleSheet(
                f"background:{_BORDER_MED}; border-radius:1px;"
            )
            lay.addWidget(indent_line)

        # نقطة اللون
        self._dot = QLabel("●")
        self._dot.setFixedWidth(10)
        self._dot.setStyleSheet(
            f"color:{self._color}; font-size:8px;"
            "background:transparent; border:none;"
        )

        # اسم التصنيف
        self._lbl = QLabel(name)
        font = QFont()
        font.setPointSize(10)
        self._lbl.setFont(font)
        self._lbl.setStyleSheet(
            f"color:{_TEXT_PRI}; background:transparent; border:none;"
        )

        # عداد التصميمات
        self._badge = QLabel(str(count) if count else "")
        self._badge.setFixedSize(24, 18)
        self._badge.setAlignment(Qt.AlignCenter)
        font_b = QFont()
        font_b.setPointSize(8)
        self._badge.setFont(font_b)
        self._badge.setStyleSheet(
            f"color:{_TEXT_MUT}; font-weight:500;"
            f"background:{_BG_SURFACE}; border:1px solid {_BORDER};"
            f"border-radius:9px;"
        )
        self._badge.setVisible(bool(count))

        lay.addWidget(self._dot)
        lay.addWidget(self._lbl, stretch=1)
        lay.addWidget(self._badge)

        self._update_style()

    def set_selected(self, s: bool):
        self._selected = s
        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(
                f"QFrame{{"
                f"  background:{_BG_SELECTED};"
                f"  border-left:3px solid {_ACCENT};"
                f"  border-radius:0 {_RADIUS_SM} {_RADIUS_SM} 0;"
                f"}}"
            )
            self._lbl.setStyleSheet(
                f"color:{_ACCENT}; font-weight:600;"
                "background:transparent; border:none;"
            )
            self._dot.setStyleSheet(
                f"color:{_ACCENT}; font-size:8px;"
                "background:transparent; border:none;"
            )
        else:
            self.setStyleSheet(
                "QFrame{"
                "  background:transparent;"
                f"  border-left:3px solid transparent;"
                f"  border-radius:0 {_RADIUS_SM} {_RADIUS_SM} 0;"
                "}"
                f"QFrame:hover{{background:{_BG_HOVER};}}"
            )
            self._lbl.setStyleSheet(
                f"color:{_TEXT_PRI}; font-weight:400;"
                "background:transparent; border:none;"
            )
            self._dot.setStyleSheet(
                f"color:{self._color}; font-size:8px;"
                "background:transparent; border:none;"
            )

    def mousePressEvent(self, e):
        self.clicked.emit(self.cat_id)
        super().mousePressEvent(e)


# ══════════════════════════════════════════════════════════
# فورم إضافة / تعديل — تصميم نظيف
# ══════════════════════════════════════════════════════════

class _CatForm(QWidget):
    saved    = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._color      = _ACCENT
        self._build()

    def _build(self):
        self.setStyleSheet(
            f"QWidget{{"
            f"  background:{_BG_SURFACE};"
            f"  border-top:1px solid {_BORDER};"
            f"}}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(8)

        # عنوان الفورم
        self._mode_lbl = QLabel("تصنيف جديد")
        self._mode_lbl.setStyleSheet(
            f"font-size:11px; font-weight:700; color:{_ACCENT};"
            "background:transparent; border:none;"
            "text-transform:uppercase; letter-spacing:0.5px;"
        )
        lay.addWidget(self._mode_lbl)

        # حقل الاسم
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم التصنيف...")
        self.inp_name.setMinimumHeight(32)
        self.inp_name.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {_BORDER_MED};
                border-radius: {_RADIUS_SM};
                padding: 0 10px;
                font-size: 12px;
                background: {_BG};
                color: {_TEXT_PRI};
            }}
            QLineEdit:focus {{
                border-color: {_ACCENT};
                background: {_BG};
            }}
        """)
        lay.addWidget(self.inp_name)

        # التصنيف الأب
        lbl_p = QLabel("تابع لـ:")
        lbl_p.setStyleSheet(
            f"font-size:11px; color:{_TEXT_SEC}; background:transparent; border:none;"
        )
        lay.addWidget(lbl_p)

        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(30)
        self.cmb_parent.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {_BORDER_MED};
                border-radius: {_RADIUS_SM};
                padding: 0 8px;
                font-size: 11px;
                background: {_BG};
                color: {_TEXT_PRI};
            }}
            QComboBox:focus {{ border-color: {_ACCENT}; }}
            QComboBox::drop-down {{ border: none; width: 16px; }}
        """)
        lay.addWidget(self.cmb_parent)

        # صف اللون
        crow = QHBoxLayout()
        crow.setSpacing(8)

        lbl_c = QLabel("اللون:")
        lbl_c.setStyleSheet(
            f"font-size:11px; color:{_TEXT_SEC}; background:transparent; border:none;"
        )

        self._color_preview = QFrame()
        self._color_preview.setFixedSize(24, 24)
        self._update_color_preview()

        btn_c = QPushButton("اختر لون")
        btn_c.setMinimumHeight(26)
        btn_c.setStyleSheet(_btn_ss(_BG, _TEXT_SEC, _BORDER_MED, _BG_HOVER))
        btn_c.clicked.connect(self._pick_color)

        crow.addWidget(lbl_c)
        crow.addWidget(self._color_preview)
        crow.addWidget(btn_c)
        crow.addStretch()
        lay.addLayout(crow)

        # أزرار
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{_BORDER}; margin:2px 0;")
        lay.addWidget(sep)

        brow = QHBoxLayout()
        brow.setSpacing(6)

        self.btn_save = QPushButton("حفظ")
        self.btn_save.setMinimumHeight(30)
        self.btn_save.setStyleSheet(_btn_ss(_ACCENT, "#fff", _ACCENT, "#3D5BEF", 30))
        self.btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(30)
        btn_cancel.setStyleSheet(_btn_ss(_BG, _TEXT_SEC, _BORDER_MED, _BG_HOVER, 30))
        btn_cancel.clicked.connect(self.canceled.emit)

        brow.addWidget(btn_cancel)
        brow.addWidget(self.btn_save, stretch=1)
        lay.addLayout(brow)

    def _update_color_preview(self):
        self._color_preview.setStyleSheet(
            f"background:{self._color}; border-radius:6px;"
            f"border:1px solid {_BORDER_MED};"
        )

    def _reload_parent(self, exclude_id=None):
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem("— بدون أب —", None)
        rows = fetch_all_item_categories(self.conn)
        tree = build_item_category_tree(rows)
        excl = set()
        if exclude_id:
            excl = set(fetch_item_category_descendants(self.conn, exclude_id))
        self._add_nodes(tree, 0, excl)
        self.cmb_parent.blockSignals(False)

    def _add_nodes(self, nodes, depth, excl):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for n in nodes:
            if n["id"] in excl:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{n['name']}", n["id"])
            if n["children"]:
                self._add_nodes(n["children"], depth + 1, excl)

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self)
        if col.isValid():
            self._color = col.name()
            self._update_color_preview()

    def load_new(self):
        self._editing_id = None
        self._color = _ACCENT
        self.inp_name.clear()
        self._update_color_preview()
        self._mode_lbl.setText("تصنيف جديد")
        self._reload_parent()

    def load_edit(self, cat_id):
        cat = fetch_item_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self._color = cat["color"] or _ACCENT
        self.inp_name.setText(cat["name"])
        self._update_color_preview()
        self._mode_lbl.setText(f"تعديل: {cat['name']}")
        self._reload_parent(exclude_id=cat_id)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            self.inp_name.setFocus()
            return
        pid = self.cmb_parent.currentData()
        try:
            if self._editing_id:
                update_item_category(self.conn, self._editing_id, name, self._color, pid)
            else:
                insert_item_category(self.conn, name, self._color, pid)
            self.saved.emit()
        except ValueError as e:
            QMessageBox.warning(self, "خطأ", str(e))


# ══════════════════════════════════════════════════════════
# Sidebar الرئيسي
# ══════════════════════════════════════════════════════════

class DesignsCategoriesPanel(QWidget):
    category_changed = pyqtSignal(object)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._active_id = "ALL"
        self._items     = []
        self._build()
        self._load()

    def _build(self):
        self.setFixedWidth(_SIDEBAR_W)
        self.setStyleSheet(
            f"QWidget{{"
            f"  background:{_BG};"
            f"  border-left: 1px solid {_BORDER};"
            f"}}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──────────────────────────────────
        hdr = QFrame()
        hdr.setFixedHeight(52)
        hdr.setStyleSheet(
            f"QFrame{{"
            f"  background:{_BG};"
            f"  border-bottom:1px solid {_BORDER};"
            f"}}"
        )
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(14, 0, 10, 0)
        hdr_lay.setSpacing(8)

        lbl = QLabel("التصنيفات")
        lbl.setStyleSheet(
            f"font-size:13px; font-weight:700; color:{_TEXT_PRI};"
            "background:transparent; border:none;"
        )

        self._btn_add = QPushButton("+")
        self._btn_add.setFixedSize(26, 26)
        self._btn_add.setToolTip("تصنيف جديد")
        self._btn_add.setStyleSheet(
            f"QPushButton{{"
            f"  background:{_ACCENT}; color:#fff;"
            f"  border:none; border-radius:13px;"
            f"  font-size:16px; font-weight:700; line-height:1;"
            f"}}"
            f"QPushButton:hover{{background:#3D5BEF;}}"
        )
        self._btn_add.clicked.connect(self._show_add_form)

        hdr_lay.addWidget(lbl, stretch=1)
        hdr_lay.addWidget(self._btn_add)
        root.addWidget(hdr)

        # ── شريط البحث ──────────────────────────
        search_frame = QFrame()
        search_frame.setStyleSheet(
            f"QFrame{{"
            f"  background:{_BG};"
            f"  border-bottom:1px solid {_BORDER};"
            f"  padding:8px 12px;"
            f"}}"
        )
        sf_lay = QHBoxLayout(search_frame)
        sf_lay.setContentsMargins(0, 6, 0, 6)
        sf_lay.setSpacing(6)

        self._inp_search = QLineEdit()
        self._inp_search.setPlaceholderText("بحث في التصنيفات...")
        self._inp_search.setMinimumHeight(30)
        self._inp_search.setStyleSheet(f"""
            QLineEdit {{
                background: {_BG_SURFACE};
                border: 1px solid {_BORDER};
                border-radius: {_RADIUS_SM};
                padding: 0 10px 0 10px;
                font-size: 11px;
                color: {_TEXT_PRI};
            }}
            QLineEdit:focus {{
                border-color: {_ACCENT};
                background: {_BG};
            }}
        """)
        self._inp_search.textChanged.connect(self._on_search)

        # زر مسح البحث
        self._btn_clear_search = QPushButton("✕")
        self._btn_clear_search.setFixedSize(22, 22)
        self._btn_clear_search.setVisible(False)
        self._btn_clear_search.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;"
            f"color:{_TEXT_MUT};font-size:10px;}}"
            f"QPushButton:hover{{color:{_DANGER};}}"
        )
        self._btn_clear_search.clicked.connect(self._clear_search)
        self._inp_search.textChanged.connect(
            lambda t: self._btn_clear_search.setVisible(bool(t))
        )

        sf_lay.addWidget(self._inp_search, stretch=1)
        sf_lay.addWidget(self._btn_clear_search)
        root.addWidget(search_frame)

        # ── قائمة التصنيفات ──────────────────────
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

        # ── شريط الإجراءات ──────────────────────
        act = QFrame()
        act.setStyleSheet(
            f"QFrame{{"
            f"  background:{_BG_SURFACE};"
            f"  border-top:1px solid {_BORDER};"
            f"}}"
        )
        ab = QHBoxLayout(act)
        ab.setContentsMargins(10, 8, 10, 8)
        ab.setSpacing(6)

        self.btn_edit = QPushButton("تعديل")
        self.btn_edit.setMinimumHeight(28)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setStyleSheet(
            _btn_ss(_BG, _TEXT_SEC, _BORDER_MED, _BG_HOVER)
        )
        self.btn_edit.clicked.connect(self._show_edit_form)

        self.btn_del = QPushButton("حذف")
        self.btn_del.setMinimumHeight(28)
        self.btn_del.setEnabled(False)
        self.btn_del.setStyleSheet(
            _btn_ss(_DANGER_LT, _DANGER, _DANGER_BDR, "#FEE2E2")
        )
        self.btn_del.clicked.connect(self._delete)

        ab.addWidget(self.btn_edit, stretch=1)
        ab.addWidget(self.btn_del)
        root.addWidget(act)

        # ── فورم مدمج ────────────────────────────
        self._form = _CatForm(self.conn)
        self._form.setVisible(False)
        self._form.saved.connect(self._on_form_saved)
        self._form.canceled.connect(lambda: self._form.setVisible(False))
        root.addWidget(self._form)

    # ── تحميل وعرض التصنيفات ──────────────────────────────

    def _load(self, query=""):
        for item in self._items:
            self._list_lay.removeWidget(item)
            item.deleteLater()
        self._items = []

        # عنصر "الكل"
        all_row = _CatRow(None, "كل التصميمات", _ACCENT, depth=0)
        all_row.clicked.connect(self._on_clicked)
        all_row.set_selected(self._active_id == "ALL")
        self._list_lay.insertWidget(self._list_lay.count() - 1, all_row)
        self._items.append(all_row)

        # فاصل خفيف
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_BORDER}; margin:3px 12px;")
        self._list_lay.insertWidget(self._list_lay.count() - 1, sep)

        rows   = fetch_all_item_categories(self.conn)
        tree   = build_item_category_tree(rows)
        counts = count_designs_per_category(self.conn)
        self._add_tree(tree, 0, counts, query.lower())

        # تفعيل/تعطيل الأزرار
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

            row = _CatRow(
                node["id"], node["name"], node["color"],
                count=cnt, depth=depth
            )
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
            self, "تأكيد", msg,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            for d in sorted(desc, reverse=True):
                delete_item_category(self.conn, d)
            self._active_id = "ALL"
            self._load()
            self.category_changed.emit(None)

    # ── API خارجي ──────────────────────────────────────────

    def refresh(self):
        self._load(query=self._inp_search.text().strip())

    def current_category_id(self):
        return None if self._active_id == "ALL" else self._active_id