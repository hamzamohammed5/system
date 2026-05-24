"""
ui/tabs/accounting/investors/_helpers.py
=========================================
دوال مساعدة مشتركة لنظام المستثمرين:
  - دوال جلب الحسابات (_fetch_*)
  - دوال ملء القوائم (_fill_*)
  - دوال تسجيل القيود (_post_*)
  - _spin و _stat_card

تغييرات (v2):
  - كل دالة تستقبل conn كـ parameter وتستخدمه مباشرة بدل أي conn محفوظ.
  - المستدعي مسؤول عن تمرير conn حي من _get_safe_conn().
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QHBoxLayout, QDoubleSpinBox, QComboBox,
    QPushButton, QWidget,
    QTableWidget, QMessageBox, QScrollArea
)
from PyQt5.QtGui  import QFont
from PyQt5.QtCore import Qt


from db.accounting.accounting_repo import insert_entry, add_entry_lines
from db.inventory.investors_repo  import link_investor_to_line


from ui.app_settings import _C

from ui.widgets.shared.table_utils import (                                  
    make_list_table as make_table,

)

SCROLL_SS = f"""
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:vertical {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-height: 30px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 6px;
        border-radius: 3px;
    }}
    QScrollBar::handle:horizontal {{
        background: {_C['border_med']};
        border-radius: 3px;
        min-width: 30px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background: {_C['border_strong']};
    }}
    QScrollBar::add-line:horizontal,
    QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
"""

_SCROLL_SS = SCROLL_SS


# ══════════════════════════════════════════════════════════
# مساعدات UI
# ══════════════════════════════════════════════════════════

def _spin(max_=999_999_999, dec=2):
    s = QDoubleSpinBox()
    s.setRange(0, max_)
    s.setDecimals(dec)
    s.setMinimumHeight(30)
    return s


def _stat_card(label: str, color: str = "#1565c0"):
    """يرجع (QFrame, QLabel_value)."""
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background: white;
            border-left: 4px solid {color};
            border-radius: 6px;
        }}
    """)
    lay = QVBoxLayout(f)
    lay.setContentsMargins(12, 8, 12, 8)
    lt = QLabel(label)
    lt.setStyleSheet("font-size:10px; color:#888; background:transparent; border:none;")
    lv = QLabel("0.00  ج")
    lv.setStyleSheet(
        f"font-size:15px; font-weight:bold; color:{color};"
        " background:transparent; border:none;"
    )
    lay.addWidget(lt)
    lay.addWidget(lv)
    return f, lv


# ══════════════════════════════════════════════════════════
# جلب الحسابات
# — كل دالة تستقبل acc_conn صريحاً من المستدعي
# ══════════════════════════════════════════════════════════

def _fetch_capital_accounts(acc_conn):
    try:
        return acc_conn.execute("""
            SELECT id, code, name FROM accounts
            WHERE type='capital' AND is_leaf=1 ORDER BY code
        """).fetchall()
    except Exception:
        return []


def _fetch_drawings_accounts(acc_conn):
    try:
        return acc_conn.execute("""
            SELECT id, code, name FROM accounts
            WHERE type='drawings' AND is_leaf=1 ORDER BY code
        """).fetchall()
    except Exception:
        return []


def _fetch_asset_accounts(acc_conn):
    try:
        return acc_conn.execute("""
            SELECT id, code, name, COALESCE(subtype,'') AS subtype
            FROM accounts WHERE type='asset' AND is_leaf=1 ORDER BY code
        """).fetchall()
    except Exception:
        return []


# ══════════════════════════════════════════════════════════
# ملء القوائم
# — كل دالة تستقبل acc_conn صريحاً من المستدعي
# ══════════════════════════════════════════════════════════

def _fill_asset_combo(cmb: QComboBox, acc_conn, prev_id=None):
    cmb.blockSignals(True)
    cmb.clear()
    for acc in _fetch_asset_accounts(acc_conn):
        sub  = acc["subtype"] if "subtype" in acc.keys() else ""
        icon = "🏦" if sub == "bank" else ("💵" if sub == "cash" else "📦")
        cmb.addItem(f"{icon} {acc['code']} — {acc['name']}", acc["id"])

    restored = False
    if prev_id is not None:
        for i in range(cmb.count()):
            if cmb.itemData(i) == prev_id:
                cmb.setCurrentIndex(i)
                restored = True
                break

    if not restored:
        for i in range(cmb.count()):
            txt = cmb.itemText(i)
            if "111" in txt or "112" in txt or "صندوق" in txt or "بنك" in txt:
                cmb.setCurrentIndex(i)
                break

    cmb.blockSignals(False)


