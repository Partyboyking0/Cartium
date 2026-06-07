from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies.auth import require_role
from ..models import Order, OrderItem, Product, Review, User
from ..schemas import OrderStatusUpdateIn, ReviewResponseIn, SellerProductIn, SellerProductUpdateIn
from ..services.commerce import ensure_category, order_to_dict, product_to_dict, replace_product_children, seller_stats, top_products, tracking_for_status

router = APIRouter(prefix="/api/seller", tags=["seller"])


@router.get("/dashboard")
def dashboard(seller: User = Depends(require_role("seller", "admin")), db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .options(selectinload(Product.category), selectinload(Product.images), selectinload(Product.specs))
        .filter(Product.seller_id == seller.id)
        .order_by(Product.id.desc())
        .all()
    )
    orders = (
        db.query(Order)
        .options(selectinload(Order.items))
        .join(OrderItem, OrderItem.order_id == Order.id)
        .filter(OrderItem.seller_id == seller.id)
        .order_by(Order.id.desc())
        .all()
    )
    reviews = (
        db.query(Review)
        .join(Product, Product.id == Review.product_id)
        .filter(Product.seller_id == seller.id)
        .order_by(Review.id.desc())
        .limit(20)
        .all()
    )
    return {
        "seller": seller,
        "products": [product_to_dict(product) for product in products],
        "orders": [order_to_dict(order) for order in orders],
        "reviews": [
            {
                "id": review.id,
                "product_id": review.product_id,
                "rating": review.rating,
                "comment": review.comment,
                "verified_purchase": review.verified_purchase,
                "seller_response": review.seller_response or "",
            }
            for review in reviews
        ],
        "stats": seller_stats(db, seller.id),
        "top_products": top_products(db, seller.id),
    }


@router.post("/products")
def create_product(payload: SellerProductIn, seller: User = Depends(require_role("seller", "admin")), db: Session = Depends(get_db)):
    category = ensure_category(db, payload.category_slug)
    product = Product(
        category_id=category.id,
        seller_id=seller.id,
        title=payload.title,
        brand=payload.brand,
        description=payload.description,
        price=payload.price,
        mrp=payload.mrp,
        stock=payload.stock,
        assured=payload.assured,
        low_stock_threshold=payload.low_stock_threshold,
        listing_status="PENDING",
        approval_note="Waiting for admin approval",
    )
    db.add(product)
    db.flush()
    replace_product_children(db, product, payload.images, payload.specs)
    db.commit()
    db.refresh(product)
    return product_to_dict(product)


@router.patch("/products/{product_id}")
def update_product(product_id: int, payload: SellerProductUpdateIn, seller: User = Depends(require_role("seller", "admin")), db: Session = Depends(get_db)):
    product = db.query(Product).options(selectinload(Product.category), selectinload(Product.images), selectinload(Product.specs)).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    data = payload.model_dump(exclude_unset=True)
    if "category_slug" in data and data["category_slug"]:
        product.category_id = ensure_category(db, data.pop("category_slug")).id
    images = data.pop("images", None)
    specs = data.pop("specs", None)
    for field, value in data.items():
        if value is not None:
            setattr(product, field, value)
    product.listing_status = "PENDING"
    product.approval_note = "Updated listing waiting for admin approval"
    replace_product_children(db, product, images, specs)
    db.commit()
    db.refresh(product)
    return product_to_dict(product)


@router.delete("/products/{product_id}")
def delete_product(product_id: int, seller: User = Depends(require_role("seller", "admin")), db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == seller.id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"status": "deleted"}


@router.patch("/orders/items/{item_id}/status")
def update_item_status(item_id: int, payload: OrderStatusUpdateIn, seller: User = Depends(require_role("seller", "admin")), db: Session = Depends(get_db)):
    item = db.query(OrderItem).filter(OrderItem.id == item_id, OrderItem.seller_id == seller.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Order item not found")
    item.status = payload.status
    item.tracking_status = tracking_for_status(payload.status)
    order = db.get(Order, item.order_id)
    if order:
        order.status = payload.status
        order.tracking_status = tracking_for_status(payload.status)
    db.commit()
    return {"status": "updated", "tracking_status": item.tracking_status}


@router.post("/reviews/{review_id}/response")
def respond_to_review(review_id: int, payload: ReviewResponseIn, seller: User = Depends(require_role("seller", "admin")), db: Session = Depends(get_db)):
    review = db.query(Review).join(Product, Product.id == Review.product_id).filter(Review.id == review_id, Product.seller_id == seller.id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    review.seller_response = payload.response
    review.seller_responded_at = datetime.utcnow()
    db.commit()
    return {"status": "responded"}
