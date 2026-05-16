"""
ui/tabs/design/designs_tab.py
==============================
تبويب إدارة التصميمات.

يتضمن:
  - جدول التصميمات مع فلتر متقدم (بالاسم + التصنيف + مجموعة المقاسات)
  - فورم إضافة/تعديل التصميم
  - لوحة ربط التصميم بمجموعات المقاسات + إدخال القيم
  - حساب القيم التلقائية بناءً على الاعتماديات
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QPushButton, QLabel, QLineEdit,
    QComboBox, QDoubleSpinBox, QGroupBox, QFormLayout,
    QMessageBox, QDialog, QDialogButtonBox, QScrollArea,
    QSizePolicy, QFrame, QCheckBox,
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QColor, QFont

from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets, fetch_dimension_set,
    fetch_fields_for_set, fetch_field_dep,
    fetch_all_design_categories, build_category_tree,
)
from db.designs.designs_repo import (
    fetch_all_designs, fetch_design,
    insert_design, update_design, delete_design,
    fetch_design_links_for_design, fetch_link,
    add_design_link, remove_design_link, update_design_link_label,
    fetch_dim_values, set_dim_value, save_all_dim_values,
    recalc_auto_values, fetch_full_design_data,
)
from ui.helpers import make_table, buttons_row, confirm_delete, danger_button


# ══════════════════════════════════════════════════════════
# لوحة إدخال قيم مجموعة مقاسات واحدة
# ══════════════════════════════════════════════════════════

class _DimValuesCard(QFrame):
    """
    بطاقة لإدخال قيم حقول مجموعة مقاسات واحدة.
    تظهر داخل لوحة ربط المقاسات بالتصميم.
    """

    remove_requested = pyqtSignal(int)   # link_id
    saved            = pyqtSignal()

    def __init__(self, conn, link_id: int, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self.link_id = link_id
        self._fields = []
        self._spins  = {}   # field_id -> QDoubleSpinBox
        self._auto_chks = {}  # field_id -> QCheckBox (is_auto)
        self._build()
        self._load_values()

    def _build(self):
        self.setStyleSheet("""
            QFrame {
                background: white;
                border: 1px solid #c5cae9;
                border-radius: 8px;
                margin: 4px;
            }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        # ── رأس البطاقة ──
        link = fetch_link(self.conn, self.link_id)
        if not link:
            return

        ds = fetch_dimension_set(self.conn, link["set_id"])
        set_name = ds["name"] if ds else "مجموعة مقاسات"
        label    = link["label"] or set_name

        hdr_row = QHBoxLayout()
        icon = QLabel("📐")
        icon.setStyleSheet("font-size:14px; background:transparent; border:none;")
        self.inp_label = QLineEdit(label)
        self.inp_label.setMinimumHeight(28)
        self.inp_label.setPlaceholderText("تسمية هذه المقاسة (مثال: مقاس L)")
        self.inp_label.setStyleSheet("""
            QLineEdit {
                font-weight: bold;
                font-size: 12px;
                color: #1565c0;
                border: none;
                border-bottom: 2px solid #c5cae9;
                background: transparent;
                padding: 2px 4px;
            }
            QLineEdit:focus { border-bottom-color: #1565c0; }
        """)
        self.inp_label.editingFinished.connect(self._save_label)

        lbl_set = QLabel(f"({set_name})")
        lbl_set.setStyleSheet("color:#888; font-size:10px; background:transparent; border:none;")

        btn_remove = QPushButton("✖")
        btn_remove.setFixedSize(24, 24)
        btn_remove.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #bbb;
                font-size: 11px;
            }
            QPushButton:hover { color: #e53935; }
        """)
        btn_remove.clicked.connect(lambda: self.remove_requested.emit(self.link_id))

        hdr_row.addWidget(icon)
        hdr_row.addWidget(self.inp_label, stretch=1)
        hdr_row.addWidget(lbl_set)
        hdr_row.addWidget(btn_remove)
        root.addLayout(hdr_row)

        # ── حقول الإدخال ──
        self._fields = fetch_fields_for_set(self.conn, link["set_id"])
        self._spins  = {}
        self._auto_chks = {}

        fields_widget = QWidget()
        fields_widget.setStyleSheet("background:transparent; border:none;")
        grid = QVBoxLayout(fields_widget)
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)

        for f in self._fields:
            row_w = QWidget()
            row_w.setStyleSheet("background:transparent; border:none;")
            row_lay = QHBoxLayout(row_w)
            row_lay.setContentsMargins(0, 0, 0, 0)
            row_lay.setSpacing(8)

            lbl = QLabel(f["label"])
            lbl.setFixedWidth(100)
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setStyleSheet("background:transparent; border:none;")

            spin = QDoubleSpinBox()
            spin.setRange(-99999, 99999)
            spin.setDecimals(4)
            spin.setMinimumHeight(28)
            spin.setMinimumWidth(100)

            unit_lbl = QLabel(f["unit"] or "")
            unit_lbl.setFixedWidth(30)
            unit_lbl.setStyleSheet("color:#888; background:transparent; border:none;")

            # زر حساب تلقائي (يظهر فقط لو الحقل له اعتمادية)
            dep = fetch_field_dep(self.conn, f["id"])
            if dep:
                btn_auto = QPushButton("⟳ حساب")
                btn_auto.setFixedHeight(26)
                btn_auto.setStyleSheet("""
                    QPushButton {
                        background: #e8f5e9;
                        border: 1px solid #a5d6a7;
                        border-radius: 4px;
                        color: #2e7d32;
                        font-size: 10px;
                        padding: 2px 8px;
                    }
                    QPushButton:hover { background: #c8e6c9; }
                """)
                dep_captured = dep
                spin_captured = spin
                fid_captured = f["id"]
                btn_auto.clicked.connect(
                    lambda _, d=dep_captured, s=spin_captured, fid=fid_captured:
                    self._calc_auto(d, s, fid)
                )

                chk_auto = QCheckBox("تلقائي")
                chk_auto.setStyleSheet("color:#2e7d32; font-size:10px; background:transparent; border:none;")
                self._auto_chks[f["id"]] = chk_auto
                chk_auto.toggled.connect(lambda checked, s=spin, b=btn_auto:
                                         (s.setReadOnly(checked),
                                          s.setStyleSheet("background:#f1f8e9;" if checked else "")))

                row_lay.addWidget(lbl)
                row_lay.addWidget(spin, stretch=1)
                row_lay.addWidget(unit_lbl)
                row_lay.addWidget(btn_auto)
                row_lay.addWidget(chk_auto)
            else:
                row_lay.addWidget(lbl)
                row_lay.addWidget(spin, stretch=1)
                row_lay.addWidget(unit_lbl)

            self._spins[f["id"]] = spin
            grid.addWidget(row_w)

        root.addWidget(fields_widget)

        # ── أزرار الحفظ ──
        btn_save    = QPushButton("💾  حفظ المقاسات")
        btn_save_all = QPushButton("⟳  حساب الكل تلقائياً")
        btn_save.setMinimumHeight(30)
        btn_save_all.setMinimumHeight(30)
        btn_save.setStyleSheet("""
            QPushButton {
                background: #1565c0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_save_all.setStyleSheet("""
            QPushButton {
                background: #e8f5e9;
                color: #2e7d32;
                border: 1px solid #a5d6a7;
                border-radius: 4px;
                padding: 4px 12px;
            }
            QPushButton:hover { background: #c8e6c9; }
        """)
        btn_save.clicked.connect(self._save_values)
        btn_save_all.clicked.connect(self._calc_all_auto)

        btn_row = QHBoxLayout()
        btn_row.addWidget(btn_save)
        btn_row.addWidget(btn_save_all)
        btn_row.addStretch()
        root.addLayout(btn_row)

    def _load_values(self):
        values = fetch_dim_values(self.conn, self.link_id)
        for fid, spin in self._spins.items():
            info = values.get(fid, {})
            val  = info.get("value_num")
            if val is not None:
                spin.setValue(float(val))
            is_auto = bool(info.get("is_auto", False))
            if fid in self._auto_chks:
                self._auto_chks[fid].setChecked(is_auto)
                spin.setReadOnly(is_auto)

    def _save_label(self):
        label = self.inp_label.text().strip()
        update_design_link_label(self.conn, self.link_id, label)

    def _calc_auto(self, dep, spin, field_id):
        """حساب قيمة حقل واحد تلقائياً."""
        # احفظ قيمة الحقل المصدر أولاً
        self._save_values(silent=True)
        from db.designs.dimension_sets_repo import calc_auto_value
        val = calc_auto_value(self.conn, field_id, self.link_id)
        if val is not None:
            spin.setValue(val)
            set_dim_value(self.conn, self.link_id, field_id, value_num=val, is_auto=True)
            if field_id in self._auto_chks:
                self._auto_chks[field_id].setChecked(True)
        else:
            QMessageBox.information(self, "تنبيه", "أدخل قيمة الحقل المصدر أولاً")

    def _calc_all_auto(self):
        """حساب كل الحقول التلقائية."""
        self._save_values(silent=True)
        computed = recalc_auto_values(self.conn, self.link_id)
        for fid, val in computed.items():
            if fid in self._spins:
                self._spins[fid].setValue(val)
            if fid in self._auto_chks:
                self._auto_chks[fid].setChecked(True)
        self.saved.emit()

    def _save_values(self, silent=False):
        values    = {}
        auto_flags = {}
        for fid, spin in self._spins.items():
            values[fid] = spin.value()
            auto_flags[fid] = self._auto_chks.get(fid, QCheckBox()).isChecked()
        save_all_dim_values(self.conn, self.link_id, values, auto_flags)
        self._save_label()
        if not silent:
            self.saved.emit()


# ══════════════════════════════════════════════════════════
# لوحة ربط التصميم بالمقاسات
# ══════════════════════════════════════════════════════════

class _DimLinksPanel(QWidget):
    """
    لوحة لإضافة وإدارة روابط التصميم بمجموعات المقاسات.
    """

    changed = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._design_id = None
        self._cards     = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── شريط الإضافة ──
        add_row = QHBoxLayout()
        lbl = QLabel("إضافة مجموعة مقاسات:")
        lbl.setStyleSheet("font-weight:bold; color:#1565c0;")
        self.cmb_set = QComboBox()
        self.cmb_set.setMinimumHeight(30)
        self.cmb_set.setMinimumWidth(200)
        self.inp_link_label = QLineEdit()
        self.inp_link_label.setPlaceholderText("التسمية (مثال: مقاس L) — اختياري")
        self.inp_link_label.setMinimumHeight(30)
        self.inp_link_label.setMinimumWidth(160)
        btn_add = QPushButton("➕  إضافة")
        btn_add.setMinimumHeight(30)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #1565c0;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 4px 14px;
                font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_add.clicked.connect(self._add_link)

        add_row.addWidget(lbl)
        add_row.addWidget(self.cmb_set, stretch=1)
        add_row.addWidget(self.inp_link_label, stretch=1)
        add_row.addWidget(btn_add)
        root.addLayout(add_row)

        # ── منطقة البطاقات (scroll) ──
        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet("background: #f9f9f9; border:none;")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(0, 0, 0, 0)
        self._cards_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._cards_widget)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f9f9f9; }")
        root.addWidget(scroll, stretch=1)

        self._load_sets_combo()

    def _load_sets_combo(self):
        prev = self.cmb_set.currentData()
        self.cmb_set.blockSignals(True)
        self.cmb_set.clear()
        for ds in fetch_all_dimension_sets(self.conn):
            self.cmb_set.addItem(ds["name"], ds["id"])
        for i in range(self.cmb_set.count()):
            if self.cmb_set.itemData(i) == prev:
                self.cmb_set.setCurrentIndex(i)
                break
        self.cmb_set.blockSignals(False)

    def load_design(self, design_id: int):
        self._design_id = design_id
        self._refresh_cards()
        self._load_sets_combo()

    def clear(self):
        self._design_id = None
        self._clear_cards()

    def _clear_cards(self):
        for card in self._cards:
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        self._cards = []

    def _refresh_cards(self):
        self._clear_cards()
        if self._design_id is None:
            return
        links = fetch_design_links_for_design(self.conn, self._design_id)
        for link in links:
            self._add_card(link["id"])

    def _add_card(self, link_id: int):
        card = _DimValuesCard(self.conn, link_id)
        card.remove_requested.connect(self._remove_link)
        card.saved.connect(self.changed.emit)
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
        self._cards.append(card)

    def _add_link(self):
        if self._design_id is None:
            QMessageBox.information(self, "تنبيه", "احفظ التصميم أولاً")
            return
        set_id = self.cmb_set.currentData()
        if set_id is None:
            QMessageBox.warning(self, "تنبيه", "اختر مجموعة مقاسات")
            return
        label = self.inp_link_label.text().strip()
        # عدد الروابط الحالية كـ sort_order
        current_count = len(fetch_design_links_for_design(self.conn, self._design_id))
        link_id = add_design_link(
            self.conn, self._design_id, set_id, label, current_count
        )
        self.inp_link_label.clear()
        self._add_card(link_id)
        self.changed.emit()

    def _remove_link(self, link_id: int):
        link = fetch_link(self.conn, link_id)
        if not link:
            return
        if QMessageBox.question(
            self, "تأكيد", "حذف هذه المقاسة من التصميم؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            remove_design_link(self.conn, link_id)
            self._refresh_cards()
            self.changed.emit()


# ══════════════════════════════════════════════════════════
# لوحة فورم التصميم
# ══════════════════════════════════════════════════════════

class _DesignFormPanel(QWidget):
    """فورم إضافة/تعديل تصميم + ربط المقاسات."""

    saved   = pyqtSignal()
    cleared = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._editing_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── قسم بيانات التصميم الأساسية (ثابت في الأعلى) ──
        top = QWidget()
        top.setStyleSheet("background:#f0f4ff; border-bottom:1px solid #c5cae9;")
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(12, 10, 12, 10)
        top_lay.setSpacing(8)

        self.lbl_mode = QLabel("─── تصميم جديد ───")
        self.lbl_mode.setStyleSheet("font-weight:bold; color:#1565c0; font-size:13px;")

        # صف الاسم والتصنيف
        info_row = QHBoxLayout()
        info_row.setSpacing(8)
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم التصميم...")
        self.inp_name.setMinimumHeight(32)

        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(32)
        self.cmb_category.setMinimumWidth(160)

        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(32)

        info_row.addWidget(QLabel("الاسم:"))
        info_row.addWidget(self.inp_name, stretch=2)
        info_row.addWidget(QLabel("التصنيف:"))
        info_row.addWidget(self.cmb_category)
        info_row.addWidget(QLabel("ملاحظات:"))
        info_row.addWidget(self.inp_notes, stretch=1)

        # أزرار
        self.btn_save   = QPushButton("💾  حفظ التصميم")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setMinimumHeight(32)
        self.btn_cancel.setMinimumHeight(32)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background:#1565c0; color:white; border:none;
                border-radius:4px; padding:4px 16px; font-weight:bold;
            }
            QPushButton:hover { background:#0d47a1; }
        """)
        self.btn_cancel.setVisible(False)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self._cancel)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()

        top_lay.addWidget(self.lbl_mode)
        top_lay.addLayout(info_row)
        top_lay.addLayout(btn_row)
        root.addWidget(top)

        # ── لوحة المقاسات ──
        dim_lbl = QLabel("  📐  مقاسات التصميم")
        dim_lbl.setStyleSheet("""
            font-weight:bold; font-size:12px; color:#1565c0;
            background:#e8f0fe; padding:6px 12px;
            border-bottom:1px solid #c5cae9;
        """)
        root.addWidget(dim_lbl)

        self._dim_panel = _DimLinksPanel(self.conn)
        self._dim_panel.changed.connect(self.saved.emit)
        root.addWidget(self._dim_panel, stretch=1)

        self._reload_categories()

    def _reload_categories(self):
        prev = self.cmb_category.currentData()
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("— بدون تصنيف —", None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
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
            self.cmb_category.addItem(
                f"{indent}{arrow}{node['name']}", node["id"]
            )
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    def load_design(self, design_id: int):
        d = fetch_design(self.conn, design_id)
        if not d:
            return
        self._editing_id = design_id
        self.inp_name.setText(d["name"])
        self.inp_notes.setText(d["notes"] or "")
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == d["category_id"]:
                self.cmb_category.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"تعديل: {d['name']}")
        self.btn_cancel.setVisible(True)
        self._dim_panel.load_design(design_id)

    def reset(self):
        self._editing_id = None
        self.inp_name.clear()
        self.inp_notes.clear()
        self.cmb_category.setCurrentIndex(0)
        self.lbl_mode.setText("─── تصميم جديد ───")
        self.btn_cancel.setVisible(False)
        self._dim_panel.clear()
        self.cleared.emit()

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصميم")
            return
        cat_id = self.cmb_category.currentData()
        notes  = self.inp_notes.text().strip()

        if self._editing_id:
            update_design(self.conn, self._editing_id, name, cat_id, notes)
        else:
            self._editing_id = insert_design(self.conn, name, cat_id, notes)
            self.lbl_mode.setText(f"تعديل: {name}")
            self.btn_cancel.setVisible(True)
            self._dim_panel.load_design(self._editing_id)

        self.saved.emit()

    def _cancel(self):
        self.reset()


# ══════════════════════════════════════════════════════════
# جدول التصميمات
# ══════════════════════════════════════════════════════════

class _DesignsTable(QWidget):
    """جدول التصميمات مع فلتر متقدم."""

    design_selected = pyqtSignal(int)    # design_id
    design_deleted  = pyqtSignal()

    def __init__(self, conn, form_panel: _DesignFormPanel, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._form      = form_panel
        self._all_rows  = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── شريط الفلتر ──
        filter_frame = QFrame()
        filter_frame.setStyleSheet("""
            QFrame {
                background: #f0f4ff;
                border: 1px solid #c5cae9;
                border-radius: 6px;
            }
        """)
        filter_lay = QVBoxLayout(filter_frame)
        filter_lay.setContentsMargins(8, 6, 8, 6)
        filter_lay.setSpacing(6)

        # صف البحث
        row1 = QHBoxLayout()
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍 بحث بالاسم...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.textChanged.connect(self._apply_filter)

        row1.addWidget(QLabel("🔍"))
        row1.addWidget(self.inp_search, stretch=1)

        # صف التصنيف + المقاسات
        row2 = QHBoxLayout()
        self.cmb_cat_filter = QComboBox()
        self.cmb_cat_filter.setMinimumHeight(28)
        self.cmb_cat_filter.setMinimumWidth(140)
        self.cmb_cat_filter.currentIndexChanged.connect(self._apply_filter)

        self.cmb_set_filter = QComboBox()
        self.cmb_set_filter.setMinimumHeight(28)
        self.cmb_set_filter.setMinimumWidth(140)
        self.cmb_set_filter.currentIndexChanged.connect(self._apply_filter)

        btn_reset = QPushButton("↺ مسح")
        btn_reset.setMinimumHeight(28)
        btn_reset.setStyleSheet("""
            QPushButton {
                background: #e8eaf6; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 10px;
                color: #3949ab; font-size:11px;
            }
            QPushButton:hover { background: #c5cae9; }
        """)
        btn_reset.clicked.connect(self._reset_filter)

        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet("color:#1565c0; font-size:10px; font-weight:bold; background:transparent; border:none;")

        row2.addWidget(QLabel("📁"))
        row2.addWidget(self.cmb_cat_filter)
        row2.addWidget(QLabel("📐"))
        row2.addWidget(self.cmb_set_filter)
        row2.addWidget(btn_reset)
        row2.addStretch()
        row2.addWidget(self.lbl_count)

        filter_lay.addLayout(row1)
        filter_lay.addLayout(row2)
        root.addWidget(filter_frame)

        # ── الجدول ──
        self.table = make_table(
            ["ID", "الاسم", "التصنيف", "عدد المقاسات", "آخر تعديل"],
            stretch_col=1
        )
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(2, 120)
        self.table.setColumnWidth(3, 90)
        self.table.setColumnWidth(4, 120)
        self.table.itemSelectionChanged.connect(self._on_select)
        root.addWidget(self.table)

        # ── أزرار ──
        btn_edit = QPushButton("✏️  تعديل")
        btn_del  = danger_button("🗑️  حذف")
        btn_view = QPushButton("👁  عرض تفاصيل")
        for b in (btn_edit, btn_del, btn_view):
            b.setMinimumHeight(28)
        btn_edit.clicked.connect(self._edit)
        btn_del.clicked.connect(self._delete)
        btn_view.clicked.connect(self._view_details)
        root.addLayout(buttons_row(btn_edit, btn_del, btn_view))

        self._reload_filter_combos()

    def _reload_filter_combos(self):
        # تصنيفات
        prev_cat = self.cmb_cat_filter.currentData()
        self.cmb_cat_filter.blockSignals(True)
        self.cmb_cat_filter.clear()
        self.cmb_cat_filter.addItem("— كل التصنيفات —", None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_cat_nodes_to_combo(self.cmb_cat_filter, tree, 0)
        for i in range(self.cmb_cat_filter.count()):
            if self.cmb_cat_filter.itemData(i) == prev_cat:
                self.cmb_cat_filter.setCurrentIndex(i)
                break
        self.cmb_cat_filter.blockSignals(False)

        # مجموعات المقاسات
        prev_set = self.cmb_set_filter.currentData()
        self.cmb_set_filter.blockSignals(True)
        self.cmb_set_filter.clear()
        self.cmb_set_filter.addItem("— كل المقاسات —", None)
        for ds in fetch_all_dimension_sets(self.conn):
            self.cmb_set_filter.addItem(ds["name"], ds["id"])
        for i in range(self.cmb_set_filter.count()):
            if self.cmb_set_filter.itemData(i) == prev_set:
                self.cmb_set_filter.setCurrentIndex(i)
                break
        self.cmb_set_filter.blockSignals(False)

    def _add_cat_nodes_to_combo(self, combo, nodes, depth):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            combo.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes_to_combo(combo, node["children"], depth + 1)

    def _load(self):
        self._all_rows = list(fetch_all_designs(self.conn))
        self._reload_filter_combos()
        self._apply_filter()

    def _apply_filter(self):
        q      = self.inp_search.text().strip().lower()
        cat_id = self.cmb_cat_filter.currentData()
        set_id = self.cmb_set_filter.currentData()
        prev   = self._selected_id()
        self.table.setRowCount(0)
        shown  = 0

        for d in self._all_rows:
            if q and q not in d["name"].lower():
                continue
            if cat_id is not None and d["category_id"] != cat_id:
                continue
            if set_id is not None:
                # تحقق إن التصميم مرتبط بهذه المجموعة
                linked = self.conn.execute(
                    "SELECT 1 FROM design_dimensions WHERE design_id=? AND set_id=?",
                    (d["id"], set_id)
                ).fetchone()
                if not linked:
                    continue
            # عدد المقاسات
            dim_cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM design_dimensions WHERE design_id=?",
                (d["id"],)
            ).fetchone()["c"]

            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(d["id"])))
            self.table.setItem(r, 1, QTableWidgetItem(d["name"]))
            self.table.setItem(r, 2, QTableWidgetItem(d["category_name"] or "—"))
            self.table.setItem(r, 3, QTableWidgetItem(str(dim_cnt)))
            updated = (d["updated_at"] or "")[:16].replace("T", " ")
            self.table.setItem(r, 4, QTableWidgetItem(updated))
            self.table.item(r, 0).setData(Qt.UserRole, d["id"])
            shown += 1

        if shown == len(self._all_rows):
            self.lbl_count.setText(f"({shown})")
        else:
            self.lbl_count.setText(f"({shown} / {len(self._all_rows)})")

        if prev is not None:
            for r in range(self.table.rowCount()):
                if self.table.item(r, 0).data(Qt.UserRole) == prev:
                    self.table.selectRow(r)
                    break

    def _reset_filter(self):
        self.inp_search.blockSignals(True)
        self.cmb_cat_filter.blockSignals(True)
        self.cmb_set_filter.blockSignals(True)
        self.inp_search.clear()
        self.cmb_cat_filter.setCurrentIndex(0)
        self.cmb_set_filter.setCurrentIndex(0)
        self.inp_search.blockSignals(False)
        self.cmb_cat_filter.blockSignals(False)
        self.cmb_set_filter.blockSignals(False)
        self._apply_filter()

    def _selected_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        did = self._selected_id()
        if did:
            self.design_selected.emit(did)

    def _edit(self):
        did = self._selected_id()
        if did is None:
            QMessageBox.information(self, "تنبيه", "اختر تصميماً أولاً")
            return
        self._form.load_design(did)

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
            self._form.reset()
            self._load()
            self.design_deleted.emit()

    def _view_details(self):
        did = self._selected_id()
        if did is None:
            QMessageBox.information(self, "تنبيه", "اختر تصميماً أولاً")
            return
        data = fetch_full_design_data(self.conn, did)
        if not data:
            return

        dlg = QDialog(self)
        dlg.setWindowTitle(f"تفاصيل التصميم — {data['name']}")
        dlg.setMinimumSize(600, 500)
        lay = QVBoxLayout(dlg)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        c_lay = QVBoxLayout(container)
        c_lay.setSpacing(12)

        # رأس
        hdr = QLabel(f"🎨  {data['name']}")
        hdr.setStyleSheet("font-size:16px; font-weight:bold; color:#1565c0;")
        c_lay.addWidget(hdr)

        if data.get("category_name"):
            cat_lbl = QLabel(f"📁  {data['category_name']}")
            cat_lbl.setStyleSheet("color:#666;")
            c_lay.addWidget(cat_lbl)

        if data.get("notes"):
            notes_lbl = QLabel(f"📝  {data['notes']}")
            notes_lbl.setWordWrap(True)
            notes_lbl.setStyleSheet("color:#555; background:#f5f5f5; padding:6px; border-radius:4px;")
            c_lay.addWidget(notes_lbl)

        # المقاسات
        for link in data.get("links", []):
            grp = QGroupBox(f"📐  {link['label']}")
            grp.setStyleSheet("QGroupBox { font-weight:bold; color:#1565c0; }")
            g_lay = QFormLayout(grp)
            g_lay.setLabelAlignment(Qt.AlignRight)
            for f in link["fields"]:
                val   = f["value"]
                label = f["label"]
                unit  = f["unit"] or ""
                auto  = " 🔄" if f["is_auto"] else ""
                val_str = f"{val:g} {unit}" if val is not None else "—"
                val_lbl = QLabel(f"{val_str}{auto}")
                val_lbl.setStyleSheet(
                    "color:#2e7d32; font-weight:bold;" if f["is_auto"]
                    else "color:#333;"
                )
                g_lay.addRow(f"{label}:", val_lbl)
            c_lay.addWidget(grp)

        c_lay.addStretch()
        scroll.setWidget(container)
        lay.addWidget(scroll)

        btns = QDialogButtonBox(QDialogButtonBox.Close)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        dlg.exec_()

    def refresh(self):
        self._load()


# ══════════════════════════════════════════════════════════
# تبويب التصميمات الرئيسي
# ══════════════════════════════════════════════════════════

class DesignsTab(QWidget):
    """التبويب الرئيسي لإدارة التصميمات."""

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn = conn
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(5)
        splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)

        # ── لوحة اليسار: الجدول + الفلتر ──
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)

        self._form = _DesignFormPanel(self.conn)
        self._table = _DesignsTable(self.conn, self._form)

        self._form.saved.connect(self._table.refresh)
        self._form.cleared.connect(self._table.refresh)
        self._table.design_deleted.connect(self._table.refresh)

        left_lay.addWidget(self._table)

        splitter.addWidget(left)
        splitter.addWidget(self._form)
        splitter.setSizes([380, 620])

        root.addWidget(splitter)

    def refresh(self):
        self._table.refresh()