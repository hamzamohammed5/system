"""
ui/tabs/accounting/investors/_helpers.py
=========================================
دوال مساعدة مشتركة لنظام المستثمرين:
  - دوال جلب الحسابات (_fetch_*)
  - دوال ملء القوائم (_fill_*)
  - دوال تسجيل القيود (_post_*)
  - _spin و _stat_card
"""

from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QDoubleSpinBox, QComboBox,
)

from db.accounting.accounting_repo import fetch_leaf_accounts, insert_entry, add_entry_lines
from db.inventory.investors_repo  import link_investor_to_line


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
# ══════════════════════════════════════════════════════════

def _post_capital_entry(acc_conn, erp_conn, investor_id, investor_name,
                        capital_acc_id, asset_acc_id, amount, date, notes=None):
    desc     = f"رأس مال — {investor_name}  {amount:,.2f} ج"
    entry_id = insert_entry(acc_conn, date, desc, entry_type="manual", notes=notes)
    lines = [
        {"account_id": asset_acc_id,   "debit": amount, "credit": 0,      "description": desc},
        {"account_id": capital_acc_id, "debit": 0,      "credit": amount,  "description": desc},
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
        {"account_id": drawings_acc_id, "debit": amount, "credit": 0,      "description": desc},
        {"account_id": asset_acc_id,    "debit": 0,      "credit": amount,  "description": desc},
    ]
    add_entry_lines(acc_conn, entry_id, lines)
    line_row = acc_conn.execute(
        "SELECT id FROM journal_lines WHERE entry_id=? AND debit>0", (entry_id,)
    ).fetchone()
    line_id = line_row["id"] if line_row else 0
    link_investor_to_line(erp_conn, investor_id, entry_id, line_id,
                          "drawings", amount, notes)
    return entry_id