def _fill_capital_combo(cmb: QComboBox, acc_conn, prev_id=None):
    cmb.blockSignals(True)
    cmb.clear()
    for acc in _fetch_capital_accounts(acc_conn):
        cmb.addItem(f"{acc['code']} — {acc['name']}", acc["id"])
    if prev_id is not None:
        for i in range(cmb.count()):
            if cmb.itemData(i) == prev_id:
                cmb.setCurrentIndex(i)
                break
    cmb.blockSignals(False)


def _fill_drawings_combo(cmb: QComboBox, acc_conn, prev_id=None):
    cmb.blockSignals(True)
    cmb.clear()
    for acc in _fetch_drawings_accounts(acc_conn):
        cmb.addItem(f"{acc['code']} — {acc['name']}", acc["id"])
    if prev_id is not None:
        for i in range(cmb.count()):
            if cmb.itemData(i) == prev_id:
                cmb.setCurrentIndex(i)
                break
    cmb.blockSignals(False)


# ══════════════════════════════════════════════════════════
# تسجيل القيود
# — كل دالة تستقبل acc_conn و erp_conn صريحاً من المستدعي
# ══════════════════════════════════════════════════════════

def _post_capital_entry(acc_conn, erp_conn, investor_id, investor_name,
                        capital_acc_id, asset_acc_id, amount, date, notes=None):
    desc     = f"رأس مال — {investor_name}  {amount:,.2f} ج"
    entry_id = insert_entry(acc_conn, date, desc, entry_type="manual", notes=notes)
    lines = [
        {"account_id": asset_acc_id,   "debit": amount, "credit": 0,
         "description": desc},
        {"account_id": capital_acc_id, "debit": 0,      "credit": amount,
         "description": desc},
    ]
    add_entry_lines(acc_conn, entry_id, lines)
    line_row = acc_conn.execute(
        "SELECT id FROM journal_lines WHERE entry_id=? AND credit>0", (entry_id,)
    ).fetchone()
    line_id = line_row["id"] if line_row else 0
    link_investor_to_line(erp_conn, investor_id, entry_id, line_id,
                          "capital", amount, notes)
    return entry_id


def _post_drawings_entry(acc_conn, erp_conn, investor_id, investor_name,
                         drawings_acc_id, asset_acc_id, amount, date, notes=None):
    desc     = f"مسحوبات — {investor_name}  {amount:,.2f} ج"
    entry_id = insert_entry(acc_conn, date, desc, entry_type="manual", notes=notes)
    lines = [
        {"account_id": drawings_acc_id, "debit": amount, "credit": 0,
         "description": desc},
        {"account_id": asset_acc_id,    "debit": 0,      "credit": amount,
         "description": desc},
    ]
    add_entry_lines(acc_conn, entry_id, lines)
    line_row = acc_conn.execute(
        "SELECT id FROM journal_lines WHERE entry_id=? AND debit>0", (entry_id,)
    ).fetchone()
    line_id = line_row["id"] if line_row else 0
    link_investor_to_line(erp_conn, investor_id, entry_id, line_id,
                          "drawings", amount, notes)
    return entry_id


class EditModeMixin:
    def init_edit_mode(self, add_btn, save_btn, cancel_btn, mode_label=None):
        self._em_add_btn    = add_btn
        self._em_save_btn   = save_btn
        self._em_cancel_btn = cancel_btn
        self._em_mode_label = mode_label
        self._editing_id    = None
        save_btn.setVisible(False)
        cancel_btn.setVisible(False)

    def enter_edit_mode(self, record_id: int, label_text: str = ""):
        self._editing_id = record_id
        self._em_add_btn.setVisible(False)
        self._em_save_btn.setVisible(True)
        self._em_cancel_btn.setVisible(True)
        if self._em_mode_label and label_text:
            self._em_mode_label.setText(label_text)

    def exit_edit_mode(self, default_label: str = ""):
        self._editing_id = None
        self._em_add_btn.setVisible(True)
        self._em_save_btn.setVisible(False)
        self._em_cancel_btn.setVisible(False)
        if self._em_mode_label and default_label:
            self._em_mode_label.setText(default_label)

    @property
    def is_editing(self) -> bool:
        return self._editing_id is not None

