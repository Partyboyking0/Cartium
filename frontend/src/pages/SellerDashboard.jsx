import { useState } from "react";

import { formatCurrency } from "../utils/ui";

export default function SellerDashboard({ data, onBack, onCreateProduct, onUpdateOrderItem, onRespondReview }) {
  const [product, setProduct] = useState({ category_slug: "electronics", title: "", brand: "", description: "", price: 0, mrp: 0, stock: 0, low_stock_threshold: 3, images: [], specs: [] });
  const [response, setResponse] = useState("Thank you for shopping with us. We appreciate your feedback.");

  const updateProduct = (field, value) => setProduct((current) => ({ ...current, [field]: value }));

  const submitProduct = () => {
    onCreateProduct(product);
    setProduct({ category_slug: "electronics", title: "", brand: "", description: "", price: 0, mrp: 0, stock: 0, low_stock_threshold: 3, images: [], specs: [] });
  };

  return (
    <main className="page-wrap dashboard-page">
      <section className="surface section-block">
        <div className="section-header">
          <div>
            <span className="eyebrow">Seller</span>
            <h2>{data?.seller?.store_name || "Seller dashboard"}</h2>
            <p>Track revenue, inventory health, customer orders, and reviews in one place.</p>
          </div>
          <button className="ghost-button" onClick={onBack}>Back</button>
        </div>
        <div className="stat-grid">
          {Object.entries(data?.stats || {}).map(([key, value]) => (
            <div className="stat-card" key={key}>
              <span>{key.replaceAll("_", " ")}</span>
              <strong>{typeof value === "number" && key.includes("revenue") ? formatCurrency(value) : value}</strong>
            </div>
          ))}
        </div>
      </section>

      <section className="surface section-block">
        <div className="section-header compact">
          <div>
            <span className="eyebrow">Products</span>
            <h2>Manage listings</h2>
            <p>Add products with pricing, stock, category, and customer-ready descriptions.</p>
          </div>
        </div>
        <div className="form-grid three-up seller-product-form">
          <input placeholder="Product title" value={product.title} onChange={(e) => updateProduct("title", e.target.value)} />
          <input placeholder="Brand" value={product.brand} onChange={(e) => updateProduct("brand", e.target.value)} />
          <input placeholder="Category slug" value={product.category_slug} onChange={(e) => updateProduct("category_slug", e.target.value)} />
          <input placeholder="MRP" type="number" value={product.mrp} onChange={(e) => updateProduct("mrp", Number(e.target.value))} />
          <input placeholder="Selling price" type="number" value={product.price} onChange={(e) => updateProduct("price", Number(e.target.value))} />
          <input placeholder="Stock" type="number" value={product.stock} onChange={(e) => updateProduct("stock", Number(e.target.value))} />
          <input placeholder="Low stock alert" type="number" value={product.low_stock_threshold} onChange={(e) => updateProduct("low_stock_threshold", Number(e.target.value))} />
          <input className="wide-input" placeholder="Product description" value={product.description} onChange={(e) => updateProduct("description", e.target.value)} />
        </div>
        <button className="primary-button" onClick={submitProduct}>Add product</button>

        <div className="mini-list seller-list">
          {(data?.products || []).map((item) => (
            <p key={item.id}>
              <strong>{item.title}</strong>
              <span>Stock {item.stock}</span>
              <span>{item.listing_status}</span>
              {item.stock <= item.low_stock_threshold ? <span className="low-stock-label">Low stock</span> : null}
            </p>
          ))}
        </div>
      </section>

      <section className="surface section-block">
        <div className="section-header compact"><div><span className="eyebrow">Orders</span><h2>Update order status</h2></div></div>
        <div className="mini-list seller-list">
          {(data?.orders || []).flatMap((order) => order.items.map((item) => (
            <p key={item.id}>
              <strong>{item.title}</strong>
              <span>{item.status}</span>
              <button className="text-button" onClick={() => onUpdateOrderItem(item.id, "SHIPPED")}>Mark shipped</button>
              <button className="text-button" onClick={() => onUpdateOrderItem(item.id, "DELIVERED")}>Delivered</button>
            </p>
          )))}
        </div>
      </section>

      <section className="surface section-block">
        <div className="section-header compact"><div><span className="eyebrow">Reviews</span><h2>Customer reviews</h2></div></div>
        <div className="mini-list seller-list">
          {(data?.reviews || []).map((review) => (
            <p key={review.id}>
              <strong>{review.rating} star</strong>
              <span>{review.comment}</span>
              <input value={response} onChange={(e) => setResponse(e.target.value)} />
              <button className="text-button" onClick={() => onRespondReview(review.id, response)}>Respond</button>
            </p>
          ))}
        </div>
      </section>
    </main>
  );
}
