"""
ui/tabs/design/dimension_sets/_values_panel.py
=====================================
لوحة إدخال قيم المقاسات — نظام Instances.

كل مجموعة مقاسات ممكن يكون ليها instances متعددة، كل instance له:
  - اسم واحد  (مثال: "A4"، "A5"، "مقاس كبير")
  - قيم لكل حقول المجموعة

التخطيط:
  ┌─────────────────────────────────────────────┐
  │  رأس: اسم المجموعة المختارة                │
  ├──────────────┬──────────────────────────────┤
  │ قائمة       │  حقول Instance المختار        │
  │ Instances   │  [الحقل: قيمة] × N           │
  │ ─────────   │  [حفظ] [حساب تلقائي]         │
  │ [+ إضافة]   │                               │
  └──────────────┴──────────────────────────────┘
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox,
    QMessageBox, QScrollArea, QFrame, QListWidget,
    QListWidgetItem, QInputDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from db.designs.dimension_sets_repo import (
    fetch_fields_for_set,
    fetch_instances_for_set, fetch_instance,
    insert_instance, update_instance, delete_instance, duplicate_instance,
    fetch_instance_values, save_instance_values, calc_instance_cross_auto,
)


def _row_val(row, key, default=None):
    try:
        v = row[key]
        return v if v is not None else default
    except (IndexError, KeyError):
        return default


# ══════════════════════════════════════════════════════════
# لوحة قائمة الـ Instances (يسار)
# ══════════════════════════════════════════════════════════

class _InstancesList(QWidget):
    """
    قائمة instances مجموعة المقاسات المختارة.
    تسمح بإضافة / تعديل اسم / حذف / نسخ.
    """

    instance_selected = pyqtSignal(int)   # instance_id
    instances_changed = pyqtSignal()       # بعد إضافة/حذف/نسخ

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── رأس ──
        hdr = QLabel("📋  القيم المحفوظة")
        hdr.setStyleSheet("""
            font-weight: bold; font-size: 12px; color: #1565c0;
            background: #e8f0fe; border-radius: 5px; padding: 5px 10px;
        """)
        root.addWidget(hdr)

        # ── القائمة ──
        self.lst = QListWidget()
        self.lst.setAlternatingRowColors(True)
        self.lst.setStyleSheet("""
            QListWidget {
                border: 1px solid #c5cae9;
                border-radius: 6px;
                background: white;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 10px;
                border-bottom: 1px solid #e8eaf6;
                color: #333;
            }
            QListWidget::item:selected {
                background: #e3f2fd;
                color: #1565c0;
                font-weight: bold;
                border-left: 3px solid #1565c0;
            }
            QListWidget::item:hover:!selected {
                background: #f5f5f5;
            }
        """)
        self.lst.currentItemChanged.connect(self._on_select)
        root.addWidget(self.lst, stretch=1)

        # ── hint إذا فاضي ──
        self._hint = QLabel("لا توجد قيم بعد\nاضغط ➕ لإضافة مجموعة قيم")
        self._hint.setAlignment(Qt.AlignCenter)
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet(
            "color: #aaa; font-size: 11px; padding: 12px;"
        )
        root.addWidget(self._hint)
        self._hint.setVisible(False)

        # ── أزرار ──
        btn_add = QPushButton("➕  إضافة")
        btn_add.setMinimumHeight(30)
        btn_add.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white; border: none;
                border-radius: 5px; padding: 4px 14px; font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
            QPushButton:disabled { background: #b0bec5; }
        """)
        btn_add.clicked.connect(self._add_instance)
        self._btn_add = btn_add

        btn_rename = QPushButton("✏️  تغيير الاسم")
        btn_rename.setMinimumHeight(30)
        btn_rename.setStyleSheet("""
            QPushButton {
                background: #e8f5e9; color: #2e7d32;
                border: 1px solid #a5d6a7; border-radius: 5px; padding: 4px 10px;
            }
            QPushButton:hover { background: #c8e6c9; }
            QPushButton:disabled { background: #f5f5f5; color: #bbb; }
        """)
        btn_rename.clicked.connect(self._rename_instance)

        btn_copy = QPushButton("📋  نسخ")
        btn_copy.setMinimumHeight(30)
        btn_copy.setStyleSheet("""
            QPushButton {
                background: #fff3e0; color: #e65100;
                border: 1px solid #ffcc80; border-radius: 5px; padding: 4px 10px;
            }
            QPushButton:hover { background: #ffe0b2; }
            QPushButton:disabled { background: #f5f5f5; color: #bbb; }
        """)
        btn_copy.clicked.connect(self._copy_instance)

        btn_del = QPushButton("🗑️  حذف")
        btn_del.setMinimumHeight(30)
        btn_del.setStyleSheet("""
            QPushButton {
                background: #fdecea; color: #b71c1c;
                border: 1px solid #ef9a9a; border-radius: 5px; padding: 4px 10px;
            }
            QPushButton:hover { background: #ffcdd2; }
            QPushButton:disabled { background: #f5f5f5; color: #bbb; }
        """)
        btn_del.clicked.connect(self._delete_instance)

        for b in (btn_rename, btn_copy, btn_del):
            b.setEnabled(False)
        self._btn_rename = btn_rename
        self._btn_copy   = btn_copy
        self._btn_del    = btn_del

        actions_row = QHBoxLayout()
        actions_row.addWidget(btn_add)
        actions_row.addWidget(btn_rename)
        actions_row.addWidget(btn_copy)
        actions_row.addWidget(btn_del)
        root.addLayout(actions_row)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self._btn_add.setEnabled(True)
        self._refresh()

    def clear(self):
        self._set_id = None
        self.lst.clear()
        self._btn_add.setEnabled(False)
        self._set_action_btns(False)
        self._hint.setVisible(False)

    def refresh(self):
        if self._set_id:
            current_id = self._current_instance_id()
            self._refresh(select_id=current_id)

    def _refresh(self, select_id: int = None):
        """
        يعيد بناء القائمة.
        select_id: ID الـ instance المطلوب تحديده بعد الإعادة.
                   لو None → يختار الأول تلقائياً.
        """
        self.lst.blockSignals(True)
        self.lst.clear()
        instances = fetch_instances_for_set(self.conn, self._set_id)
        for inst in instances:
            display = inst["name"].strip() if inst["name"].strip() else f"مجموعة #{inst['id']}"
            item = QListWidgetItem(display)
            item.setData(Qt.UserRole, inst["id"])
            self.lst.addItem(item)
        self.lst.blockSignals(False)

        has_items = self.lst.count() > 0
        self._hint.setVisible(not has_items)

        if not has_items:
            self._set_action_btns(False)
            return

        # اختر الـ instance المطلوب أو الأول
        target_row = 0
        if select_id is not None:
            for i in range(self.lst.count()):
                if self.lst.item(i).data(Qt.UserRole) == select_id:
                    target_row = i
                    break

        self.lst.setCurrentRow(target_row)
        # الـ signal بيتبعت تلقائياً من currentItemChanged

    def _current_instance_id(self):
        item = self.lst.currentItem()
        return item.data(Qt.UserRole) if item else None

    def _on_select(self, current, previous):
        if current:
            iid = current.data(Qt.UserRole)
            self._set_action_btns(True)
            self.instance_selected.emit(iid)
        else:
            self._set_action_btns(False)

    def _set_action_btns(self, enabled: bool):
        for b in (self._btn_rename, self._btn_copy, self._btn_del):
            b.setEnabled(enabled)

    # ── CRUD ──

    def _add_instance(self):
        if not self._set_id:
            return
        name, ok = QInputDialog.getText(
            self, "إضافة مجموعة قيم",
            "اسم مجموعة القيم الجديدة:\n(مثال: A4، مقاس L، النموذج الأول...)",
        )
        if ok:
            new_id = insert_instance(self.conn, self._set_id, name.strip())
            self._refresh(select_id=new_id)
            self.instances_changed.emit()

    def _rename_instance(self):
        iid = self._current_instance_id()
        if not iid:
            return
        inst = fetch_instance(self.conn, iid)
        current_name = inst["name"] if inst else ""
        name, ok = QInputDialog.getText(
            self, "تغيير الاسم", "الاسم الجديد:", text=current_name
        )
        if ok:
            update_instance(self.conn, iid, name.strip())
            self._refresh(select_id=iid)
            self.instances_changed.emit()

    def _copy_instance(self):
        iid = self._current_instance_id()
        if not iid:
            return
        inst = fetch_instance(self.conn, iid)
        src_name = inst["name"] if inst else ""
        name, ok = QInputDialog.getText(
            self, "نسخ مجموعة القيم",
            "اسم النسخة الجديدة:",
            text=f"{src_name} (نسخة)" if src_name else "نسخة جديدة"
        )
        if ok:
            new_id = duplicate_instance(self.conn, iid, name.strip())
            self._refresh(select_id=new_id)
            self.instances_changed.emit()

    def _delete_instance(self):
        iid = self._current_instance_id()
        if not iid:
            return
        inst = fetch_instance(self.conn, iid)
        name = inst["name"] if inst and inst["name"] else f"مجموعة #{iid}"
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف «{name}» وكل قيمها؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_instance(self.conn, iid)
            self._refresh()
            self.instances_changed.emit()


