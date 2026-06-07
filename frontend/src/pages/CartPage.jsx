import { useEffect, useMemo, useState } from "react";

import { buildFallbackImage, cartSummary, formatCurrency } from "../utils/ui";

export default function CartPage({ cart, carts = [], activeCartId, authUser, onBack, onRemove, onUpdateQuantity, onProceed, onCreateCart, onSwitchCart, onRenameCart, onDeleteCart }) {
  const summary = cartSummary(cart);
  const activeCart = useMemo(() => carts.find((item) => item.id === activeCartId) || carts[0] || null, [carts, activeCartId]);
  const [newCartName, setNewCartName] = useState("");
  const [renameValue, setRenameValue] = useState(activeCart?.name || "Main cart");
  const [busyAction, setBusyAction] = useState("");
  const proceedLabel = !summary.items
    ? "Add items to continue"
    : authUser
      ? "Continue"
      : "Sign in to continue";

  useEffect(() => {
    setRenameValue(activeCart?.name || "Main cart");
  }, [activeCart?.id, activeCart?.name]);

  const runAction = async (actionName, action) => {
    setBusyAction(actionName);
    try {
      await action();
    } finally {
      setBusyAction("");
    }
  };

  const createCart = async (event) => {
    event.preventDefault();
    const name = newCartName.trim();
    if (!name) return;
    await runAction("create", async () => {
      await onCreateCart(name);
      setNewCartName("");
    });
  };

  const renameCart = async (event) => {
    event.preventDefault();
    const name = renameValue.trim();
    if (!name || !activeCart) return;
    await runAction("rename", async () => onRenameCart(name));
  };

  const switchCart = async (event) => {
    const nextCartId = Number(event.target.value);
    if (!nextCartId || nextCartId === activeCartId) return;
    await runAction("switch", async () => onSwitchCart(nextCartId));
  };

  const deleteCart = async () => {
    if (!activeCart || carts.length <= 1) return;
    const confirmed = window.confirm(`Delete ${activeCart.name}? Items in this cart will be removed.`);
    if (!confirmed) return;
    await runAction("delete", onDeleteCart);
  };

  return (
    <main className="page-wrap">
      <div className="cart-layout">
        <section className="surface cart-list">
          <SectionIntro
            title={activeCart ? activeCart.name : "Your cart"}
            subtitle={summary.items ? "Adjust quantities, compare pricing, and keep the total in view." : "This cart is empty. Switch carts or add products from the catalog."}
            onBack={onBack}
          />

          {authUser ? (
            <CartManager
              carts={carts}
              activeCart={activeCart}
              activeCartId={activeCartId}
              newCartName={newCartName}
              setNewCartName={setNewCartName}
              renameValue={renameValue}
              setRenameValue={setRenameValue}
              busyAction={busyAction}
              onCreate={createCart}
              onSwitch={switchCart}
              onRename={renameCart}
              onDelete={deleteCart}
            />
          ) : (
            <div className="multi-cart-panel guest-note">
              <strong>Login to unlock multiple carts.</strong>
              <span>Your current guest cart will be added to your active cart after sign in.</span>
            </div>
          )}

          {!cart.length ? (
            <div className="empty-state">No items in this cart yet.</div>
          ) : (
            cart.map((item) => (
              <article key={item.id} className="cart-item">
                <div className="cart-media">
                  <img
                    src={item.images?.[0]?.url || buildFallbackImage(item)}
                    alt={item.title}
                    onError={(event) => {
                      event.currentTarget.onerror = null;
                      event.currentTarget.src = buildFallbackImage(item);
                    }}
                  />
                </div>

                <div className="cart-copy">
                  <h3>{item.title}</h3>
                  <p className="muted-copy">{item.brand}</p>
                  <div className="price-line compact">
                    <strong>{formatCurrency(item.price)}</strong>
                    <span>{formatCurrency(item.mrp)}</span>
                  </div>
                </div>

                <div className="cart-actions">
                  <div className="qty-control">
                    <button type="button" onClick={() => onUpdateQuantity(item.id, item.quantity - 1)}>-</button>
                    <span>{item.quantity}</span>
                    <button type="button" onClick={() => onUpdateQuantity(item.id, item.quantity + 1)}>+</button>
                  </div>
                  <button type="button" className="text-button" onClick={() => onRemove(item.id)}>Remove</button>
                </div>
              </article>
            ))
          )}
        </section>

        <aside className="surface summary-card cart-summary-sticky">
          <h2>Order snapshot</h2>
          {activeCart ? <p className="muted-copy">Active cart: {activeCart.name}</p> : null}
          <div className="summary-row"><span>Items</span><strong>{summary.items}</strong></div>
          <div className="summary-row"><span>MRP total</span><strong>{formatCurrency(summary.mrpTotal)}</strong></div>
          <div className="summary-row"><span>Savings</span><strong>{formatCurrency(summary.savings)}</strong></div>
          <div className="summary-row total"><span>Pay now</span><strong>{formatCurrency(summary.subtotal)}</strong></div>
          <p className="muted-copy">{authUser ? `${carts.length || 1} saved cart${(carts.length || 1) > 1 ? "s" : ""} on this account.` : "Sign in if you want multiple saved carts."}</p>
          <button type="button" className="primary-button" onClick={onProceed} disabled={!summary.items}>{proceedLabel}</button>
          <button type="button" className="ghost-button" onClick={onBack}>Keep shopping</button>
        </aside>
      </div>
    </main>
  );
}

