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
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.font import FS_XS, FS_SM, FS_BASE, fs
from ui.constants import (
    CAT_ROW_MIN_H, CAT_ROW_MARGIN_H, CAT_ROW_MARGIN_R, CAT_ROW_SPACING,
    CAT_ROW_DEPTH_INDENT, CAT_ROW_INDENT_LINE_W, CAT_ROW_INDENT_LINE_H,
    CAT_ROW_DOT_W, CAT_ROW_BADGE_W, CAT_ROW_BADGE_H, CAT_ROW_BADGE_RADIUS,
    CAT_FORM_RADIUS, CAT_FORM_MARGIN, CAT_FORM_SPACING, CAT_FORM_INP_H,
    CAT_FORM_CMB_H, CAT_FORM_COLOR_PREVIEW_SIZE, CAT_FORM_COLOR_PREVIEW_RADIUS,
    CAT_FORM_BTN_COLOR_H, CAT_FORM_BTN_H, CAT_FORM_BTN_DEFAULT_H,
    CAT_FORM_BTN_SPACING, CAT_FORM_COLOR_ROW_SPACING,
)


def _btn_ss(bg, fg, bdr, hover_bg, height=CAT_FORM_BTN_DEFAULT_H):
    from ui.theme import _C
    from ui.font import FS_BASE
    _r = f"{CAT_FORM_RADIUS}px"
    return (
        f"QPushButton{{"
        f"  background:{bg}; color:{fg};"
        f"  border:1px solid {bdr}; border-radius:{_r};"
        f"  padding:0 12px; font-size:{FS_BASE}px; min-height:{height}px;"
        f"}}"
        f"QPushButton:hover{{background:{hover_bg};}}"
        f"QPushButton:pressed{{opacity:0.85;}}"
    )


# ══════════════════════════════════════════════════════════
# عنصر تصنيف واحد
# ══════════════════════════════════════════════════════════

class _CatRow(QFrame, WidgetMixin):
    clicked = pyqtSignal(object)

    def __init__(self, cat_id, name, color, count=0, depth=0, parent=None):
        super().__init__(parent)
        self._init_widget_mixin(lang=False, data=False)

        self.cat_id    = cat_id
        self._selected = False
        self._cat_color = color
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(CAT_ROW_MIN_H)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(CAT_ROW_MARGIN_H + depth * CAT_ROW_DEPTH_INDENT, 0, CAT_ROW_MARGIN_R, 0)
        lay.setSpacing(CAT_ROW_SPACING)

        # خط ربط للعناصر الفرعية
        if depth > 0:
            indent_line = QFrame()
            indent_line.setFixedWidth(CAT_ROW_INDENT_LINE_W)
            indent_line.setFixedHeight(CAT_ROW_INDENT_LINE_H)
            lay.addWidget(indent_line)
            self._indent_line = indent_line

        # نقطة اللون
        self._dot = QLabel("●")
        self._dot.setFixedWidth(CAT_ROW_DOT_W)

        # اسم التصنيف
        self._lbl = QLabel(name)
        font = QFont()
        font.setPointSize(FS_BASE)
        self._lbl.setFont(font)

        # عداد التصميمات
        self._badge = QLabel(str(count) if count else "")
        self._badge.setFixedSize(CAT_ROW_BADGE_W, CAT_ROW_BADGE_H)
        self._badge.setAlignment(Qt.AlignCenter)
        font_b = QFont()
        font_b.setPointSize(fs(FS_XS, -2))
        self._badge.setFont(font_b)
        self._badge.setVisible(bool(count))

        lay.addWidget(self._dot)
        lay.addWidget(self._lbl, stretch=1)
        lay.addWidget(self._badge)

        self._depth = depth
        self._refresh_style()

    def set_selected(self, s: bool):
        self._selected = s
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        _r = f"{CAT_FORM_RADIUS}px"
        _accent      = _C["accent"]
        _accent_light = _C["accent_light"]
        _bg_hover    = _C["bg_hover"]
        _border_med  = _C["border_med"]
        _border      = _C["border"]
        _bg_surface  = _C["bg_surface"]
        _text_pri    = _C["text_primary"]
        _text_mut    = _C["text_muted"]
        _cat_color   = self._cat_color or _accent

        # indent_line
        if self._depth > 0 and hasattr(self, '_indent_line'):
            self._indent_line.setStyleSheet(
                f"background:{_border_med}; border-radius:1px;"
            )

        if self._selected:
            self.setStyleSheet(
                f"QFrame{{"
                f"  background:{_accent_light};"
                f"  border-left:3px solid {_accent};"
                f"  border-radius:0 {_r} {_r} 0;"
                f"}}"
            )
            self._lbl.setStyleSheet(
                f"color:{_accent}; font-weight:600;"
                "background:transparent; border:none;"
            )
            self._dot.setStyleSheet(
                f"color:{_accent}; font-size:{fs(FS_XS,-2)}px;"
                "background:transparent; border:none;"
            )
        else:
            self.setStyleSheet(
                "QFrame{"
                "  background:transparent;"
                f"  border-left:3px solid transparent;"
                f"  border-radius:0 {_r} {_r} 0;"
                "}"
                f"QFrame:hover{{background:{_bg_hover};}}"
            )
            self._lbl.setStyleSheet(
                f"color:{_text_pri}; font-weight:400;"
                "background:transparent; border:none;"
            )
            self._dot.setStyleSheet(
                f"color:{_cat_color}; font-size:{fs(FS_XS,-2)}px;"
                "background:transparent; border:none;"
            )

        self._badge.setStyleSheet(
            f"color:{_text_mut}; font-weight:500;"
            f"background:{_bg_surface}; border:1px solid {_border};"
            f"border-radius:{CAT_ROW_BADGE_RADIUS}px;"
        )

    def mousePressEvent(self, e):
        self.clicked.emit(self.cat_id)
        super().mousePressEvent(e)


