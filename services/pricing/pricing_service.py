"""
services/pricing/pricing_service.py
=====================================
طبقة الـ service للتسعير — الوسيط الوحيد بين tabs/ وdb/pricing/pricing_repo.

القاعدة المعمارية:
    tabs/  →  pricing_service  →  pricing_repo  →  DB

لا يجوز لـ tabs/ استدعاء pricing_repo مباشرةً أبداً.
"""

from db.pricing.pricing_repo import (
    fetch_all_pricing,
    fetch_pricing,
    upsert_pricing,
    delete_pricing,
)
from db.shared.items_repo import fetch_items_by_type, fetch_item


def get_all_pricing(conn, limit: int = 500, offset: int = 0) -> list:
    """يرجع المنتجات النهائية مع بيانات التسعير."""
    return fetch_all_pricing(conn, limit=limit, offset=offset)


def get_pricing(conn, item_id: int):
    """يرجع سعر منتج واحد أو None."""
    return fetch_pricing(conn, item_id)


def save_pricing(conn, item_id: int, margin: float, price: float):
    """يحفظ أو يحدّث سعر منتج."""
    upsert_pricing(conn, item_id, margin, price)


def remove_pricing(conn, item_id: int):
    """يحذف سعر منتج."""
    delete_pricing(conn, item_id)


def get_final_products(conn) -> list:
    """يرجع المنتجات النهائية للـ combo."""
    return fetch_items_by_type(conn, "final")


def get_item(conn, item_id: int):
    """يرجع بيانات صنف واحد."""
    return fetch_item(conn, item_id)


def get_priced_item_ids(conn) -> set:
    """يرجع set من item_ids التي لها سعر في جدول pricing."""
    rows = conn.execute("SELECT item_id FROM pricing").fetchall()
    return {r["item_id"] for r in rows}


def get_products_by_type(conn, item_type: str) -> list:
    """يرجع الأصناف حسب النوع (final / semi)."""
    return fetch_items_by_type(conn, item_type)
