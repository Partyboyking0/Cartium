from typing import Any

from ..seed import PRODUCTS


class CatalogService:
    """Serve the seeded storefront catalog with images and metadata for the frontend."""

    def __init__(self) -> None:
        self._products = [self._normalize_product(item, index) for index, item in enumerate(PRODUCTS, start=1)]

    @staticmethod
    def _normalize_product(item: dict[str, Any], index: int) -> dict[str, Any]:
        category_name, category_slug = item["category"]
        return {
            "id": index,
            "title": item["title"],
            "brand": item["brand"],
            "description": item["description"],
            "price": float(item["price"]),
            "mrp": float(item["mrp"]),
            "rating": float(item["rating"]),
            "reviews": int(item["reviews"]),
            "stock": int(item["stock"]),
            "assured": True,
            "seller_id": 2,
            "listing_status": "APPROVED",
            "approval_note": "Approved for storefront",
            "low_stock_threshold": 5,
            "category": category_name,
            "category_slug": category_slug,
            "images": [
                {"id": image_index, "url": url, "alt": f"{item['title']} image {image_index}"}
                for image_index, url in enumerate(item.get("images", []), start=1)
            ],
            "specs": [
                {"id": spec_index, "name": name, "value": value}
                for spec_index, (name, value) in enumerate(item.get("specs", {}).items(), start=1)
            ],
        }

    def list_products(self, search: str | None = None) -> list[dict[str, Any]]:
        products = list(self._products)
        if search:
            query = search.lower().strip()
            products = [
                item
                for item in products
                if query in item["title"].lower()
                or query in item["brand"].lower()
                or query in item["category"].lower()
            ]
        return products

    def get_product(self, product_id: int) -> dict[str, Any] | None:
        for item in self._products:
            if item["id"] == product_id:
                return item
        return None


catalog_service = CatalogService()
