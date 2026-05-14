"""
ui/widgets/shared/filter_bar.py
========================
FilterBar — شريط فلتر مشترك يُستخدم في كل التبويبات.

يوفر:
  - بحث نصي بالاسم (QLineEdit مع زر مسح)
  - فلتر بالتصنيف (CategoryCombo)
  - signal filter_changed يُطلق عند أي تغيير

الاستخدام:
    from ui.widgets.filter_bar import FilterBar

    self._filter = FilterBar(conn, scope="raw")
    self._filter.filter_changed.connect(self._apply_filter)
    layout.addWidget(self._filter)

    # في دالة التحميل:
    def _apply_filter(self):
        name_q  = self._filter.name_query      # str
        cat_id  = self._filter.category_id     # int | None
        rows = [r for r in self._all_rows
                if self._filter.match(r["name"], r["category_id"])]
        ...
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QLabel, QComboBox,
)
from PyQt5.QtCore import pyqtSignal, Qt, QTimer
from PyQt5.QtGui  import QColor

from db.categories_repo import fetch_all_categories, build_tree
from ui.events import bus


class FilterBar(QWidget):
    """
    شريط فلتر أفقي:
      [🔍 بحث بالاسم ...]  [✖]   [🏷 التصنيف ▼]   [↺ مسح الكل]
    """
    filter_changed = pyqtSignal()

    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self._build()
        # تحديث الـ combo لو تغيرت التصنيفات
        bus.data_changed.connect(self._reload_categories)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        self.setStyleSheet("""
            QWidget {
                background: #f0f4ff;
                border: 1px solid #d0d9f0;
                border-radius: 6px;
            }
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(8)

        # ── أيقونة بحث ──
        lbl_icon = QLabel("🔍")
        lbl_icon.setStyleSheet(
            "background:transparent; border:none; font-size:13px;"
        )
        lbl_icon.setFixedWidth(20)
        lay.addWidget(lbl_icon)

        # ── حقل البحث ──
        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("بحث بالاسم...")
        self.inp_search.setMinimumHeight(28)
        self.inp_search.setStyleSheet("""
            QLineEdit {
                background: white;
                border: 1px solid #c5cae9;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #1565c0;
            }
        """)
        # تأخير بسيط لتجنب البحث عند كل حرف
        self._search_timer = QTimer()
        self._search_timer.setSingleShot(True)
        self._search_timer.setInterval(250)
        self._search_timer.timeout.connect(self.filter_changed.emit)
        self.inp_search.textChanged.connect(
            lambda: self._search_timer.start()
        )
        lay.addWidget(self.inp_search, stretch=2)

        # ── زر مسح البحث ──
        self.btn_clear_search = QPushButton("✖")
        self.btn_clear_search.setFixedSize(24, 24)
        self.btn_clear_search.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #999;
                font-size: 11px;
            }
            QPushButton:hover { color: #e53935; }
        """)
        self.btn_clear_search.setToolTip("مسح البحث")
        self.btn_clear_search.clicked.connect(self._clear_search)
        lay.addWidget(self.btn_clear_search)

        # ── فاصل ──
        sep = QLabel("│")
        sep.setStyleSheet(
            "color:#c5cae9; background:transparent; border:none; font-size:16px;"
        )
        lay.addWidget(sep)

        # ── label التصنيف ──
        lbl_cat = QLabel("🏷")
        lbl_cat.setStyleSheet(
            "background:transparent; border:none; font-size:13px;"
        )
        lbl_cat.setFixedWidth(20)
        lay.addWidget(lbl_cat)

        # ── combo التصنيف ──
        self.cmb_cat = QComboBox()
        self.cmb_cat.setMinimumHeight(28)
        self.cmb_cat.setMinimumWidth(160)
        self.cmb_cat.setStyleSheet("""
            QComboBox {
                background: white;
                border: 1px solid #c5cae9;
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 12px;
            }
            QComboBox:focus { border-color: #1565c0; }
            QComboBox::drop-down { border: none; }
        """)
        self._reload_categories()
        self.cmb_cat.currentIndexChanged.connect(self.filter_changed.emit)
        lay.addWidget(self.cmb_cat, stretch=1)

        # ── زر مسح الكل ──
        btn_reset = QPushButton("↺ مسح الكل")
        btn_reset.setMinimumHeight(28)
        btn_reset.setStyleSheet("""
            QPushButton {
                background: #e8eaf6;
                border: 1px solid #c5cae9;
                border-radius: 4px;
                padding: 2px 10px;
                font-size: 11px;
                color: #3949ab;
            }
            QPushButton:hover {
                background: #c5cae9;
            }
        """)
        btn_reset.clicked.connect(self.reset)
        lay.addWidget(btn_reset)

        # ── عداد النتائج ──
        self.lbl_count = QLabel("")
        self.lbl_count.setStyleSheet(
            "color:#1565c0; font-size:10px; font-weight:bold;"
            "background:transparent; border:none;"
        )
        self.lbl_count.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.lbl_count)

    # ══════════════════════════════════════════════════════
    # تحميل التصنيفات
    # ══════════════════════════════════════════════════════

    def _reload_categories(self):
        prev = self.cmb_cat.currentData() if self.cmb_cat.count() else None
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("— كل التصنيفات —", None)

        rows = fetch_all_categories(self.conn, self.scope)
        tree = build_tree(rows)
        self._add_cat_nodes(tree, depth=0)

        # استعادة الاختيار السابق
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == prev:
                self.cmb_cat.setCurrentIndex(i)
                break

        self.cmb_cat.blockSignals(False)

    def _add_cat_nodes(self, nodes: list, depth: int):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_cat.addItem(
                f"{indent}{arrow}{node['name']}", node["id"]
            )
            idx = self.cmb_cat.count() - 1
            self.cmb_cat.setItemData(
                idx, QColor(node["color"]), Qt.ForegroundRole
            )
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    @property
    def name_query(self) -> str:
        return self.inp_search.text().strip().lower()

    @property
    def category_id(self):
        return self.cmb_cat.currentData()

    def match(self, name: str, cat_id) -> bool:
        """
        يرجع True لو الصف يطابق الفلتر الحالي.
        name   : اسم العنصر
        cat_id : category_id الخاص بالعنصر (ممكن None)
        """
        q = self.name_query
        if q and q not in (name or "").lower():
            return False
        fcat = self.category_id
        if fcat is not None and cat_id != fcat:
            return False
        return True

    def set_count(self, shown: int, total: int):
        """يحدّث عداد النتائج."""
        if shown == total:
            self.lbl_count.setText(f"({total})")
        else:
            self.lbl_count.setText(f"({shown} / {total})")

    def reset(self):
        self.inp_search.blockSignals(True)
        self.cmb_cat.blockSignals(True)
        self.inp_search.clear()
        self.cmb_cat.setCurrentIndex(0)
        self.inp_search.blockSignals(False)
        self.cmb_cat.blockSignals(False)
        self.filter_changed.emit()

    def _clear_search(self):
        self.inp_search.clear()
