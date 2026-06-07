from __future__ import annotations

import re
from typing import Any

from sqlalchemy.orm import Session, selectinload

from .intent import classify_intent
from .model_loader import generate_response
from .prompts import build_chat_prompt
from .rag import format_context_for_prompt, retrieve_relevant_context
from ..core.config import settings
from ..models import CartItem, Category, Order, Product, User
from ..services.commerce import cart_summary, get_cart_items, get_or_create_active_cart
from ..services.user_personalization_service import format_personalization_context, get_user_profile


def money(value: float) -> str:
    return f"Rs {float(value):,.0f}"


def extract_product_ids(message: str) -> list[int]:
    ids = [int(match) for match in re.findall(r"CTM\s*(\d+)", message, flags=re.I)]
    if not ids:
        ids = [int(match) for match in re.findall(r"product\s*(\d+)", message, flags=re.I)]
    return ids


def extract_budget(message: str) -> float | None:
    match = re.search(r"(?:under|below|less than|budget)\s*(?:rs|inr)?\s*([0-9][0-9,]*)", message, flags=re.I)
    return float(match.group(1).replace(",", "")) if match else None


def product_line(product: Product) -> str:
    return f"CTM{product.id} - {product.title} by {product.brand}: {money(product.price)}, stock {product.stock}, rating {product.rating}"


def _expanded_keywords(message: str) -> list[str]:
    words = [word for word in re.findall(r"[a-zA-Z0-9]+", message.lower()) if len(word) > 2]
    stop = {"suggest", "show", "find", "recommend", "under", "below", "gift", "need", "products", "product", "cartium", "top", "rated", "best", "new", "buy", "compare", "difference", "between", "versus", "and", "with", "what", "which"}
    keywords = [word for word in words if word not in stop]
    synonyms = {
        "phone": ["phone", "phones", "mobile", "mobiles", "smartphone", "smartphones"],
        "phones": ["phone", "phones", "mobile", "mobiles", "smartphone", "smartphones"],
        "smartphone": ["phone", "phones", "mobile", "mobiles", "smartphone", "smartphones"],
        "smartphones": ["phone", "phones", "mobile", "mobiles", "smartphone", "smartphones"],
        "mobile": ["phone", "phones", "mobile", "mobiles", "smartphone", "smartphones"],
        "mobiles": ["phone", "phones", "mobile", "mobiles", "smartphone", "smartphones"],
        "electronics": ["electronics", "electronic", "headphones", "laptop", "phone", "mobile"],
        "electronic": ["electronics", "electronic", "headphones", "laptop", "phone", "mobile"],
        "headphone": ["headphone", "headphones", "earphone", "audio"],
        "headphones": ["headphone", "headphones", "earphone", "audio"],
        "laptop": ["laptop", "computer", "notebook"],
        "laptops": ["laptop", "computer", "notebook"],
    }
    expanded: list[str] = []
    for word in keywords:
        expanded.extend(synonyms.get(word, [word]))
    return list(dict.fromkeys(expanded))


def _is_no_match(text: str) -> bool:
    return text.startswith("I could not find") or text.startswith("I need at least") or text.startswith("I could not identify")



def search_products(db: Session, message: str, limit: int = 4) -> list[Product]:
    budget = extract_budget(message)
    query = (
        db.query(Product)
        .options(selectinload(Product.category))
        .join(Category, Product.category_id == Category.id)
        .filter(Product.listing_status == "APPROVED")
    )
    if budget is not None:
        query = query.filter(Product.price <= budget)

    products = query.all()
    keywords = _expanded_keywords(message)
    if not keywords:
        return sorted(products, key=lambda item: (-float(item.rating or 0), float(item.price or 0)))[:limit]

    scored: list[tuple[int, Product]] = []
    for product in products:
        category = product.category
        haystack = " ".join([
            product.title or "",
            product.brand or "",
            product.description or "",
            category.name if category else "",
            category.slug if category else "",
        ]).lower()
        haystack_tokens = set(re.findall(r"[a-zA-Z0-9]+", haystack))
        brand_tokens = set(re.findall(r"[a-zA-Z0-9]+", (product.brand or "").lower()))
        title_tokens = set(re.findall(r"[a-zA-Z0-9]+", (product.title or "").lower()))
        score = 0
        for word in keywords:
            if word in haystack_tokens:
                score += 1
            if word in brand_tokens:
                score += 2
            if word in title_tokens:
                score += 2
        if score > 0:
            scored.append((score, product))

    if not scored:
        return []
    scored.sort(key=lambda pair: (-pair[0], -float(pair[1].rating or 0), float(pair[1].price or 0)))
    return [product for _, product in scored[:limit]]


def action_product_search(db: Session, message: str) -> str:
    products = search_products(db, message)
    if not products:
        return "I could not find matching products in Cartium's approved catalog. Try a different category or budget."
    return "Recommended products:\n" + "\n".join(product_line(product) for product in products)


def action_product_comparison(db: Session, message: str) -> str:
    ids = extract_product_ids(message)
    products = db.query(Product).filter(Product.id.in_(ids), Product.listing_status == "APPROVED").all() if ids else []
    if len(products) < 2:
        products = search_products(db, message, limit=2)
    if len(products) < 2:
        return "I need at least two matching Cartium products to compare. Share product codes like CTM101 and CTM102."
    return "Comparison:\n" + "\n".join(product_line(product) for product in products[:4])


