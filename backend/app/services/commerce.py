"""Shared commerce helpers for routers."""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..models import Cart, CartItem, Category, Order, OrderItem, PaymentTransaction, Product, ProductImage, ProductSpec, Review, User


def product_to_dict(product: Product) -> dict:
    category = product.category
    return {
        "id": product.id,
        "title": product.title,
        "brand": product.brand,
        "description": product.description,
        "price": float(product.price),
        "mrp": float(product.mrp),
        "rating": float(product.rating),
        "reviews": int(product.reviews),
        "stock": int(product.stock),
        "assured": bool(product.assured),
        "seller_id": int(product.seller_id or 0),
        "listing_status": product.listing_status,
        "approval_note": product.approval_note,
        "low_stock_threshold": int(product.low_stock_threshold or 5),
        "category": category.name if category else "Misc",
        "category_slug": category.slug if category else "misc",
        "images": [
            {"id": image.id, "url": image.url, "alt": image.alt}
            for image in sorted(product.images, key=lambda item: item.id)
        ],
        "specs": [
            {"id": spec.id, "name": spec.name, "value": spec.value}
            for spec in sorted(product.specs, key=lambda item: item.id)
        ],
    }


def order_to_dict(order: Order) -> dict:
    return {
        "id": order.id,
        "order_number": order.order_number,
        "user_id": order.user_id,
        "customer_name": order.customer_name,
        "phone": order.phone,
        "address_line": order.address_line,
        "city": order.city,
        "state": order.state,
        "pincode": order.pincode,
        "total_amount": float(order.total_amount),
        "payment_method": order.payment_method,
        "payment_status": order.payment_status,
        "payment_reference": order.payment_reference,
        "status": order.status,
        "tracking_status": order.tracking_status,
        "refund_status": order.refund_status,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "items": [
            {
                "id": item.id,
                "product_id": item.product_id,
                "title": item.title,
                "price": float(item.price),
                "quantity": item.quantity,
                "seller_id": item.seller_id,
                "status": item.status,
                "tracking_status": item.tracking_status,
            }
            for item in order.items
        ],
    }


def cart_summary(items: list[CartItem]) -> dict:
    mrp_total = sum(float(item.product.mrp) * item.quantity for item in items)
    subtotal = sum(float(item.product.price) * item.quantity for item in items)
    discount = max(0.0, mrp_total - subtotal)
    delivery_fee = 0.0 if subtotal >= 499 or subtotal == 0 else 49.0
    return {
        "mrp_total": mrp_total,
        "subtotal": subtotal,
        "discount": discount,
        "delivery_fee": delivery_fee,
        "total": subtotal + delivery_fee,
    }


def cart_to_dict(items: list[CartItem]) -> dict:
    return {
        "items": [
            {"id": item.id, "quantity": item.quantity, "product": product_to_dict(item.product)}
            for item in items
        ],
        "summary": cart_summary(items),
    }


def get_or_create_active_cart(db: Session, user_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.user_id == user_id, Cart.is_active.is_(True)).order_by(Cart.id.asc()).first()
    if cart:
        return cart

    cart = db.query(Cart).filter(Cart.user_id == user_id).order_by(Cart.id.asc()).first()
    if cart:
        cart.is_active = True
        db.flush()
        return cart

    cart = Cart(user_id=user_id, name="Main cart", is_active=True)
    db.add(cart)
    db.flush()
    return cart


def get_cart_items(db: Session, user_id: int, cart_id: int | None = None) -> list[CartItem]:
    if cart_id is None:
        cart_id = get_or_create_active_cart(db, user_id).id

    return (
        db.query(CartItem)
        .options(
            selectinload(CartItem.product).selectinload(Product.category),
            selectinload(CartItem.product).selectinload(Product.images),
            selectinload(CartItem.product).selectinload(Product.specs),
        )
        .filter(CartItem.user_id == user_id, CartItem.cart_id == cart_id)
        .order_by(CartItem.id.desc())
        .all()
    )


