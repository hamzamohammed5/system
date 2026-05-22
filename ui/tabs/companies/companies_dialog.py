"""
ui/tabs/companies/companies_dialog.py
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QLineEdit, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QColorDialog, QWidget, QFrame,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor

from db.companies.companies_repo import (
    fetch_all_companies, fetch_company,
    insert_company, update_company,
    delete_company, toggle_company_active,
)
from ui.app_settings import _C
from ui.widgets.shared.message_box import msg_question, msg_info, msg_critical


class CompaniesDialog(QDialog):
    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self._conn       = central_conn
        self._editing_id = None
        self._color      = "#1565c0"

        self.setWindowTitle("🏢  إدارة الشركات")
        self.setMinimumSize(820, 560)
        self.setModal(True)
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel("🏢  إدارة الشركات")
        title.setStyleSheet(f"""
            font-size: 14pt; font-weight: bold;
            color: {_C['accent']}; padding: 4px 0;
            background: transparent;
        """)
        root.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(6)

        splitter.addWidget(self._build_table_panel())
        splitter.addWidget(self._build_form_panel())
        splitter.setSizes([460, 320])
        root.addWidget(splitter)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close_btn = QPushButton("✖  إغلاق")
        close_btn.setFixedHeight(34)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 4px 18px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        close_btn.clicked.connect(self.accept)
        btn_row.addWidget(close_btn)
        root.addLayout(btn_row)

    def _build_table_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet("background: transparent;")
        lay   = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        toolbar = QHBoxLayout()
        lbl = QLabel("الشركات المسجلة")
        lbl.setStyleSheet("font-weight: bold; font-size: 11pt; background: transparent;")
        toolbar.addWidget(lbl)
        toolbar.addStretch()

        add_btn = QPushButton("➕  إضافة شركة")
        add_btn.setFixedHeight(32)
        add_btn.setStyleSheet(self._btn_style("#2e7d52", "#1b5e38"))
        add_btn.clicked.connect(self._new_company)
        toolbar.addWidget(add_btn)
        lay.addLayout(toolbar)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(["الاسم", "الاختصار", "الحالة", "إجراءات"])
        self._table.setSelectionBehavior(QTableWidget.SelectRows)
        self._table.setEditTriggers(QTableWidget.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.Fixed)
        self._table.setColumnWidth(3, 110)
        self._table.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {_C['border']};
                border-radius: 6px;
                background: {_C['bg_input']};
                alternate-background-color: {_C['bg_surface']};
                gridline-color: {_C['border']};
            }}
            QTableWidget::item {{
                padding: 4px 8px;
                border: none;
                border-bottom: 1px solid {_C['border']};
                background: transparent;
            }}
            QTableWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent_text']};
            }}
            QHeaderView::section {{
                background: {_C['bg_surface_2']};
                padding: 6px 8px; border: none;
                border-bottom: 2px solid {_C['border_med']};
                font-weight: 600; color: {_C['text_muted']};
            }}
        """)
        lay.addWidget(self._table)
        return panel

    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        panel.setStyleSheet(f"""
            QWidget {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: 8px;
            }}
        """)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        self._form_title = QLabel("✨  شركة جديدة")
        self._form_title.setStyleSheet(
            "font-weight: bold; font-size: 11pt; background: transparent;"
        )
        lay.addWidget(self._form_title)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background: {_C['border']}; border: none;")
        sep.setFixedHeight(1)
        lay.addWidget(sep)

        def _lbl(text):
            l = QLabel(text)
            l.setStyleSheet(
                f"font-size: 10pt; color: {_C['text_sec']}; background: transparent;"
            )
            return l

        def _inp(placeholder=""):
            e = QLineEdit()
            e.setPlaceholderText(placeholder)
            e.setFixedHeight(32)
            e.setStyleSheet(f"""
                QLineEdit {{
                    border: 1px solid {_C['border_med']};
                    border-radius: 5px; padding: 2px 8px;
                    background: {_C['bg_input']};
                }}
                QLineEdit:focus {{ border-color: {_C['accent']}; }}
            """)
            return e

        lay.addWidget(_lbl("اسم الشركة *"))
        self._inp_name = _inp("مثال: شركة النور للطباعة")
        lay.addWidget(self._inp_name)

        lay.addWidget(_lbl("الاسم المختصر"))
        self._inp_short = _inp("مثال: النور")
        lay.addWidget(self._inp_short)

        lay.addWidget(_lbl("اللون المميز"))
        color_row = QHBoxLayout()
        self._color_preview = QLabel()
        self._color_preview.setFixedSize(32, 32)
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: 5px;"
            "border: 1px solid #ccc;"
        )
        color_btn = QPushButton("اختر لوناً")
        color_btn.setFixedHeight(32)
        color_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 2px 10px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_preview)
        color_row.addWidget(color_btn)
        color_row.addStretch()
        lay.addLayout(color_row)

        lay.addWidget(_lbl("ملاحظات"))
        self._inp_notes = QTextEdit()
        self._inp_notes.setMaximumHeight(80)
        self._inp_notes.setStyleSheet(f"""
            QTextEdit {{
                border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 4px;
                background: {_C['bg_input']}; font-size: 10pt;
            }}
            QTextEdit:focus {{ border-color: {_C['accent']}; }}
        """)
        lay.addWidget(self._inp_notes)

        lay.addStretch()

        form_btns = QHBoxLayout()
        self._save_btn = QPushButton("💾  حفظ")
        self._save_btn.setFixedHeight(34)
        self._save_btn.setStyleSheet(
            self._btn_style(_C['accent'], _C['accent_hover'])
        )
        self._save_btn.clicked.connect(self._save)
        form_btns.addWidget(self._save_btn)

        self._cancel_btn = QPushButton("✖  إلغاء")
        self._cancel_btn.setFixedHeight(34)
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: 1px solid {_C['border_med']};
                border-radius: 5px; padding: 4px 14px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)
        self._cancel_btn.clicked.connect(self._reset_form)
        form_btns.addWidget(self._cancel_btn)
        lay.addLayout(form_btns)

        return panel

    def _btn_style(self, bg, hover):
        return f"""
            QPushButton {{
                background: {bg}; color: white; font-weight: 600;
                border: none; border-radius: 5px; padding: 4px 14px;
            }}
            QPushButton:hover {{ background: {hover}; }}
        """

    def _load(self):
        rows = fetch_all_companies(self._conn)
        self._table.setRowCount(0)
        for r in rows:
            ri = self._table.rowCount()
            self._table.insertRow(ri)

            name_lbl = QLabel(f"  {r['name']}")
            name_lbl.setStyleSheet(f"""
                background: {r['color'] or '#1565c0'};
                color: white; font-weight: 600;
                border-radius: 4px; padding: 3px 8px;
            """)
            self._table.setCellWidget(ri, 0, name_lbl)

            short = QTableWidgetItem(r["short_name"] or "—")
            short.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(ri, 1, short)

            status_text = "✅ نشطة" if r["is_active"] else "⏸ موقوفة"
            status = QTableWidgetItem(status_text)
            status.setTextAlignment(Qt.AlignCenter)
            status.setForeground(
                QColor("#2e7d52") if r["is_active"] else QColor("#888")
            )
            self._table.setItem(ri, 2, status)

            btns_widget = QWidget()
            btns_widget.setStyleSheet("background: transparent; border: none;")
            btns_lay = QHBoxLayout(btns_widget)
            btns_lay.setContentsMargins(4, 2, 4, 2)
            btns_lay.setSpacing(4)
            btns_lay.setAlignment(Qt.AlignCenter)

            _btn_ss = lambda bg, hov: f"""
                QPushButton {{
                    background: {bg}; border: none;
                    border-radius: 4px; font-size: 12pt;
                    min-width: 28px; min-height: 28px;
                    max-width: 28px; max-height: 28px;
                }}
                QPushButton:hover {{ background: {hov}; }}
            """

            edit_btn = QPushButton("✏")
            edit_btn.setToolTip("تعديل")
            edit_btn.setStyleSheet(_btn_ss("#e3f2fd", "#bbdefb"))
            edit_btn.clicked.connect(
                lambda _, rid=r["id"]: self._edit_company(rid)
            )

            toggle_btn = QPushButton("⏸" if r["is_active"] else "▶")
            toggle_btn.setToolTip("إيقاف / تفعيل")
            toggle_btn.setStyleSheet(_btn_ss("#fff8e1", "#ffecb3"))
            toggle_btn.clicked.connect(
                lambda _, rid=r["id"]: self._toggle(rid)
            )

            del_btn = QPushButton("🗑")
            del_btn.setToolTip("حذف")
            del_btn.setStyleSheet(_btn_ss("#fdecea", "#ffcdd2"))
            del_btn.clicked.connect(
                lambda _, rid=r["id"], nm=r["name"]: self._delete(rid, nm)
            )

            btns_lay.addWidget(edit_btn)
            btns_lay.addWidget(toggle_btn)
            btns_lay.addWidget(del_btn)
            self._table.setCellWidget(ri, 3, btns_widget)
            self._table.setRowHeight(ri, 42)

    def _new_company(self):
        self._editing_id = None
        self._form_title.setText("✨  شركة جديدة")
        self._inp_name.clear()
        self._inp_short.clear()
        self._inp_notes.clear()
        self._color = "#1565c0"
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: 5px; border: 1px solid #ccc;"
        )
        self._inp_name.setFocus()

    def _edit_company(self, company_id: int):
        row = fetch_company(self._conn, company_id)
        if not row:
            return
        self._editing_id = company_id
        self._form_title.setText(f"✏️  تعديل: {row['name']}")
        self._inp_name.setText(row["name"])
        self._inp_short.setText(row["short_name"] or "")
        self._inp_notes.setPlainText(row["notes"] or "")
        self._color = row["color"] or "#1565c0"
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: 5px; border: 1px solid #ccc;"
        )

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self, "اختر لون الشركة")
        if c.isValid():
            self._color = c.name()
            self._color_preview.setStyleSheet(
                f"background: {self._color}; border-radius: 5px; border: 1px solid #ccc;"
            )

    def _save(self):
        name  = self._inp_name.text().strip()
        short = self._inp_short.text().strip()
        notes = self._inp_notes.toPlainText().strip()

        if not name:
            msg_warning(self, "تنبيه", "اسم الشركة مطلوب")
            return

        try:
            if self._editing_id:
                update_company(
                    self._conn, self._editing_id,
                    name=name, short_name=short,
                    color=self._color, notes=notes
                )
                msg_info(self, "تم", f"تم تحديث بيانات «{name}»")
            else:
                insert_company(
                    self._conn,
                    name=name, short_name=short,
                    color=self._color, notes=notes
                )
                msg_info(
                    self, "تم",
                    f"تم إنشاء شركة «{name}» بنجاح.\n"
                    "تم إنشاء قواعد البيانات الخاصة بها."
                )
            self._reset_form()
            self._load()
        except Exception as e:
            msg_critical(self, "خطأ", str(e))

    def _reset_form(self):
        self._editing_id = None
        self._form_title.setText("✨  شركة جديدة")
        self._inp_name.clear()
        self._inp_short.clear()
        self._inp_notes.clear()
        self._color = "#1565c0"
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: 5px; border: 1px solid #ccc;"
        )

    def _toggle(self, company_id: int):
        toggle_company_active(self._conn, company_id)
        self._load()

    def _delete(self, company_id: int, name: str):
        if msg_question(
            self, "تأكيد الحذف",
            f"هل تريد حذف شركة «{name}»؟\n\n"
            "ملاحظة: ملفات قواعد البيانات ستبقى على القرص."
        ):
            try:
                delete_company(self._conn, company_id)
                self._load()
            except Exception as e:
                msg_critical(self, "خطأ", str(e))
