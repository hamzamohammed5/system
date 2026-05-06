"""
db/connection.py
================
اتصال قاعدة البيانات فقط — لا schema هنا.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "erp.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.isolation_level = None   # ← autocommit — كل read بيشوف أحدث بيانات
    return conn