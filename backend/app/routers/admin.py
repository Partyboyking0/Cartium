from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies.auth import require_role
from ..models import Complaint, FraudFlag, Order, PaymentTransaction, Product, User
from ..schemas import AdminUserUpdateIn, ComplaintUpdateIn, ProductModerationIn, RefundUpdateIn
from ..services.commerce import growth_stats, order_to_dict, product_to_dict

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/dashboard")
def dashboard(admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.desc()).limit(50).all()
    products = (
        db.query(Product)
        .options(selectinload(Product.category), selectinload(Product.images), selectinload(Product.specs))
        .order_by(Product.id.desc())
        .limit(80)
        .all()
    )
    orders = db.query(Order).options(selectinload(Order.items)).order_by(Order.id.desc()).limit(50).all()
    transactions = db.query(PaymentTransaction).order_by(PaymentTransaction.id.desc()).limit(50).all()
    complaints = db.query(Complaint).options(selectinload(Complaint.user)).order_by(Complaint.id.desc()).limit(50).all()
    fraud_flags = db.query(FraudFlag).order_by(FraudFlag.id.desc()).limit(50).all()

    total_revenue = float(db.query(func.coalesce(func.sum(Order.total_amount), 0)).scalar() or 0)
    stats = {
        "total_users": db.query(User).count(),
        "active_users": db.query(User).filter(User.is_active.is_(True)).count(),
        "total_products": db.query(Product).count(),
        "total_orders": db.query(Order).count(),
        "total_revenue": total_revenue,
        "paid_orders": db.query(Order).filter(Order.payment_status == "PAID").count(),
        "pending_orders": db.query(Order).filter(Order.payment_status == "PENDING").count(),
        "pending_sellers": db.query(User).filter(User.role == "seller", User.seller_status == "PENDING").count(),
        "pending_products": db.query(Product).filter(Product.listing_status == "PENDING").count(),
        "refunded_transactions": db.query(PaymentTransaction).filter(PaymentTransaction.refund_status == "REFUNDED").count(),
    }

    return {
        "stats": stats,
        "growth": growth_stats(db),
        "users": users,
        "products": [product_to_dict(product) for product in products],
        "orders": [order_to_dict(order) for order in orders],
        "transactions": transactions,
        "complaints": complaints,
        "fraud_flags": fraud_flags,
    }


@router.patch("/users/{user_id}")
def update_user(user_id: int, payload: AdminUserUpdateIn, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/products/{product_id}/moderation")
def moderate_product(product_id: int, payload: ProductModerationIn, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.listing_status = payload.listing_status
    product.approval_note = payload.approval_note or ""
    db.commit()
    db.refresh(product)
    return product_to_dict(product)


@router.delete("/products/{product_id}")
def remove_product(product_id: int, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    db.delete(product)
    db.commit()
    return {"status": "removed"}


@router.patch("/transactions/{transaction_id}/refund")
def update_refund(transaction_id: int, payload: RefundUpdateIn, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    transaction = db.get(PaymentTransaction, transaction_id)
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    transaction.refund_status = payload.refund_status
    order = db.get(Order, transaction.order_id)
    if order:
        order.refund_status = payload.refund_status
    db.commit()
    return transaction


@router.patch("/complaints/{complaint_id}")
def update_complaint(complaint_id: int, payload: ComplaintUpdateIn, admin: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    complaint = db.get(Complaint, complaint_id)
    if not complaint:
        raise HTTPException(status_code=404, detail="Complaint not found")
    complaint.status = payload.status
    if payload.resolution_note is not None:
        complaint.resolution_note = payload.resolution_note
    db.commit()
    return complaint
