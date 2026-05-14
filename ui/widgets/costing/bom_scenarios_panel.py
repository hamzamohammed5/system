"""
ui/widgets/costing/bom_scenarios_panel.py
==================================
_BomScenariosPanel — لوحة إدارة سيناريوهات BOM.

تُستخدم داخل _FormPanel (product_form.py) وتظهر فوق منطقة المكونات.

الوظائف:
  - عرض السيناريوهات الموجودة كـ tabs أو قايمة
  - إضافة سيناريو جديد (من الصفر أو نسخ)
  - حذف سيناريو
  - تحديد سيناريو كـ default
  - عند تغيير السيناريو → يُعاد تحميل BOM

وضعان:
  - in-memory mode (منتج جديد لم يُحفظ بعد): السيناريوهات محفوظة في
    الذاكرة فقط، والمستخدم يقدر يسمي ويضيف سيناريوهات قبل الحفظ.
  - DB mode (منتج موجود): السيناريوهات محفوظة في قاعدة البيانات.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QLineEdit,
    QComboBox, QMessageBox, QFrame, QInputDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QFont

from db.bom_scenarios_repo import (
    fetch_scenarios, fetch_scenario, insert_scenario,
    update_scenario, delete_scenario, set_default_scenario,
    clone_scenario, fetch_default_scenario,
)
from ui.events import bus


class _BomScenariosPanel(QFrame):
    """
    لوحة أفقية تعرض السيناريوهات وتتيح التبديل بينها.

    Signals:
        scenario_changed(scenario_id) — يُطلق عند تغيير السيناريو الحالي
                                        (في الـ in-memory mode يُطلق بـ index سالب)
    """

    scenario_changed = pyqtSignal(int)

    # ── هيكل السيناريو في الـ in-memory mode ──
    # كل سيناريو: {"id": int (سالب مؤقت), "name": str, "is_default": bool}
    _NEXT_TEMP_ID = -1  # ID مؤقت سالب لتجنب التعارض مع DB IDs

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._item_id    = None          # None = in-memory mode
        self._scenarios  = []            # قايمة السيناريوهات (DB أو memory)
        self._current_id = None
        self._in_memory  = True          # True = منتج جديد لم يُحفظ بعد
        self._build()
        self._init_memory_scenario()     # ابدأ بسيناريو افتراضي في الذاكرة

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

        # أيقونة
        lbl_icon = QLabel("🎯")
        lbl_icon.setStyleSheet("background:transparent; border:none; font-size:14px;")
        lay.addWidget(lbl_icon)

        # label
        lbl = QLabel("السيناريو:")
        lbl.setStyleSheet(
            "font-weight:bold; font-size:11px; color:#6a1b9a;"
            "background:transparent; border:none;"
        )
        lay.addWidget(lbl)

        # combo السيناريوهات
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

        # badge الـ default
        self.lbl_default_badge = QLabel("⭐ افتراضي")
        self.lbl_default_badge.setStyleSheet(
            "color:#f57f17; font-weight:bold; font-size:10px;"
            "background:#fff9c4; border:1px solid #f9a825;"
            "border-radius:3px; padding:1px 6px;"
            "border:none; background:transparent;"
        )
        self.lbl_default_badge.setVisible(False)
        lay.addWidget(self.lbl_default_badge)

        lay.addStretch()

        # زر "جعله افتراضي"
        self.btn_set_default = QPushButton("⭐ افتراضي")
        self.btn_set_default.setMinimumHeight(28)
        self.btn_set_default.setFixedWidth(100)
        self.btn_set_default.setStyleSheet("""
            QPushButton {
                background: #fff9c4; color: #f57f17;
                border: 1px solid #f9a825; border-radius: 4px;
                font-size: 10px; font-weight: bold; padding: 2px 6px;
            }
            QPushButton:hover { background: #fff176; }
            QPushButton:disabled { background: #f5f5f5; color: #bbb; border-color: #ddd; }
        """)
        self.btn_set_default.setToolTip("جعل هذا السيناريو هو الافتراضي للحسابات")
        self.btn_set_default.clicked.connect(self._set_default)
        lay.addWidget(self.btn_set_default)

        # زر تعديل الاسم
        btn_rename = QPushButton("✏️ تعديل")
        btn_rename.setMinimumHeight(28)
        btn_rename.setFixedWidth(80)
        btn_rename.setStyleSheet("""
            QPushButton {
                background: #fff3e0; color: #e65100;
                border: 1px solid #ffcc80; border-radius: 4px;
                font-size: 10px; font-weight: bold; padding: 2px 6px;
            }
            QPushButton:hover { background: #ffe0b2; }
        """)
        btn_rename.setToolTip("تعديل اسم السيناريو الحالي")
        btn_rename.clicked.connect(self._rename)
        lay.addWidget(btn_rename)

        # زر نسخ
        btn_clone = QPushButton("📋 نسخ")
        btn_clone.setMinimumHeight(28)
        btn_clone.setFixedWidth(70)
        btn_clone.setStyleSheet("""
            QPushButton {
                background: #e3f2fd; color: #1565c0;
                border: 1px solid #90caf9; border-radius: 4px;
                font-size: 10px; font-weight: bold; padding: 2px 6px;
            }
            QPushButton:hover { background: #bbdefb; }
        """)
        btn_clone.setToolTip("نسخ السيناريو الحالي لسيناريو جديد")
        btn_clone.clicked.connect(self._clone)
        lay.addWidget(btn_clone)

        # زر إضافة
        btn_add = QPushButton("➕ جديد")
        btn_add.setMinimumHeight(28)
        btn_add.setFixedWidth(70)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #e8f5e9; color: #2e7d32;
                border: 1px solid #a5d6a7; border-radius: 4px;
                font-size: 10px; font-weight: bold; padding: 2px 6px;
            }
            QPushButton:hover { background: #c8e6c9; }
        """)
        btn_add.setToolTip("إضافة سيناريو جديد فارغ")
        btn_add.clicked.connect(self._add_new)
        lay.addWidget(btn_add)

        # زر حذف
        btn_del = QPushButton("🗑")
        btn_del.setMinimumHeight(28)
        btn_del.setFixedWidth(36)
        btn_del.setStyleSheet("""
            QPushButton {
                background: #ffebee; color: #c62828;
                border: 1px solid #ef9a9a; border-radius: 4px;
                font-size: 12px; padding: 2px;
            }
            QPushButton:hover { background: #ffcdd2; }
        """)
        btn_del.setToolTip("حذف السيناريو الحالي")
        btn_del.clicked.connect(self._delete)
        lay.addWidget(btn_del)

    # ══════════════════════════════════════════════════════
    # In-Memory Mode — إدارة السيناريوهات في الذاكرة
    # ══════════════════════════════════════════════════════

    def _next_temp_id(self) -> int:
        """يولّد ID مؤقت سالب فريد."""
        _BomScenariosPanel._NEXT_TEMP_ID -= 1
        return _BomScenariosPanel._NEXT_TEMP_ID

    def _init_memory_scenario(self):
        """يُنشئ سيناريو افتراضي في الذاكرة للمنتجات الجديدة."""
        self._in_memory = True
        self._item_id   = None
        temp_id = self._next_temp_id()
        self._scenarios = [{"id": temp_id, "name": "سيناريو 1", "is_default": True}]
        self._current_id = temp_id
        self._rebuild_combo()
        self._sync_current()

    def get_memory_scenarios(self) -> list:
        """
        يرجع السيناريوهات المحفوظة في الذاكرة.
        يُستدعى من _FormPanel عند الحفظ لكتابة السيناريوهات في DB.
        كل عنصر: {"id": int (temp), "name": str, "is_default": bool}
        """
        return list(self._scenarios)

    def get_current_memory_index(self) -> int:
        """
        يرجع index السيناريو الحالي في قايمة الذاكرة.
        يُستخدم لمعرفة أي سيناريو كان المستخدم عليه عند الحفظ.
        """
        for i, sc in enumerate(self._scenarios):
            if sc["id"] == self._current_id:
                return i
        return 0

    def switch_to_db_mode(self, item_id: int, current_scenario_index: int = 0):
        """
        التحويل من in-memory mode إلى DB mode بعد حفظ المنتج.
        item_id: ID المنتج الجديد في DB
        current_scenario_index: index السيناريو الحالي في DB
        """
        self._in_memory = False
        self._item_id   = item_id
        self._scenarios = []
        self._current_id = None
        self._reload()

        # اختر السيناريو المناسب
        if 0 <= current_scenario_index < len(self._scenarios):
            target_sc = self._scenarios[current_scenario_index]
            self._current_id = target_sc["id"]
            self._rebuild_combo()
            self._sync_current()

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_item(self, item_id: int):
        """تحميل سيناريوهات منتج موجود (DB mode)."""
        self._in_memory = False
        self._item_id   = item_id
        self._reload()

    def clear(self):
        """مسح اللوحة والرجوع لـ in-memory mode."""
        self._init_memory_scenario()

    def current_scenario_id(self) -> int | None:
        return self._current_id

    def is_in_memory(self) -> bool:
        return self._in_memory

    def ensure_default_scenario(self, item_id: int) -> int:
        """
        يتأكد من وجود سيناريو default للمنتج.
        لو مفيش → ينشئ واحد.
        يرجع id السيناريو الـ default.
        """
        sc = fetch_default_scenario(self.conn, item_id)
        if sc:
            return sc["id"]
        return insert_scenario(self.conn, item_id, "سيناريو 1", is_default=True)

    # ══════════════════════════════════════════════════════
    # تحميل (DB mode)
    # ══════════════════════════════════════════════════════

    def _reload(self):
        """إعادة تحميل من DB."""
        if self._item_id is None:
            return
        rows = fetch_scenarios(self.conn, self._item_id)
        self._scenarios = [dict(r) for r in rows]
        prev_id = self._current_id
        self._rebuild_combo()

        # استعادة الاختيار السابق أو الـ default
        restored = False
        if prev_id is not None:
            for sc in self._scenarios:
                if sc["id"] == prev_id:
                    self._current_id = prev_id
                    restored = True
                    break

        if not restored:
            for sc in self._scenarios:
                if sc["is_default"]:
                    self._current_id = sc["id"]
                    break

        self._rebuild_combo()
        self._sync_current()

    def _rebuild_combo(self):
        """إعادة بناء الـ combo من self._scenarios."""
        self.cmb_scenarios.blockSignals(True)
        self.cmb_scenarios.clear()

        for sc in self._scenarios:
            star = "⭐ " if sc["is_default"] else ""
            self.cmb_scenarios.addItem(f"{star}{sc['name']}", sc["id"])

        # اختر الحالي
        for i, sc in enumerate(self._scenarios):
            if sc["id"] == self._current_id:
                self.cmb_scenarios.setCurrentIndex(i)
                break

        self.cmb_scenarios.blockSignals(False)

    def _sync_current(self):
        """مزامنة الـ _current_id مع الـ combo."""
        sc_id = self.cmb_scenarios.currentData()
        self._current_id = sc_id

        is_default = False
        for sc in self._scenarios:
            if sc["id"] == sc_id and sc["is_default"]:
                is_default = True
                break

        self.lbl_default_badge.setVisible(is_default)
        self.btn_set_default.setEnabled(not is_default and sc_id is not None)

    # ══════════════════════════════════════════════════════
    # Signal handlers
    # ══════════════════════════════════════════════════════

    def _on_scenario_changed(self, _):
        self._sync_current()
        if self._current_id is not None:
            self.scenario_changed.emit(self._current_id)

    # ══════════════════════════════════════════════════════
    # أزرار — تعمل في كلا الوضعين
    # ══════════════════════════════════════════════════════

    def _set_default(self):
        if self._current_id is None:
            return

        if self._in_memory:
            # في الذاكرة: غيّر is_default في القايمة
            for sc in self._scenarios:
                sc["is_default"] = (sc["id"] == self._current_id)
            self._rebuild_combo()
            self._sync_current()
        else:
            # في DB
            set_default_scenario(self.conn, self._current_id)
            bus.data_changed.emit()
            self._reload()

    def _rename(self):
        if self._current_id is None:
            return

        # ابحث عن الاسم الحالي
        current_name = ""
        for sc in self._scenarios:
            if sc["id"] == self._current_id:
                current_name = sc["name"]
                break

        name, ok = QInputDialog.getText(
            self, "تعديل اسم السيناريو", "الاسم الجديد:",
            text=current_name
        )
        if not ok or not name.strip():
            return

        if self._in_memory:
            # في الذاكرة: عدّل الاسم مباشرة
            for sc in self._scenarios:
                if sc["id"] == self._current_id:
                    sc["name"] = name.strip()
                    break
            self._rebuild_combo()
            self._sync_current()
        else:
            # في DB
            update_scenario(self.conn, self._current_id, name.strip())
            bus.data_changed.emit()
            self._reload()

    def _clone(self):
        if self._current_id is None:
            return

        current_name = ""
        for sc in self._scenarios:
            if sc["id"] == self._current_id:
                current_name = sc["name"]
                break

        default_name = f"نسخة من {current_name}" if current_name else "سيناريو جديد"
        name, ok = QInputDialog.getText(
            self, "نسخ السيناريو", "اسم السيناريو الجديد:",
            text=default_name
        )
        if not ok or not name.strip():
            return

        if self._in_memory:
            # في الذاكرة: أضف سيناريو جديد (النسخ الفعلي للمكونات سيتم في FormPanel)
            new_id = self._next_temp_id()
            self._scenarios.append({
                "id": new_id,
                "name": name.strip(),
                "is_default": False,
                "_cloned_from": self._current_id,  # علامة للـ FormPanel يعرف يعمل clone
            })
            self._current_id = new_id
            self._rebuild_combo()
            self._sync_current()
            # نطلق الـ signal عشان الـ FormPanel يعرف يعمل clone للمكونات
            self.scenario_changed.emit(new_id)
        else:
            # في DB
            try:
                new_id = clone_scenario(self.conn, self._current_id, name.strip())
                self._current_id = new_id
                bus.data_changed.emit()
                self._reload()
            except Exception as e:
                QMessageBox.warning(self, "خطأ", str(e))

    def _add_new(self):
        count = len(self._scenarios) + 1
        name, ok = QInputDialog.getText(
            self, "سيناريو جديد", "اسم السيناريو:",
            text=f"سيناريو {count}"
        )
        if not ok or not name.strip():
            return

        if self._in_memory:
            # في الذاكرة: أضف سيناريو جديد فارغ
            new_id = self._next_temp_id()
            self._scenarios.append({
                "id": new_id,
                "name": name.strip(),
                "is_default": False,
            })
            self._current_id = new_id
            self._rebuild_combo()
            self._sync_current()
            self.scenario_changed.emit(new_id)
        else:
            # في DB
            if self._item_id is None:
                return
            new_id = insert_scenario(
                self.conn, self._item_id, name.strip(), is_default=False
            )
            self._current_id = new_id
            bus.data_changed.emit()
            self._reload()
            self.scenario_changed.emit(new_id)

    def _delete(self):
        if self._current_id is None:
            return
        if len(self._scenarios) <= 1:
            QMessageBox.warning(
                self, "تنبيه",
                "لا يمكن حذف السيناريو الوحيد."
            )
            return

        current_name = ""
        for sc in self._scenarios:
            if sc["id"] == self._current_id:
                current_name = sc["name"]
                break

        reply = QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف السيناريو «{current_name}»؟",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return

        if self._in_memory:
            # في الذاكرة: احذف من القايمة
            was_default = False
            for sc in self._scenarios:
                if sc["id"] == self._current_id:
                    was_default = sc["is_default"]
                    break

            self._scenarios = [sc for sc in self._scenarios if sc["id"] != self._current_id]

            # لو كان default، اجعل الأول default
            if was_default and self._scenarios:
                self._scenarios[0]["is_default"] = True

            self._current_id = self._scenarios[0]["id"] if self._scenarios else None
            self._rebuild_combo()
            self._sync_current()
            if self._current_id is not None:
                self.scenario_changed.emit(self._current_id)
        else:
            # في DB
            if delete_scenario(self.conn, self._current_id):
                self._current_id = None
                bus.data_changed.emit()
                self._reload()
            else:
                QMessageBox.warning(self, "خطأ", "تعذر حذف السيناريو.")