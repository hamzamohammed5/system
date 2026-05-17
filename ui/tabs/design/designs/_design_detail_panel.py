"""
ui/tabs/design/designs/_designs_categories_panel.py
====================================================
لوحة إدارة تصنيفات التصميمات المستقلة — sidebar على يسار تبويب التصميمات.

تستخدم جدول design_item_categories المستقل تماماً عن
design_categories الخاص بمجموعات المقاسات.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel,
    QColorDialog, QMessageBox, QFrame,
    QScrollArea,
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

# ── ألوان ──
_BG          = "#ffffff"
_BG_SUBTLE   = "#f8fafc"
_BG_HOVER    = "#f1f5f9"
_BORDER      = "#e2e8f0"
_BORDER_MED  = "#cbd5e1"
_TEXT        = "#0f172a"
_TEXT_MED    = "#475569"
_TEXT_MUTED  = "#94a3b8"
_PURPLE      = "#7c3aed"
_PURPLE_LT   = "#f5f3ff"
_PURPLE_MED  = "#ddd6fe"
_RED         = "#dc2626"
_RED_LT      = "#fef2f2"

_SIDEBAR_W   = 220


def _btn_ss(bg, fg, border, hover_bg):
    return (
        f"QPushButton {{ background:{bg}; color:{fg}; border:1px solid {border};"
        f" border-radius:6px; padding:4px 10px; font-size:11px; }}"
        f"QPushButton:hover {{ background:{hover_bg}; }}"
    )


# ══════════════════════════════════════════════════════════
# عنصر تصنيف واحد
# ══════════════════════════════════════════════════════════

class _CategoryItem(QFrame):
    clicked = pyqtSignal(object)   # cat_id أو None

    def __init__(self, cat_id, name: str, color: str,
                 count: int = 0, depth: int = 0, parent=None):
        super().__init__(parent)
        self.cat_id    = cat_id
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(36)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10 + depth * 14, 4, 10, 4)
        lay.setSpacing(8)

        self._dot = QLabel("●")
        self._dot.setFixedWidth(14)
        self._dot.setStyleSheet(
            f"color:{color or _PURPLE}; font-size:10px;"
            " background:transparent; border:none;"
        )

        self._lbl = QLabel(name)
        self._lbl.setStyleSheet(
            f"font-size:12px; color:{_TEXT}; background:transparent; border:none;"
        )

        self._cnt = QLabel(str(count) if count else "")
        self._cnt.setFixedWidth(26)
        self._cnt.setAlignment(Qt.AlignCenter)
        self._cnt.setStyleSheet(f"""
            color:{_TEXT_MUTED}; font-size:10px;
            background:{_BG_SUBTLE}; border:1px solid {_BORDER};
            border-radius:10px; padding:0 4px;
        """)
        self._cnt.setVisible(bool(count))

        lay.addWidget(self._dot)
        lay.addWidget(self._lbl, stretch=1)
        lay.addWidget(self._cnt)
        self._update_style()

    def set_selected(self, sel: bool):
        self._selected = sel
        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_PURPLE_LT};
                    border-left: 3px solid {_PURPLE};
                    border-radius: 6px;
                }}
            """)
            self._lbl.setStyleSheet(
                f"font-size:12px; color:{_PURPLE}; font-weight:600;"
                " background:transparent; border:none;"
            )
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: transparent;
                    border-left: 3px solid transparent;
                    border-radius: 6px;
                }}
                QFrame:hover {{ background: {_BG_HOVER}; }}
            """)
            self._lbl.setStyleSheet(
                f"font-size:12px; color:{_TEXT}; background:transparent; border:none;"
            )

    def mousePressEvent(self, event):
        self.clicked.emit(self.cat_id)
        super().mousePressEvent(event)


# ══════════════════════════════════════════════════════════
# فورم إضافة / تعديل مدمج
# ══════════════════════════════════════════════════════════

class _CategoryForm(QWidget):
    saved    = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._color      = _PURPLE
        self._build()

    def _build(self):
        from PyQt5.QtWidgets import QLineEdit
        self.setStyleSheet(f"""
            QWidget {{
                background: {_BG_SUBTLE};
                border-top: 1px solid {_BORDER};
            }}
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(8)

        self._mode_lbl = QLabel("تصنيف جديد")
        self._mode_lbl.setStyleSheet(
            f"font-size:11px; font-weight:600; color:{_PURPLE};"
            " background:transparent; border:none;"
        )
        lay.addWidget(self._mode_lbl)

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم التصنيف...")
        self.inp_name.setMinimumHeight(30)
        self.inp_name.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {_BORDER_MED}; border-radius:6px;
                padding: 3px 8px; font-size:11px; background:{_BG};
            }}
            QLineEdit:focus {{ border-color:{_PURPLE}; }}
        """)
        lay.addWidget(self.inp_name)

        # اختيار التصنيف الأب
        from PyQt5.QtWidgets import QComboBox
        lbl_parent = QLabel("تابع لـ:")
        lbl_parent.setStyleSheet(
            f"font-size:11px; color:{_TEXT_MED}; background:transparent; border:none;"
        )
        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(28)
        self.cmb_parent.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {_BORDER_MED}; border-radius:6px;
                padding: 2px 8px; font-size:11px; background:{_BG};
            }}
            QComboBox:focus {{ border-color:{_PURPLE}; }}
            QComboBox::drop-down {{ border:none; }}
        """)
        lay.addWidget(lbl_parent)
        lay.addWidget(self.cmb_parent)

        # اللون
        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        lbl_c = QLabel("اللون:")
        lbl_c.setStyleSheet(
            f"font-size:11px; color:{_TEXT_MED}; background:transparent; border:none;"
        )
        self._color_dot = QLabel("●●●")
        self._color_dot.setStyleSheet(
            f"color:{self._color}; font-size:14px; background:transparent; border:none;"
        )
        btn_color = QPushButton("اختر")
        btn_color.setMinimumHeight(26)
        btn_color.setStyleSheet(_btn_ss(_BG, _TEXT_MED, _BORDER_MED, _BG_HOVER))
        btn_color.clicked.connect(self._pick_color)
        color_row.addWidget(lbl_c)
        color_row.addWidget(self._color_dot)
        color_row.addStretch()
        color_row.addWidget(btn_color)
        lay.addLayout(color_row)

        # أزرار
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.btn_save = QPushButton("💾  حفظ")
        self.btn_save.setMinimumHeight(28)
        self.btn_save.setStyleSheet(_btn_ss(_PURPLE, "#fff", _PURPLE, "#6d28d9"))
        self.btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setMinimumHeight(28)
        btn_cancel.setStyleSheet(_btn_ss(_BG, _TEXT_MED, _BORDER_MED, _BG_HOVER))
        btn_cancel.clicked.connect(self.canceled.emit)

        btn_row.addWidget(self.btn_save, stretch=1)
        btn_row.addWidget(btn_cancel)
        lay.addLayout(btn_row)

    def _reload_parent_combo(self, exclude_id=None):
        self.cmb_parent.blockSignals(True)
        self.cmb_parent.clear()
        self.cmb_parent.addItem("— بدون أب (رئيسي) —", None)
        rows = fetch_all_item_categories(self.conn)
        tree = build_item_category_tree(rows)
        excluded = set()
        if exclude_id is not None:
            excluded = set(fetch_item_category_descendants(self.conn, exclude_id))
        self._add_parent_nodes(tree, 0, excluded)
        self.cmb_parent.blockSignals(False)

    def _add_parent_nodes(self, nodes, depth, excluded):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            if node["id"] in excluded:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_parent_nodes(node["children"], depth + 1, excluded)

    def _pick_color(self):
        col = QColorDialog.getColor(QColor(self._color), self, "لون التصنيف")
        if col.isValid():
            self._color = col.name()
            self._color_dot.setStyleSheet(
                f"color:{self._color}; font-size:14px; background:transparent; border:none;"
            )

    def load_new(self):
        self._editing_id = None
        self._color      = _PURPLE
        self.inp_name.clear()
        self._color_dot.setStyleSheet(
            f"color:{self._color}; font-size:14px; background:transparent; border:none;"
        )
        self._mode_lbl.setText("تصنيف جديد")
        self._reload_parent_combo()

    def load_edit(self, cat_id: int):
        cat = fetch_item_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self._color      = cat["color"] or _PURPLE
        self.inp_name.setText(cat["name"])
        self._color_dot.setStyleSheet(
            f"color:{self._color}; font-size:14px; background:transparent; border:none;"
        )
        self._mode_lbl.setText(f"تعديل: {cat['name']}")
        self._reload_parent_combo(exclude_id=cat_id)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            return
        parent_id = self.cmb_parent.currentData()
        try:
            if self._editing_id:
                update_item_category(self.conn, self._editing_id,
                                     name, self._color, parent_id)
            else:
                insert_item_category(self.conn, name, self._color, parent_id)
            self.saved.emit()
        except ValueError as e:
            QMessageBox.warning(self, "خطأ", str(e))


