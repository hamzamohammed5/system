"""
ui/tabs/design/designs/_designs_categories_panel.py
====================================================
Sidebar تصنيفات التصميمات — تصميم محسّن.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QColorDialog, QMessageBox, QFrame,
    QScrollArea, QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor

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

_SIDEBAR_W = 220

# ── palette ──
_BG         = "#ffffff"
_BG2        = "#f8fafc"
_BG_HOVER   = "#f1f5f9"
_BORDER     = "#e2e8f0"
_BORDER2    = "#cbd5e1"
_TEXT       = "#0f172a"
_TEXT2      = "#475569"
_TEXT3      = "#94a3b8"
_PURPLE     = "#7c3aed"
_PURPLE_LT  = "#f5f3ff"
_PURPLE_MD  = "#ddd6fe"
_RED        = "#dc2626"
_RED_LT     = "#fef2f2"


def _ss_btn(bg, fg, border, hbg):
    return (
        f"QPushButton{{background:{bg};color:{fg};border:1px solid {border};"
        f"border-radius:6px;padding:4px 10px;font-size:11px;}}"
        f"QPushButton:hover{{background:{hbg};}}"
    )


# ══════════════════════════════════════════════════════════
# عنصر تصنيف
# ══════════════════════════════════════════════════════════

class _CatRow(QFrame):
    clicked = pyqtSignal(object)

    def __init__(self, cat_id, name, color, count=0, depth=0, parent=None):
        super().__init__(parent)
        self.cat_id    = cat_id
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(34)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10 + depth * 14, 3, 10, 3)
        lay.setSpacing(7)

        # نقطة اللون
        self._dot = QLabel("●")
        self._dot.setFixedWidth(12)
        self._dot.setStyleSheet(
            f"color:{color or _PURPLE};font-size:9px;"
            "background:transparent;border:none;"
        )

        self._lbl = QLabel(name)
        self._lbl.setStyleSheet(
            f"font-size:12px;color:{_TEXT};"
            "background:transparent;border:none;"
        )

        self._badge = QLabel(str(count) if count else "")
        self._badge.setFixedWidth(24)
        self._badge.setAlignment(Qt.AlignCenter)
        self._badge.setStyleSheet(
            f"color:{_TEXT3};font-size:10px;"
            f"background:{_BG2};border:1px solid {_BORDER};"
            "border-radius:9px;padding:0 3px;"
        )
        self._badge.setVisible(bool(count))

        lay.addWidget(self._dot)
        lay.addWidget(self._lbl, stretch=1)
        lay.addWidget(self._badge)
        self._update_style()

    def set_selected(self, s):
        self._selected = s
        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(
                f"QFrame{{background:{_PURPLE_LT};"
                f"border-left:3px solid {_PURPLE};border-radius:6px;}}"
            )
            self._lbl.setStyleSheet(
                f"font-size:12px;color:{_PURPLE};font-weight:600;"
                "background:transparent;border:none;"
            )
        else:
            self.setStyleSheet(
                "QFrame{background:transparent;"
                "border-left:3px solid transparent;border-radius:6px;}"
                f"QFrame:hover{{background:{_BG_HOVER};}}"
            )
            self._lbl.setStyleSheet(
                f"font-size:12px;color:{_TEXT};"
                "background:transparent;border:none;"
            )

    def mousePressEvent(self, e):
        self.clicked.emit(self.cat_id)
        super().mousePressEvent(e)


# ══════════════════════════════════════════════════════════
# فورم إضافة / تعديل
# ══════════════════════════════════════════════════════════

class _CatForm(QWidget):
    saved    = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._color      = _PURPLE
        self._build()

    def _build(self):
        self.setStyleSheet(
            f"QWidget{{background:{_BG2};border-top:1px solid {_BORDER};}}"
        )
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(7)

        self._mode_lbl = QLabel("تصنيف جديد")
        self._mode_lbl.setStyleSheet(
            f"font-size:11px;font-weight:600;color:{_PURPLE};"
            "background:transparent;border:none;"
        )
        lay.addWidget(self._mode_lbl)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم التصنيف...")
        self.inp_name.setMinimumHeight(30)
        self.inp_name.setStyleSheet(
            f"QLineEdit{{border:1px solid {_BORDER2};border-radius:6px;"
            f"padding:3px 8px;font-size:11px;background:{_BG};}}"
            f"QLineEdit:focus{{border-color:{_PURPLE};}}"
        )
        lay.addWidget(self.inp_name)

        lbl_p = QLabel("تابع لـ:")
        lbl_p.setStyleSheet(
            f"font-size:11px;color:{_TEXT2};background:transparent;border:none;"
        )
        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(28)
        self.cmb_parent.setStyleSheet(
            f"QComboBox{{border:1px solid {_BORDER2};border-radius:6px;"
            f"padding:2px 8px;font-size:11px;background:{_BG};}}"
            f"QComboBox:focus{{border-color:{_PURPLE};}}"
            "QComboBox::drop-down{border:none;}"
        )
        lay.addWidget(lbl_p)
        lay.addWidget(self.cmb_parent)

        # لون
        crow = QHBoxLayout()
        crow.setSpacing(6)
        lbl_c = QLabel("اللون:")
        lbl_c.setStyleSheet(
            f"font-size:11px;color:{_TEXT2};background:transparent;border:none;"
        )
        self._cdot = QLabel("●●●")
        self._cdot.setStyleSheet(
            f"color:{self._color};font-size:13px;"
            "background:transparent;border:none;"
        )
        btn_c = QPushButton("اختر")
        btn_c.setMinimumHeight(26)
        btn_c.setStyleSheet(_ss_btn(_BG, _TEXT2, _BORDER2, _BG_HOVER))
        btn_c.clicked.connect(self._pick_color)
        crow.addWidget(lbl_c)
        crow.addWidget(self._cdot)
        crow.addStretch()
        crow.addWidget(btn_c)
        lay.addLayout(crow)

        # أزرار
        brow = QHBoxLayout()
        brow.setSpacing(6)
        self.btn_save = QPushButton("💾  حفظ")
        self.btn_save.setMinimumHeight(28)
        self.btn_save.setStyleSheet(_ss_btn(_PURPLE, "#fff", _PURPLE, "#6d28d9"))
        self.btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(28)
        btn_cancel.setStyleSheet(_ss_btn(_BG, _TEXT2, _BORDER2, _BG_HOVER))
        btn_cancel.clicked.connect(self.canceled.emit)

        brow.addWidget(self.btn_save, stretch=1)
        brow.addWidget(btn_cancel)
        lay.addLayout(brow)

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
            self._cdot.setStyleSheet(
                f"color:{self._color};font-size:13px;"
                "background:transparent;border:none;"
            )

    def load_new(self):
        self._editing_id = None
        self._color = _PURPLE
        self.inp_name.clear()
        self._cdot.setStyleSheet(
            f"color:{self._color};font-size:13px;"
            "background:transparent;border:none;"
        )
        self._mode_lbl.setText("تصنيف جديد")
        self._reload_parent()

    def load_edit(self, cat_id):
        cat = fetch_item_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self._color = cat["color"] or _PURPLE
        self.inp_name.setText(cat["name"])
        self._cdot.setStyleSheet(
            f"color:{self._color};font-size:13px;"
            "background:transparent;border:none;"
        )
        self._mode_lbl.setText(f"تعديل: {cat['name']}")
        self._reload_parent(exclude_id=cat_id)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
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
            f"QWidget{{background:{_BG};"
            f"border-left:1px solid {_BORDER};}}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──
        hdr = QFrame()
        hdr.setStyleSheet(
            f"QFrame{{background:{_BG2};"
            f"border-bottom:1px solid {_BORDER};}}"
        )
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 10, 10, 10)
        hdr_lay.setSpacing(8)

        title_row = QHBoxLayout()
        lbl = QLabel("🏷  التصنيفات")
        lbl.setStyleSheet(
            f"font-size:12px;font-weight:600;color:{_TEXT};"
            "background:transparent;border:none;"
        )
        self._btn_add = QPushButton("+")
        self._btn_add.setFixedSize(24, 24)
        self._btn_add.setToolTip("تصنيف جديد")
        self._btn_add.setStyleSheet(
            f"QPushButton{{background:{_PURPLE};color:#fff;border:none;"
            "border-radius:12px;font-size:15px;font-weight:bold;}}"
            "QPushButton:hover{background:#6d28d9;}"
        )
        self._btn_add.clicked.connect(self._show_add_form)
        title_row.addWidget(lbl, stretch=1)
        title_row.addWidget(self._btn_add)
        hdr_lay.addLayout(title_row)

        # بحث
        search_row = QHBoxLayout()
        search_row.setSpacing(5)
        search_row.setContentsMargins(0, 0, 0, 0)
        lbl_s = QLabel("🔍")
        lbl_s.setStyleSheet("background:transparent;border:none;font-size:12px;")
        self._inp_search = QLineEdit()
        self._inp_search.setPlaceholderText("بحث...")
        self._inp_search.setMinimumHeight(26)
        self._inp_search.setStyleSheet(
            f"QLineEdit{{border:1px solid {_BORDER};border-radius:5px;"
            f"padding:2px 6px;font-size:11px;background:{_BG};}}"
            f"QLineEdit:focus{{border-color:{_PURPLE};}}"
        )
        self._inp_search.textChanged.connect(self._on_search)
        search_row.addWidget(lbl_s)
        search_row.addWidget(self._inp_search)
        hdr_lay.addLayout(search_row)

        root.addWidget(hdr)

        # ── قائمة ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea{{border:none;background:{_BG};}}"
            "QScrollBar:vertical{background:#f0f0f0;width:4px;border-radius:2px;}"
            "QScrollBar::handle:vertical{background:#c5cae9;border-radius:2px;min-height:20px;}"
            "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
        )
        self._list_w = QWidget()
        self._list_w.setStyleSheet(f"background:{_BG};")
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(8, 8, 8, 8)
        self._list_lay.setSpacing(1)
        self._list_lay.addStretch()
        scroll.setWidget(self._list_w)
        root.addWidget(scroll, stretch=1)

        # ── شريط أزرار ──
        act = QFrame()
        act.setStyleSheet(
            f"QFrame{{background:{_BG2};border-top:1px solid {_BORDER};}}"
        )
        ab = QHBoxLayout(act)
        ab.setContentsMargins(8, 6, 8, 6)
        ab.setSpacing(6)

        self.btn_edit = QPushButton("✏️  تعديل")
        self.btn_edit.setMinimumHeight(26)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setStyleSheet(_ss_btn(_BG, _TEXT2, _BORDER2, _BG_HOVER))
        self.btn_edit.clicked.connect(self._show_edit_form)

        self.btn_del = QPushButton("🗑️")
        self.btn_del.setFixedSize(28, 26)
        self.btn_del.setEnabled(False)
        self.btn_del.setStyleSheet(_ss_btn(_RED_LT, _RED, "#fca5a5", "#fee2e2"))
        self.btn_del.clicked.connect(self._delete)

        ab.addWidget(self.btn_edit, stretch=1)
        ab.addWidget(self.btn_del)
        root.addWidget(act)

        # ── فورم مدمج ──
        self._form = _CatForm(self.conn)
        self._form.setVisible(False)
        self._form.saved.connect(self._on_form_saved)
        self._form.canceled.connect(lambda: self._form.setVisible(False))
        root.addWidget(self._form)

    def _load(self, query=""):
        for item in self._items:
            self._list_lay.removeWidget(item)
            item.deleteLater()
        self._items = []

        # "الكل"
        all_item = _CatRow(None, "🎨  كل التصميمات", _PURPLE, depth=0)
        all_item.clicked.connect(self._on_clicked)
        all_item.set_selected(self._active_id == "ALL")
        self._list_lay.insertWidget(self._list_lay.count() - 1, all_item)
        self._items.append(all_item)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{_BORDER};margin:3px 2px;")
        self._list_lay.insertWidget(self._list_lay.count() - 1, sep)

        rows   = fetch_all_item_categories(self.conn)
        tree   = build_item_category_tree(rows)
        counts = count_designs_per_category(self.conn)
        self._add_tree(tree, 0, counts, query.lower())

        has = self._active_id not in ("ALL", None)
        self.btn_edit.setEnabled(has)
        self.btn_del.setEnabled(has)

    def _add_tree(self, nodes, depth, counts, query):
        for node in nodes:
            if query and query not in node["name"].lower():
                if not node["children"]:
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

    def _on_search(self, text):
        self._load(query=text)

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
        msg    = f"حذف تصنيف «{cat['name']}»؟"
        cc     = len(desc) - 1
        if cc:
            msg += f"\n⚠️ {cc} تصنيف فرعي سيُحذف."
        if total:
            msg += f"\n⚠️ {total} تصميم سيفقد تصنيفه."
        if QMessageBox.question(self, "تأكيد", msg,
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            for d in sorted(desc, reverse=True):
                delete_item_category(self.conn, d)
            self._active_id = "ALL"
            self._load()
            self.category_changed.emit(None)

    def refresh(self):
        self._load()

    def current_category_id(self):
        return None if self._active_id == "ALL" else self._active_id