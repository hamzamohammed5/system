"""
db/accounting_statements_repo.py
=================================
القوائم المالية: ميزان المراجعة، قائمة الدخل، الميزانية، حقوق الملكية.
"""

from db.accounting.accounting_accounts_repo import get_normal_balance


# ══════════════════════════════════════════════════════════
# ميزان المراجعة
# ══════════════════════════════════════════════════════════

def trial_balance(conn) -> list:
    try:
        rows = conn.execute("""
            SELECT a.code, a.name, a.type,
                   COALESCE(SUM(jl.debit),0)  AS total_debit,
                   COALESCE(SUM(jl.credit),0) AS total_credit
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.is_leaf = 1
            GROUP BY a.id
            ORDER BY a.code
        """).fetchall()
        result = []
        for r in rows:
            result.append({
                "code":         r["code"],
                "name":         r["name"],
                "type":         r["type"],
                "total_debit":  r["total_debit"],
                "total_credit": r["total_credit"],
                "balance":      r["total_debit"] - r["total_credit"],
            })
        return result
    except Exception:
        return []


# ══════════════════════════════════════════════════════════
# قائمة الدخل
# ══════════════════════════════════════════════════════════

def income_statement(conn) -> dict:
    try:
        rev_rows = conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.credit)-SUM(jl.debit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = 'revenue' AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """).fetchall()

        exp_rows = conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.debit)-SUM(jl.credit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = 'expense' AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """).fetchall()
    except Exception:
        rev_rows, exp_rows = [], []

    total_rev  = sum(r["amount"] for r in rev_rows)
    total_exp  = sum(r["amount"] for r in exp_rows)
    net_income = total_rev - total_exp

    return {
        "revenues":   [dict(r) for r in rev_rows],
        "expenses":   [dict(r) for r in exp_rows],
        "total_rev":  total_rev,
        "total_exp":  total_exp,
        "net_income": net_income,
    }


# ══════════════════════════════════════════════════════════
# الميزانية العمومية
# ══════════════════════════════════════════════════════════

def balance_sheet(conn) -> dict:
    def _fetch(acc_type):
        try:
            return conn.execute("""
                SELECT a.code, a.name,
                       COALESCE(SUM(jl.debit)-SUM(jl.credit), 0) AS amount
                FROM accounts a
                LEFT JOIN journal_lines jl ON jl.account_id = a.id
                WHERE a.type = ? AND a.is_leaf = 1
                GROUP BY a.id ORDER BY a.code
            """, (acc_type,)).fetchall()
        except Exception:
            return []

    assets   = _fetch("asset")
    liab     = _fetch("liability")
    capital  = _fetch("capital")
    drawings = _fetch("drawings")

    inc        = income_statement(conn)
    net_income = inc["net_income"]

    total_assets  = sum(r["amount"] for r in assets)
    total_liab    = sum(r["amount"] for r in liab)
    total_capital = sum(r["amount"] for r in capital)
    total_draw    = sum(r["amount"] for r in drawings)
    total_equity  = total_capital - total_draw + net_income

    return {
        "assets":        [dict(r) for r in assets],
        "liabilities":   [dict(r) for r in liab],
        "capital":       [dict(r) for r in capital],
        "drawings":      [dict(r) for r in drawings],
        "net_income":    net_income,
        "total_assets":  total_assets,
        "total_liab":    total_liab,
        "total_equity":  total_equity,
    }


# ══════════════════════════════════════════════════════════
# قائمة حقوق الملكية
# ══════════════════════════════════════════════════════════

def owners_equity_statement(conn) -> dict:
    try:
        capital_rows = conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.credit)-SUM(jl.debit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = 'capital' AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """).fetchall()

        drawings_rows = conn.execute("""
            SELECT a.code, a.name,
                   COALESCE(SUM(jl.debit)-SUM(jl.credit), 0) AS amount
            FROM accounts a
            LEFT JOIN journal_lines jl ON jl.account_id = a.id
            WHERE a.type = 'drawings' AND a.is_leaf = 1
            GROUP BY a.id ORDER BY a.code
        """).fetchall()
    except Exception:
        capital_rows, drawings_rows = [], []

    inc           = income_statement(conn)
    net_income    = inc["net_income"]
    total_capital = sum(r["amount"] for r in capital_rows)
    total_draw    = sum(r["amount"] for r in drawings_rows)
    total_equity  = total_capital - total_draw + net_income

    return {
        "capital_accounts":  [dict(r) for r in capital_rows],
        "drawings_accounts": [dict(r) for r in drawings_rows],
        "net_income":        net_income,
        "total_capital":     total_capital,
        "total_drawings":    total_draw,
        "total_equity":      total_equity,
    }