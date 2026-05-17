"""
db/settings_repo.py
===================
قراءة/كتابة جدول settings فقط.
"""


def get_setting(conn, key: str, default=None):
    """
    يقرأ قيمة من جدول settings.
    يرجع النص كما هو من DB، أو default لو المفتاح مش موجود.
    """
    row = conn.execute(
        "SELECT value FROM settings WHERE key=?", (key,)
    ).fetchone()
    return row["value"] if row else default


def set_setting(conn, key: str, value):
    conn.execute(
        "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value)
    )
    conn.commit()