import { buildFallbackImage, formatCurrency, getDiscountPercent } from "../utils/ui";

export default function HeroPanel({ product, onSelectProduct, onAddToCart, categoryCount }) {
  if (!product) return null;

  const discountPercent = getDiscountPercent(product);
  const heroImage = product.images?.[0]?.url || buildFallbackImage(product);

  return (
    <section className="surface hero-panel">
      <div className="hero-copy">
        <span className="eyebrow">Fresh from the catalog</span>
        <h1>{product.title}</h1>
        <p>{product.description}</p>

        <div className="hero-price-line">
          <strong>{formatCurrency(product.price)}</strong>
          <span>{formatCurrency(product.mrp)}</span>
          {discountPercent ? <em>{discountPercent}% off</em> : null}
        </div>

        <div className="hero-actions">
          <button type="button" className="primary-button" onClick={() => onAddToCart(product)}>Add to cart</button>
          <button type="button" className="ghost-button" onClick={() => onSelectProduct(product.id)}>Explore details</button>
        </div>

        <div className="hero-stats">
          <div className="stat-card">
            <strong>{product.rating}</strong>
            <span>Top-rated pick</span>
          </div>
          <div className="stat-card">
            <strong>{product.stock}</strong>
            <span>Ready to ship</span>
          </div>
          <div className="stat-card">
            <strong>{categoryCount}</strong>
            <span>Live categories</span>
          </div>
        </div>
      </div>

      <div className="hero-visual">
        <img
          src={heroImage}
          alt={product.images?.[0]?.alt || product.title}
          onError={(event) => {
            event.currentTarget.onerror = null;
            event.currentTarget.src = buildFallbackImage(product);
          }}
        />
      </div>
    </section>
  );
}
