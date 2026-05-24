"""
ui/widgets/shared/filter_bar.py
========================
FilterBar — شريط فلتر مشترك يُستخدم في كل التبويبات.

[إصلاح v2]:
  - استخدام SearchBar من panles_helper/list_header بدل QLineEdit يدوي
  - LiveConnMixin للـ connection
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QPushButton, QComboBox,
)
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui  import QColor

from db.shared.categories_repo import fetch_all_categories, build_tree
from ui.widgets.shared.connection_mixin import LiveConnMixin
from ui.widgets.shared.panels import SearchBar
from ui.events import bus


class FilterBar(QWidget, LiveConnMixin):
    """
    شريط فلتر أفقي:
      [🔍 بحث بالاسم ...]   [🏷 التصنيف ▼]   [↺ مسح الكل]
    """
    filter_changed = pyqtSignal()

    def __init__(self, conn, scope: str = "all", parent=None):
        super().__init__(parent)
        self.conn  = conn
        self.scope = scope
        self._build()
        bus.data_changed.connect(self._reload_categories)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        from ui.app_settings import _C
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

        # ── SearchBar الموحد بدل QLineEdit يدوي ──
        self._search_bar = SearchBar(
            placeholder="بحث بالاسم...",
            delay_ms=250,
            height=28,
        )
        self._search_bar.search_changed.connect(lambda _: self.filter_changed.emit())
        # expose inp_search للتوافق مع الكود القديم
        self.inp_search = self._search_bar.inp
        lay.addWidget(self._search_bar, stretch=2)

        sep = QLabel("│")
        sep.setStyleSheet(
            "color:#c5cae9; background:transparent; border:none; font-size:16px;"
        )
        lay.addWidget(sep)

        lbl_cat = QLabel("🏷")
        lbl_cat.setStyleSheet(
            "background:transparent; border:none; font-size:13px;"
        )
        lbl_cat.setFixedWidth(20)
        lay.addWidget(lbl_cat)

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
            QPushButton:hover { background: #c5cae9; }
        """)
        btn_reset.clicked.connect(self.reset)
        lay.addWidget(btn_reset)

        self.lbl_count = QLabel("")
        from PyQt5.QtCore import Qt
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
        try:
            conn = self._live_conn()
        except Exception:
            return

        prev = self.cmb_cat.currentData() if self.cmb_cat.count() else None
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("— كل التصنيفات —", None)

        try:
            rows = fetch_all_categories(conn, self.scope)
            tree = build_tree(rows)
            self._add_cat_nodes(tree, depth=0)
        except Exception:
            pass

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
                idx, QColor(node["color"]), 0x0100  # Qt.ForegroundRole
            )
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    @property
    def name_query(self) -> str:
        return self._search_bar.text()

    @property
    def category_id(self):
        return self.cmb_cat.currentData()

    def match(self, name: str, cat_id) -> bool:
        q = self.name_query
        if q and q not in (name or "").lower():
            return False
        fcat = self.category_id
        if fcat is not None and cat_id != fcat:
            return False
        return True

    def set_count(self, shown: int, total: int):
        if shown == total:
            self.lbl_count.setText(f"({total})")
        else:
            self.lbl_count.setText(f"({shown} / {total})")

    def reset(self):
        self._search_bar.clear()
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.setCurrentIndex(0)
        self.cmb_cat.blockSignals(False)
        self.filter_changed.emit()

    def _clear_search(self):
        self._search_bar.clear()