import { useState } from "react";

import ProductCard from "../components/ProductCard";

export default function AccountPage({ account, authUser, onBack, onSaveProfile, onAddAddress, onAddPayment, onSelectProduct, onAddToCart }) {
  const [profile, setProfile] = useState({ name: authUser?.name || "", phone: authUser?.phone || "", store_name: authUser?.store_name || "" });
  const [address, setAddress] = useState({ label: "Home", customer_name: authUser?.name || "", phone: authUser?.phone || "", address_line: "", city: "", state: "", pincode: "" });
  const [payment, setPayment] = useState({ provider: "RAZORPAY", label: "Razorpay", upi_id: "", card_last4: "", is_default: false });

  return (
    <main className="page-wrap account-page">
      <section className="surface section-block">
        <div className="section-header"><div><span className="eyebrow">Account</span><h2>Profile</h2><p>{authUser?.email}</p></div><button className="ghost-button" onClick={onBack}>Back</button></div>
        <div className="form-grid three-up">
          <label><span>Name</span><input value={profile.name} onChange={(e) => setProfile({ ...profile, name: e.target.value })} /></label>
          <label><span>Phone</span><input value={profile.phone} onChange={(e) => setProfile({ ...profile, phone: e.target.value })} /></label>
          <label><span>Store name</span><input value={profile.store_name} onChange={(e) => setProfile({ ...profile, store_name: e.target.value })} /></label>
        </div>
        <button className="primary-button" onClick={() => onSaveProfile(profile)}>Save profile</button>
      </section>

      <section className="surface section-block">
        <div className="section-header compact"><div><span className="eyebrow">Addresses</span><h2>Multiple addresses</h2></div></div>
        <div className="mini-list">{account.addresses.map((item) => <p key={item.id}><strong>{item.label}</strong> - {item.address_line}, {item.city} {item.pincode}</p>)}</div>
        <div className="form-grid three-up">
          <input placeholder="Label" value={address.label} onChange={(e) => setAddress({ ...address, label: e.target.value })} />
          <input placeholder="Name" value={address.customer_name} onChange={(e) => setAddress({ ...address, customer_name: e.target.value })} />
          <input placeholder="Phone" value={address.phone} onChange={(e) => setAddress({ ...address, phone: e.target.value })} />
          <input placeholder="Address" value={address.address_line} onChange={(e) => setAddress({ ...address, address_line: e.target.value })} />
          <input placeholder="City" value={address.city} onChange={(e) => setAddress({ ...address, city: e.target.value })} />
          <input placeholder="State" value={address.state} onChange={(e) => setAddress({ ...address, state: e.target.value })} />
          <input placeholder="Pincode" value={address.pincode} onChange={(e) => setAddress({ ...address, pincode: e.target.value })} />
        </div>
        <button className="secondary-button" onClick={() => onAddAddress(address)}>Add address</button>
      </section>

      <section className="surface section-block">
        <div className="section-header compact"><div><span className="eyebrow">Payments</span><h2>Saved payment methods</h2></div></div>
        <div className="mini-list">{account.payments.map((item) => <p key={item.id}><strong>{item.provider}</strong> - {item.label}</p>)}</div>
        <div className="form-grid three-up">
          <input value="RAZORPAY" readOnly />
          <input placeholder="Label" value={payment.label} onChange={(e) => setPayment({ ...payment, label: e.target.value })} />
          <input value="Handled securely by Razorpay Checkout" readOnly />
        </div>
        <button className="secondary-button" onClick={() => onAddPayment(payment)}>Save payment</button>
      </section>

      <section className="surface section-block">
        <div className="section-header compact"><div><span className="eyebrow">Personalized</span><h2>Wishlist and recently viewed</h2></div></div>
        <div className="product-grid compact-grid">{[...account.wishlist, ...account.recent].slice(0, 6).map((product) => <ProductCard key={`${product.id}-${product.title}`} product={product} onSelectProduct={onSelectProduct} onAddToCart={onAddToCart} />)}</div>
      </section>
    </main>
  );
}
