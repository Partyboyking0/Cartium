import { useState } from "react";

import { cartSummary, formatCurrency } from "../utils/ui";

export default function CheckoutPage({ cart, authUser, onBack, onPlaceOrder }) {
  const summary = cartSummary(cart);
  const [address, setAddress] = useState({
    label: "Home",
    customer_name: authUser?.name || "",
    phone: authUser?.phone || "",
    address_line: authUser?.address_line || "",
    city: authUser?.city || "",
    state: authUser?.state || "",
    pincode: authUser?.pincode || "",
  });
  const [busy, setBusy] = useState(false);

  const updateAddress = (field, value) => setAddress((current) => ({ ...current, [field]: value }));

  const submit = async (event) => {
    event.preventDefault();
    setBusy(true);
    try {
      await onPlaceOrder({ address });
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="page-wrap checkout-page">
      <section className="surface checkout-card">
        <button type="button" className="text-button back-button" onClick={onBack}>Back to cart</button>
        <div className="section-header compact"><div><span className="eyebrow">Checkout</span><h2>Delivery and Razorpay payment</h2><p>Enter your delivery details and complete payment securely with Razorpay.</p></div></div>
        <form className="checkout-form" onSubmit={submit}>
          <div className="form-grid two-up">
            <label><span>Name</span><input value={address.customer_name} onChange={(e) => updateAddress("customer_name", e.target.value)} placeholder="Full name" required /></label>
            <label><span>Phone</span><input value={address.phone} onChange={(e) => updateAddress("phone", e.target.value)} placeholder="Mobile number" required /></label>
          </div>
          <label><span>Address</span><textarea value={address.address_line} onChange={(e) => updateAddress("address_line", e.target.value)} placeholder="House number, street, area" required /></label>
          <div className="form-grid three-up">
            <label><span>City</span><input value={address.city} onChange={(e) => updateAddress("city", e.target.value)} placeholder="City" required /></label>
            <label><span>State</span><input value={address.state} onChange={(e) => updateAddress("state", e.target.value)} placeholder="State" required /></label>
            <label><span>Pincode</span><input value={address.pincode} onChange={(e) => updateAddress("pincode", e.target.value)} placeholder="6-digit pincode" required /></label>
          </div>

          <div className="razorpay-only">
            <strong>Razorpay secure checkout</strong>
            <span>Pay securely using UPI, cards, wallets, or netbanking through Razorpay.</span>
          </div>

          <button type="submit" className="primary-button" disabled={busy || !cart.length}>{busy ? "Opening Razorpay..." : `Pay ${formatCurrency(summary.subtotal)} with Razorpay`}</button>
        </form>
      </section>
      <aside className="surface summary-card">
        <h2>Order summary</h2>
        <div className="summary-row"><span>Items</span><strong>{summary.items}</strong></div>
        <div className="summary-row"><span>MRP</span><strong>{formatCurrency(summary.mrpTotal)}</strong></div>
        <div className="summary-row"><span>Discount</span><strong>{formatCurrency(summary.savings)}</strong></div>
        <div className="summary-row total"><span>Total</span><strong>{formatCurrency(summary.subtotal)}</strong></div>
      </aside>
    </main>
  );
}
