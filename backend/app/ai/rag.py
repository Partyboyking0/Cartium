from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session, selectinload

from ..core.config import settings
from ..models import Product
from ..services.catalog_service import catalog_service
from ..services.commerce import product_to_dict

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = BACKEND_ROOT / "data"


class SentenceTransformerEmbeddingFunction:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def __call__(self, input: list[str]) -> list[list[float]]:
        return self.embed_documents(input)

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self.model.encode(input, normalize_embeddings=True).tolist()

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self.embed_documents(input)

    def name(self) -> str:
        return self.model_name


def _embedding_function():
    try:
        return SentenceTransformerEmbeddingFunction(settings.embedding_model_name)
    except Exception:
        return None


def get_chroma_client():
    try:
        import chromadb
    except Exception as exc:
        raise RuntimeError("Install chromadb to use the Cartium AI vector store") from exc
    Path(settings.chroma_db_path).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=settings.chroma_db_path)


def get_or_create_collection():
    client = get_chroma_client()
    embedding_function = _embedding_function()
    if embedding_function is None:
        return client.get_or_create_collection(name=settings.chroma_collection_name)
    return client.get_or_create_collection(name=settings.chroma_collection_name, embedding_function=embedding_function)


def get_products_for_rag(db: Session | None = None) -> list[dict[str, Any]]:
    """Adapter for product ingestion. Uses DB products when a Session is provided; falls back to catalog_service."""
    if db is not None:
        products = (
            db.query(Product)
            .options(selectinload(Product.category), selectinload(Product.images), selectinload(Product.specs))
            .filter(Product.listing_status == "APPROVED")
            .all()
        )
        return [product_to_dict(product) for product in products]
    return catalog_service.list_products()


def _product_document(product: dict[str, Any]) -> str:
    specs = ", ".join(f"{item.get('name')}: {item.get('value')}" for item in product.get("specs", []))
    return (
        f"Product CTM{product['id']}: {product['title']} by {product['brand']}. "
        f"Category: {product.get('category')} ({product.get('category_slug')}). "
        f"Price: Rs {product['price']:,.0f}. MRP: Rs {product['mrp']:,.0f}. "
        f"Stock: {product['stock']}. Rating: {product['rating']}. Reviews: {product.get('reviews', 0)}. "
        f"Description: {product.get('description', '')}. Specs: {specs or 'Not available'}."
    )


def ingest_products_to_chroma(db: Session | None = None) -> int:
    collection = get_or_create_collection()
    products = get_products_for_rag(db)
    if not products:
        return 0
    collection.upsert(
        ids=[f"product-{product['id']}" for product in products],
        documents=[_product_document(product) for product in products],
        metadatas=[{
            "type": "product", "product_id": str(product["id"]), "name": product["title"],
            "category": product.get("category", ""), "brand": product.get("brand", ""),
            "price": float(product.get("price") or 0), "stock": int(product.get("stock") or 0),
            "rating": float(product.get("rating") or 0),
        } for product in products],
    )
    return len(products)


def ingest_faqs_to_chroma() -> int:
    path = DATA_DIR / "faqs.json"
    if not path.exists():
        return 0
    faqs = json.loads(path.read_text(encoding="utf-8"))
    if not faqs:
        return 0
    collection = get_or_create_collection()
    collection.upsert(
        ids=[f"faq-{index}" for index, _ in enumerate(faqs, start=1)],
        documents=[f"Question: {item['question']}\nAnswer: {item['answer']}" for item in faqs],
        metadatas=[{"type": "faq", "question": item["question"]} for item in faqs],
    )
    return len(faqs)


def ingest_policies_to_chroma() -> int:
    path = DATA_DIR / "policies.txt"
    if not path.exists():
        return 0
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return 0
    chunks = [chunk.strip() for chunk in raw.split("\n\n") if chunk.strip()]
    collection = get_or_create_collection()
    collection.upsert(
        ids=[f"policy-{index}" for index, _ in enumerate(chunks, start=1)],
        documents=chunks,
        metadatas=[{"type": "policy", "policy_name": chunk.splitlines()[0][:80]} for chunk in chunks],
    )
    return len(chunks)


def ingest_all_data(db: Session | None = None) -> dict[str, int]:
    return {"products": ingest_products_to_chroma(db), "faqs": ingest_faqs_to_chroma(), "policies": ingest_policies_to_chroma()}


def retrieve_relevant_context(query: str, top_k: int = 5) -> dict[str, Any]:
    collection = get_or_create_collection()
    return collection.query(query_texts=[query], n_results=top_k or settings.max_context_docs)


def format_context_for_prompt(results: dict[str, Any]) -> tuple[str, list[dict[str, Any]]]:
    documents = (results.get("documents") or [[]])[0]
    metadatas = (results.get("metadatas") or [[]])[0]
    distances = (results.get("distances") or [[]])[0]
    lines: list[str] = []
    sources: list[dict[str, Any]] = []
    for index, document in enumerate(documents):
        metadata = metadatas[index] if index < len(metadatas) else {}
        distance = distances[index] if index < len(distances) else None
        lines.append(f"[{index + 1}] {document}")
        sources.append({
            "type": metadata.get("type"),
            "name": metadata.get("name") or metadata.get("question") or metadata.get("policy_name"),
            "product_id": metadata.get("product_id"),
            "score": None if distance is None else float(distance),
        })
    return "\n".join(lines), sources
