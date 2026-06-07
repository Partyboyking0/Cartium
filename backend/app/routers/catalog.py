from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Product
from ..services.catalog_service import catalog_service
from ..services.commerce import product_to_dict

router = APIRouter(tags=["catalog"])


@router.get("/api/products")
def list_products(
    search: str | None = Query(default=None, description="Search products by title, brand, or category"),
    category: str | None = Query(default=None),
    max_price: float | None = Query(default=None, ge=0),
    min_rating: float | None = Query(default=None, ge=0, le=5),
    db: Session = Depends(get_db),
):
    try:
        query = (
            db.query(Product)
            .options(selectinload(Product.category), selectinload(Product.images), selectinload(Product.specs))
            .filter(Product.listing_status == "APPROVED")
        )
        products = query.order_by(Product.id.asc()).all()
        items = [product_to_dict(product) for product in products]
    except SQLAlchemyError:
        items = catalog_service.list_products(search=None)

    if search:
        term = search.lower().strip()
        items = [item for item in items if term in " ".join([item.get("title", ""), item.get("brand", ""), item.get("category", ""), item.get("category_slug", ""), item.get("description", "")]).lower()]
    if category and category != "all":
        items = [item for item in items if item.get("category_slug") == category]
    if max_price is not None:
        items = [item for item in items if float(item.get("price", 0)) <= max_price]
    if min_rating is not None:
        items = [item for item in items if float(item.get("rating", 0)) >= min_rating]
    return {"items": items}


@router.get("/api/products/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    try:
        product = (
            db.query(Product)
            .options(selectinload(Product.category), selectinload(Product.images), selectinload(Product.specs))
            .filter(Product.id == product_id, Product.listing_status == "APPROVED")
            .first()
        )
        if product:
            return product_to_dict(product)
    except SQLAlchemyError:
        pass

    product = catalog_service.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
