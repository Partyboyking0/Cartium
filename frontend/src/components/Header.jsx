export default function Header({ query, setQuery, onOpenCatalog, onOpenAuth, onOpenCart, onOpenOrders, onOpenAccount, onOpenDashboard, cartCount, authUser, onLogout }) {
  const userLabel = authUser ? `${authUser.name} - ${authUser.role}` : null;
  const dashboardLabel = authUser?.role === "admin" ? "Admin" : authUser?.role === "seller" ? "Seller" : null;

  return (
    <header className="site-header">
      <div className="header-wrap">
        <div className="header-top">
          <button className="brand-lockup" type="button" onClick={onOpenCatalog}>
            <span>Cartium</span>
            <small>Shop smart. Sell faster.</small>
          </button>

          <div className="header-meta">
            <span className="header-pill">Marketplace</span>
            <span className="header-location desktop-only">Fast delivery, secure payments, trusted sellers.</span>
          </div>
        </div>

        <div className="header-main">
          <label className="search-shell">
            <span className="search-icon">Search</span>
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search for products, brands and more" aria-label="Search products" />
          </label>

          <nav className="header-nav" aria-label="Primary navigation">
            <button type="button" className="nav-link desktop-only" onClick={onOpenCatalog}>Shop</button>
            {userLabel ? <button type="button" className="signed-pill" onClick={onOpenAccount}>{userLabel}</button> : null}
            <button type="button" className={authUser ? "nav-link" : "nav-primary"} onClick={authUser ? onOpenAccount : onOpenAuth}>{authUser ? "Account" : "Login"}</button>
            {authUser ? <button type="button" className="nav-link" onClick={onOpenOrders}>Orders</button> : null}
            {dashboardLabel ? <button type="button" className="nav-link" onClick={onOpenDashboard}>{dashboardLabel}</button> : null}
            <button type="button" className="nav-link" onClick={onOpenCart}>Cart<span className="nav-badge">{cartCount}</span></button>
            {authUser ? <button type="button" className="nav-link desktop-only" onClick={onLogout}>Logout</button> : null}
          </nav>
        </div>
      </div>
    </header>
  );
}
