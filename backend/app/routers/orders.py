from uuid import uuid4

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

try:
    import razorpay
except ImportError:  # pragma: no cover - deployment dependency guard
    razorpay = None

from ..core.config import settings
from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import CartItem, Complaint, Order, OrderItem, PaymentTransaction, Product, User
from ..schemas import AddressIn, CheckoutIn, ComplaintIn, RazorpayCheckoutCreateIn, RazorpayCheckoutVerifyIn, RazorpayOrderOut
from ..services.commerce import cart_summary, get_cart_items, get_or_create_active_cart, make_order_number, order_to_dict

router = APIRouter(prefix="/api/orders", tags=["orders"])
legacy_router = APIRouter(prefix="/api/razorpay", tags=["razorpay"])


def razorpay_client():
    if razorpay is None:
        raise HTTPException(status_code=500, detail="Razorpay dependency is not installed")
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise HTTPException(status_code=500, detail="Razorpay is not configured on the backend")
    return razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))




def checkout_payload_from_optional_body(payload: RazorpayCheckoutCreateIn | None, user: User) -> RazorpayCheckoutCreateIn:
    if payload:
        return payload
    return RazorpayCheckoutCreateIn(
        address=AddressIn(
            label="Home",
            customer_name=user.name or "Customer",
            phone=user.phone or "9999999999",
            address_line=user.address_line or "Address not provided",
            city=user.city or "City",
            state=user.state or "State",
            pincode=user.pincode or "000000",
        )
    )


def ensure_checkout_cart(cart_items: list[CartItem]) -> None:
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    for item in cart_items:
        if item.product.stock < item.quantity:
            raise HTTPException(status_code=400, detail=f"Only {item.product.stock} left for {item.product.title}")


def create_paid_order_from_cart(db: Session, user: User, payload: RazorpayCheckoutVerifyIn) -> Order:
    existing_order = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.payment_reference == payload.razorpay_payment_id)
        .first()
    )
    if existing_order:
        return existing_order

    active_cart = get_or_create_active_cart(db, user.id)
    cart_items = get_cart_items(db, user.id, active_cart.id)
    ensure_checkout_cart(cart_items)
    summary = cart_summary(cart_items)
    address = payload.address

    order = Order(
        order_number=make_order_number(),
        user_id=user.id,
        customer_name=address.customer_name,
        phone=address.phone,
        address_line=address.address_line,
        city=address.city,
        state=address.state,
        pincode=address.pincode,
        total_amount=summary["total"],
        payment_method="RAZORPAY",
        payment_status="PAID",
        payment_reference=payload.razorpay_payment_id,
        razorpay_order_id=payload.razorpay_order_id,
        status="PLACED",
        tracking_status="Order placed",
        refund_status="NONE",
    )

    for cart_item in cart_items:
        product = cart_item.product
        product.stock = max(0, product.stock - cart_item.quantity)
        order.items.append(
            OrderItem(
                product_id=product.id,
                title=product.title,
                price=product.price,
                quantity=cart_item.quantity,
                seller_id=product.seller_id,
                status="PLACED",
                tracking_status="Placed",
            )
        )

    db.add(order)
    db.flush()
    db.add(
        PaymentTransaction(
            order_id=order.id,
            user_id=user.id,
            provider="RAZORPAY",
            amount=summary["total"],
            status="PAID",
            reference=payload.razorpay_payment_id,
            refund_status="NONE",
        )
    )
    db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.cart_id == active_cart.id).delete()
    db.commit()
    db.refresh(order)
    return order


@router.get("")
def list_orders(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    orders = (
        db.query(Order)
        .options(selectinload(Order.items))
        .filter(Order.user_id == user.id)
        .order_by(Order.id.desc())
        .all()
    )
    return {"items": [order_to_dict(order) for order in orders]}


@router.get("/{order_id}")
def order_detail(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).options(selectinload(Order.items)).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order_to_dict(order)


@router.post("/razorpay/create", response_model=RazorpayOrderOut)
def create_razorpay_order(payload: RazorpayCheckoutCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_items = get_cart_items(db, user.id)
    ensure_checkout_cart(cart_items)
    summary = cart_summary(cart_items)
    amount = int(round(summary["total"] * 100))
    if amount <= 0:
        raise HTTPException(status_code=400, detail="Order amount must be greater than zero")

    client = razorpay_client()
    receipt = f"rcpt_{uuid4().hex[:24]}"
    try:
        razorpay_order = client.order.create(
            {
                "amount": amount,
                "currency": "INR",
                "receipt": receipt,
                "payment_capture": 1,
                "notes": {
                    "user_id": str(user.id),
                    "customer": payload.address.customer_name,
                },
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Could not create Razorpay order") from exc

    return {
        "razorpay_order_id": razorpay_order["id"],
        "amount": int(razorpay_order.get("amount", amount)),
        "currency": razorpay_order.get("currency", "INR"),
        "key_id": settings.razorpay_key_id,
    }




@router.post("/razorpay/create-order", response_model=RazorpayOrderOut)
def create_razorpay_order_legacy(payload: RazorpayCheckoutCreateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_razorpay_order(payload, user, db)


@router.post("/razorpay/verify")
def verify_razorpay_payment(payload: RazorpayCheckoutVerifyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    client = razorpay_client()
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": payload.razorpay_order_id,
                "razorpay_payment_id": payload.razorpay_payment_id,
                "razorpay_signature": payload.razorpay_signature,
            }
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Razorpay payment verification failed") from exc

    order = create_paid_order_from_cart(db, user, payload)
    return order_to_dict(order)


@router.post("/checkout")
def checkout(payload: CheckoutIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Use Razorpay checkout: create /api/orders/razorpay/create, then verify /api/orders/razorpay/verify",
    )


@router.post("/{order_id}/reorder")
def reorder(order_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).options(selectinload(Order.items)).filter(Order.id == order_id, Order.user_id == user.id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    active_cart = get_or_create_active_cart(db, user.id)
    added = 0
    for item in order.items:
        product = db.get(Product, item.product_id)
        if not product or product.stock <= 0:
            continue
        existing = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.cart_id == active_cart.id, CartItem.product_id == product.id).first()
        if existing:
            existing.quantity = min(10, existing.quantity + item.quantity)
        else:
            db.add(CartItem(user_id=user.id, cart_id=active_cart.id, product_id=product.id, quantity=min(10, item.quantity)))
        added += 1
    db.commit()
    return {"status": "added", "items_added": added}


@router.post("/complaints")
def create_complaint(payload: ComplaintIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    complaint = Complaint(user_id=user.id, **payload.model_dump())
    db.add(complaint)
    db.commit()
    db.refresh(complaint)
    return complaint


@legacy_router.post("/create-order", response_model=RazorpayOrderOut)
def legacy_create_razorpay_order(payload: RazorpayCheckoutCreateIn | None = Body(default=None), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return create_razorpay_order(checkout_payload_from_optional_body(payload, user), user, db)


@legacy_router.post("/verify")
def legacy_verify_razorpay_payment(payload: RazorpayCheckoutVerifyIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return verify_razorpay_payment(payload, user, db)
