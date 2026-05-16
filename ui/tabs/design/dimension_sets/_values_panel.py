"""
ui/tabs/design/dimension_sets/_values_panel.py
=====================================
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox,
    QMessageBox, QScrollArea, QFrame,
)
from PyQt5.QtCore import Qt

from db.designs.dimension_sets_repo import (
    fetch_fields_for_set,
    fetch_standalone_values,
    calc_standalone_cross_auto,
)


def _row_val(row, key, default=None):
    """
    قراءة آمنة من sqlite3.Row — لا يدعم .get() مثل dict.
    يرجع default لو العمود غير موجود أو قيمته None.
    """
    try:
        v = row[key]
        return v if v is not None else default
    except (IndexError, KeyError):
        return default


# ══════════════════════════════════════════════════════════
# لوحة إدخال القيم
# ══════════════════════════════════════════════════════════

class _ValuesPanel(QWidget):
    """
    لوحة إدخال قيم المقاسات مباشرة على مجموعة محددة.
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._rows   = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        hdr = QLabel("📊  إدخال قيم المقاسات")
        hdr.setStyleSheet("""
            font-weight: bold; font-size: 13px; color: #1565c0;
            background: #e8f0fe; border-radius: 6px; padding: 6px 12px;
        """)
        root.addWidget(hdr)

        self._hint = QLabel("اختر مجموعة مقاسات من القائمة لبدء الإدخال")
        self._hint.setStyleSheet("color: #888; font-size: 11px; padding: 4px;")
        self._hint.setAlignment(Qt.AlignCenter)
        root.addWidget(self._hint)

        self._col_header = QWidget()
        self._col_header.setVisible(False)
        self._col_header.setStyleSheet(
            "background: #f0f4ff; border-bottom: 1px solid #c5cae9;"
        )
        col_lay = QHBoxLayout(self._col_header)
        col_lay.setContentsMargins(10, 4, 10, 4)
        col_lay.setSpacing(8)

        def _hdr_lbl(text, width=None, stretch=0):
            l = QLabel(text)
            l.setStyleSheet(
                "font-size: 10px; font-weight: bold; color: #555;"
                "background: transparent; border: none;"
            )
            l.setAlignment(Qt.AlignCenter)
            if width:
                l.setFixedWidth(width)
            return l, stretch

        lbl_name,  _ = _hdr_lbl("الاسم / التسمية", 110)
        lbl_field, _ = _hdr_lbl("الحقل", 100)
        lbl_val,   _ = _hdr_lbl("القيمة", 0)
        lbl_unit,  _ = _hdr_lbl("الوحدة", 30)
        lbl_ref,   _ = _hdr_lbl("المرجع (المصدر)", 110)
        lbl_act,   _ = _hdr_lbl("", 52)

        col_lay.addWidget(lbl_name)
        col_lay.addWidget(lbl_field)
        col_lay.addWidget(lbl_val, 1)
        col_lay.addWidget(lbl_unit)
        col_lay.addWidget(lbl_ref)
        col_lay.addWidget(lbl_act)
        root.addWidget(self._col_header)

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
        self._fields_w   = QWidget()
        self._fields_w.setStyleSheet("background: white;")
        self._fields_lay = QVBoxLayout(self._fields_w)
        self._fields_lay.setSpacing(4)
        self._fields_lay.setContentsMargins(6, 6, 6, 6)
        self._fields_lay.addStretch()
        self._scroll.setWidget(self._fields_w)
        root.addWidget(self._scroll, stretch=1)

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
        self.btn_save.clicked.connect(self._save_values)

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

        self.btn_reset = QPushButton("↺  مسح")
        self.btn_reset.setMinimumHeight(32)
        self.btn_reset.setEnabled(False)
        self.btn_reset.setStyleSheet("""
            QPushButton {
                background: #fff3e0; color: #e65100;
                border: 1px solid #ffcc80; border-radius: 5px; padding: 4px 14px;
            }
            QPushButton:hover    { background: #ffe0b2; }
            QPushButton:disabled { background: #f5f5f5; color: #bbb; border-color: #ddd; }
        """)
        self.btn_reset.clicked.connect(self._reset_values)

        self.lbl_status = QLabel("")
        self.lbl_status.setStyleSheet("color: #2e7d32; font-size: 11px;")

        bar.addWidget(self.btn_save)
        bar.addWidget(self.btn_calc)
        bar.addWidget(self.btn_reset)
        bar.addStretch()
        bar.addWidget(self.lbl_status)
        root.addLayout(bar)

    def load_set(self, set_id: int):
        self._set_id = set_id
        self._rows   = {}
        self._clear_fields()
        self._hint.setVisible(False)

        fields     = fetch_fields_for_set(self.conn, set_id)
        num_fields = [f for f in fields if f["field_type"] == "number"]

        if not num_fields:
            self._col_header.setVisible(False)
            lbl = QLabel("هذه المجموعة ليس لها حقول رقمية — أضف حقولاً أولاً")
            lbl.setStyleSheet("color: #888; font-size: 11px; padding: 12px;")
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setWordWrap(True)
            self._fields_lay.insertWidget(0, lbl)
            self._set_buttons(False, False)
            return

        self._col_header.setVisible(True)
        saved    = fetch_standalone_values(self.conn, set_id)
        has_auto = any(bool(_row_val(f, "source_field_id")) for f in num_fields)

        for f in num_fields:
            saved_info = saved.get(f["id"], {})
            row_w = self._build_row(f, saved_info)
            self._fields_lay.insertWidget(
                self._fields_lay.count() - 1, row_w
            )

        self._set_buttons(True, has_auto)
        self.lbl_status.setText("")

    def _build_row(self, field_data, saved_info: dict) -> QWidget:
        fid = field_data["id"]

        # قراءة آمنة من sqlite3.Row
        has_dep    = bool(_row_val(field_data, "source_field_id"))
        src_set_id = _row_val(field_data, "source_set_id")
        src_fid    = _row_val(field_data, "source_field_id")
        dep_offset = float(_row_val(field_data, "dep_offset") or 0)
        src_label  = _row_val(field_data, "source_label", "")
        src_set_nm = _row_val(field_data, "source_set_name", "")

        current_value = saved_info.get("value_num")
        saved_name    = saved_info.get("value_text") or ""

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

        name_inp = QLineEdit()
        name_inp.setPlaceholderText("اسم / تسمية...")
        name_inp.setFixedWidth(110)
        name_inp.setMinimumHeight(28)
        name_inp.setStyleSheet("""
            QLineEdit {
                border: 1px solid #c5cae9; border-radius: 4px;
                padding: 2px 6px; background: white; font-size: 11px;
            }
            QLineEdit:focus { border-color: #1565c0; }
        """)
        if saved_name:
            name_inp.setText(saved_name)

        lbl = QLabel(field_data["label"])
        lbl.setFixedWidth(100)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet(
            "background: transparent; border: none;"
            "font-weight: bold; color: #333;"
        )

        spin = QDoubleSpinBox()
        spin.setRange(-99999, 99999)
        spin.setDecimals(4)
        spin.setMinimumHeight(28)
        spin.setMinimumWidth(110)
        spin.setStyleSheet("""
            QDoubleSpinBox {
                border: 1px solid #c5cae9; border-radius: 4px;
                padding: 2px 6px; background: white;
            }
            QDoubleSpinBox:focus { border-color: #1565c0; }
        """)
        if current_value is not None:
            spin.setValue(float(current_value))

        unit_lbl = QLabel(field_data["unit"] or "cm")
        unit_lbl.setFixedWidth(30)
        unit_lbl.setStyleSheet(
            "color: #888; background: transparent; border: none; font-size: 10px;"
        )

        lay.addWidget(name_inp)
        lay.addWidget(lbl)
        lay.addWidget(spin, stretch=1)
        lay.addWidget(unit_lbl)

        ref_lbl = QLabel("")
        ref_lbl.setFixedWidth(110)
        ref_lbl.setAlignment(Qt.AlignCenter)
        ref_lbl.setWordWrap(False)

        if has_dep and src_fid:
            actual_src_set = src_set_id if src_set_id else self._set_id
            self._refresh_ref_label(ref_lbl, src_fid, actual_src_set, dep_offset)
            ref_lbl.setVisible(True)
        else:
            ref_lbl.setVisible(False)

        lay.addWidget(ref_lbl)

        if has_dep and src_fid:
            actual_src_set = src_set_id if src_set_id else self._set_id
            tooltip_txt = f"يعتمد على: {src_label}"
            if src_set_nm:
                tooltip_txt += f"\nمن مجموعة: {src_set_nm}"

            btn_auto = QPushButton("⟳")
            btn_auto.setFixedSize(30, 28)
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
                       sfid=src_fid, ssid=actual_src_set, off=dep_offset:
                self._calc_one(fid_, sp_, rl_, sfid, ssid, off)
            )

            badge = QLabel("↗")
            badge.setFixedSize(20, 20)
            badge.setAlignment(Qt.AlignCenter)
            badge.setToolTip(tooltip_txt)
            badge.setStyleSheet("""
                background: #e8f5e9; border-radius: 3px;
                color: #2e7d32; font-size: 10px; border: none;
            """)

            lay.addWidget(badge)
            lay.addWidget(btn_auto)
        else:
            spacer = QLabel("")
            spacer.setFixedWidth(52)
            spacer.setStyleSheet("background: transparent; border: none;")
            lay.addWidget(spacer)

        self._rows[fid] = {
            "spin":     spin,
            "name_inp": name_inp,
            "ref_lbl":  ref_lbl if has_dep else None,
            "src_fid":  src_fid,
            "src_sid":  src_set_id if src_set_id else (self._set_id if has_dep else None),
            "offset":   dep_offset,
        }
        return frame

    def _refresh_ref_label(self, ref_lbl, source_field_id, source_set_id, offset):
        try:
            row = self.conn.execute(
                "SELECT dsv.value_num, ds.name AS set_name "
                "FROM dimension_set_values dsv "
                "JOIN dimension_sets ds ON ds.id = dsv.set_id "
                "WHERE dsv.set_id=? AND dsv.field_id=?",
                (source_set_id, source_field_id)
            ).fetchone()

            if row and row["value_num"] is not None:
                src_val = float(row["value_num"])
                result  = src_val + float(offset)
                sign    = f"+{offset:g}" if offset >= 0 else f"{offset:g}"
                ref_lbl.setText(f"{src_val:g}{sign}={result:g}")
                ref_lbl.setToolTip(
                    f"مصدر: {row['set_name']}\n"
                    f"القيمة: {src_val:g}  |  offset: {offset:g}  |  النتيجة: {result:g}"
                )
                ref_lbl.setStyleSheet("""
                    color: #1565c0; font-size: 10px;
                    background: #e8f0fe; border: 1px solid #bbdefb;
                    border-radius: 3px; padding: 1px 4px;
                """)
            else:
                ref_lbl.setText("مصدر: —")
                ref_lbl.setToolTip("لا توجد قيمة محفوظة في المجموعة المصدر")
                ref_lbl.setStyleSheet("""
                    color: #aaa; font-size: 10px;
                    background: #f5f5f5; border: 1px solid #e0e0e0;
                    border-radius: 3px; padding: 1px 4px;
                """)
        except Exception as e:
            ref_lbl.setText("مصدر: ؟")
            ref_lbl.setToolTip(str(e))

    def _refresh_all_ref_labels(self):
        for fid, row_data in self._rows.items():
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

    def _set_buttons(self, enabled, has_auto=False):
        self.btn_save.setEnabled(enabled)
        self.btn_calc.setEnabled(enabled and has_auto)
        self.btn_reset.setEnabled(enabled)

    def _calc_one(self, field_id, spin, ref_lbl, source_field_id, source_set_id, offset):
        if self._set_id is None:
            return
        self._save_values(silent=True)

        val = calc_standalone_cross_auto(self.conn, field_id, self._set_id)
        if val is not None:
            spin.setValue(val)
            spin.setStyleSheet("""
                QDoubleSpinBox {
                    border: 2px solid #43a047; border-radius: 4px;
                    padding: 2px 6px; background: #f1f8e9;
                }
            """)
            self.conn.execute("""
                INSERT INTO dimension_set_values (set_id, field_id, value_num)
                VALUES (?, ?, ?)
                ON CONFLICT(set_id, field_id) DO UPDATE SET value_num=excluded.value_num
            """, (self._set_id, field_id, val))
            self.conn.commit()
            self.lbl_status.setText(f"✓ {val:.4g}")
            if ref_lbl:
                self._refresh_ref_label(ref_lbl, source_field_id, source_set_id, offset)
        else:
            QMessageBox.information(
                self, "تنبيه",
                "لا توجد قيمة للحقل المصدر بعد.\n"
                "أدخل قيمة الحقل المصدر في مجموعتها أولاً ثم احسب."
            )

    def _calc_all_auto(self):
        if self._set_id is None:
            return
        self._save_values(silent=True)

        fields = fetch_fields_for_set(self.conn, self._set_id)
        count  = 0

        for f in fields:
            if f["field_type"] != "number" or not _row_val(f, "source_field_id"):
                continue
            fid = f["id"]
            if fid not in self._rows:
                continue

            val = calc_standalone_cross_auto(self.conn, fid, self._set_id)
            if val is not None:
                self._rows[fid]["spin"].setValue(val)
                self._rows[fid]["spin"].setStyleSheet("""
                    QDoubleSpinBox {
                        border: 2px solid #43a047; border-radius: 4px;
                        padding: 2px 6px; background: #f1f8e9;
                    }
                """)
                self.conn.execute("""
                    INSERT INTO dimension_set_values (set_id, field_id, value_num)
                    VALUES (?, ?, ?)
                    ON CONFLICT(set_id, field_id) DO UPDATE SET value_num=excluded.value_num
                """, (self._set_id, fid, val))

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
            else "⚠ لا توجد قيم مصدر كافية — أدخل القيم في مجموعاتها أولاً"
        )

    def _save_values(self, silent=False):
        if self._set_id is None:
            return

        for fid, row_data in self._rows.items():
            val      = row_data["spin"].value()
            row_name = row_data["name_inp"].text().strip()
            self.conn.execute("""
                INSERT INTO dimension_set_values (set_id, field_id, value_num, value_text)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(set_id, field_id) DO UPDATE SET
                    value_num  = excluded.value_num,
                    value_text = excluded.value_text
            """, (self._set_id, fid, val, row_name or None))
        self.conn.commit()

        if not silent:
            self.lbl_status.setText("✓ تم الحفظ")
            for row_data in self._rows.values():
                row_data["spin"].setStyleSheet("""
                    QDoubleSpinBox {
                        border: 1px solid #c5cae9; border-radius: 4px;
                        padding: 2px 6px; background: white;
                    }
                    QDoubleSpinBox:focus { border-color: #1565c0; }
                """)
            self._refresh_all_ref_labels()

    def _reset_values(self):
        if self._set_id is None:
            return
        if QMessageBox.question(
            self, "تأكيد", "مسح كل القيم والأسماء المدخلة؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            for row_data in self._rows.values():
                row_data["spin"].setValue(0.0)
                row_data["name_inp"].clear()
                rl = row_data.get("ref_lbl")
                if rl:
                    rl.setText("مصدر: —")
                    rl.setStyleSheet("""
                        color: #aaa; font-size: 10px;
                        background: #f5f5f5; border: 1px solid #e0e0e0;
                        border-radius: 3px; padding: 1px 4px;
                    """)
            self.lbl_status.setText("↺ تم المسح")

    def clear(self):
        self._set_id = None
        self._rows   = {}
        self._clear_fields()
        self._col_header.setVisible(False)
        self._set_buttons(False)
        self._hint.setVisible(True)
        self.lbl_status.setText("")