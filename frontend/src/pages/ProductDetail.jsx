import { useEffect, useState } from "react";

import { buildFallbackImage, formatCount, formatCurrency, getDiscountPercent } from "../utils/ui";

export default function ProductDetail({ product, reviews, authUser, onBack, onAddToCart, onAddReview, onToggleWishlist }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const [review, setReview] = useState({ rating: 5, comment: "" });

  useEffect(() => {
    setActiveIndex(0);
    setReview({ rating: 5, comment: "" });
  }, [product?.id]);

  if (!product) {
    return <main className="page-wrap"><div className="empty-state">Loading product details...</div></main>;
  }

  const activeImage = product.images?.[activeIndex] || product.images?.[0];
  const discountPercent = getDiscountPercent(product);

  const submitReview = (event) => {
    event.preventDefault();
    onAddReview({ product_id: product.id, rating: Number(review.rating), comment: review.comment });
    setReview({ rating: 5, comment: "" });
  };

  return (
    <main className="page-wrap detail-page-full">
      <button type="button" className="text-button back-button" onClick={onBack}>Back to catalog</button>

      <div className="detail-layout">
        <section className="surface detail-gallery">
          <div className="gallery-main">
            <img src={activeImage?.url || buildFallbackImage(product)} alt={activeImage?.alt || product.title} onError={(event) => { event.currentTarget.onerror = null; event.currentTarget.src = buildFallbackImage(product); }} />
          </div>
          {product.images?.length ? <div className="thumb-row">{product.images.map((image, index) => <button key={image.id} type="button" className={index === activeIndex ? "thumb-chip active" : "thumb-chip"} onClick={() => setActiveIndex(index)}><img src={image.url} alt={image.alt || product.title} /></button>)}</div> : null}
        </section>

        <section className="surface detail-panel">
          <span className="eyebrow">{product.category}</span>
          <h1>{product.title}</h1>
          <p className="detail-brand">{product.brand}</p>
          <p className="detail-description">{product.description}</p>
          <div className="hero-price-line detail-price-line"><strong>{formatCurrency(product.price)}</strong><span>{formatCurrency(product.mrp)}</span>{discountPercent ? <em>{discountPercent}% off</em> : null}</div>
          <div className="product-meta-row detail-meta-row"><span className="rating-pill">{product.rating} star</span><span className="muted-copy">{formatCount(product.reviews)} reviews</span><span className="muted-copy">Stock: {product.stock}</span></div>
          <div className="product-actions detail-actions-row"><button type="button" className="primary-button" onClick={() => onAddToCart(product)}>Add to cart</button><button type="button" className="ghost-button" onClick={() => onToggleWishlist(product.id)}>Wishlist</button></div>
          <div className="spec-list"><h2>Highlights</h2>{product.specs?.length ? product.specs.map((spec) => <div key={spec.id} className="spec-row"><span>{spec.name}</span><strong>{spec.value}</strong></div>) : <p className="muted-copy">Detailed specifications will appear here for richer catalog entries.</p>}</div>
        </section>
      </div>

      <section className="surface section-block reviews-panel">
        <div className="section-header"><div><span className="eyebrow">Reviews</span><h2>Ratings and customer feedback</h2><p>Verified purchase badges appear when the user has delivered orders for the product.</p></div></div>
        {authUser ? <form className="review-form" onSubmit={submitReview}><select value={review.rating} onChange={(e) => setReview({ ...review, rating: e.target.value })}><option value="5">5 stars</option><option value="4">4 stars</option><option value="3">3 stars</option><option value="2">2 stars</option><option value="1">1 star</option></select><input value={review.comment} onChange={(e) => setReview({ ...review, comment: e.target.value })} placeholder="Write a review" /><button className="primary-button">Submit</button></form> : <p className="muted-copy">Login to write a review.</p>}
        <div className="review-list">{reviews.length ? reviews.map((item) => <article className="review-card" key={item.id}><strong>{item.rating} star</strong><span>{item.verified_purchase ? "Verified purchase" : "Customer review"}</span><p>{item.comment}</p>{item.seller_response ? <p className="seller-reply">Seller: {item.seller_response}</p> : null}</article>) : <div className="empty-state">No reviews yet.</div>}</div>
      </section>
    </main>
  );
}
