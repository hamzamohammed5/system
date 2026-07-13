"""
ui/tabs/companies/companies_dialog.py
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QColorDialog, QWidget,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QColor
from ui.widgets.panels.themed_inputs import ThemedLineEdit, ThemedFrame, ThemedTextEdit

from services.companies.company_service import CompanyService
from ui.theme import _C
from ui.font import FS_SM, FS_BASE, FS_MD, FS_LG, FS_XL
from ui.widgets.core.i18n import tr
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.dialogs.message import msg_question, msg_info, msg_warning, msg_critical
from ui.constants import (
    SEPARATOR_LINE_H,
    COMPANIES_DLG_BORDER_W, COMPANIES_DLG_HDR_BORDER_W,
    COMPANIES_DLG_MIN_W, COMPANIES_DLG_MIN_H,
    COMPANIES_DLG_ROOT_MARGIN, COMPANIES_DLG_ROOT_SPACING,
    COMPANIES_DLG_TITLE_PAD_V,
    COMPANIES_DLG_SPLITTER_HANDLE_W,
    COMPANIES_DLG_SPLITTER_L, COMPANIES_DLG_SPLITTER_R,
    COMPANIES_DLG_CLOSE_BTN_H, COMPANIES_DLG_CLOSE_BTN_RADIUS, COMPANIES_DLG_CLOSE_BTN_PAD_H,
    COMPANIES_DLG_TABLE_PANEL_SPACING, COMPANIES_DLG_ADD_BTN_H,
    COMPANIES_DLG_TABLE_COL3_W, COMPANIES_DLG_TABLE_RADIUS,
    COMPANIES_DLG_TABLE_ITEM_PAD_V, COMPANIES_DLG_TABLE_ITEM_PAD_H,
    COMPANIES_DLG_HDR_PAD_V, COMPANIES_DLG_HDR_PAD_H,
    COMPANIES_DLG_FORM_RADIUS, COMPANIES_DLG_FORM_MARGIN, COMPANIES_DLG_FORM_SPACING,
    COMPANIES_DLG_INP_H, COMPANIES_DLG_INP_RADIUS,
    COMPANIES_DLG_INP_PAD_V, COMPANIES_DLG_INP_PAD_H,
    COMPANIES_DLG_COLOR_PREVIEW_SIZE, COMPANIES_DLG_COLOR_PREVIEW_RADIUS,
    COMPANIES_DLG_COLOR_BTN_H, COMPANIES_DLG_COLOR_BTN_PAD_H,
    COMPANIES_DLG_NOTES_MAX_H, COMPANIES_DLG_NOTES_RADIUS, COMPANIES_DLG_NOTES_PAD,
    COMPANIES_DLG_SAVE_BTN_H, COMPANIES_DLG_CANCEL_BTN_H,
    COMPANIES_DLG_CANCEL_BTN_RADIUS, COMPANIES_DLG_CANCEL_BTN_PAD_H,
    COMPANIES_DLG_BTN_RADIUS, COMPANIES_DLG_BTN_PAD_H,
    COMPANIES_DLG_NAME_BADGE_RADIUS, COMPANIES_DLG_NAME_BADGE_PAD_V, COMPANIES_DLG_NAME_BADGE_PAD_H,
    COMPANIES_DLG_BTNS_CELL_MARGIN_H, COMPANIES_DLG_BTNS_CELL_MARGIN_V, COMPANIES_DLG_BTNS_CELL_SPACING,
    COMPANIES_DLG_ACTION_BTN_SIZE, COMPANIES_DLG_ACTION_BTN_RADIUS,
    COMPANIES_DLG_ROW_H,
)


class CompaniesDialog(QDialog, WidgetMixin):
    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self._conn       = central_conn
        self._svc        = CompanyService(central_conn)
        self._editing_id = None
        self._color      = _C['accent']

        self.setWindowTitle(tr("companies_manage_title"))
        self.setMinimumSize(COMPANIES_DLG_MIN_W, COMPANIES_DLG_MIN_H)
        self.setModal(True)
        self._init_widget_mixin(data=False)
        self._build()
        self._refresh_style()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*COMPANIES_DLG_ROOT_MARGIN)
        root.setSpacing(COMPANIES_DLG_ROOT_SPACING)

        self._title = QLabel(tr("companies_manage_title"))
        root.addWidget(self._title)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(COMPANIES_DLG_SPLITTER_HANDLE_W)

        splitter.addWidget(self._build_table_panel())
        splitter.addWidget(self._build_form_panel())
        splitter.setSizes([COMPANIES_DLG_SPLITTER_L, COMPANIES_DLG_SPLITTER_R])
        root.addWidget(splitter)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self._close_btn = QPushButton(tr("shared_close_btn"))
        self._close_btn.setFixedHeight(COMPANIES_DLG_CLOSE_BTN_H)
        self._close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self._close_btn)
        root.addLayout(btn_row)

    def _build_table_panel(self) -> QWidget:
        panel = QWidget()
        self._table_panel = panel
        lay   = QVBoxLayout(panel)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(COMPANIES_DLG_TABLE_PANEL_SPACING)

        toolbar = QHBoxLayout()
        self._table_lbl = QLabel(tr("companies_registered"))
        toolbar.addWidget(self._table_lbl)
        toolbar.addStretch()

        self._add_btn = QPushButton(tr("company_add_btn"))
        self._add_btn.setFixedHeight(COMPANIES_DLG_ADD_BTN_H)
        self._add_btn.clicked.connect(self._new_company)
        toolbar.addWidget(self._add_btn)
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
        self._table.setColumnWidth(3, COMPANIES_DLG_TABLE_COL3_W)
        lay.addWidget(self._table)
        return panel

    def _build_form_panel(self) -> QWidget:
        panel = QWidget()
        self._form_panel = panel
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(*COMPANIES_DLG_FORM_MARGIN)
        lay.setSpacing(COMPANIES_DLG_FORM_SPACING)

        self._form_title = QLabel(tr("company_new_title"))
        lay.addWidget(self._form_title)

        self._sep = ThemedFrame()
        self._sep.setFrameShape(ThemedFrame.HLine)
        self._sep.setFixedHeight(SEPARATOR_LINE_H)
        lay.addWidget(self._sep)

        self._name_lbl = QLabel(tr("company_name_label"))
        lay.addWidget(self._name_lbl)
        self._inp_name = ThemedLineEdit()
        self._inp_name.setPlaceholderText(tr("company_name_placeholder"))
        self._inp_name.setFixedHeight(COMPANIES_DLG_INP_H)
        lay.addWidget(self._inp_name)

        self._short_lbl = QLabel(tr("company_short_name_label"))
        lay.addWidget(self._short_lbl)
        self._inp_short = ThemedLineEdit()
        self._inp_short.setPlaceholderText(tr("company_short_placeholder"))
        self._inp_short.setFixedHeight(COMPANIES_DLG_INP_H)
        lay.addWidget(self._inp_short)

        self._color_lbl = QLabel(tr("company_color_label"))
        lay.addWidget(self._color_lbl)
        color_row = QHBoxLayout()
        self._color_preview = QLabel()
        self._color_preview.setFixedSize(COMPANIES_DLG_COLOR_PREVIEW_SIZE, COMPANIES_DLG_COLOR_PREVIEW_SIZE)
        self._color_btn = QPushButton(tr("company_choose_color"))
        self._color_btn.setFixedHeight(COMPANIES_DLG_COLOR_BTN_H)
        self._color_btn.clicked.connect(self._pick_color)
        color_row.addWidget(self._color_preview)
        color_row.addWidget(self._color_btn)
        color_row.addStretch()
        lay.addLayout(color_row)

        self._notes_lbl = QLabel(tr("company_notes_label"))
        lay.addWidget(self._notes_lbl)
        self._inp_notes = ThemedTextEdit()
        self._inp_notes.setMaximumHeight(COMPANIES_DLG_NOTES_MAX_H)
        lay.addWidget(self._inp_notes)

        lay.addStretch()

        form_btns = QHBoxLayout()
        self._save_btn = QPushButton(tr("btn_save"))
        self._save_btn.setFixedHeight(COMPANIES_DLG_SAVE_BTN_H)
        self._save_btn.clicked.connect(self._save)
        form_btns.addWidget(self._save_btn)

        self._cancel_btn = QPushButton(tr("btn_cancel"))
        self._cancel_btn.setFixedHeight(COMPANIES_DLG_CANCEL_BTN_H)
        self._cancel_btn.clicked.connect(self._reset_form)
        form_btns.addWidget(self._cancel_btn)
        lay.addLayout(form_btns)

        return panel

    def _refresh_style(self, *_):
        from ui.theme import _C

        self._title.setStyleSheet(f"""
            font-size: {FS_XL}px; font-weight: bold;
            color: {_C['accent']}; padding: {COMPANIES_DLG_TITLE_PAD_V}px 0;
            background: transparent;
        """)
        self._close_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};
                border-radius: {COMPANIES_DLG_CLOSE_BTN_RADIUS}px; padding: {COMPANIES_DLG_TITLE_PAD_V}px {COMPANIES_DLG_CLOSE_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)

        # ── table panel ──────────────────────────────────
        self._table_panel.setStyleSheet("background: transparent;")
        self._table_lbl.setStyleSheet(f"font-weight: bold; font-size: {FS_MD}px; background: transparent;")
        self._add_btn.setStyleSheet(self._btn_style(_C['success'], _C['success_hover']))
        self._table.setStyleSheet(f"""
            QTableWidget {{
                border: {COMPANIES_DLG_BORDER_W}px solid {_C['border']};
                border-radius: {COMPANIES_DLG_TABLE_RADIUS}px;
                background: {_C['bg_input']};
                alternate-background-color: {_C['bg_surface']};
                gridline-color: {_C['border']};
            }}
            QTableWidget::item {{
                padding: {COMPANIES_DLG_TABLE_ITEM_PAD_V}px {COMPANIES_DLG_TABLE_ITEM_PAD_H}px;
                border: none;
                border-bottom: {COMPANIES_DLG_BORDER_W}px solid {_C['border']};
                background: transparent;
            }}
            QTableWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent_text']};
            }}
            QHeaderView::section {{
                background: {_C['bg_surface_2']};
                padding: {COMPANIES_DLG_HDR_PAD_V}px {COMPANIES_DLG_HDR_PAD_H}px; border: none;
                border-bottom: {COMPANIES_DLG_HDR_BORDER_W}px solid {_C['border_med']};
                font-weight: 600; color: {_C['text_muted']};
            }}
        """)

        # ── form panel ───────────────────────────────────
        self._form_panel.setStyleSheet(f"""
            QWidget {{
                background: {_C['bg_surface']};
                border: {COMPANIES_DLG_BORDER_W}px solid {_C['border']};
                border-radius: {COMPANIES_DLG_FORM_RADIUS}px;
            }}
        """)
        self._form_title.setStyleSheet(
            f"font-weight: bold; font-size: {FS_MD}px; background: transparent;"
        )
        self._sep.setStyleSheet(f"background: {_C['border']}; border: none;")

        _lbl_ss = f"font-size: {FS_SM}px; color: {_C['text_sec']}; background: transparent;"
        self._name_lbl.setStyleSheet(_lbl_ss)
        self._short_lbl.setStyleSheet(_lbl_ss)
        self._color_lbl.setStyleSheet(_lbl_ss)
        self._notes_lbl.setStyleSheet(_lbl_ss)

        _inp_ss = f"""
            QLineEdit {{
                border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};
                border-radius: {COMPANIES_DLG_INP_RADIUS}px; padding: {COMPANIES_DLG_INP_PAD_V}px {COMPANIES_DLG_INP_PAD_H}px;
                background: {_C['bg_input']};
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; }}
        """
        self._inp_name.setStyleSheet(_inp_ss)
        self._inp_short.setStyleSheet(_inp_ss)

        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: {COMPANIES_DLG_COLOR_PREVIEW_RADIUS}px;"
            f"border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};"
        )
        self._color_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};
                border-radius: {COMPANIES_DLG_INP_RADIUS}px; padding: {COMPANIES_DLG_INP_PAD_V}px {COMPANIES_DLG_COLOR_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)

        self._inp_notes.setStyleSheet(f"""
            QTextEdit {{
                border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};
                border-radius: {COMPANIES_DLG_NOTES_RADIUS}px; padding: {COMPANIES_DLG_NOTES_PAD}px;
                background: {_C['bg_input']}; font-size: {FS_BASE}px;
            }}
            QTextEdit:focus {{ border-color: {_C['accent']}; }}
        """)

        self._save_btn.setStyleSheet(
            self._btn_style(_C['accent'], _C['accent_hover'])
        )
        self._cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};
                border-radius: {COMPANIES_DLG_CANCEL_BTN_RADIUS}px; padding: {COMPANIES_DLG_INP_PAD_V}px {COMPANIES_DLG_CANCEL_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
        """)

        # إعادة تلوين معاينة اللون الحالية بعد أي تغيير ثيم
        # (يُعاد رسم صفوف الجدول أيضاً لأن أزرارها تعتمد على _C)
        if hasattr(self, "_table") and self._table.rowCount():
            self._load()

    def _refresh_lang(self, *_):
        self.setWindowTitle(tr("companies_manage_title"))
        self._title.setText(tr("companies_manage_title"))
        self._close_btn.setText(tr("shared_close_btn"))

        self._table_lbl.setText(tr("companies_registered"))
        self._add_btn.setText(tr("company_add_btn"))
        self._table.setHorizontalHeaderLabels([
            tr("company_col_name"), tr("company_col_short"),
            tr("company_col_status"), tr("company_col_actions"),
        ])

        if self._editing_id:
            row = self._svc.get_company(self._editing_id)
            if row:
                self._form_title.setText(tr("company_edit_title").format(name=row.name))
        else:
            self._form_title.setText(tr("company_new_title"))

        self._name_lbl.setText(tr("company_name_label"))
        self._inp_name.setPlaceholderText(tr("company_name_placeholder"))
        self._short_lbl.setText(tr("company_short_name_label"))
        self._inp_short.setPlaceholderText(tr("company_short_placeholder"))
        self._color_lbl.setText(tr("company_color_label"))
        self._color_btn.setText(tr("company_choose_color"))
        self._notes_lbl.setText(tr("company_notes_label"))
        self._save_btn.setText(tr("btn_save"))
        self._cancel_btn.setText(tr("btn_cancel"))

        if self._table.rowCount():
            self._load()

    def _btn_style(self, bg, hover):
        return f"""
            QPushButton {{
                background: {bg}; color: {_C['bg_input']}; font-weight: 600;
                border: none; border-radius: {COMPANIES_DLG_BTN_RADIUS}px; padding: {COMPANIES_DLG_INP_PAD_V}px {COMPANIES_DLG_BTN_PAD_H}px;
            }}
            QPushButton:hover {{ background: {hover}; }}
        """

    def _load(self):
        rows = self._svc.list_companies()
        self._table.setRowCount(0)
        for r in rows:
            ri = self._table.rowCount()
            self._table.insertRow(ri)

            name_lbl = QLabel(f"  {r.name}")
            name_lbl.setStyleSheet(f"""
                background: {r.color or _C['accent']};
                color: {_C['bg_input']}; font-weight: 600;
                border-radius: {COMPANIES_DLG_NAME_BADGE_RADIUS}px; padding: {COMPANIES_DLG_NAME_BADGE_PAD_V}px {COMPANIES_DLG_NAME_BADGE_PAD_H}px;
            """)
            self._table.setCellWidget(ri, 0, name_lbl)

            short = QTableWidgetItem(r.short_name or tr("dash"))
            short.setTextAlignment(Qt.AlignCenter)
            self._table.setItem(ri, 1, short)

            status_text = tr("company_status_active") if r.is_active else tr("company_status_paused")
            status = QTableWidgetItem(status_text)
            status.setTextAlignment(Qt.AlignCenter)
            status.setForeground(
                QColor(_C["success"]) if r.is_active else QColor(_C["text_muted"])
            )
            self._table.setItem(ri, 2, status)

            btns_widget = QWidget()
            btns_widget.setStyleSheet("background: transparent; border: none;")
            btns_lay = QHBoxLayout(btns_widget)
            btns_lay.setContentsMargins(COMPANIES_DLG_BTNS_CELL_MARGIN_H, COMPANIES_DLG_BTNS_CELL_MARGIN_V,
                                         COMPANIES_DLG_BTNS_CELL_MARGIN_H, COMPANIES_DLG_BTNS_CELL_MARGIN_V)
            btns_lay.setSpacing(COMPANIES_DLG_BTNS_CELL_SPACING)
            btns_lay.setAlignment(Qt.AlignCenter)

            _btn_ss = lambda bg, hov: f"""
                QPushButton {{
                    background: {bg}; border: none;
                    border-radius: {COMPANIES_DLG_ACTION_BTN_RADIUS}px; font-size: {FS_LG}px;
                    min-width: {COMPANIES_DLG_ACTION_BTN_SIZE}px; min-height: {COMPANIES_DLG_ACTION_BTN_SIZE}px;
                    max-width: {COMPANIES_DLG_ACTION_BTN_SIZE}px; max-height: {COMPANIES_DLG_ACTION_BTN_SIZE}px;
                }}
                QPushButton:hover {{ background: {hov}; }}
            """

            edit_btn = QPushButton(tr("company_edit_icon"))
            edit_btn.setToolTip(tr("company_tooltip_edit"))
            edit_btn.setStyleSheet(_btn_ss(_C["t_account_dr_bg"], _C["accent_mid"]))
            edit_btn.clicked.connect(
                lambda _, rid=r.id: self._edit_company(rid)
            )

            toggle_btn = QPushButton(tr("company_toggle_pause") if r.is_active else tr("company_toggle_play"))
            toggle_btn.setToolTip(tr("company_tooltip_toggle"))
            toggle_btn.setStyleSheet(_btn_ss(_C["warning_bg"], _C["warning_border"]))
            toggle_btn.clicked.connect(
                lambda _, rid=r.id: self._toggle(rid)
            )

            del_btn = QPushButton(tr("company_delete_icon"))
            del_btn.setToolTip(tr("company_tooltip_delete"))
            del_btn.setStyleSheet(_btn_ss(_C["danger_bg"], _C["danger_hover"]))
            del_btn.clicked.connect(
                lambda _, rid=r.id, nm=r.name: self._delete(rid, nm)
            )

            btns_lay.addWidget(edit_btn)
            btns_lay.addWidget(toggle_btn)
            btns_lay.addWidget(del_btn)
            self._table.setCellWidget(ri, 3, btns_widget)
            self._table.setRowHeight(ri, COMPANIES_DLG_ROW_H)

    def _new_company(self):
        self._editing_id = None
        self._form_title.setText(tr("company_new_title"))
        self._inp_name.clear()
        self._inp_short.clear()
        self._inp_notes.clear()
        self._color = _C["accent"]
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: {COMPANIES_DLG_COLOR_PREVIEW_RADIUS}px;"
            f"border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};"
        )
        self._inp_name.setFocus()

    def _edit_company(self, company_id: int):
        row = self._svc.get_company(company_id)
        if not row:
            return
        self._editing_id = company_id
        self._form_title.setText(tr("company_edit_title").format(name=row.name))
        self._inp_name.setText(row.name)
        self._inp_short.setText(row.short_name or "")
        self._inp_notes.setPlainText(row.notes or "")
        self._color = row.color or _C["accent"]
        self._color_preview.setStyleSheet(
            f"background: {self._color}; border-radius: {COMPANIES_DLG_COLOR_PREVIEW_RADIUS}px;"
            f"border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};"
        )

    def _pick_color(self):
        c = QColorDialog.getColor(QColor(self._color), self, tr("company_pick_color_title"))
        if c.isValid():
            self._color = c.name()
            self._color_preview.setStyleSheet(
                f"background: {self._color}; border-radius: {COMPANIES_DLG_COLOR_PREVIEW_RADIUS}px;"
                f"border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};"
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
                self._svc.update_company(
                    self._editing_id,
                    name=name, short_name=short,
                    color=self._color, notes=notes
                )
                msg_info(self, tr("done"), tr("company_updated_msg").format(name=name))
            else:
                self._svc.add_company(
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
            f"background: {self._color}; border-radius: {COMPANIES_DLG_COLOR_PREVIEW_RADIUS}px;"
            f"border: {COMPANIES_DLG_BORDER_W}px solid {_C['border_med']};"
        )

    def _toggle(self, company_id: int):
        self._svc.toggle_active(company_id)
        self._load()

    def _delete(self, company_id: int, name: str):
        if msg_question(
            self, tr("confirm_delete"),
            tr("company_delete_confirm").format(name=name)
        ):
            try:
                self._svc.delete_company(company_id)
                self._load()
            except Exception as e:
                msg_critical(self, tr("error"), str(e))
