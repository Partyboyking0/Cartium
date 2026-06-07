import { buildFallbackImage, formatCount, formatCurrency, getDiscountPercent } from "../utils/ui";

export default function ProductCard({ product, onSelectProduct, onAddToCart }) {
  const discountPercent = getDiscountPercent(product);

  return (
    <article className="product-card">
      <button type="button" className="product-media" onClick={() => onSelectProduct(product.id)}>
        <img
          src={product.images?.[0]?.url || buildFallbackImage(product)}
          alt={product.images?.[0]?.alt || product.title}
          onError={(event) => {
            event.currentTarget.onerror = null;
            event.currentTarget.src = buildFallbackImage(product);
          }}
        />
      </button>

      <div className="product-tags">
        <span className="tag tag-brand">{product.brand}</span>
        {product.assured ? <span className="tag tag-good">Assured</span> : null}
      </div>

      <button type="button" className="product-title" onClick={() => onSelectProduct(product.id)}>
        {product.title}
      </button>

      <p className="product-copy">{product.description}</p>

      <div className="product-meta-row">
        <span className="rating-pill">{product.rating} star</span>
        <span className="muted-copy">{formatCount(product.reviews)} reviews</span>
      </div>

      <div className="price-line">
        <strong>{formatCurrency(product.price)}</strong>
        <span>{formatCurrency(product.mrp)}</span>
        {discountPercent ? <em>{discountPercent}% off</em> : null}
      </div>

      <div className="product-actions">
        <button type="button" className="ghost-button" onClick={() => onSelectProduct(product.id)}>View details</button>
        <button type="button" className="primary-button" onClick={() => onAddToCart(product)}>Add to cart</button>
      </div>
    </article>
  );
}