def buttons_row(*buttons) -> QHBoxLayout:
    row = QHBoxLayout()
    row.setSpacing(6)
    for btn in buttons:
        row.addWidget(btn)
    row.addStretch()
    return row


# ══════════════════════════════════════════════════════════
# live_conn — connection صالح دايماً
# ══════════════════════════════════════════════════════════

def live_conn(stored_conn=None, db: str = "erp"):
    """
    يرجع connection صالح دايماً.

    - لو stored_conn مش None وصالح → يستخدمه كما هو.
    - لو stored_conn None أو مغلق أو فشل → يجيب connection
      جديد من company_state.

    الاستخدام:
        conn = live_conn(self.conn)
        rows = fetch_all_categories(conn, self.scope)
    """
    if stored_conn is not None:
        try:
            stored_conn.execute("SELECT 1")
            return stored_conn
        except Exception:
            pass
    from db.companies.company_state import company_state
    return company_state._get_conn(db)


def make_detail_scroll(min_content_width: int = 520) -> QScrollArea:
    """
    QScrollArea للـ detail panels مع horizontal scroll حقيقي.

    المهم: بعد ما تعمل make_detail_scroll، استخدم set_detail_content()
    لوضع المحتوى جواه — هو بيضبط setMinimumWidth على الـ content
    عشان الـ horizontal scroll يظهر فعلاً لما النافذة تضيق.
    """
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    scroll.setStyleSheet(SCROLL_SS)
    scroll._min_content_width = min_content_width
    return scroll


def set_detail_content(scroll: QScrollArea, content: QWidget,
                       bg: str = "#f8f9fb"):
    """
    يضع الـ content جوا الـ scroll مع ضبط minimum width
    عشان الـ horizontal scroll يظهر لما المحتوى أعرض من الـ panel.
    """
    min_w = getattr(scroll, '_min_content_width', 520)
    content.setStyleSheet(f"background:{bg};")
    content.setMinimumWidth(min_w)
    scroll.setWidget(content)


def bold_label(text: str) -> QLabel:
    lbl = QLabel(text)
    f = QFont()
    f.setBold(True)
    lbl.setFont(f)
    return lbl


def section_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("role", "section")
    f = QFont()
    f.setBold(True)
    lbl.setFont(f)
    lbl.setStyleSheet(f"color: {_C['text_sec']};")
    return lbl


def danger_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{
            color: {_C['danger']};
            background: {_C['danger_bg']};
            border: 1px solid {_C['danger_border']};
            border-radius: 5px;
            padding: 3px 12px;
        }}
        QPushButton:hover {{
            background: #FCDBD9;
            border-color: {_C['danger']};
        }}
    """)
    return btn


def success_button(text: str) -> QPushButton:
    btn = QPushButton(text)
    btn.setStyleSheet(f"""
        QPushButton {{
            background: {_C['success']};
            color: white;
            font-weight: 600;
            border: none;
            border-radius: 5px;
            padding: 4px 16px;
        }}
        QPushButton:hover {{
            background: #236B42;
        }}
    """)
    return btn

def setup_table_columns(
    table: QTableWidget,
    widths: dict = None,
    stretch_col: int = -1,
    min_width: int = 50,
):
    from PyQt5.QtWidgets import QHeaderView
    hh = table.horizontalHeader()
    n  = table.columnCount()
    for i in range(n):
        if i == stretch_col:
            hh.setSectionResizeMode(i, QHeaderView.Stretch)
        else:
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            if widths and i in widths:
                table.setColumnWidth(i, widths[i])
    hh.setMinimumSectionSize(min_width)

def confirm_delete(parent, name: str) -> bool:
    return QMessageBox.question(
        parent, "تأكيد الحذف", f"هل تريد حذف «{name}»؟",
        QMessageBox.Yes | QMessageBox.No
    ) == QMessageBox.Yes