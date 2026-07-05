"""
services/pricing/offers_service.py
=====================================
طبقة الـ service للعروض — الوسيط الوحيد بين tabs/ وdb/pricing/offers_repo.

القاعدة المعمارية:
    tabs/  →  offers_service  →  offers_repo  →  DB

لا يجوز لـ tabs/ استدعاء offers_repo أو pricing_repo مباشرةً أبداً.
"""

from db.pricing.offers_repo import (
    fetch_all_offers,
    fetch_offer,
    insert_offer,
    update_offer,
    delete_offer,
    fetch_offer_items,
    replace_offer_items,
    calc_offer_summary,
)
from db.pricing.pricing_repo import fetch_pricing
from db.shared.items_repo import fetch_items_by_type
from services.pricing.pricing_service import get_priced_item_ids


def get_all_offers(conn) -> list:
    """يرجع كل العروض المحفوظة."""
    return fetch_all_offers(conn)


def get_offer(conn, offer_id: int):
    """يرجع بيانات عرض واحد أو None."""
    return fetch_offer(conn, offer_id)


def create_offer(conn, name: str, discount: float,
                  notes: str = "", category_id: int = None) -> int:
    """ينشئ عرضاً جديداً ويرجع الـ id الخاص به."""
    return insert_offer(conn, name, discount, notes, category_id)


def modify_offer(conn, offer_id: int, name: str, discount: float,
                  notes: str = "", category_id: int = None):
    """يحدّث بيانات عرض موجود."""
    update_offer(conn, offer_id, name, discount, notes, category_id)


def remove_offer(conn, offer_id: int):
    """يحذف عرضاً بالكامل."""
    delete_offer(conn, offer_id)


def get_offer_items(conn, offer_id: int) -> list:
    """يرجع بنود عرض معيّن."""
    return fetch_offer_items(conn, offer_id)


def save_offer_items(conn, offer_id: int, items: list):
    """يستبدل بنود عرض بقائمة جديدة (item_id, qty)."""
    replace_offer_items(conn, offer_id, items)


def get_offer_summary(conn, offer_id: int) -> dict:
    """يرجع ملخص كامل للعرض (تكلفة/سعر/ربح لكل بند + إجماليات)."""
    return calc_offer_summary(conn, offer_id)


def get_item_price(conn, item_id: int) -> float:
    """يرجع سعر عنصر واحد من جدول pricing، أو 0.0 لو غير مُسعّر."""
    row = fetch_pricing(conn, item_id)
    return row["price"] if row else 0.0


def has_pricing(conn, item_id: int) -> bool:
    """يتحقق إن كان العنصر له سعر في جدول pricing."""
    return fetch_pricing(conn, item_id) is not None


def get_priced_ids(conn) -> set:
    """يرجع set من item_ids التي لها سعر في جدول pricing."""
    return get_priced_item_ids(conn)


def get_offer_candidate_items(conn, item_type: str) -> list:
    """يرجع الأصناف حسب النوع (final / semi) لعرضها في اختيار منتجات العرض."""
    return fetch_items_by_type(conn, item_type)


def get_item_cost(conn, item_id: int) -> float:
    """يرجع تكلفة الإنتاج لعنصر واحد."""
    from models.costing import calc_cost
    return calc_cost(conn, item_id)