def action_stock_check(db: Session, message: str) -> str:
    ids = extract_product_ids(message)
    product = db.query(Product).filter(Product.id == ids[0], Product.listing_status == "APPROVED").first() if ids else None
    if product is None:
        matches = search_products(db, message, limit=1)
        product = matches[0] if matches else None
    if product is None:
        return "I could not identify the product for stock check. Please share the product code, for example CTM101."
    return f"{product_line(product)}. Size-level stock is not available in the current Cartium data."


def action_add_to_cart(db: Session, user: User, message: str) -> str:
    ids = extract_product_ids(message)
    if not ids:
        matches = search_products(db, message, limit=1)
        ids = [matches[0].id] if matches else []
    if not ids:
        return "I could not identify which product to add. Please mention a product code like CTM101."
    product = db.query(Product).filter(Product.id == ids[0], Product.listing_status == "APPROVED").first()
    if not product:
        return "That product is not available in Cartium's approved catalog."
    if product.stock <= 0:
        return f"{product.title} is currently out of stock, so I cannot add it to your cart."
    cart = get_or_create_active_cart(db, user.id)
    item = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.cart_id == cart.id, CartItem.product_id == product.id).first()
    if item:
        item.quantity += 1
    else:
        db.add(CartItem(user_id=user.id, cart_id=cart.id, product_id=product.id, quantity=1))
    db.commit()
    return f"Added {product.title} to your active cart."


def action_remove_from_cart(db: Session, user: User, message: str) -> str:
    ids = extract_product_ids(message)
    if not ids:
        return "Please mention the product code you want removed, for example CTM101."
    cart = get_or_create_active_cart(db, user.id)
    item = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.cart_id == cart.id, CartItem.product_id == ids[0]).first()
    if not item:
        return "That product is not in your active cart."
    db.delete(item)
    db.commit()
    return "Removed the product from your active cart."


def action_view_cart(db: Session, user: User) -> str:
    items = get_cart_items(db, user.id)
    if not items:
        return "Your active cart is empty right now."
    summary = cart_summary(items)
    lines = [f"{item.quantity} x {item.product.title} - {money(float(item.product.price) * item.quantity)}" for item in items]
    lines.append(f"Total: {money(summary['total'])}. Savings vs MRP: {money(summary['discount'])}.")
    return "Your active cart:\n" + "\n".join(lines)


def action_order_status(db: Session, user: User, message: str) -> str:
    order_number_match = re.search(r"OD[0-9A-Z]+", message, flags=re.I)
    query = db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc())
    if order_number_match:
        query = query.filter(Order.order_number == order_number_match.group(0).upper())
    order = query.first()
    if not order:
        return "I could not find an order for your account with the available Cartium data."
    return f"Order {order.order_number} is {order.status}. Tracking status: {order.tracking_status}. Payment status: {order.payment_status}."


def action_payment_help() -> str:
    return (
        "Cartium checkout uses Razorpay for secure UPI, card, wallet, and netbanking payments. "
        "Your order is created only after Razorpay confirms the payment. "
        "Next step: open your active cart and continue to checkout when you are ready."
    )


def run_backend_action(intent: str, db: Session, user: User, message: str) -> str:
    if intent in {"product_search", "personalized_recommendation", "product_details"}:
        return action_product_search(db, message)
    if intent == "product_comparison":
        return action_product_comparison(db, message)
    if intent == "stock_check":
        return action_stock_check(db, message)
    if intent == "add_to_cart":
        return action_add_to_cart(db, user, message)
    if intent == "remove_from_cart":
        return action_remove_from_cart(db, user, message)
    if intent == "view_cart":
        return action_view_cart(db, user)
    if intent == "order_status":
        return action_order_status(db, user, message)
    if intent == "payment_help":
        return action_payment_help()
    return ""


def deterministic_reply(intent: str, action_result: str, context: str, personalization: str) -> str:
    if action_result:
        if intent == "personalized_recommendation" and personalization:
            return f"Based on your Cartium profile:\n{personalization}\n\n{action_result}"
        return action_result
    if context:
        return context.split("\n")[0][:900]
    return "I can help with product search, comparisons, stock checks, cart actions, orders, returns, shipping, and refunds. What would you like to do next?"


def chat_with_assistant(db: Session, user: User, message: str, user_id: str | None = None) -> dict[str, Any]:
    intent = classify_intent(message)
    profile = get_user_profile(db, user.id if user else user_id)
    personalization = format_personalization_context(profile)
    action_result = run_backend_action(intent, db, user, message) if user else ""
    context = ""
    sources: list[dict[str, Any]] = []
    try:
        results = retrieve_relevant_context(message, top_k=settings.max_context_docs)
        context, sources = format_context_for_prompt(results)
    except Exception:
        pass
    prompt = build_chat_prompt(context=context, personalization=personalization, question=message, action_result=action_result)
    grounded_intents = {
        "product_search",
        "product_comparison",
        "product_details",
        "stock_check",
        "add_to_cart",
        "remove_from_cart",
        "view_cart",
        "order_status",
        "personalized_recommendation",
        "payment_help",
    }
    if intent in grounded_intents and action_result and not _is_no_match(action_result):
        reply = deterministic_reply(intent, action_result, context, personalization)
        return {"reply": reply, "intent": intent, "sources": sources}

    try:
        reply = generate_response(prompt) or deterministic_reply(intent, action_result, context, personalization)
    except Exception:
        reply = deterministic_reply(intent, action_result, context, personalization)
    return {"reply": reply, "intent": intent, "sources": sources}
