"""
ui/tabs/costing/shared/bom_scenarios_panel.py
==================================
_BomScenariosPanel — لوحة إدارة سيناريوهات BOM.
"""

from PyQt5.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QMessageBox, QInputDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QFont

from .bom_scenarios._memory_scenarios import MemoryScenariosMixin
from .bom_scenarios._db_scenarios     import DbScenariosMixin


class _BomScenariosPanel(QFrame, MemoryScenariosMixin, DbScenariosMixin):
    """
    لوحة أفقية تعرض السيناريوهات وتتيح التبديل بينها.

    Signals:
        scenario_changed(scenario_id) — يُطلق عند تغيير السيناريو الحالي
    """

    scenario_changed = pyqtSignal(int)

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._item_id    = None
        self._scenarios  = []
        self._current_id = None
        self._in_memory  = True
        self._build()
        self._init_memory_scenario()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background: #f3e5f5;
                border: 1px solid #ce93d8;
                border-radius: 6px;
            }
        """)
        self.setFixedHeight(46)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(8)

        lbl_icon = QLabel("🎯")
        lbl_icon.setStyleSheet("background:transparent; border:none; font-size:14px;")
        lay.addWidget(lbl_icon)

        lbl = QLabel("السيناريو:")
        lbl.setStyleSheet(
            "font-weight:bold; font-size:11px; color:#6a1b9a;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl)

        self.cmb_scenarios = QComboBox()
        self.cmb_scenarios.setMinimumWidth(200)
        self.cmb_scenarios.setMinimumHeight(30)
        self.cmb_scenarios.setStyleSheet("""
            QComboBox {
                background: white; border: 1px solid #ce93d8;
                border-radius: 4px; padding: 2px 8px;
                font-size: 11px; color: #4a148c;
            }
            QComboBox:focus { border-color: #7b1fa2; }
            QComboBox::drop-down { border: none; }
        """)
        self.cmb_scenarios.currentIndexChanged.connect(self._on_scenario_changed)
        lay.addWidget(self.cmb_scenarios)

        self.lbl_default_badge = QLabel("⭐ افتراضي")
        self.lbl_default_badge.setStyleSheet(
            "color:#f57f17; font-weight:bold; font-size:10px;"
            "border:none; background:transparent;"
        )
        self.lbl_default_badge.setVisible(False)
        lay.addWidget(self.lbl_default_badge)

        lay.addStretch()

        self.btn_set_default = self._make_btn(
            "⭐ افتراضي", 100,
            "#fff9c4", "#f57f17", "#f9a825", "#fff176"
        )
        self.btn_set_default.setToolTip("جعل هذا السيناريو هو الافتراضي")
        self.btn_set_default.clicked.connect(self._set_default)
        lay.addWidget(self.btn_set_default)

        btn_rename = self._make_btn("✏️ تعديل", 80, "#fff3e0", "#e65100", "#ffcc80", "#ffe0b2")
        btn_rename.setToolTip("تعديل اسم السيناريو الحالي")
        btn_rename.clicked.connect(self._rename)
        lay.addWidget(btn_rename)

        btn_clone = self._make_btn("📋 نسخ", 70, "#e3f2fd", "#1565c0", "#90caf9", "#bbdefb")
        btn_clone.setToolTip("نسخ السيناريو الحالي")
        btn_clone.clicked.connect(self._clone)
        lay.addWidget(btn_clone)

        btn_add = self._make_btn("➕ جديد", 70, "#e8f5e9", "#2e7d32", "#a5d6a7", "#c8e6c9")
        btn_add.setToolTip("إضافة سيناريو جديد فارغ")
        btn_add.clicked.connect(self._add_new)
        lay.addWidget(btn_add)

        btn_del = self._make_btn("🗑", 36, "#ffebee", "#c62828", "#ef9a9a", "#ffcdd2")
        btn_del.setToolTip("حذف السيناريو الحالي")
        btn_del.clicked.connect(self._delete)
        lay.addWidget(btn_del)

    @staticmethod
    def _make_btn(text: str, width: int,
                  bg: str, fg: str, border: str, hover: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setMinimumHeight(28)
        btn.setFixedWidth(width)
        # ✅ f-string واحدة متكاملة — بدون string concatenation
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {bg};
                color: {fg};
                border: 1px solid {border};
                border-radius: 4px;
                font-size: 10px;
                font-weight: bold;
                padding: 2px 6px;
            }}
            QPushButton:hover {{ background: {hover}; }}
            QPushButton:disabled {{
                background: #f5f5f5;
                color: #bbb;
                border-color: #ddd;
            }}
        """)
        return btn

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def clear(self):
        """مسح اللوحة والرجوع لـ in-memory mode."""
        self._init_memory_scenario()

    def current_scenario_id(self) -> int | None:
        return self._current_id

    def is_in_memory(self) -> bool:
        return self._in_memory

    # ══════════════════════════════════════════════════════
    # بناء الـ Combo
    # ══════════════════════════════════════════════════════

    def _rebuild_combo(self):
        self.cmb_scenarios.blockSignals(True)
        self.cmb_scenarios.clear()
        for sc in self._scenarios:
            star = "⭐ " if sc["is_default"] else ""
            self.cmb_scenarios.addItem(f"{star}{sc['name']}", sc["id"])
        for i, sc in enumerate(self._scenarios):
            if sc["id"] == self._current_id:
                self.cmb_scenarios.setCurrentIndex(i)
                break
        self.cmb_scenarios.blockSignals(False)

    def _sync_current(self):
        sc_id = self.cmb_scenarios.currentData()
        self._current_id = sc_id

        is_default = any(
            sc["id"] == sc_id and sc["is_default"]
            for sc in self._scenarios
        )
        self.lbl_default_badge.setVisible(is_default)
        self.btn_set_default.setEnabled(not is_default and sc_id is not None)

    # ══════════════════════════════════════════════════════
    # Signal handler
    # ══════════════════════════════════════════════════════

    def _on_scenario_changed(self, _):
        self._sync_current()
        if self._current_id is not None:
            self.scenario_changed.emit(self._current_id)

    # ══════════════════════════════════════════════════════
    # أزرار
    # ══════════════════════════════════════════════════════

    def _set_default(self):
        if self._current_id is None:
            return
        if self._in_memory:
            self._memory_set_default(self._current_id)
        else:
            self._db_set_default(self._current_id)

    def _rename(self):
        if self._current_id is None:
            return
        current_name = next(
            (sc["name"] for sc in self._scenarios if sc["id"] == self._current_id),
            ""
        )
        name, ok = QInputDialog.getText(
            self, "تعديل اسم السيناريو", "الاسم الجديد:", text=current_name
        )
        if not ok or not name.strip():
            return
        if self._in_memory:
            self._memory_rename(self._current_id, name.strip())
        else:
            self._db_rename(self._current_id, name.strip())

    def _clone(self):
        if self._current_id is None:
            return
        current_name = next(
            (sc["name"] for sc in self._scenarios if sc["id"] == self._current_id),
            ""
        )
        default_name = f"نسخة من {current_name}" if current_name else "سيناريو جديد"
        name, ok = QInputDialog.getText(
            self, "نسخ السيناريو", "اسم السيناريو الجديد:", text=default_name
        )
        if not ok or not name.strip():
            return
        if self._in_memory:
            new_id = self._memory_clone(self._current_id, name.strip())
            self._current_id = new_id
            self._rebuild_combo()
            self._sync_current()
            self.scenario_changed.emit(new_id)
        else:
            new_id = self._db_clone(self._current_id, name.strip())
            if new_id is not None:
                self._current_id = new_id
                self._reload()
                self.scenario_changed.emit(new_id)

    def _add_new(self):
        count = len(self._scenarios) + 1
        name, ok = QInputDialog.getText(
            self, "سيناريو جديد", "اسم السيناريو:", text=f"سيناريو {count}"
        )
        if not ok or not name.strip():
            return
        if self._in_memory:
            new_id = self._memory_add_new(name.strip())
            self._current_id = new_id
            self._rebuild_combo()
            self._sync_current()
            self.scenario_changed.emit(new_id)
        else:
            new_id = self._db_add_new(name.strip())
            if new_id is not None:
                self._current_id = new_id
                self._reload()
                self.scenario_changed.emit(new_id)

    def _delete(self):
        if self._current_id is None:
            return
        if len(self._scenarios) <= 1:
            QMessageBox.warning(self, "تنبيه", "لا يمكن حذف السيناريو الوحيد.")
            return
        current_name = next(
            (sc["name"] for sc in self._scenarios if sc["id"] == self._current_id),
            ""
        )
        reply = QMessageBox.question(
            self, "تأكيد الحذف", f"حذف السيناريو «{current_name}»؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
        if self._in_memory:
            if self._memory_delete(self._current_id):
                self._rebuild_combo()
                self._sync_current()
                if self._current_id is not None:
                    self.scenario_changed.emit(self._current_id)
        else:
            if self._db_delete(self._current_id):
                self._current_id = None
                self._reload()
            else:
                QMessageBox.warning(self, "خطأ", "تعذر حذف السيناريو.")