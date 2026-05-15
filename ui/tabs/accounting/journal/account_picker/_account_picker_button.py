"""
ui/tabs/accounting/journal/account_picker/_account_picker_button.py
====================================================================
_AccountPickerButton — زر يفتح _AccountTreePopup ويعرض الحساب المختار.
"""

from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout,
    QPushButton, QLabel, QDialog, QSizePolicy,
)
from PyQt5.QtCore import Qt, QPoint, QTimer

from db.accounting.accounting_repo import fetch_account, get_normal_balance
from ._account_tree_popup import _AccountTreePopup, _TYPE_ORDER


class _AccountPickerButton(QWidget):
    """زر يفتح _AccountTreePopup ويعرض الحساب المختار مع مؤشر DR/CR."""

    def __init__(self, conn, acc_types=None, parent=None):
        super().__init__(parent)
        self.conn            = conn
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

        self.btn = QPushButton("— اختر الحساب —")
        self.btn.setMinimumHeight(30)
        self.btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.btn.setStyleSheet("""
            QPushButton {
                background: white; border: 1px solid #c5cae9;
                border-radius: 4px; padding: 2px 10px;
                text-align: right; font-size: 11px; color: #333;
            }
            QPushButton:hover { border-color: #1565c0; background: #f0f4ff; }
        """)
        self.btn.clicked.connect(self._open_popup)

        self.lbl_nb = QLabel("")
        self.lbl_nb.setFixedWidth(44)
        self.lbl_nb.setAlignment(Qt.AlignCenter)
        self.lbl_nb.setStyleSheet(
            "font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px;"
        )

        lay.addWidget(self.btn, stretch=1)
        lay.addWidget(self.lbl_nb)

    def _open_popup(self):
        popup = _AccountTreePopup(self.conn, self.acc_types, parent=self)
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
                acc = fetch_account(self.conn, acc_id)
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
                "font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px;"
            )
            return
        acc = fetch_account(self.conn, self._account_id)
        if not acc:
            return
        nb = get_normal_balance(acc["type"])
        if nb == "dr":
            self.lbl_nb.setText("DR↑")
            self.lbl_nb.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#1565c0;"
                "background:#e3f2fd; border-radius:3px; padding:2px 4px;"
            )
        else:
            self.lbl_nb.setText("CR↑")
            self.lbl_nb.setStyleSheet(
                "font-size:10px; font-weight:bold; color:#c62828;"
                "background:#fdecea; border-radius:3px; padding:2px 4px;"
            )

    def current_account_id(self):
        return self._account_id

    def current_account_type(self):
        return self._account_type

    def set_account(self, acc_id: int, acc_name: str = None):
        self._account_id = acc_id
        acc = fetch_account(self.conn, acc_id)
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
        self.btn.setText("— اختر الحساب —")
        self.lbl_nb.setText("")
        self.lbl_nb.setStyleSheet(
            "font-size:10px; font-weight:bold; border-radius:3px; padding:2px 4px;"
        )