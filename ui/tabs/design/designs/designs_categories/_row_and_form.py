"""
ui/tabs/design/designs/designs_categories/_row_and_form.py
====================================================

"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QColorDialog, QMessageBox, QFrame,
    QComboBox,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont

from db.designs.design_item_categories_repo import (
    fetch_all_item_categories,
    fetch_item_category,
    insert_item_category,
    update_item_category,
    build_item_category_tree,
    fetch_item_category_descendants,
)
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_XS, FS_SM, FS_BASE, fs

# ── Palette من _C ──────────────────────────────────────
_BG          = _C["bg_input"]
_BG_SURFACE  = _C["bg_surface"]
_BG_HOVER    = _C["bg_hover"]
_BG_SELECTED = _C["accent_light"]
_BORDER      = _C["border"]
_BORDER_MED  = _C["border_med"]

_TEXT_PRI    = _C["text_primary"]
_TEXT_SEC    = _C["text_sec"]
_TEXT_MUT    = _C["text_muted"]

_ACCENT      = _C["accent"]

_RADIUS_SM   = "5px"


def _btn_ss(bg, fg, bdr, hover_bg, height=28):
    return (
        f"QPushButton{{"
        f"  background:{bg}; color:{fg};"
        f"  border:1px solid {bdr}; border-radius:{_RADIUS_SM};"
        f"  padding:0 12px; font-size:{FS_BASE}px; min-height:{height}px;"
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
            f"color:{self._color}; font-size:{fs(FS_XS,-2)}px;"
            "background:transparent; border:none;"
        )

        # اسم التصنيف
        self._lbl = QLabel(name)
        font = QFont()
        font.setPointSize(FS_BASE)
        self._lbl.setFont(font)
        self._lbl.setStyleSheet(
            f"color:{_TEXT_PRI}; background:transparent; border:none;"
        )

        # عداد التصميمات
        self._badge = QLabel(str(count) if count else "")
        self._badge.setFixedSize(24, 18)
        self._badge.setAlignment(Qt.AlignCenter)
        font_b = QFont()
        font_b.setPointSize(fs(FS_XS, -2))
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
                f"color:{_ACCENT}; font-size:{fs(FS_XS,-2)}px;"
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
                f"color:{self._color}; font-size:{fs(FS_XS,-2)}px;"
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
        self._mode_lbl = QLabel(tr("design_cats_new_form_title"))
        self._mode_lbl.setStyleSheet(
            f"font-size:{FS_SM}px; font-weight:700; color:{_ACCENT};"
            "background:transparent; border:none;"
            "text-transform:uppercase; letter-spacing:0.5px;"
        )
        lay.addWidget(self._mode_lbl)

        # حقل الاسم
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("design_cats_name_placeholder"))
        self.inp_name.setMinimumHeight(32)
        self.inp_name.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {_BORDER_MED};
                border-radius: {_RADIUS_SM};
                padding: 0 10px;
                font-size: {FS_BASE}px;
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
        lbl_p = QLabel(tr("design_cats_parent_label"))
        lbl_p.setStyleSheet(
            f"font-size:{FS_SM}px; color:{_TEXT_SEC}; background:transparent; border:none;"
        )
        lay.addWidget(lbl_p)

        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(30)
        self.cmb_parent.setStyleSheet(f"""
            QComboBox {{
                border: 1px solid {_BORDER_MED};
                border-radius: {_RADIUS_SM};
                padding: 0 8px;
                font-size: {FS_SM}px;
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

        lbl_c = QLabel(tr("design_cats_color_label"))
        lbl_c.setStyleSheet(
            f"font-size:{FS_SM}px; color:{_TEXT_SEC}; background:transparent; border:none;"
        )

        self._color_preview = QFrame()
        self._color_preview.setFixedSize(24, 24)
        self._update_color_preview()

        btn_c = QPushButton(tr("design_cats_pick_color_btn"))
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

        self.btn_save = QPushButton(tr("design_cats_save_btn"))
        self.btn_save.setMinimumHeight(30)
        self.btn_save.setStyleSheet(_btn_ss(_ACCENT, _C["accent_text"], _ACCENT, _C["accent_hover"], 30))
        self.btn_save.clicked.connect(self._save)

        btn_cancel = QPushButton(tr("design_cats_cancel_btn"))
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
        self.cmb_parent.addItem(tr("design_cats_no_parent"), None)
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
        self._mode_lbl.setText(tr("design_cats_new_form_title"))
        self._reload_parent()

    def load_edit(self, cat_id):
        cat = fetch_item_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self._color = cat["color"] or _ACCENT
        self.inp_name.setText(cat["name"])
        self._update_color_preview()
        self._mode_lbl.setText(tr("design_cats_edit_form_title").format(name=cat['name']))
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
            QMessageBox.warning(self, tr("error"), str(e))