function CartManager({ carts, activeCart, activeCartId, newCartName, setNewCartName, renameValue, setRenameValue, busyAction, onCreate, onSwitch, onRename, onDelete }) {
  const cartCount = carts.length || 1;

  return (
    <section className="multi-cart-panel" aria-label="Cart manager">
      <div className="cart-manager-head">
        <div>
          <span className="eyebrow">Multi cart</span>
          <h3>Manage shopping lists</h3>
          <p>Use separate carts for groceries, gifts, office orders, or later purchases.</p>
        </div>
        <span className="cart-count-pill">{cartCount}/8 carts</span>
      </div>

      <div className="cart-select-row">
        <label>
          <span>Active cart</span>
          <select value={activeCartId || ""} onChange={onSwitch} disabled={busyAction === "switch" || !carts.length}>
            {carts.map((item) => (
              <option key={item.id} value={item.id}>{item.name}</option>
            ))}
          </select>
        </label>
      </div>

      <form className="cart-manager-form" onSubmit={onCreate}>
        <label>
          <span>Create a new cart</span>
          <input value={newCartName} onChange={(event) => setNewCartName(event.target.value)} placeholder="Cart name, like Diwali gifts" maxLength="80" />
        </label>
        <button type="submit" className="secondary-button" disabled={busyAction === "create" || !newCartName.trim() || cartCount >= 8}>
          {busyAction === "create" ? "Creating..." : "Create and switch"}
        </button>
      </form>

      <form className="cart-manager-form" onSubmit={onRename}>
        <label>
          <span>Rename selected cart</span>
          <input value={renameValue} onChange={(event) => setRenameValue(event.target.value)} placeholder="Cart name" maxLength="80" />
        </label>
        <button type="submit" className="ghost-button" disabled={busyAction === "rename" || !activeCart || !renameValue.trim()}>
          {busyAction === "rename" ? "Saving..." : "Rename"}
        </button>
      </form>

      <div className="cart-manager-foot">
        <span>{activeCart ? `${activeCart.name} is selected for checkout.` : "No cart selected yet."}</span>
        <button type="button" className="text-button danger-text" onClick={onDelete} disabled={busyAction === "delete" || cartCount <= 1}>
          {busyAction === "delete" ? "Deleting..." : "Delete selected cart"}
        </button>
      </div>
    </section>
  );
}

function SectionIntro({ title, subtitle, onBack }) {
  return (
    <div className="section-header compact cart-header">
      <div>
        <button type="button" className="text-button back-button" onClick={onBack}>Back to catalog</button>
        <h2>{title}</h2>
        <p>{subtitle}</p>
      </div>
    </div>
  );
}