# ══════════════════════════════════════════════════════════
# Sidebar الرئيسي
# ══════════════════════════════════════════════════════════

class DesignsCategoriesPanel(QWidget):
    """
    Sidebar يسار تبويب التصميمات — تصنيفات مستقلة (design_item_categories).
    Signal: category_changed(cat_id | None)
    """

    category_changed = pyqtSignal(object)   # None = الكل

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._active_id = "ALL"
        self._items     = []
        self._build()
        self._load()

    def _build(self):
        self.setFixedWidth(_SIDEBAR_W)
        self.setStyleSheet(f"""
            QWidget {{
                background: {_BG};
                border-left: 1px solid {_BORDER};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──
        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background: {_BG_SUBTLE};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 10, 8, 10)

        lbl = QLabel("🏷  التصنيفات")
        lbl.setStyleSheet(
            f"font-size:12px; font-weight:600; color:{_TEXT};"
            " background:transparent; border:none;"
        )

        self._btn_add = QPushButton("+")
        self._btn_add.setFixedSize(26, 26)
        self._btn_add.setToolTip("تصنيف جديد")
        self._btn_add.setStyleSheet(f"""
            QPushButton {{
                background:{_PURPLE}; color:#fff; border:none;
                border-radius:13px; font-size:16px; font-weight:bold;
            }}
            QPushButton:hover {{ background:#6d28d9; }}
        """)
        self._btn_add.clicked.connect(self._show_add_form)

        hdr_lay.addWidget(lbl, stretch=1)
        hdr_lay.addWidget(self._btn_add)
        root.addWidget(hdr)

        # ── قائمة ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{_BG}; }}
            QScrollBar:vertical {{
                background:#f0f0f0; width:5px; border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
                background:#c5cae9; border-radius:3px; min-height:20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet(f"background:{_BG};")
        self._list_layout = QVBoxLayout(self._list_widget)
        self._list_layout.setContentsMargins(8, 8, 8, 8)
        self._list_layout.setSpacing(2)
        self._list_layout.addStretch()

        scroll.setWidget(self._list_widget)
        root.addWidget(scroll, stretch=1)

        # ── شريط الأزرار ──
        action_bar = QFrame()
        action_bar.setStyleSheet(f"""
            QFrame {{
                background: {_BG_SUBTLE};
                border-top: 1px solid {_BORDER};
            }}
        """)
        ab_lay = QHBoxLayout(action_bar)
        ab_lay.setContentsMargins(8, 6, 8, 6)
        ab_lay.setSpacing(6)

        self.btn_edit = QPushButton("✏️  تعديل")
        self.btn_edit.setMinimumHeight(26)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setStyleSheet(_btn_ss(_BG, _TEXT_MED, _BORDER_MED, _BG_HOVER))
        self.btn_edit.clicked.connect(self._show_edit_form)

        self.btn_del = QPushButton("🗑️")
        self.btn_del.setFixedSize(30, 26)
        self.btn_del.setEnabled(False)
        self.btn_del.setStyleSheet(_btn_ss(_RED_LT, _RED, "#fca5a5", "#fee2e2"))
        self.btn_del.clicked.connect(self._delete)

        ab_lay.addWidget(self.btn_edit, stretch=1)
        ab_lay.addWidget(self.btn_del)
        root.addWidget(action_bar)

        # ── الفورم المدمج ──
        self._form = _CategoryForm(self.conn)
        self._form.setVisible(False)
        self._form.saved.connect(self._on_form_saved)
        self._form.canceled.connect(lambda: self._form.setVisible(False))
        root.addWidget(self._form)

    # ── تحميل القائمة ────────────────────────────────

    def _load(self):
        for item in self._items:
            self._list_layout.removeWidget(item)
            item.deleteLater()
        self._items = []

        # "الكل"
        all_item = _CategoryItem(None, "🎨  كل التصميمات", _PURPLE, depth=0)
        all_item.clicked.connect(self._on_item_clicked)
        all_item.set_selected(self._active_id == "ALL")
        self._list_layout.insertWidget(self._list_layout.count() - 1, all_item)
        self._items.append(all_item)

        # فاصل
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color:{_BORDER}; margin:2px 4px;")
        self._list_layout.insertWidget(self._list_layout.count() - 1, sep)

        rows   = fetch_all_item_categories(self.conn)
        tree   = build_item_category_tree(rows)
        counts = count_designs_per_category(self.conn)
        self._add_tree_items(tree, 0, counts)

        has_cat = (self._active_id != "ALL" and self._active_id is not None)
        self.btn_edit.setEnabled(has_cat)
        self.btn_del.setEnabled(has_cat)

    def _add_tree_items(self, nodes, depth, counts):
        for node in nodes:
            desc = fetch_item_category_descendants(self.conn, node["id"])
            cnt  = sum(counts.get(d, 0) for d in desc)

            item = _CategoryItem(
                node["id"], node["name"], node["color"],
                count=cnt, depth=depth
            )
            item.clicked.connect(self._on_item_clicked)
            item.set_selected(self._active_id == node["id"])

            self._list_layout.insertWidget(self._list_layout.count() - 1, item)
            self._items.append(item)

            if node["children"]:
                self._add_tree_items(node["children"], depth + 1, counts)

    # ── Signal handlers ──────────────────────────────

    def _on_item_clicked(self, cat_id):
        self._active_id = "ALL" if cat_id is None else cat_id
        for item in self._items:
            item.set_selected(item.cat_id == cat_id)
        has_cat = (self._active_id != "ALL")
        self.btn_edit.setEnabled(has_cat)
        self.btn_del.setEnabled(has_cat)
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
        child_cats = len(desc) - 1
        if child_cats:
            msg += f"\n⚠️ يحتوي على {child_cats} تصنيف فرعي."
        if total:
            msg += f"\n⚠️ {total} تصميم سيفقد تصنيفه."

        if QMessageBox.question(
            self, "تأكيد الحذف", msg,
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            for did in sorted(desc, reverse=True):
                delete_item_category(self.conn, did)
            self._active_id = "ALL"
            self._load()
            self.category_changed.emit(None)

    # ── API ──────────────────────────────────────────

    def refresh(self):
        self._load()

    def current_category_id(self):
        return None if self._active_id == "ALL" else self._active_id