# ══════════════════════════════════════════════════════════
# لوحة تعديل قيم Instance واحد (يمين)
# ══════════════════════════════════════════════════════════

class _InstanceEditor(QWidget):
    """
    عرض وتعديل قيم حقول instance واحد.
    """

    saved = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn          = conn
        self._set_id       = None
        self._instance_id  = None
        self._rows         = {}   # field_id → {"spin": ..., "ref_lbl": ...}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(6)

        # ── رأس ──
        self._hdr = QLabel("📊  اختر مجموعة قيم من القائمة")
        self._hdr.setStyleSheet("""
            font-weight: bold; font-size: 12px; color: #1565c0;
            background: #e8f0fe; border-radius: 5px; padding: 5px 10px;
        """)
        root.addWidget(self._hdr)

        # ── رسالة الانتظار ──
        self._hint = QLabel("اختر مجموعة قيم من القائمة يسار لبدء الإدخال")
        self._hint.setAlignment(Qt.AlignCenter)
        self._hint.setWordWrap(True)
        self._hint.setStyleSheet("color: #aaa; font-size: 11px; padding: 24px;")
        root.addWidget(self._hint)

        # ── ScrollArea للحقول ──
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #e0e0e0; border-radius: 6px; background: white;
            }
            QScrollBar:vertical {
                background: #f5f5f5; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #bdbdbd; border-radius: 4px; min-height: 30px;
            }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0px; }
        """)
        self._scroll.setVisible(False)
        self._fields_w   = QWidget()
        self._fields_w.setStyleSheet("background: white;")
        self._fields_lay = QVBoxLayout(self._fields_w)
        self._fields_lay.setSpacing(6)
        self._fields_lay.setContentsMargins(8, 8, 8, 8)
        self._fields_lay.addStretch()
        self._scroll.setWidget(self._fields_w)
        root.addWidget(self._scroll, stretch=1)

        # ── أزرار ──
        bar = QHBoxLayout()
        self.btn_save = QPushButton("💾  حفظ القيم")
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setEnabled(False)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white; border: none;
                border-radius: 5px; padding: 4px 18px; font-weight: bold;
            }
            QPushButton:hover  { background: #0d47a1; }
            QPushButton:disabled { background: #b0bec5; }
        """)
        self.btn_save.clicked.connect(self._save)

        self.btn_calc = QPushButton("⟳  حساب التلقائي")
        self.btn_calc.setMinimumHeight(32)
        self.btn_calc.setEnabled(False)
        self.btn_calc.setStyleSheet("""
            QPushButton {
                background: #e8f5e9; color: #2e7d32;
                border: 1px solid #a5d6a7; border-radius: 5px; padding: 4px 14px;
            }
            QPushButton:hover    { background: #c8e6c9; }
            QPushButton:disabled { background: #f5f5f5; color: #bbb; border-color: #ddd; }
        """)
        self.btn_calc.clicked.connect(self._calc_all_auto)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #2e7d32; font-size: 11px;")

        bar.addWidget(self.btn_save)
        bar.addWidget(self.btn_calc)
        bar.addStretch()
        bar.addWidget(self.lbl_status)
        root.addLayout(bar)

    def load(self, set_id: int, instance_id: int):
        self._set_id      = set_id
        self._instance_id = instance_id
        self._rows        = {}
        self._clear_fields()
        self.lbl_status.setText("")

        inst = fetch_instance(self.conn, instance_id)
        name = inst["name"] if inst and inst["name"].strip() else f"مجموعة #{instance_id}"
        self._hdr.setText(f"📊  قيم: {name}")

        fields    = fetch_fields_for_set(self.conn, set_id)
        num_fields = [f for f in fields if f["field_type"] == "number"]

        if not num_fields:
            self._hint.setText("هذه المجموعة ليس لها حقول رقمية — أضف حقولاً أولاً")
            self._hint.setVisible(True)
            self._scroll.setVisible(False)
            self.btn_save.setEnabled(False)
            self.btn_calc.setEnabled(False)
            return

        self._hint.setVisible(False)
        self._scroll.setVisible(True)

        saved    = fetch_instance_values(self.conn, instance_id)
        has_auto = any(bool(_row_val(f, "source_field_id")) for f in num_fields)

        for f in num_fields:
            saved_val = saved.get(f["id"], {}).get("value_num")
            row_w     = self._build_field_row(f, saved_val)
            self._fields_lay.insertWidget(self._fields_lay.count() - 1, row_w)

        self.btn_save.setEnabled(True)
        self.btn_calc.setEnabled(has_auto)

    def _build_field_row(self, field_data, current_value) -> QWidget:
        fid     = field_data["id"]
        has_dep = bool(_row_val(field_data, "source_field_id"))
        src_fid = _row_val(field_data, "source_field_id")
        src_sid = _row_val(field_data, "source_set_id")
        dep_off = float(_row_val(field_data, "dep_offset") or 0)
        src_lbl = _row_val(field_data, "source_label", "")

        frame = QFrame()
        frame.setStyleSheet("""
            QFrame {
                background: #fafafa;
                border: 1px solid #e8eaf6;
                border-radius: 6px;
            }
            QFrame:hover {
                border-color: #90caf9;
                background: #f3f8ff;
            }
        """)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)

        # ── label الحقل ──
        lbl = QLabel(field_data["label"])
        lbl.setFixedWidth(120)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet(
            "background: transparent; border: none;"
            "font-weight: bold; color: #333;"
        )

        # ── spin القيمة ──
        spin = QDoubleSpinBox()
        spin.setRange(-99999, 99999)
        spin.setDecimals(4)
        spin.setMinimumHeight(30)
        spin.setMinimumWidth(120)
        spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #c5cae9; border-radius: 4px;
                padding: 2px 6px; background: white;
            }
            QDoubleSpinBox:focus { border-color: #1565c0; }
        """)
        if current_value is not None:
            spin.setValue(float(current_value))

        # ── label الوحدة ──
        unit_lbl = QLabel(field_data["unit"] or "")
        unit_lbl.setFixedWidth(36)
        unit_lbl.setStyleSheet(
            "color: #888; background: transparent; border: none; font-size: 10px;"
        )

        lay.addWidget(lbl)
        lay.addWidget(spin, stretch=1)
        lay.addWidget(unit_lbl)

        # ── ref label + زر الحساب التلقائي ──
        ref_lbl = None
        if has_dep and src_fid:
            actual_src_set = src_sid if src_sid else self._set_id
            ref_lbl = QLabel("")
            ref_lbl.setFixedWidth(130)
            ref_lbl.setAlignment(Qt.AlignCenter)
            ref_lbl.setWordWrap(False)
            self._refresh_ref_label(ref_lbl, src_fid, actual_src_set, dep_off)

            tooltip_txt = f"يعتمد على: {src_lbl}"
            src_set_nm  = _row_val(field_data, "source_set_name", "")
            if src_set_nm:
                tooltip_txt += f"\nمن مجموعة: {src_set_nm}"

            btn_auto = QPushButton("⟳")
            btn_auto.setFixedSize(28, 28)
            btn_auto.setToolTip(tooltip_txt)
            btn_auto.setStyleSheet("""
                QPushButton {
                    background: #e8f5e9; border: 1px solid #a5d6a7;
                    border-radius: 4px; color: #2e7d32;
                    font-size: 13px; font-weight: bold;
                }
                QPushButton:hover { background: #c8e6c9; }
            """)
            btn_auto.clicked.connect(
                lambda _, fid_=fid, sp_=spin, rl_=ref_lbl,
                       sfid=src_fid, ssid=actual_src_set, off=dep_off:
                self._calc_one(fid_, sp_, rl_, sfid, ssid, off)
            )
            lay.addWidget(ref_lbl)
            lay.addWidget(btn_auto)
        else:
            spacer = QLabel("")
            spacer.setFixedWidth(162)
            spacer.setStyleSheet("background: transparent; border: none;")
            lay.addWidget(spacer)

        self._rows[fid] = {
            "spin":    spin,
            "ref_lbl": ref_lbl,
            "src_fid": src_fid,
            "src_sid": src_sid if src_sid else (self._set_id if has_dep else None),
            "offset":  dep_off,
        }
        return frame

    def _refresh_ref_label(self, ref_lbl, source_field_id,
                            source_set_id, offset):
        """يعرض قيمة المصدر + النتيجة في ref_lbl."""
        try:
            # نبحث عن أول instance للمجموعة المصدر
            src_inst = self.conn.execute(
                "SELECT id FROM dimension_set_instances WHERE set_id=?"
                " ORDER BY sort_order, id LIMIT 1",
                (source_set_id,)
            ).fetchone()
            if not src_inst:
                raise ValueError("لا يوجد instance")

            row = self.conn.execute(
                "SELECT dsv.value_num, ds.name AS set_name"
                " FROM dimension_set_values dsv"
                " JOIN dimension_sets ds ON ds.id = dsv.set_id"
                " WHERE dsv.instance_id=? AND dsv.field_id=?",
                (src_inst["id"], source_field_id)
            ).fetchone()

            if row and row["value_num"] is not None:
                src_val = float(row["value_num"])
                result  = src_val + float(offset)
                sign    = f"+{offset:g}" if offset >= 0 else f"{offset:g}"
                ref_lbl.setText(f"{src_val:g}{sign}={result:g}")
                ref_lbl.setToolTip(
                    f"مصدر: {row['set_name']}\n"
                    f"القيمة: {src_val:g}  |  offset: {offset:g}"
                    f"  |  النتيجة: {result:g}"
                )
                ref_lbl.setStyleSheet("""
                    color: #1565c0; font-size: 10px;
                    background: #e8f0fe; border: 1px solid #bbdefb;
                    border-radius: 3px; padding: 1px 4px;
                """)
            else:
                ref_lbl.setText("مصدر: —")
                ref_lbl.setStyleSheet("""
                    color: #aaa; font-size: 10px;
                    background: #f5f5f5; border: 1px solid #e0e0e0;
                    border-radius: 3px; padding: 1px 4px;
                """)
        except Exception:
            ref_lbl.setText("مصدر: ؟")

    def _refresh_all_ref_labels(self):
        for _, row_data in self._rows.items():
            rl  = row_data.get("ref_lbl")
            sfd = row_data.get("src_fid")
            ssd = row_data.get("src_sid")
            off = row_data.get("offset", 0.0)
            if rl and sfd and ssd:
                self._refresh_ref_label(rl, sfd, ssd, off)

    def _clear_fields(self):
        while self._fields_lay.count() > 1:
            item = self._fields_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _calc_one(self, field_id, spin, ref_lbl,
                   source_field_id, source_set_id, offset):
        """حساب حقل واحد تلقائياً."""
        if not self._instance_id:
            return
        # احفظ أولاً عشان نحسب صح
        self._save(silent=True)
        val = calc_instance_cross_auto(self.conn, field_id, self._instance_id)
        if val is not None:
            spin.setValue(val)
            spin.setStyleSheet("""
                QDoubleSpinBox {
                    border: 2px solid #43a047; border-radius: 4px;
                    padding: 2px 6px; background: #f1f8e9;
                }
            """)
            self.conn.execute("""
                INSERT INTO dimension_set_values
                    (set_id, field_id, instance_id, value_num)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(instance_id, field_id) DO UPDATE
                    SET value_num=excluded.value_num
            """, (self._set_id, field_id, self._instance_id, val))
            self.conn.commit()
            self.lbl_status.setText(f"✓ {val:.4g}")
            if ref_lbl:
                self._refresh_ref_label(ref_lbl, source_field_id,
                                         source_set_id, offset)
        else:
            QMessageBox.information(
                self, "تنبيه",
                "لا توجد قيمة للحقل المصدر بعد.\n"
                "أدخل قيمة المصدر في مجموعتها أولاً."
            )

    def _calc_all_auto(self):
        """حساب كل الحقول التلقائية."""
        if not self._instance_id:
            return
        self._save(silent=True)

        fields = fetch_fields_for_set(self.conn, self._set_id)
        count  = 0
        for f in fields:
            if f["field_type"] != "number" or not _row_val(f, "source_field_id"):
                continue
            fid = f["id"]
            if fid not in self._rows:
                continue
            val = calc_instance_cross_auto(self.conn, fid, self._instance_id)
            if val is not None:
                self._rows[fid]["spin"].setValue(val)
                self._rows[fid]["spin"].setStyleSheet("""
                    QDoubleSpinBox {
                        border: 2px solid #43a047; border-radius: 4px;
                        padding: 2px 6px; background: #f1f8e9;
                    }
                """)
                self.conn.execute("""
                    INSERT INTO dimension_set_values
                        (set_id, field_id, instance_id, value_num)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(instance_id, field_id) DO UPDATE
                        SET value_num=excluded.value_num
                """, (self._set_id, fid, self._instance_id, val))

                rl  = self._rows[fid].get("ref_lbl")
                sfd = self._rows[fid].get("src_fid")
                ssd = self._rows[fid].get("src_sid")
                off = self._rows[fid].get("offset", 0.0)
                if rl and sfd and ssd:
                    self._refresh_ref_label(rl, sfd, ssd, off)
                count += 1

        self.conn.commit()
        self.lbl_status.setText(
            f"✓ تم حساب {count} حقل" if count
            else "⚠ لا توجد قيم مصدر — أدخل القيم في مجموعاتها أولاً"
        )

    def _save(self, silent=False):
        if not self._instance_id:
            return
        values = {fid: row["spin"].value()
                  for fid, row in self._rows.items()}
        save_instance_values(self.conn, self._instance_id,
                              self._set_id, values)
        if not silent:
            self.lbl_status.setText("✓ تم الحفظ")
            for row in self._rows.values():
                row["spin"].setStyleSheet("""
                    QDoubleSpinBox {
                        border: 1px solid #c5cae9; border-radius: 4px;
                        padding: 2px 6px; background: white;
                    }
                    QDoubleSpinBox:focus { border-color: #1565c0; }
                """)
            self._refresh_all_ref_labels()
            self.saved.emit()

    def clear(self):
        self._set_id      = None
        self._instance_id = None
        self._rows        = {}
        self._clear_fields()
        self._hdr.setText("📊  اختر مجموعة قيم من القائمة")
        self._hint.setText("اختر مجموعة قيم من القائمة يسار لبدء الإدخال")
        self._hint.setVisible(True)
        self._scroll.setVisible(False)
        self.btn_save.setEnabled(False)
        self.btn_calc.setEnabled(False)
        self.lbl_status.setText("")


# ══════════════════════════════════════════════════════════
# اللوحة الرئيسية (تجمع القائمة + المحرر)
# ══════════════════════════════════════════════════════════

class _ValuesPanel(QWidget):
    """
    اللوحة الرئيسية لإدخال قيم المقاسات بنظام الـ Instances.

    يسار: قائمة instances + أزرار إدارتها
    يمين: محرر قيم الـ instance المختار
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        # ── رأس: اسم المجموعة المختارة ──
        self._set_hdr = QLabel("📐  إدخال القيم")
        self._set_hdr.setStyleSheet("""
            font-weight: bold; font-size: 13px; color: #1565c0;
            background: #e8f0fe; border-radius: 6px; padding: 6px 12px;
        """)
        root.addWidget(self._set_hdr)

        # ── hint اختيار مجموعة ──
        self._hint = QLabel("اختر مجموعة مقاسات من القائمة لبدء الإدخال")
        self._hint.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        self._hint.setAlignment(Qt.AlignCenter)
        root.addWidget(self._hint)

        # ── Splitter: قائمة يسار | محرر يمين ──
        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setHandleWidth(5)
        self._splitter.setStyleSheet("""
            QSplitter::handle { background: #e0e0e0; }
            QSplitter::handle:hover { background: #bbdefb; }
        """)
        self._splitter.setVisible(False)

        self._instances_list = _InstancesList(self.conn)
        self._editor         = _InstanceEditor(self.conn)

        self._instances_list.instance_selected.connect(self._on_instance_selected)
        # instances_changed لا يمسح الـ editor تلقائياً — الاختيار في القائمة هو اللي يلود

        self._splitter.addWidget(self._instances_list)
        self._splitter.addWidget(self._editor)
        self._splitter.setSizes([220, 480])

        root.addWidget(self._splitter, stretch=1)

    def load_set(self, set_id: int):
        """يُستدعى من _SetsPanel عند اختيار مجموعة."""
        self._set_id = set_id

        # جلب اسم المجموعة
        try:
            ds = self.conn.execute(
                "SELECT name FROM dimension_sets WHERE id=?", (set_id,)
            ).fetchone()
            set_name = ds["name"] if ds else f"مجموعة #{set_id}"
        except Exception:
            set_name = f"مجموعة #{set_id}"

        self._set_hdr.setText(f"📐  {set_name}")
        self._hint.setVisible(False)
        self._splitter.setVisible(True)

        self._editor.clear()
        self._instances_list.load_set(set_id)

    def clear(self):
        self._set_id = None
        self._set_hdr.setText("📐  إدخال القيم")
        self._hint.setVisible(True)
        self._splitter.setVisible(False)
        self._instances_list.clear()
        self._editor.clear()

    def _on_instance_selected(self, instance_id: int):
        if self._set_id:
            self._editor.load(self._set_id, instance_id)