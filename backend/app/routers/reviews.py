from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import Order, OrderItem, Product, Review, User
from ..schemas import ReviewIn

router = APIRouter(prefix="/api/reviews", tags=["reviews"])


def review_to_dict(review: Review) -> dict:
    return {
        "id": review.id,
        "user_id": review.user_id,
        "product_id": review.product_id,
        "rating": review.rating,
        "comment": review.comment,
        "verified_purchase": bool(review.verified_purchase),
        "seller_response": review.seller_response or "",
        "seller_responded_at": review.seller_responded_at.isoformat() if review.seller_responded_at else None,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "user": {
            "id": review.user.id,
            "name": review.user.name,
            "email": review.user.email,
            "role": review.user.role,
        } if review.user else None,
    }


@router.get("/product/{product_id}")
def product_reviews(product_id: int, db: Session = Depends(get_db)):
    reviews = (
        db.query(Review)
        .options(selectinload(Review.user))
        .filter(Review.product_id == product_id)
        .order_by(Review.id.desc())
        .all()
    )
    return {"items": [review_to_dict(review) for review in reviews]}


@router.post("")
def add_review(payload: ReviewIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    verified = (
        db.query(OrderItem)
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.user_id == user.id, OrderItem.product_id == product.id, Order.status == "DELIVERED")
        .first()
        is not None
    )
    review = Review(user_id=user.id, product_id=product.id, rating=payload.rating, comment=payload.comment, verified_purchase=verified)
    db.add(review)
    product.reviews += 1
    product.rating = round(((product.rating * max(product.reviews - 1, 1)) + payload.rating) / product.reviews, 2)
    db.commit()
    db.refresh(review)
    return review_to_dict(review)