# ══════════════════════════════════════════════════════════
# فورم إضافة / تعديل — تصميم نظيف
# ══════════════════════════════════════════════════════════

class _CatForm(QWidget, WidgetMixin):
    saved    = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self._init_widget_mixin(data=False)

        self.conn        = conn
        self._editing_id = None
        self._color      = None  # يُحدَّث في _refresh_style
        self._build()

    def _build(self):
        from ui.theme import _C
        from ui.widgets.core.i18n import tr
        self._color = self._color or _C["accent"]

        lay = QVBoxLayout(self)
        lay.setContentsMargins(*CAT_FORM_MARGIN)
        lay.setSpacing(CAT_FORM_SPACING)

        # عنوان الفورم
        self._mode_lbl = QLabel(tr("design_cats_new_form_title"))
        lay.addWidget(self._mode_lbl)

        # حقل الاسم
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("design_cats_name_placeholder"))
        self.inp_name.setMinimumHeight(CAT_FORM_INP_H)
        lay.addWidget(self.inp_name)

        # التصنيف الأب
        self._lbl_p = QLabel(tr("design_cats_parent_label"))
        lay.addWidget(self._lbl_p)

        self.cmb_parent = QComboBox()
        self.cmb_parent.setMinimumHeight(CAT_FORM_CMB_H)
        lay.addWidget(self.cmb_parent)

        # صف اللون
        crow = QHBoxLayout()
        crow.setSpacing(CAT_FORM_COLOR_ROW_SPACING)

        self._lbl_c = QLabel(tr("design_cats_color_label"))

        self._color_preview = QFrame()
        self._color_preview.setFixedSize(CAT_FORM_COLOR_PREVIEW_SIZE, CAT_FORM_COLOR_PREVIEW_SIZE)

        self._btn_c = QPushButton(tr("design_cats_pick_color_btn"))
        self._btn_c.setMinimumHeight(CAT_FORM_BTN_COLOR_H)
        self._btn_c.clicked.connect(self._pick_color)

        crow.addWidget(self._lbl_c)
        crow.addWidget(self._color_preview)
        crow.addWidget(self._btn_c)
        crow.addStretch()
        lay.addLayout(crow)

        # أزرار
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        lay.addWidget(sep)

        brow = QHBoxLayout()
        brow.setSpacing(CAT_FORM_BTN_SPACING)

        self.btn_save = QPushButton(tr("design_cats_save_btn"))
        self.btn_save.setMinimumHeight(CAT_FORM_BTN_H)
        self.btn_save.clicked.connect(self._save)

        self._btn_cancel = QPushButton(tr("design_cats_cancel_btn"))
        self._btn_cancel.setMinimumHeight(CAT_FORM_BTN_H)
        self._btn_cancel.clicked.connect(self.canceled.emit)

        brow.addWidget(self._btn_cancel)
        brow.addWidget(self.btn_save, stretch=1)
        lay.addLayout(brow)

        self._sep = sep
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        _r = f"{CAT_FORM_RADIUS}px"
        _accent      = _C["accent"]
        _accent_hover = _C["accent_hover"]
        _accent_text = _C["accent_text"]
        _bg          = _C["bg_input"]
        _bg_surface  = _C["bg_surface"]
        _bg_hover    = _C["bg_hover"]
        _border      = _C["border"]
        _border_med  = _C["border_med"]
        _text_pri    = _C["text_primary"]
        _text_sec    = _C["text_sec"]

        self.setStyleSheet(
            f"QWidget{{"
            f"  background:{_bg_surface};"
            f"  border-top:1px solid {_border};"
            f"}}"
        )

        if hasattr(self, '_mode_lbl'):
            self._mode_lbl.setStyleSheet(
                f"font-size:{FS_SM}px; font-weight:700; color:{_accent};"
                "background:transparent; border:none;"
                "text-transform:uppercase; letter-spacing:0.5px;"
            )

        if hasattr(self, 'inp_name'):
            self.inp_name.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {_border_med};
                    border-radius: {_r};
                    padding: 0 10px;
                    font-size: {FS_BASE}px;
                    background: {_bg};
                    color: {_text_pri};
                }}
                QLineEdit:focus {{
                    border-color: {_accent};
                    background: {_bg};
                }}
            """)

        if hasattr(self, '_lbl_p'):
            self._lbl_p.setStyleSheet(
                f"font-size:{FS_SM}px; color:{_text_sec}; background:transparent; border:none;"
            )

        if hasattr(self, 'cmb_parent'):
            self.cmb_parent.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid {_border_med};
                    border-radius: {_r};
                    padding: 0 8px;
                    font-size: {FS_SM}px;
                    background: {_bg};
                    color: {_text_pri};
                }}
                QComboBox:focus {{ border-color: {_accent}; }}
                QComboBox::drop-down {{ border: none; width: 16px; }}
            """)

        if hasattr(self, '_lbl_c'):
            self._lbl_c.setStyleSheet(
                f"font-size:{FS_SM}px; color:{_text_sec}; background:transparent; border:none;"
            )

        if hasattr(self, '_btn_c'):
            self._btn_c.setStyleSheet(_btn_ss(_bg, _text_sec, _border_med, _bg_hover))

        if hasattr(self, '_sep'):
            self._sep.setStyleSheet(f"color:{_border}; margin:2px 0;")

        if hasattr(self, 'btn_save'):
            self.btn_save.setStyleSheet(
                _btn_ss(_accent, _accent_text, _accent, _accent_hover, CAT_FORM_BTN_H)
            )

        if hasattr(self, '_btn_cancel'):
            self._btn_cancel.setStyleSheet(
                _btn_ss(_bg, _text_sec, _border_med, _bg_hover, CAT_FORM_BTN_H)
            )

        self._update_color_preview()

    def _refresh_lang(self, *_):
        from ui.widgets.core.i18n import tr
        if hasattr(self, '_mode_lbl'):
            if self._editing_id is None:
                self._mode_lbl.setText(tr("design_cats_new_form_title"))
        if hasattr(self, 'inp_name'):
            self.inp_name.setPlaceholderText(tr("design_cats_name_placeholder"))
        if hasattr(self, '_lbl_p'):
            self._lbl_p.setText(tr("design_cats_parent_label"))
        if hasattr(self, '_lbl_c'):
            self._lbl_c.setText(tr("design_cats_color_label"))
        if hasattr(self, '_btn_c'):
            self._btn_c.setText(tr("design_cats_pick_color_btn"))
        if hasattr(self, 'btn_save'):
            self.btn_save.setText(tr("design_cats_save_btn"))
        if hasattr(self, '_btn_cancel'):
            self._btn_cancel.setText(tr("design_cats_cancel_btn"))

    def _update_color_preview(self):
        if not hasattr(self, '_color_preview'):
            return
        from ui.theme import _C
        _border_med = _C["border_med"]
        color = self._color or _C["accent"]
        self._color_preview.setStyleSheet(
            f"background:{color}; border-radius:{CAT_FORM_COLOR_PREVIEW_RADIUS}px;"
            f"border:1px solid {_border_med};"
        )

    def _reload_parent(self, exclude_id=None):
        from ui.widgets.core.i18n import tr
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
        from ui.widgets.core.i18n import tr
        indent = "    " * depth
        arrow  = tr("category_tree_arrow") if depth > 0 else ""
        for n in nodes:
            if n["id"] in excl:
                continue
            self.cmb_parent.addItem(f"{indent}{arrow}{n['name']}", n["id"])
            if n["children"]:
                self._add_nodes(n["children"], depth + 1, excl)

    def _pick_color(self):
        from ui.theme import _C
        col = QColorDialog.getColor(QColor(self._color or _C["accent"]), self)
        if col.isValid():
            self._color = col.name()
            self._update_color_preview()

    def load_new(self):
        from ui.theme import _C
        from ui.widgets.core.i18n import tr
        self._editing_id = None
        self._color = _C["accent"]
        self.inp_name.clear()
        self._update_color_preview()
        self._mode_lbl.setText(tr("design_cats_new_form_title"))
        self._reload_parent()

    def load_edit(self, cat_id):
        from ui.theme import _C
        from ui.widgets.core.i18n import tr
        cat = fetch_item_category(self.conn, cat_id)
        if not cat:
            return
        self._editing_id = cat_id
        self._color = cat["color"] or _C["accent"]
        self.inp_name.setText(cat["name"])
        self._update_color_preview()
        self._mode_lbl.setText(tr("design_cats_edit_form_title").format(name=cat['name']))
        self._reload_parent(exclude_id=cat_id)
        for i in range(self.cmb_parent.count()):
            if self.cmb_parent.itemData(i) == cat["parent_id"]:
                self.cmb_parent.setCurrentIndex(i)
                break

    def _save(self):
        from ui.widgets.core.i18n import tr
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
