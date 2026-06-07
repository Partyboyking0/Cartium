import { formatCurrency } from "../utils/ui";

const steps = ["PLACED", "PACKED", "SHIPPED", "DELIVERED"];

export default function OrdersPage({ orders, onBack, onReorder }) {
  return (
    <main className="page-wrap">
      <section className="surface section-block">
        <div className="section-header">
          <div><span className="eyebrow">Orders</span><h2>Order history and tracking</h2><p>Track placed, packed, shipped, and delivered orders.</p></div>
          <button type="button" className="ghost-button" onClick={onBack}>Back to catalog</button>
        </div>
        {!orders.length ? <div className="empty-state">No orders yet.</div> : orders.map((order) => (
          <article className="order-card" key={order.id}>
            <div className="order-card-head"><div><h3>{order.order_number}</h3><p>{order.payment_method} · {order.payment_status}</p></div><strong>{formatCurrency(order.total_amount)}</strong></div>
            <div className="tracking-line">{steps.map((step) => <span key={step} className={steps.indexOf(step) <= steps.indexOf(order.status) ? "active" : ""}>{step}</span>)}</div>
            <div className="order-items">{order.items.map((item) => <p key={item.id}>{item.quantity} x {item.title} · {item.tracking_status}</p>)}</div>
            <button type="button" className="secondary-button" onClick={() => onReorder(order.id)}>Reorder</button>
          </article>
        ))}
      </section>
    </main>
  );
}
