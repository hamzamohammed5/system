"""
ui/tabs/accounting/investors/_helpers.py
=========================================
دوال مساعدة مشتركة لنظام المستثمرين.

[تحديث v3 — إزالة التكرار الكامل]:
  - _spin    → spin_field   من form_utils مباشرة (re-export فقط)
  - _stat_card → stat_card_pair من stat_row مباشرة (re-export فقط)
  - لا يوجد كود مكرر هنا
"""

from PyQt5.QtWidgets import QComboBox

# ── re-export من الـ shared الموحد ──
from ui.widgets.shared.form_utils import spin_field as _spin          # noqa: F401
from ui.widgets.shared.stat_row   import stat_card_pair as _stat_card  # noqa: F401

from db.accounting.accounting_repo import fetch_leaf_accounts, insert_entry, add_entry_lines
from db.accounting.investors_repo  import link_investor_to_line


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
