from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import Cart, CartItem, Product, User
from ..schemas import CartAdd, CartCreate, CartRename, CartUpdate
from ..services.commerce import cart_to_dict, get_cart_items, get_or_create_active_cart

router = APIRouter(prefix="/api/cart", tags=["cart"])


def cart_payload(db: Session, user_id: int, cart: Cart):
    payload = cart_to_dict(get_cart_items(db, user_id, cart.id))
    payload["cart"] = cart
    return payload


def get_owned_cart(db: Session, user_id: int, cart_id: int) -> Cart:
    cart = db.query(Cart).filter(Cart.id == cart_id, Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")
    return cart


def activate_cart_record(db: Session, user_id: int, cart: Cart) -> Cart:
    db.query(Cart).filter(Cart.user_id == user_id, Cart.id != cart.id).update({"is_active": False})
    cart.is_active = True
    db.flush()
    return cart


@router.get("/carts")
def list_carts(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    active = get_or_create_active_cart(db, user.id)
    db.commit()
    carts = db.query(Cart).filter(Cart.user_id == user.id).order_by(Cart.is_active.desc(), Cart.id.asc()).all()
    return {"items": carts, "active_cart_id": active.id}


@router.post("/carts")
def create_cart(payload: CartCreate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart_count = db.query(Cart).filter(Cart.user_id == user.id).count()
    if cart_count >= 8:
        raise HTTPException(status_code=400, detail="You can keep up to 8 carts")

    cart = Cart(user_id=user.id, name=payload.name.strip(), is_active=True)
    db.add(cart)
    db.flush()
    activate_cart_record(db, user.id, cart)
    db.commit()
    db.refresh(cart)
    return cart


@router.patch("/carts/{cart_id}")
def rename_cart(cart_id: int, payload: CartRename, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_owned_cart(db, user.id, cart_id)
    cart.name = payload.name.strip()
    db.commit()
    db.refresh(cart)
    return cart


@router.patch("/carts/{cart_id}/activate")
def activate_cart(cart_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_owned_cart(db, user.id, cart_id)
    activate_cart_record(db, user.id, cart)
    db.commit()
    db.refresh(cart)
    return cart_payload(db, user.id, cart)


@router.delete("/carts/{cart_id}")
def delete_cart(cart_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_owned_cart(db, user.id, cart_id)
    total_carts = db.query(Cart).filter(Cart.user_id == user.id).count()
    if total_carts <= 1:
        raise HTTPException(status_code=400, detail="You must keep at least one cart")

    was_active = cart.is_active
    db.delete(cart)
    db.flush()
    if was_active:
        replacement = db.query(Cart).filter(Cart.user_id == user.id).order_by(Cart.id.asc()).first()
        if replacement:
            activate_cart_record(db, user.id, replacement)
    db.commit()
    active = get_or_create_active_cart(db, user.id)
    return cart_payload(db, user.id, active)


@router.get("")
def get_cart(cart_id: int | None = Query(default=None), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_owned_cart(db, user.id, cart_id) if cart_id else get_or_create_active_cart(db, user.id)
    db.commit()
    return cart_payload(db, user.id, cart)


@router.post("")
def add_to_cart(payload: CartAdd, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    product = db.get(Product, payload.product_id)
    if not product or product.listing_status != "APPROVED":
        raise HTTPException(status_code=404, detail="Product not found")
    if product.stock <= 0:
        raise HTTPException(status_code=400, detail="Product is out of stock")

    cart = get_owned_cart(db, user.id, payload.cart_id) if payload.cart_id else get_or_create_active_cart(db, user.id)
    item = db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.cart_id == cart.id, CartItem.product_id == product.id).first()
    if item:
        item.quantity = min(item.quantity + payload.quantity, 10)
    else:
        db.add(CartItem(user_id=user.id, cart_id=cart.id, product_id=product.id, quantity=payload.quantity))
    db.commit()
    return cart_payload(db, user.id, cart)


@router.patch("/{item_id}")
def update_cart(item_id: int, payload: CartUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    item.quantity = payload.quantity
    db.commit()
    cart = item.cart or get_or_create_active_cart(db, user.id)
    return cart_payload(db, user.id, cart)


@router.delete("/{item_id}")
def remove_cart_item(item_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.user_id == user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Cart item not found")
    cart = item.cart or get_or_create_active_cart(db, user.id)
    db.delete(item)
    db.commit()
    return cart_payload(db, user.id, cart)


@router.delete("")
def clear_cart(cart_id: int | None = Query(default=None), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cart = get_owned_cart(db, user.id, cart_id) if cart_id else get_or_create_active_cart(db, user.id)
    db.query(CartItem).filter(CartItem.user_id == user.id, CartItem.cart_id == cart.id).delete()
    db.commit()
    return cart_payload(db, user.id, cart)
