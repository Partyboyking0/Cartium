from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..dependencies.auth import get_current_user
from ..models import RecentlyViewedProduct, SavedPaymentMethod, User, UserAddress, WishlistItem, Product
from ..schemas import AccountUpdateIn, AddressIn, AddressUpdateIn, SavedPaymentMethodIn
from ..services.commerce import product_to_dict

router = APIRouter(prefix="/api/account", tags=["account"])


@router.get("/profile")
def profile(user: User = Depends(get_current_user)):
    return user


@router.patch("/profile")
def update_profile(payload: AccountUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return user


@router.get("/addresses")
def list_addresses(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(UserAddress).filter(UserAddress.user_id == user.id).order_by(UserAddress.is_default.desc(), UserAddress.id.desc()).all()
    return {"items": items}


@router.post("/addresses")
def add_address(payload: AddressIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not db.query(UserAddress).filter(UserAddress.user_id == user.id).first():
        is_default = True
    else:
        is_default = False
    address = UserAddress(user_id=user.id, is_default=is_default, **payload.model_dump())
    db.add(address)
    db.commit()
    db.refresh(address)
    return address


@router.patch("/addresses/{address_id}")
def update_address(address_id: int, payload: AddressUpdateIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.query(UserAddress).filter(UserAddress.id == address_id, UserAddress.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    data = payload.model_dump(exclude_unset=True)
    if data.get("is_default"):
        db.query(UserAddress).filter(UserAddress.user_id == user.id).update({"is_default": False})
    for field, value in data.items():
        if value is not None:
            setattr(address, field, value)
    db.commit()
    db.refresh(address)
    return address


@router.delete("/addresses/{address_id}")
def delete_address(address_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    address = db.query(UserAddress).filter(UserAddress.id == address_id, UserAddress.user_id == user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")
    db.delete(address)
    db.commit()
    return {"status": "deleted"}


@router.get("/payment-methods")
def list_payment_methods(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(SavedPaymentMethod).filter(SavedPaymentMethod.user_id == user.id).order_by(SavedPaymentMethod.is_default.desc(), SavedPaymentMethod.id.desc()).all()
    return {"items": items}


@router.post("/payment-methods")
def add_payment_method(payload: SavedPaymentMethodIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.is_default:
        db.query(SavedPaymentMethod).filter(SavedPaymentMethod.user_id == user.id).update({"is_default": False})
    method = SavedPaymentMethod(user_id=user.id, **payload.model_dump())
    db.add(method)
    db.commit()
    db.refresh(method)
    return method


@router.delete("/payment-methods/{method_id}")
def delete_payment_method(method_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    method = db.query(SavedPaymentMethod).filter(SavedPaymentMethod.id == method_id, SavedPaymentMethod.user_id == user.id).first()
    if not method:
        raise HTTPException(status_code=404, detail="Payment method not found")
    db.delete(method)
    db.commit()
    return {"status": "deleted"}


@router.get("/recently-viewed")
def recently_viewed(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(RecentlyViewedProduct)
        .options(selectinload(RecentlyViewedProduct.product).selectinload(Product.category), selectinload(RecentlyViewedProduct.product).selectinload(Product.images), selectinload(RecentlyViewedProduct.product).selectinload(Product.specs))
        .filter(RecentlyViewedProduct.user_id == user.id)
        .order_by(RecentlyViewedProduct.viewed_at.desc())
        .limit(8)
        .all()
    )
    return {"items": [product_to_dict(row.product) for row in rows if row.product]}


@router.get("/wishlist")
def wishlist(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = (
        db.query(WishlistItem)
        .options(selectinload(WishlistItem.product).selectinload(Product.category), selectinload(WishlistItem.product).selectinload(Product.images), selectinload(WishlistItem.product).selectinload(Product.specs))
        .filter(WishlistItem.user_id == user.id)
        .order_by(WishlistItem.id.desc())
        .all()
    )
    return {"items": [product_to_dict(row.product) for row in rows if row.product]}


@router.post("/wishlist/{product_id}")
def toggle_wishlist(product_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(WishlistItem).filter(WishlistItem.user_id == user.id, WishlistItem.product_id == product_id).first()
    if item:
        db.delete(item)
        db.commit()
        return {"status": "removed"}
    if not db.get(Product, product_id):
        raise HTTPException(status_code=404, detail="Product not found")
    db.add(WishlistItem(user_id=user.id, product_id=product_id))
    db.commit()
    return {"status": "added"}
