"""
ui/tabs/accounting/journal/account_picker/_account_picker_button.py
====================================================================
_AccountPickerButton — زر يفتح _AccountTreePopup ويعرض الحساب المختار.

إصلاح (v3):
  - _open_popup() تمرر conn لـ popup.get_selected_type(conn) صريحاً.
  - لا يعتمد على self._conn المحفوظ في الـ popup.
  - باقي SafeConnMixin شغال صح من v2.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout,
    QPushButton, QLabel, QDialog, QSizePolicy,
)
from PyQt5.QtCore import Qt, QPoint, QTimer

from db.accounting.accounting_repo import fetch_account, get_normal_balance
from ui.widgets.core.conn import SafeConnMixin
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ._account_tree_popup import _AccountTreePopup, _TYPE_ORDER


class _AccountPickerButton(SafeConnMixin, QWidget):
    """زر يفتح _AccountTreePopup ويعرض الحساب المختار مع مؤشر DR/CR."""

    def __init__(self, conn, acc_types=None, parent=None):
        super().__init__(parent)
        self._init_safe_conn(conn, "accounting")
        self.acc_types       = acc_types
        self._account_id     = None
        self._account_name   = None
        self._account_type   = None
        self._on_changed_cb  = None
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)

        self.btn = QPushButton(tr("select_account"))
        self.btn.setMinimumHeight(30)
        self.btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn.setStyleSheet(
            f"QPushButton {{ background: {_C['bg_input']}; border: 1px solid {_C['border_med']};"            "border-radius: 4px; padding: 2px 10px;"            f"text-align: right; font-size: 11px; color: {_C['text_primary']}; }}"            f"QPushButton:hover {{ border-color: {_C['accent']}; background: {_C['journal_header_bg']}; }}"
        )
        self.btn.clicked.connect(self._open_popup)

        self.lbl_nb = QLabel("")
        self.lbl_nb.setFixedWidth(44)
        self.lbl_nb.setAlignment(Qt.AlignCenter)
        self.lbl_nb.setStyleSheet(
            f"font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px; color:{_C["text_disabled"]};"
        )

        lay.addWidget(self.btn, stretch=1)
        lay.addWidget(self.lbl_nb)

    def _open_popup(self):
        # conn حي دائماً من _get_safe_conn()
        conn = self._get_safe_conn()
        popup = _AccountTreePopup(conn, self.acc_types, parent=self)
        pos = self.btn.mapToGlobal(QPoint(0, self.btn.height()))
        popup.move(pos)
        popup.resize(max(self.width() + 60, 440), 460)
        popup._expanded.add("group:equity")
        for t in (self.acc_types or _TYPE_ORDER):
            popup._expanded.add(f"type:{t}")
        popup._render()
        if popup.exec_() == QDialog.Accepted:
            acc_id, acc_name = popup.get_selected()
            if acc_id:
                # [إصلاح v3] نمرر conn صريح لـ get_selected_type
                # بدل الاعتماد على conn محفوظ في الـ popup
                acc = fetch_account(conn, acc_id)
                self._account_id   = acc_id
                self._account_name = acc_name
                self._account_type = acc["type"] if acc else None
                self.btn.setText(acc_name)
                self._update_nb_label()
                QTimer.singleShot(50, self._fire_changed)

    def _fire_changed(self):
        if self._on_changed_cb:
            self._on_changed_cb()

    def set_on_changed(self, cb):
        self._on_changed_cb = cb

    def _update_nb_label(self):
        if not self._account_id:
            self.lbl_nb.setText("")
            self.lbl_nb.setStyleSheet(
                f"font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px; color:{_C["text_disabled"]};"
            )
            return
        acc = fetch_account(self._get_safe_conn(), self._account_id)
        if not acc:
            return
        nb = get_normal_balance(acc["type"])
        if nb == "dr":
            self.lbl_nb.setText("DR↑")
            self.lbl_nb.setStyleSheet(
                f"font-size:10px; font-weight:bold; color:{_C['badge_dr_text']};"                f"background:{_C['badge_dr_bg']}; border-radius:3px; padding:2px 4px;"
            )
        else:
            self.lbl_nb.setText("CR↑")
            self.lbl_nb.setStyleSheet(
                f"font-size:10px; font-weight:bold; color:{_C['badge_cr_text']};"                f"background:{_C['badge_cr_bg']}; border-radius:3px; padding:2px 4px;"
            )

    def current_account_id(self):
        return self._account_id

    def current_account_type(self):
        return self._account_type

    def set_account(self, acc_id: int, acc_name: str = None):
        self._account_id = acc_id
        acc = fetch_account(self._get_safe_conn(), acc_id)
        self._account_type = acc["type"] if acc else None
        if acc_name:
            self._account_name = acc_name
            self.btn.setText(acc_name)
        elif acc:
            self._account_name = f"{acc['code']} — {acc['name']}"
            self.btn.setText(self._account_name)
        self._update_nb_label()

    def reset(self):
        self._account_id   = None
        self._account_name = None
        self._account_type = None
        self.btn.setText(tr("select_account"))
        self.lbl_nb.setText("")
        self.lbl_nb.setStyleSheet(
            f"font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px; color:{_C["text_disabled"]};"
        )