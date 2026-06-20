"""
ui/tabs/design/designs/_design_detail_panel.py
=====================================================
لوحة تفاصيل التصميم — يمين تبويب التصميمات.
مع دعم كامل لتغيير حجم الخط ديناميكياً.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QFrame,
    QScrollArea, QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from db.designs.designs_repo import (
    fetch_design, insert_design, update_design,
)
from db.designs.designs_sizes_repo import (
    fetch_design_sizes, delete_design_size,
)
from db.designs.design_item_categories_repo import (
    fetch_all_item_categories,
    build_item_category_tree,
)
from ._size_card   import _SizeCard
from ._size_dialog import _SizeDialog
from ui.events import bus
from ui.tabs.design.design_styles import get_styles
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import get_font_size, fs

# ── Palette من _C ──────────────────────────────────────
_BG          = _C["bg_input"]
_BG_SURFACE  = _C["bg_surface"]
_BORDER      = _C["border"]
_BORDER_MED  = _C["border_med"]
_TEXT_PRI    = _C["text_primary"]
_TEXT_SEC    = _C["text_sec"]
_TEXT_MUT    = _C["text_muted"]
_ACCENT      = _C["accent"]
_ACCENT_LT   = _C["accent_light"]
_ACCENT_BDR  = _C["accent_mid"]
_ACCENT_DARK = _C["accent_hover"]
_SUCCESS     = _C["success"]
_SUCCESS_LT  = _C["success_bg"]
_SUCCESS_BDR = _C["success_border"]
_DANGER      = _C["danger"]
_RADIUS_SM   = "6px"
_RADIUS_XS   = "4px"


class _DesignDetailPanel(QWidget):
    saved   = pyqtSignal()
    cleared = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._design_id  = None
        self._set_filter = None
        self._size_cards = []
        self._build()
        self._reload_categories()
        bus.font_changed.connect(self._on_font_changed)

    def _on_font_changed(self, size: int):
        """إعادة تطبيق الـ stylesheets عند تغيير حجم الخط."""
        self._apply_dynamic_styles()

    def _apply_dynamic_styles(self):
        s = get_styles()

        # Header labels
        self._lbl_title.setStyleSheet(s.label_header())
        self._lbl_badge.setStyleSheet(s.badge_accent())

        # Buttons
        self.btn_new.setStyleSheet(s.btn_ghost())
        self.btn_save.setStyleSheet(s.btn_primary())
        self._btn_add_size.setStyleSheet(s.btn_success())

        # Inputs
        self.inp_name.setStyleSheet(s.input_field())
        self.inp_notes.setStyleSheet(s.input_field())
        self.cmb_cat.setStyleSheet(s.combo_field())

        # Section labels
        self._lbl_sizes.setStyleSheet(s.label_section())
        self.lbl_sizes_count.setStyleSheet(s.badge_count())

        # Field labels
        for lbl in self._field_labels:
            lbl.setStyleSheet(s.label_field())

    def _build(self):
        s = get_styles()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._field_labels = []   # نحتفظ بمراجع لتحديثها لاحقاً

        # ── Header ──────────────────────────────────────
        hdr = QFrame()
        hdr.setStyleSheet(f"QFrame {{ background:{_BG}; border-bottom:1px solid {_BORDER}; }}")
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(18, 14, 18, 16)
        hdr_lay.setSpacing(14)

        # صف العنوان
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self._lbl_title = QLabel(tr("design_detail_new_title"))
        self._lbl_title.setStyleSheet(s.label_header())

        self._lbl_badge = QLabel(tr("design_detail_new_badge"))
        self._lbl_badge.setStyleSheet(s.badge_accent())
        self._lbl_badge.setVisible(False)

        title_row.addWidget(self._lbl_title, stretch=1)
        title_row.addWidget(self._lbl_badge)

        # أزرار الحفظ
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.btn_new = QPushButton(tr("design_detail_new_btn"))
        self.btn_new.setStyleSheet(s.btn_ghost())
        self.btn_new.clicked.connect(self.reset)

        self.btn_save = QPushButton(tr("design_detail_save_btn"))
        self.btn_save.setStyleSheet(s.btn_primary())
        self.btn_save.clicked.connect(self._save)

        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_save)

        hdr_lay.addLayout(title_row)

        # حقل الاسم
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        lbl_name = QLabel(tr("design_detail_name_label"))
        lbl_name.setStyleSheet(s.label_field())
        self._field_labels.append(lbl_name)
        name_col.addWidget(lbl_name)
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("design_detail_name_placeholder"))
        self.inp_name.setStyleSheet(s.input_field())
        name_col.addWidget(self.inp_name)
        hdr_lay.addLayout(name_col)

        # التصنيف + الملاحظات
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        cat_col = QVBoxLayout()
        cat_col.setSpacing(4)
        lbl_cat = QLabel(tr("design_detail_category_label"))
        lbl_cat.setStyleSheet(s.label_field())
        self._field_labels.append(lbl_cat)
        cat_col.addWidget(lbl_cat)
        self.cmb_cat = QComboBox()
        self.cmb_cat.setStyleSheet(s.combo_field())
        self.cmb_cat.setMinimumWidth(160)
        cat_col.addWidget(self.cmb_cat)

        notes_col = QVBoxLayout()
        notes_col.setSpacing(4)
        lbl_notes = QLabel(tr("design_detail_notes_label"))
        lbl_notes.setStyleSheet(s.label_field())
        self._field_labels.append(lbl_notes)
        notes_col.addWidget(lbl_notes)
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("design_detail_notes_placeholder"))
        self.inp_notes.setStyleSheet(s.input_field())
        notes_col.addWidget(self.inp_notes)

        row2.addLayout(cat_col, stretch=1)
        row2.addLayout(notes_col, stretch=2)
        hdr_lay.addLayout(row2)
        hdr_lay.addLayout(btn_row)
        root.addWidget(hdr)

        # ── قسم المقاسات ────────────────────────────────
        sizes_hdr = QFrame()
        sizes_hdr.setStyleSheet(
            f"QFrame {{ background:{_BG_SURFACE}; border-bottom:1px solid {_BORDER}; }}"
        )
        sh_lay = QHBoxLayout(sizes_hdr)
        sh_lay.setContentsMargins(18, 10, 18, 10)
        sh_lay.setSpacing(8)

        self._lbl_sizes = QLabel(tr("design_detail_sizes_section"))
        self._lbl_sizes.setStyleSheet(s.label_section())

        self.lbl_sizes_count = QLabel("")
        self.lbl_sizes_count.setStyleSheet(s.badge_count())
        self.lbl_sizes_count.setVisible(False)

        self._btn_add_size = QPushButton(tr("design_detail_add_size_btn"))
        self._btn_add_size.setStyleSheet(s.btn_success())
        self._btn_add_size.clicked.connect(self._add_size)

        sh_lay.addWidget(self._lbl_sizes)
        sh_lay.addWidget(self.lbl_sizes_count)
        sh_lay.addStretch()
        sh_lay.addWidget(self._btn_add_size)
        root.addWidget(sizes_hdr)

        # ── Scroll المقاسات ─────────────────────────────
        self._sizes_scroll = QScrollArea()
        self._sizes_scroll.setWidgetResizable(True)
        self._sizes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._sizes_scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{_BG_SURFACE}; }}
            QScrollBar:vertical {{
                background:{_BG_SURFACE}; width:5px; border-radius:2px;
            }}
            QScrollBar::handle:vertical {{
                background:{_BORDER_MED}; border-radius:2px; min-height:20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        self._sizes_widget = QWidget()
        self._sizes_widget.setStyleSheet(f"background:{_BG_SURFACE};")
        self._sizes_layout = QVBoxLayout(self._sizes_widget)
        self._sizes_layout.setContentsMargins(14, 14, 14, 14)
        self._sizes_layout.setSpacing(10)
        self._sizes_layout.addStretch()

        self._sizes_scroll.setWidget(self._sizes_widget)
        root.addWidget(self._sizes_scroll, stretch=1)

        # Empty state
        self._empty_sizes = QFrame()
        self._empty_sizes.setStyleSheet("background:transparent; border:none;")
        es_lay = QVBoxLayout(self._empty_sizes)
        es_lay.setAlignment(Qt.AlignCenter)
        es_lay.setSpacing(6)

        es_icon = QLabel("📐")
        es_icon.setAlignment(Qt.AlignCenter)
        es_icon.setStyleSheet(f"font-size:{fs(get_font_size(),+12)}pt; background:transparent;")

        self._es_lbl = QLabel(tr("design_detail_no_sizes_title"))
        self._es_lbl.setAlignment(Qt.AlignCenter)
        self._es_lbl.setStyleSheet(s.label_secondary())

        self._es_sub = QLabel(tr("design_detail_no_sizes_hint"))
        self._es_sub.setAlignment(Qt.AlignCenter)
        self._es_sub.setStyleSheet(s.label_muted())

        es_lay.addWidget(es_icon)
        es_lay.addWidget(self._es_lbl)
        es_lay.addWidget(self._es_sub)

        self._sizes_layout.insertWidget(0, self._empty_sizes)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def connect_categories_panel(self, cats_panel):
        cats_panel.category_changed.connect(lambda _: self._reload_categories())

    def load_design(self, design_id: int):
        self._design_id = design_id
        design = fetch_design(self.conn, design_id)
        if not design:
            return

        self.inp_name.setText(design["name"])
        self.inp_notes.setText(design["notes"] or "")
        self._lbl_title.setText(design["name"])
        self._lbl_badge.setText(tr("design_detail_saved_badge"))
        self._lbl_badge.setVisible(True)

        cat_id = design["item_category_id"]
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == cat_id:
                self.cmb_cat.setCurrentIndex(i)
                break

        self._load_sizes()

    def reset(self):
        self._design_id = None
        self.inp_name.clear()
        self.inp_notes.clear()
        self.cmb_cat.setCurrentIndex(0)
        self._lbl_title.setText(tr("design_detail_new_title"))
        self._lbl_badge.setVisible(False)
        self._clear_size_cards()
        self.cleared.emit()

    def filter_by_set(self, set_id):
        self._set_filter = set_id
        if self._design_id:
            self._load_sizes()

    def _reload_categories(self):
        prev = self.cmb_cat.currentData()
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem(tr("design_detail_no_category"), None)

        rows = fetch_all_item_categories(self.conn)
        tree = build_item_category_tree(rows)
        self._add_cat_nodes(tree, 0)

        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == prev:
                self.cmb_cat.setCurrentIndex(i)
                break
        self.cmb_cat.blockSignals(False)

    def _add_cat_nodes(self, nodes, depth):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_cat.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    # ══════════════════════════════════════════════════════
    # حفظ
    # ══════════════════════════════════════════════════════

    def _save(self):
        s = get_styles()
        name = self.inp_name.text().strip()
        if not name:
            self.inp_name.setFocus()
            self.inp_name.setStyleSheet(
                s.input_field() + f"QLineEdit{{border-color:{_DANGER};}}"
            )
            QMessageBox.warning(self, tr("warning"), tr("design_detail_name_required"))
            return

        self.inp_name.setStyleSheet(s.input_field())
        cat_id = self.cmb_cat.currentData()
        notes  = self.inp_notes.text().strip()

        if self._design_id:
            update_design(self.conn, self._design_id, name, cat_id, notes)
        else:
            self._design_id = insert_design(self.conn, name, cat_id, notes)

        self._lbl_title.setText(name)
        self._lbl_badge.setText(tr("design_detail_saved_badge"))
        self._lbl_badge.setVisible(True)
        self.saved.emit()

    # ══════════════════════════════════════════════════════
    # المقاسات
    # ══════════════════════════════════════════════════════

    def _load_sizes(self):
        self._clear_size_cards()
        if not self._design_id:
            return

        sizes = fetch_design_sizes(self.conn, self._design_id)

        if self._set_filter is not None:
            sizes = [s for s in sizes if s["set_id"] == self._set_filter]

        count = len(sizes)
        self._empty_sizes.setVisible(count == 0)

        if count > 0:
            self.lbl_sizes_count.setText(str(count))
            self.lbl_sizes_count.setVisible(True)
        else:
            self.lbl_sizes_count.setVisible(False)

        for size_data in sizes:
            card = _SizeCard(self.conn, size_data)
            card.edit_requested.connect(self._edit_size)
            card.delete_requested.connect(self._delete_size)
            card.path_changed.connect(lambda: self._load_sizes())
            self._sizes_layout.insertWidget(
                self._sizes_layout.count() - 1, card
            )
            self._size_cards.append(card)

    def _clear_size_cards(self):
        for card in self._size_cards:
            self._sizes_layout.removeWidget(card)
            card.deleteLater()
        self._size_cards = []
        self._empty_sizes.setVisible(True)
        self.lbl_sizes_count.setVisible(False)

    def _add_size(self):
        if not self._design_id:
            name = self.inp_name.text().strip()
            if not name:
                QMessageBox.warning(self, tr("warning"), tr("design_detail_save_first_warn"))
                return
            self._save()
            if not self._design_id:
                return

        dlg = _SizeDialog(self.conn, self._design_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_sizes()

    def _edit_size(self, size_id: int):
        sizes = fetch_design_sizes(self.conn, self._design_id)
        size_data = next((s for s in sizes if s["id"] == size_id), None)
        if not size_data:
            return
        dlg = _SizeDialog(self.conn, self._design_id,
                          size_data=size_data, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_sizes()

    def _delete_size(self, size_id: int):
        if QMessageBox.question(
            self, tr("confirm_delete"),
            tr("design_detail_delete_size_confirm"),
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_design_size(self.conn, size_id)
            self._load_sizes()