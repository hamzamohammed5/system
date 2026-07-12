"""
ui/tabs/accounting/investors/_helpers.py
=========================================
دوال مساعدة مشتركة لنظام المستثمرين.

[تحديث v3 — إزالة التكرار الكامل]:
  - _spin    → spin_field   من form_utils مباشرة (re-export فقط)
  - _stat_card → stat_card_pair من stat_row مباشرة (re-export فقط)
  - لا يوجد كود مكرر هنا
"""

from ui.widgets.panels.themed_inputs import ThemedComboBox

from ui.widgets.panels.form_fields import spin_field as _spin          # noqa: F401
from ui.widgets.components.stat_card import stat_card_pair as _stat_card  # noqa: F401

from services.accounting.journal_service import JournalService, JournalLine
from services.accounting.accounts_service import AccountsService
from services.accounting.investors_service import InvestorsService
from ui.widgets.core.i18n import tr


# ══════════════════════════════════════════════════════════
# جلب الحسابات
# ══════════════════════════════════════════════════════════

def _fetch_capital_accounts(acc_conn):
    try:
        return AccountsService(acc_conn).list_leaf_accounts(acc_types=["capital"])
    except Exception:
        return []


def _fetch_drawings_accounts(acc_conn):
    try:
        return AccountsService(acc_conn).list_leaf_accounts(acc_types=["drawings"])
    except Exception:
        return []


def _fetch_asset_accounts(acc_conn):
    try:
        return AccountsService(acc_conn).list_leaf_accounts(acc_types=["asset"])
    except Exception:
        return []


# ══════════════════════════════════════════════════════════
# ملء القوائم
# ══════════════════════════════════════════════════════════

def _fill_asset_combo(cmb: ThemedComboBox, acc_conn, prev_id=None):
    cmb.blockSignals(True)
    cmb.clear()
    for acc in _fetch_asset_accounts(acc_conn):
        sub  = acc["subtype"] if "subtype" in acc.keys() else ""
        icon = tr("asset_icon_bank") if sub == "bank" else (tr("asset_icon_cash") if sub == "cash" else tr("asset_icon_other"))
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


def _fill_capital_combo(cmb: ThemedComboBox, acc_conn, prev_id=None):
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


def _fill_drawings_combo(cmb: ThemedComboBox, acc_conn, prev_id=None):
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
    desc   = tr("capital_entry_desc").format(name=investor_name, amount=f"{amount:,.2f}", currency=tr("currency_abbr"))
    result = JournalService(acc_conn).post_entry(
        entry_data={"date": date, "description": desc, "entry_type": "manual", "notes": notes},
        lines=[
            JournalLine(account_id=asset_acc_id,   dr=amount, cr=0,      note=desc),
            JournalLine(account_id=capital_acc_id, dr=0,      cr=amount, note=desc),
        ],
    )
    entry_id = result.entry_id
    line_id  = JournalService(acc_conn).get_line_id(entry_id, "credit")
    InvestorsService(erp_conn, acc_conn=acc_conn).link_to_line(
        investor_id, entry_id, line_id, "capital", amount, notes)
    return entry_id


def _post_drawings_entry(acc_conn, erp_conn, investor_id, investor_name,
                         drawings_acc_id, asset_acc_id, amount, date, notes=None):
    desc   = tr("drawings_entry_desc").format(name=investor_name, amount=f"{amount:,.2f}", currency=tr("currency_abbr"))
    result = JournalService(acc_conn).post_entry(
        entry_data={"date": date, "description": desc, "entry_type": "manual", "notes": notes},
        lines=[
            JournalLine(account_id=drawings_acc_id, dr=amount, cr=0,      note=desc),
            JournalLine(account_id=asset_acc_id,    dr=0,      cr=amount, note=desc),
        ],
    )
    entry_id = result.entry_id
    line_id  = JournalService(acc_conn).get_line_id(entry_id, "debit")
    InvestorsService(erp_conn, acc_conn=acc_conn).link_to_line(
        investor_id, entry_id, line_id, "drawings", amount, notes)
    return entry_id