def make_order_number() -> str:
    return f"OD{datetime.utcnow():%Y%m%d}{uuid4().hex[:8].upper()}"


def payment_status_for(method: str) -> str:
    return "PENDING" if method == "COD" else "PAID"


def tracking_for_status(status: str) -> str:
    return {
        "PLACED": "Placed",
        "PACKED": "Packed",
        "SHIPPED": "Shipped",
        "DELIVERED": "Delivered",
    }.get(status, status.title())


def seller_stats(db: Session, seller_id: int) -> dict:
    product_count = db.query(Product).filter(Product.seller_id == seller_id).count()
    low_stock_count = db.query(Product).filter(Product.seller_id == seller_id, Product.stock <= Product.low_stock_threshold).count()
    pending_products = db.query(Product).filter(Product.seller_id == seller_id, Product.listing_status == "PENDING").count()
    rows = db.query(OrderItem).filter(OrderItem.seller_id == seller_id).all()
    units_sold = sum(item.quantity for item in rows)
    revenue = sum(float(item.price) * item.quantity for item in rows)
    order_count = len({item.order_id for item in rows})
    return {
        "product_count": product_count,
        "units_sold": units_sold,
        "revenue": revenue,
        "order_count": order_count,
        "low_stock_count": low_stock_count,
        "pending_products": pending_products,
    }


def top_products(db: Session, seller_id: int) -> list[dict]:
    rows = db.query(OrderItem).filter(OrderItem.seller_id == seller_id).all()
    grouped: dict[int, dict] = defaultdict(lambda: {"product_id": 0, "title": "", "units_sold": 0, "revenue": 0.0})
    for item in rows:
        entry = grouped[item.product_id]
        entry["product_id"] = item.product_id
        entry["title"] = item.title
        entry["units_sold"] += item.quantity
        entry["revenue"] += float(item.price) * item.quantity
    return sorted(grouped.values(), key=lambda item: item["units_sold"], reverse=True)[:5]


def growth_stats(db: Session) -> dict:
    now = datetime.utcnow()
    last_7 = now - timedelta(days=7)
    previous_7 = now - timedelta(days=14)

    users_last = db.query(User).filter(User.created_at >= last_7).count()
    users_prev = db.query(User).filter(User.created_at >= previous_7, User.created_at < last_7).count()
    orders_last = db.query(Order).filter(Order.created_at >= last_7).count()
    orders_prev = db.query(Order).filter(Order.created_at >= previous_7, Order.created_at < last_7).count()
    revenue_last = float(db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.created_at >= last_7).scalar() or 0)
    revenue_prev = float(db.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.created_at >= previous_7, Order.created_at < last_7).scalar() or 0)

    def pct(current: float, previous: float) -> float:
        if previous == 0:
            return 100.0 if current else 0.0
        return round(((current - previous) / previous) * 100, 2)

    return {
        "users_last_7_days": users_last,
        "orders_last_7_days": orders_last,
        "revenue_last_7_days": revenue_last,
        "users_growth_percent": pct(users_last, users_prev),
        "orders_growth_percent": pct(orders_last, orders_prev),
        "revenue_growth_percent": pct(revenue_last, revenue_prev),
    }


def ensure_category(db: Session, slug: str) -> Category:
    category = db.query(Category).filter(Category.slug == slug).first()
    if category:
        return category
    name = slug.replace("-", " ").title()
    category = Category(name=name, slug=slug)
    db.add(category)
    db.flush()
    return category


def replace_product_children(db: Session, product: Product, images: list[str] | None, specs: list | None) -> None:
    if images is not None:
        product.images.clear()
        for index, url in enumerate(images, start=1):
            product.images.append(ProductImage(url=url, alt=f"{product.title} image {index}"))

    if specs is not None:
        product.specs.clear()
        for spec in specs:
            product.specs.append(ProductSpec(name=spec.name, value=spec.value))
