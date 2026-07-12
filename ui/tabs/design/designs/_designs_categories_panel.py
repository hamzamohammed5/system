"""
ui/tabs/design/designs/_designs_categories_panel.py
====================================================
Sidebar تصنيفات التصميمات — مع دعم كامل لتغيير حجم الخط ديناميكياً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel,
    QMessageBox, QFrame,
    QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.widgets.panels.themed_inputs import ThemedLineEdit

from services.design import get_design_service
from ui.tabs.design.design_styles import get_styles
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.constants import (
    DESIGN_CATS_SIDEBAR_W,
    DESIGN_CATS_HDR_H,
    DESIGN_CATS_HDR_MARGIN_L,
    DESIGN_CATS_HDR_MARGIN_R,
    DESIGN_CATS_HDR_SPACING,
    DESIGN_CATS_BTN_ADD_SIZE,
    DESIGN_CATS_BTN_ADD_RADIUS,
    DESIGN_CATS_SEARCH_MARGIN_V,
    DESIGN_CATS_SEARCH_SPACING,
    DESIGN_CATS_INP_MIN_H,
    DESIGN_CATS_BTN_CLEAR_SIZE,
    DESIGN_CATS_LIST_MARGIN_V,
    DESIGN_CATS_LIST_SPACING,
    DESIGN_CATS_ACT_MARGIN_H,
    DESIGN_CATS_ACT_MARGIN_V,
    DESIGN_CATS_ACT_SPACING,
    DESIGN_CATS_BTN_MIN_H,
    DESIGN_CATS_SEP_H,
    DESIGN_CATS_SCROLL_W,
    DESIGN_CATS_SCROLL_RADIUS,
    DESIGN_CATS_SCROLL_MIN_H,
    DESIGN_CATS_SEARCH_FRAME_PAD_V,
    DESIGN_CATS_SEARCH_FRAME_PAD_H,
    DESIGN_CATS_SEP_MARGIN_V,
    DESIGN_CATS_SEP_MARGIN_H,
    INPUT_BORDER_W,
)

from .designs_categories._row_and_form import _btn_ss, _CatForm, _CatRow


class DesignsCategoriesPanel(QWidget, WidgetMixin):
    category_changed = pyqtSignal(object)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._svc       = get_design_service(conn)
        self._active_id = "ALL"
        self._items     = []
        self._build()
        self._load()
        self._init_widget_mixin(lang=False, data=False)
        self._refresh_style()

    def _refresh_style(self, *_):
        from ui.theme import _C
        s = get_styles()

        self._lbl_header.setStyleSheet(
            f"font-size:{s.large}pt; font-weight:700; color:{_C['text_primary']};"
            "background:transparent; border:none;"
        )
        self._btn_add.setStyleSheet(
            f"QPushButton{{"
            f"  background:{_C['accent']}; color:{_C['accent_text']};"
            f"  border:none; border-radius:{DESIGN_CATS_BTN_ADD_RADIUS}px;"
            f"  font-size:{s.large}pt; font-weight:700;"
            f"}}"
            f"QPushButton:hover{{background:{_C['accent_hover']};}}"
        )
        self._inp_search.setStyleSheet(s.input_search())

        self.btn_edit.setStyleSheet(
            s.btn(_C["bg_input"], _C["text_sec"], _C["border_med"], _C["bg_hover"])
        )
        self.btn_del.setStyleSheet(
            s.btn(_C["danger_bg"], _C["danger"], _C["danger_border"], _C["danger_bg"])
        )

        # [إصلاح dark-theme] الودجتس دي كانت بتاخد لون الخلفية وقت البناء
        # بس (_build) ومفيهاش أي تحديث هنا، فكانت بتفضل بلون الثيم القديم
        # حتى بعد التحويل لـ dark — بالظبط زي مشكلة toolbar/_grid_widget
        # في _designs_table.py.
        if hasattr(self, '_hdr'):
            self._hdr.setStyleSheet(
                f"QFrame{{ background:{_C['bg_input']}; border-bottom:{INPUT_BORDER_W}px solid {_C['border']}; }}"
            )
        self.setStyleSheet(
            f"QWidget{{ background:{_C['bg_input']}; border-left:{INPUT_BORDER_W}px solid {_C['border']}; }}"
        )
        if hasattr(self, '_search_frame'):
            self._search_frame.setStyleSheet(
                f"QFrame{{ background:{_C['bg_input']}; border-bottom:{INPUT_BORDER_W}px solid {_C['border']}; "
                f"padding:{DESIGN_CATS_SEARCH_FRAME_PAD_V}px {DESIGN_CATS_SEARCH_FRAME_PAD_H}px; }}"
            )
        if hasattr(self, '_scroll'):
            self._scroll.setStyleSheet(
                f"QScrollArea{{border:none; background:{_C['bg_input']};}}"
                f"QScrollBar:vertical{{"
                f"  background:{_C['bg_surface']}; width:{DESIGN_CATS_SCROLL_W}px; border-radius:{DESIGN_CATS_SCROLL_RADIUS}px;"
                f"}}"
                f"QScrollBar::handle:vertical{{"
                f"  background:{_C['border_med']}; border-radius:{DESIGN_CATS_SCROLL_RADIUS}px; min-height:{DESIGN_CATS_SCROLL_MIN_H}px;"
                f"}}"
                "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{height:0;}"
            )
        if hasattr(self, '_list_w'):
            self._list_w.setStyleSheet(f"background:{_C['bg_input']};")
        if hasattr(self, '_act'):
            self._act.setStyleSheet(
                f"QFrame{{ background:{_C['bg_surface']}; border-top:{INPUT_BORDER_W}px solid {_C['border']}; }}"
            )

        # الصفوف (_CatRow) والفاصل (sep) بتتلون وقت _load() بس — لازم
        # نعيد التحميل عشان تاخد ألوان الثيم الجديد بدل ما تفضل بالقديمة.
        if hasattr(self, '_items'):
            self._load(query=self._inp_search.text().strip() if hasattr(self, '_inp_search') else "")

    def _build(self):
        from ui.theme import _C
        s = get_styles()
        self.setFixedWidth(DESIGN_CATS_SIDEBAR_W)
        self.setStyleSheet(
            f"QWidget{{ background:{_C['bg_input']}; border-left:{INPUT_BORDER_W}px solid {_C['border']}; }}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──────────────────────────────────────
        hdr = QFrame()
        self._hdr = hdr   # [إصلاح dark-theme] مرجع لتحديث اللون في _refresh_style
        hdr.setFixedHeight(DESIGN_CATS_HDR_H)
        hdr.setStyleSheet(
            f"QFrame{{ background:{_C['bg_input']}; border-bottom:{INPUT_BORDER_W}px solid {_C['border']}; }}"
        )
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(DESIGN_CATS_HDR_MARGIN_L, 0, DESIGN_CATS_HDR_MARGIN_R, 0)
        hdr_lay.setSpacing(DESIGN_CATS_HDR_SPACING)

        self._lbl_header = QLabel(tr("design_cats_panel_title"))
        self._lbl_header.setStyleSheet(
            f"font-size:{s.large}pt; font-weight:700; color:{_C['text_primary']};"
            "background:transparent; border:none;"
        )

        self._btn_add = QPushButton(tr("design_cats_add_icon"))
        self._btn_add.setFixedSize(DESIGN_CATS_BTN_ADD_SIZE, DESIGN_CATS_BTN_ADD_SIZE)
        self._btn_add.setToolTip(tr("design_cats_add_tooltip"))
        self._btn_add.setStyleSheet(
            f"QPushButton{{"
            f"  background:{_C['accent']}; color:{_C['accent_text']};"
            f"  border:none; border-radius:{DESIGN_CATS_BTN_ADD_RADIUS}px;"
            f"  font-size:{s.large}pt; font-weight:700;"
            f"}}"
            f"QPushButton:hover{{background:{_C['accent_hover']};}}"
        )
        self._btn_add.clicked.connect(self._show_add_form)

        hdr_lay.addWidget(self._lbl_header, stretch=1)
        hdr_lay.addWidget(self._btn_add)
        root.addWidget(hdr)

        # ── شريط البحث ──────────────────────────────
        search_frame = QFrame()
        self._search_frame = search_frame   # [إصلاح dark-theme]
        search_frame.setStyleSheet(
            f"QFrame{{ background:{_C['bg_input']}; border-bottom:{INPUT_BORDER_W}px solid {_C['border']}; padding:{DESIGN_CATS_SEARCH_FRAME_PAD_V}px {DESIGN_CATS_SEARCH_FRAME_PAD_H}px; }}"
        )
        sf_lay = QHBoxLayout(search_frame)
        sf_lay.setContentsMargins(0, DESIGN_CATS_SEARCH_MARGIN_V, 0, DESIGN_CATS_SEARCH_MARGIN_V)
        sf_lay.setSpacing(DESIGN_CATS_SEARCH_SPACING)

        self._inp_search = ThemedLineEdit()
        self._inp_search.setPlaceholderText(tr("design_cats_search_placeholder"))
        self._inp_search.setMinimumHeight(DESIGN_CATS_INP_MIN_H)
        self._inp_search.setStyleSheet(s.input_search())
        self._inp_search.textChanged.connect(self._on_search)

        self._btn_clear_search = QPushButton(tr("combo_clear_search"))
        self._btn_clear_search.setFixedSize(DESIGN_CATS_BTN_CLEAR_SIZE, DESIGN_CATS_BTN_CLEAR_SIZE)
        self._btn_clear_search.setVisible(False)
        self._btn_clear_search.setStyleSheet(
            f"QPushButton{{background:transparent;border:none;"
            f"color:{_C['text_muted']};}}"
            f"QPushButton:hover{{color:{_C['danger']};}}"
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
        self._scroll = scroll   # [إصلاح dark-theme]
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"QScrollArea{{border:none; background:{_C['bg_input']};}}"
            f"QScrollBar:vertical{{"
            f"  background:{_C['bg_surface']}; width:{DESIGN_CATS_SCROLL_W}px; border-radius:{DESIGN_CATS_SCROLL_RADIUS}px;"
            f"}}"
            f"QScrollBar::handle:vertical{{"
            f"  background:{_C['border_med']}; border-radius:{DESIGN_CATS_SCROLL_RADIUS}px; min-height:{DESIGN_CATS_SCROLL_MIN_H}px;"
            f"}}"
            "QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical{height:0;}"
        )

        self._list_w = QWidget()
        self._list_w.setStyleSheet(f"background:{_C['bg_input']};")
        self._list_lay = QVBoxLayout(self._list_w)
        self._list_lay.setContentsMargins(0, DESIGN_CATS_LIST_MARGIN_V, 0, DESIGN_CATS_LIST_MARGIN_V)
        self._list_lay.setSpacing(DESIGN_CATS_LIST_SPACING)
        self._list_lay.addStretch()

        scroll.setWidget(self._list_w)
        root.addWidget(scroll, stretch=1)

        # ── شريط الإجراءات ──────────────────────────
        act = QFrame()
        self._act = act   # [إصلاح dark-theme]
        act.setStyleSheet(
            f"QFrame{{ background:{_C['bg_surface']}; border-top:{INPUT_BORDER_W}px solid {_C['border']}; }}"
        )
        ab = QHBoxLayout(act)
        ab.setContentsMargins(DESIGN_CATS_ACT_MARGIN_H, DESIGN_CATS_ACT_MARGIN_V,
                              DESIGN_CATS_ACT_MARGIN_H, DESIGN_CATS_ACT_MARGIN_V)
        ab.setSpacing(DESIGN_CATS_ACT_SPACING)

        self.btn_edit = QPushButton(tr("design_cats_edit_btn"))
        self.btn_edit.setMinimumHeight(DESIGN_CATS_BTN_MIN_H)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setStyleSheet(s.btn(_C["bg_input"], _C["text_sec"], _C["border_med"], _C["bg_hover"]))
        self.btn_edit.clicked.connect(self._show_edit_form)

        self.btn_del = QPushButton(tr("design_cats_delete_btn"))
        self.btn_del.setMinimumHeight(DESIGN_CATS_BTN_MIN_H)
        self.btn_del.setEnabled(False)
        self.btn_del.setStyleSheet(s.btn(_C["danger_bg"], _C["danger"], _C["danger_border"], _C["danger_bg"]))
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
        from ui.theme import _C
        for item in self._items:
            self._list_lay.removeWidget(item)
            item.deleteLater()
        self._items = []

        all_row = _CatRow(None, tr("design_cats_all"), _C["accent"], depth=0)
        all_row.clicked.connect(self._on_clicked)
        all_row.set_selected(self._active_id == "ALL")
        self._list_lay.insertWidget(self._list_lay.count() - 1, all_row)
        self._items.append(all_row)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(DESIGN_CATS_SEP_H)
        sep.setStyleSheet(f"background:{_C['border']}; margin:{DESIGN_CATS_SEP_MARGIN_V}px {DESIGN_CATS_SEP_MARGIN_H}px;")
        self._list_lay.insertWidget(self._list_lay.count() - 1, sep)

        rows   = self._svc.list_item_categories()
        tree   = self._svc.build_tree(rows)
        counts = self._svc.count_designs_per_category()
        self._add_tree(tree, 0, counts, query.lower())

        has_selection = self._active_id not in ("ALL", None)
        self.btn_edit.setEnabled(has_selection)
        self.btn_del.setEnabled(has_selection)

    def _add_tree(self, nodes, depth, counts, query):
        from ui.theme import _C
        for node in nodes:
            name_lower = node["name"].lower()
            if query and query not in name_lower and not node["children"]:
                continue

            desc = self._svc.get_descendants(node["id"])
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
        cat = self._svc.get_item_category(self._active_id)
        if not cat:
            return

        desc   = self._svc.get_descendants(self._active_id)
        counts = self._svc.count_designs_per_category()
        total  = sum(counts.get(d, 0) for d in desc)

        msg = tr("delete_confirm_msg").format(name=cat['name'])
        cc  = len(desc) - 1
        if cc:
            msg += f"\n{tr('design_cats_has_children_warn').format(count=cc)}"
        if total:
            msg += f"\n{tr('design_cats_has_designs_warn').format(count=total)}"

        if QMessageBox.question(
            self, tr("confirm_delete"), msg, QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            for d in sorted(desc, reverse=True):
                self._svc.delete_item_category(d)
            self._active_id = "ALL"
            self._load()
            self.category_changed.emit(None)

    def refresh(self):
        self._load(query=self._inp_search.text().strip())

    def current_category_id(self):
        return None if self._active_id == "ALL" else self._active_id
