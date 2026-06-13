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
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.widgets.shared.message_box import msg_question, msg_info, msg_warning, msg_critical


class CompaniesDialog(QDialog):
    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self._conn       = central_conn
        self._editing_id = None
        self._color      = _C['accent']

        self.setWindowTitle(tr("companies_manage_title"))
        self.setMinimumSize(820, 560)
        self.setModal(True)
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(10)

        title = QLabel(tr("companies_manage_title"))
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
        close_btn = QPushButton(tr("shared_close_btn"))
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
        lbl = QLabel(tr("companies_registered"))
        lbl.setStyleSheet("font-weight: bold; font-size: 11pt; background: transparent;")
        toolbar.addWidget(lbl)
        toolbar.addStretch()

        add_btn = QPushButton(tr("company_add_btn"))
        add_btn.setFixedHeight(32)
        add_btn.setStyleSheet(self._btn_style(_C['success'], _C['success_hover']))
        add_btn.clicked.connect(self._new_company)
        toolbar.addWidget(add_btn)
        lay.addLayout(toolbar)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels([
            tr("company_col_name"), tr("company_col_short"),
            tr("company_col_status"), tr("company_col_actions"),
        ])
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

        self._form_title = QLabel(tr("company_new_title"))
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

        lay.addWidget(_lbl(tr("company_name_label")))
        self._inp_name = _inp(tr("company_name_placeholder"))
        lay.addWidget(self._inp_name)

        lay.addWidget(_lbl(tr("company_short_name_label")))
        self._inp_short = _inp(tr("company_short_placeholder"))
        lay.addWidget(self._inp_short)

        lay.addWidget(_lbl(tr("company_color_label")))
        color_row = QHBoxLayout()
        self._color_preview = QLabel()
        self._color_preview.setFixedSize(32, 32)
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: 5px;"
            f"border: 1px solid {_C['border_med']};"
        )
        color_btn = QPushButton(tr("company_choose_color"))
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

        lay.addWidget(_lbl(tr("company_notes_label")))
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
        self._save_btn = QPushButton(tr("btn_save"))
        self._save_btn.setFixedHeight(34)
        self._save_btn.setStyleSheet(
            self._btn_style(_C['accent'], _C['accent_hover'])
        )
        self._save_btn.clicked.connect(self._save)
        form_btns.addWidget(self._save_btn)

        self._cancel_btn = QPushButton(tr("btn_cancel"))
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
                background: {bg}; color: {_C['bg_input']}; font-weight: 600;
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
                background: {r['color'] or _C['accent']};
                color: {_C['bg_input']}; font-weight: 600;
                border-radius: 4px; padding: 3px 8px;
            """)
            self._table.setCellWidget(ri, 0, name_lbl)

            short = QTableWidgetItem(r["short_name"] or tr("dash"))
            short.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(ri, 1, short)

            status_text = tr("company_status_active") if r["is_active"] else tr("company_status_paused")
            status = QTableWidgetItem(status_text)
            status.setTextAlignment(Qt.AlignCenter)
            status.setForeground(
                QColor(_C["success"]) if r["is_active"] else QColor(_C["text_muted"])
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
            edit_btn.setToolTip(tr("company_tooltip_edit"))
            edit_btn.setStyleSheet(_btn_ss(_C["t_account_dr_bg"], _C["accent_mid"]))
            edit_btn.clicked.connect(
                lambda _, rid=r["id"]: self._edit_company(rid)
            )

            toggle_btn = QPushButton("⏸" if r["is_active"] else "▶")
            toggle_btn.setToolTip(tr("company_tooltip_toggle"))
            toggle_btn.setStyleSheet(_btn_ss(_C["warning_bg"], _C["warning_border"]))
            toggle_btn.clicked.connect(
                lambda _, rid=r["id"]: self._toggle(rid)
            )

            del_btn = QPushButton("🗑")
            del_btn.setToolTip(tr("company_tooltip_delete"))
            del_btn.setStyleSheet(_btn_ss(_C["danger_bg"], _C["danger_hover"]))
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
        self._form_title.setText(tr("company_new_title"))
        self._inp_name.clear()
        self._inp_short.clear()
        self._inp_notes.clear()
        self._color = _C["accent"]
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: 5px;"
            f"border: 1px solid {_C['border_med']};"
        )
        self._inp_name.setFocus()

    def _edit_company(self, company_id: int):
        row = fetch_company(self._conn, company_id)
        if not row:
            return
        self._editing_id = company_id
        self._form_title.setText(tr("company_edit_title").format(name=row["name"]))
        self._inp_name.setText(row["name"])
        self._inp_short.setText(row["short_name"] or "")
        self._inp_notes.setPlainText(row["notes"] or "")
        self._color = row["color"] or _C["accent"]
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: 5px;"
            f"border: 1px solid {_C['border_med']};"
        )

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self, tr("company_pick_color_title"))
        if c.isValid():
            self._color = c.name()
            self._color_preview.setStyleSheet(
                f"background: {self._color}; border-radius: 5px;"
                f"border: 1px solid {_C['border_med']};"
            )

    def _save(self):
        name  = self._inp_name.text().strip()
        short = self._inp_short.text().strip()
        notes = self._inp_notes.toPlainText().strip()

        if not name:
            msg_warning(self, tr("warning"), tr("company_name_required"))
            return

        try:
            if self._editing_id:
                update_company(
                    self._conn, self._editing_id,
                    name=name, short_name=short,
                    color=self._color, notes=notes
                )
                msg_info(self, tr("done"), tr("company_updated_msg").format(name=name))
            else:
                insert_company(
                    self._conn,
                    name=name, short_name=short,
                    color=self._color, notes=notes
                )
                msg_info(self, tr("done"), tr("company_created_msg").format(name=name))
            self._reset_form()
            self._load()
        except Exception as e:
            msg_critical(self, tr("error"), str(e))

    def _reset_form(self):
        self._editing_id = None
        self._form_title.setText(tr("company_new_title"))
        self._inp_name.clear()
        self._inp_short.clear()
        self._inp_notes.clear()
        self._color = _C["accent"]
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: 5px;"
            f"border: 1px solid {_C['border_med']};"
        )

    def _toggle(self, company_id: int):
        toggle_company_active(self._conn, company_id)
        self._load()

    def _delete(self, company_id: int, name: str):
        if msg_question(
            self, tr("confirm_delete"),
            tr("company_delete_confirm").format(name=name)
        ):
            try:
                delete_company(self._conn, company_id)
                self._load()
            except Exception as e:
                msg_critical(self, tr("error"), str(e))
