from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from ..models import CartItem, RecentlyViewedProduct, User, WishlistItem

BACKEND_ROOT = Path(__file__).resolve().parents[2]
USERS_FILE = BACKEND_ROOT / "data" / "users.json"


def _fallback_users() -> dict[str, Any]:
    if not USERS_FILE.exists():
        return {}
    try:
        return json.loads(USERS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def get_user_profile(db: Session | None, user_id: int | str | None) -> dict[str, Any]:
    if db is not None and user_id is not None:
        try:
            numeric_id = int(str(user_id).replace("user_", ""))
            user = db.query(User).filter(User.id == numeric_id).first()
            if user:
                wishlist = db.query(WishlistItem.product_id).filter(WishlistItem.user_id == user.id).limit(20).all()
                viewed = db.query(RecentlyViewedProduct.product_id).filter(RecentlyViewedProduct.user_id == user.id).limit(20).all()
                cart = db.query(CartItem.product_id).filter(CartItem.user_id == user.id).limit(20).all()
                return {
                    "id": user.id,
                    "name": user.name,
                    "role": user.role,
                    "city": user.city,
                    "state": user.state,
                    "wishlist": [f"CTM{row[0]}" for row in wishlist],
                    "recently_viewed": [f"CTM{row[0]}" for row in viewed],
                    "cart": [f"CTM{row[0]}" for row in cart],
                }
        except Exception:
            pass
    return _fallback_users().get(str(user_id or "user_001"), {})


def format_personalization_context(profile: dict[str, Any]) -> str:
    if not profile:
        return ""
    parts = []
    if profile.get("name"):
        parts.append(f"Name: {profile['name']}")
    if profile.get("preferred_categories"):
        parts.append(f"Preferred categories: {', '.join(profile['preferred_categories'])}")
    if profile.get("budget_range"):
        parts.append(f"Budget range: {profile['budget_range']}")
    if profile.get("sizes"):
        sizes = ", ".join(f"{key}: {value}" for key, value in profile["sizes"].items())
        parts.append(f"Sizes: {sizes}")
    for key in ["wishlist", "recently_viewed", "cart"]:
        if profile.get(key):
            parts.append(f"{key.replace('_', ' ').title()}: {', '.join(profile[key])}")
    return "\n".join(parts)
