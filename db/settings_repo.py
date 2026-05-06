"""
db/settings_repo.py
===================
قراءة/كتابة جدول settings فقط.
"""


def get_setting(conn, key: str, default: float = 0.0) -> float:
    row = conn.execute(
        "SELECT value FROM settings WHERE key=?", (key,)
    ).fetchone()
    return row["value"] if row else default


def set_setting(conn, key: str, value: float):
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()
