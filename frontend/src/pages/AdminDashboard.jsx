import { formatCurrency } from "../utils/ui";

export default function AdminDashboard({ data, onBack, onUpdateUser, onModerateProduct, onRefund, onResolveComplaint }) {
  const stats = data?.stats || {};
  return (
    <main className="page-wrap dashboard-page">
      <section className="surface section-block">
        <div className="section-header"><div><span className="eyebrow">Admin</span><h2>Platform control</h2><p>Users, sellers, products, payments, complaints, and fraud monitoring.</p></div><button className="ghost-button" onClick={onBack}>Back</button></div>
        <div className="stat-grid">{Object.entries(stats).map(([key, value]) => <div className="stat-card" key={key}><span>{key.replaceAll("_", " ")}</span><strong>{key.includes("revenue") ? formatCurrency(value) : value}</strong></div>)}</div>
      </section>

      <section className="surface section-block"><div className="section-header compact"><div><span className="eyebrow">Users</span><h2>User management</h2></div></div>
        <div className="admin-table">{(data?.users || []).map((user) => <div key={user.id}><span>{user.name}</span><span>{user.email}</span><span>{user.role}</span><button className="text-button" onClick={() => onUpdateUser(user.id, { is_active: !user.is_active })}>{user.is_active ? "Ban" : "Activate"}</button><button className="text-button" onClick={() => onUpdateUser(user.id, { role: user.role === "seller" ? "buyer" : "seller" })}>Switch role</button></div>)}</div>
      </section>

      <section className="surface section-block"><div className="section-header compact"><div><span className="eyebrow">Products</span><h2>Product control</h2></div></div>
        <div className="admin-table">{(data?.products || []).map((product) => <div key={product.id}><span>{product.title}</span><span>{product.listing_status}</span><span>{formatCurrency(product.price)}</span><button className="text-button" onClick={() => onModerateProduct(product.id, "APPROVED")}>Approve</button><button className="text-button" onClick={() => onModerateProduct(product.id, "REJECTED")}>Reject</button></div>)}</div>
      </section>

      <section className="surface section-block"><div className="section-header compact"><div><span className="eyebrow">Payments</span><h2>Transactions and refunds</h2></div></div>
        <div className="admin-table">{(data?.transactions || []).map((tx) => <div key={tx.id}><span>{tx.provider}</span><span>{formatCurrency(tx.amount)}</span><span>{tx.refund_status}</span><button className="text-button" onClick={() => onRefund(tx.id)}>Refund</button></div>)}</div>
      </section>

      <section className="surface section-block"><div className="section-header compact"><div><span className="eyebrow">Moderation</span><h2>Reports and fraud</h2></div></div>
        <div className="mini-list">{(data?.complaints || []).map((item) => <p key={item.id}><strong>{item.subject}</strong> · {item.status} <button className="text-button" onClick={() => onResolveComplaint(item.id)}>Resolve</button></p>)}</div>
        <div className="mini-list">{(data?.fraud_flags || []).map((flag) => <p key={flag.id}><strong>{flag.severity}</strong> · {flag.reason}</p>)}</div>
      </section>
    </main>
  );
}
