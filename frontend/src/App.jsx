import React, { useEffect, useMemo, useState } from "react";

import { api, getAuthToken, setAuthToken } from "./api";
import { AIChatWidget, ErrorBoundary, Footer, Header } from "./components";
import { AccountPage, AdminDashboard, AuthPage, CartPage, CheckoutPage, HomePage, OrdersPage, ProductDetail, SellerDashboard } from "./pages";
import { uniqueCategories } from "./utils/ui";

const CART_KEY = "cartium-cart";

function readStoredValue(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch {
    return fallback;
  }
}

function cartRowsFromApi(cart) {
  return (cart?.items || []).map((line) => ({ ...line.product, id: line.id, product_id: line.product.id, quantity: line.quantity }));
}

function loadExternalScript(src) {
  return new Promise((resolve, reject) => {
    const existingScript = document.querySelector(`script[src="${src}"]`);
    if (existingScript) {
      if (existingScript.dataset.loaded === "true") return resolve();
      existingScript.addEventListener("load", resolve, { once: true });
      existingScript.addEventListener("error", reject, { once: true });
      return;
    }

    const script = document.createElement("script");
    script.src = src;
    script.async = true;
    script.onload = () => {
      script.dataset.loaded = "true";
      resolve();
    };
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

function loadRazorpayCheckout() {
  if (window.Razorpay) return Promise.resolve();
  return loadExternalScript("https://checkout.razorpay.com/v1/checkout.js");
}

export default function App() {
  const [page, setPage] = useState("home");
  const [query, setQuery] = useState("");
  const [products, setProducts] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [loading, setLoading] = useState(true);
  const [chatOpen, setChatOpen] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [postAuthPage, setPostAuthPage] = useState("home");
  const [cart, setCart] = useState(() => readStoredValue(CART_KEY, []));
  const [carts, setCarts] = useState([]);
  const [activeCartId, setActiveCartId] = useState(null);
  const [authUser, setAuthUser] = useState(null);
  const [orders, setOrders] = useState([]);
  const [reviews, setReviews] = useState([]);
  const [account, setAccount] = useState({ addresses: [], payments: [], wishlist: [], recent: [] });
  const [sellerData, setSellerData] = useState(null);
  const [adminData, setAdminData] = useState(null);

  const isAuthed = Boolean(authUser && getAuthToken());

  useEffect(() => {
    if (!isAuthed) {
      localStorage.setItem(CART_KEY, JSON.stringify(cart));
    }
  }, [cart, isAuthed]);

  useEffect(() => {
    if (!notice) return undefined;
    const timer = window.setTimeout(() => setNotice(""), 2800);
    return () => window.clearTimeout(timer);
  }, [notice]);

  useEffect(() => {
    if (page === "auth") setChatOpen(false);
  }, [page]);

  useEffect(() => {
    let active = true;
    const loadCatalog = async () => {
      setLoading(true);
      setError("");
      try {
        await api.health();
        const response = await api.products();
        if (active) setProducts(Array.isArray(response.items) ? response.items : []);
      } catch (err) {
        if (active) setError(err.message || "Unable to load the catalog right now.");
      } finally {
        if (active) setLoading(false);
      }
    };
    loadCatalog();
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!getAuthToken()) return;
    api.me().then((user) => {
      setAuthUser(user);
      return refreshCartWorkspace();
    }).catch(() => {
      setAuthToken("");
      setAuthUser(null);
    });
  }, []);

  const categories = useMemo(() => uniqueCategories(products), [products]);

  const filteredProducts = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return products.filter((product) => {
      const categoryMatch = selectedCategory === "all" || product.category_slug === selectedCategory;
      if (!categoryMatch) return false;
      if (!normalizedQuery) return true;
      const haystack = [product.title, product.brand, product.category, product.category_slug, product.description].filter(Boolean).join(" ").toLowerCase();
      return haystack.includes(normalizedQuery);
    });
  }, [products, query, selectedCategory]);

  const featuredProduct = useMemo(() => {
    const source = filteredProducts.length ? filteredProducts : products;
    return [...source].sort((left, right) => right.rating - left.rating || left.price - right.price)[0] || null;
  }, [filteredProducts, products]);

  const cartCount = useMemo(() => cart.reduce((total, item) => total + item.quantity, 0), [cart]);

  const openCatalog = () => {
    setPage("home");
    setSelectedProduct(null);
    setError("");
  };

  async function refreshRemoteCart(cartId = null) {
    const remoteCart = await api.cart(cartId);
    setCart(cartRowsFromApi(remoteCart));
    if (remoteCart?.cart) {
      setActiveCartId(remoteCart.cart.id);
    }
    return remoteCart;
  }

  async function refreshCartWorkspace(cartId = null) {
    const [cartList, remoteCart] = await Promise.all([api.cartList(), api.cart(cartId)]);
    setCarts(cartList.items || []);
    setActiveCartId(remoteCart?.cart?.id || cartList.active_cart_id || null);
    setCart(cartRowsFromApi(remoteCart));
    return { cartList, remoteCart };
  }

  async function refreshOrders() {
    const response = await api.orders();
    setOrders(response.items || []);
    return response.items || [];
  }

  async function loadAccount() {
    if (!isAuthed) {
      setPostAuthPage("account");
      setPage("auth");
      return;
    }
    const [addresses, payments, wishlist, recent] = await Promise.all([api.addresses(), api.paymentMethods(), api.wishlist(), api.recentlyViewed()]);
    setAccount({ addresses: addresses.items || [], payments: payments.items || [], wishlist: wishlist.items || [], recent: recent.items || [] });
    setPage("account");
  }

  const addToCart = async (product) => {
    setError("");
    try {
      if (isAuthed) {
        await api.addCart({ product_id: product.id, quantity: 1, cart_id: activeCartId });
        await refreshRemoteCart();
      } else {
        setCart((current) => {
          const existing = current.find((item) => (item.product_id || item.id) === product.id);
          if (existing) return current.map((item) => ((item.product_id || item.id) === product.id ? { ...item, quantity: item.quantity + 1 } : item));
          return [...current, { ...product, product_id: product.id, quantity: 1 }];
        });
      }
      setNotice(`${product.title} added to your cart.`);
      setPage("cart");
    } catch (err) {
      setError(err.message || "Could not add to cart");
    }
  };

  const removeFromCart = async (itemId) => {
    if (isAuthed) {
      await api.removeCart(itemId);
      await refreshRemoteCart();
    } else {
      setCart((current) => current.filter((item) => item.id !== itemId));
    }
    setNotice("Item removed from your cart.");
  };

  const updateCartQuantity = async (itemId, nextQuantity) => {
    if (nextQuantity <= 0) {
      await removeFromCart(itemId);
      return;
    }
    if (isAuthed) {
      await api.updateCart(itemId, { quantity: nextQuantity });
      await refreshRemoteCart();
    } else {
      setCart((current) => current.map((item) => (item.id === itemId ? { ...item, quantity: nextQuantity } : item)));
    }
  };

  const openProduct = async (productId) => {
    setError("");
    setPage("detail");
    setSelectedProduct(products.find((item) => item.id === productId) || null);
    try {
      const [product, reviewResponse] = await Promise.all([api.product(productId), api.reviews(productId).catch(() => ({ items: [] }))]);
      setSelectedProduct(product);
      setReviews(reviewResponse.items || []);
    } catch (err) {
      setError(err.message || "Unable to load product details right now.");
    }
  };

  const handleLogin = async (response) => {
    setAuthToken(response.token);
    setAuthUser(response.user);
    try {
      for (const item of cart) {
        await api.addCart({ product_id: item.product_id || item.id, quantity: item.quantity, cart_id: activeCartId });
      }
      await refreshCartWorkspace();
    } catch {
      await refreshCartWorkspace().catch(() => {});
    }
    localStorage.removeItem(CART_KEY);
    setPage(postAuthPage);
    setNotice(`Signed in as ${response.user.name}.`);
  };

  const handleLogout = async () => {
    await api.logout().catch(() => {});
    setAuthToken("");
    setAuthUser(null);
    setCart([]);
    setCarts([]);
    setActiveCartId(null);
    setOrders([]);
    setAccount({ addresses: [], payments: [], wishlist: [], recent: [] });
    setPage("home");
    setNotice("You have been logged out.");
  };

  const openAuth = (nextPage = page === "cart" ? "cart" : "home") => {
    setPostAuthPage(nextPage);
    setPage("auth");
  };

  const openOrders = async () => {
    if (!isAuthed) return openAuth("orders");
    await refreshOrders();
    setPage("orders");
  };

  const openDashboard = async () => {
    if (!isAuthed) return openAuth("home");
    if (authUser.role === "seller") {
      setSellerData(await api.sellerDashboard());
      setPage("seller");
    } else if (authUser.role === "admin") {
      setAdminData(await api.adminDashboard());
      setPage("admin");
    }
  };

  const createNamedCart = async (name) => {
    if (!isAuthed) return openAuth("cart");
    setError("");
    try {
      const newCart = await api.createCart({ name });
      await refreshCartWorkspace(newCart.id);
      setNotice(`${newCart.name} cart created and selected.`);
    } catch (err) {
      setError(err.message || "Could not create cart");
      throw err;
    }
  };

  const switchCart = async (cartId) => {
    if (!isAuthed) return;
    setError("");
    try {
      await api.activateCart(cartId);
      await refreshCartWorkspace(cartId);
    } catch (err) {
      setError(err.message || "Could not switch cart");
      throw err;
    }
  };

  const renameActiveCart = async (name) => {
    if (!isAuthed || !activeCartId) return;
    setError("");
    try {
      await api.renameCart(activeCartId, { name });
      await refreshCartWorkspace(activeCartId);
      setNotice("Cart renamed.");
    } catch (err) {
      setError(err.message || "Could not rename cart");
      throw err;
    }
  };

  const deleteActiveCart = async () => {
    if (!isAuthed || !activeCartId) return;
    setError("");
    try {
      const response = await api.deleteCart(activeCartId);
      await refreshCartWorkspace(response?.cart?.id || null);
      setNotice("Cart deleted.");
    } catch (err) {
      setError(err.message || "Could not delete cart");
      throw err;
    }
  };

  const proceedFromCart = () => {
    if (!cart.length) return setNotice("Add at least one product before you continue.");
    if (!isAuthed) return openAuth("checkout");
    setPage("checkout");
  };

  const placeOrder = async (payload) => {
    if (!isAuthed) return openAuth("checkout");
    setError("");

    try {
      await loadRazorpayCheckout();
      if (!window.Razorpay) throw new Error("Razorpay checkout could not load");

      const razorpayOrder = await api.createRazorpayOrder({ address: payload.address });
      await new Promise((resolve, reject) => {
        const checkout = new window.Razorpay({
          key: razorpayOrder.key_id,
          amount: razorpayOrder.amount,
          currency: razorpayOrder.currency,
          name: "Cartium",
          description: "Secure order payment",
          order_id: razorpayOrder.razorpay_order_id,
          prefill: {
            name: payload.address.customer_name || authUser?.name || "",
            email: authUser?.email || "",
            contact: payload.address.phone || authUser?.phone || "",
          },
          notes: {
            user_id: String(authUser?.id || ""),
          },
          theme: { color: "#2874f0" },
          handler: async (response) => {
            try {
              const order = await api.verifyRazorpayPayment({ ...response, address: payload.address });
              setNotice(`Order ${order.order_number} placed.`);
              await refreshRemoteCart();
              await refreshOrders();
              setPage("orders");
              resolve(order);
            } catch (err) {
              reject(err);
            }
          },
          modal: {
            ondismiss: () => reject(new Error("Payment cancelled before completion.")),
          },
        });

        checkout.on("payment.failed", (response) => {
          reject(new Error(response?.error?.description || "Razorpay payment failed"));
        });
        checkout.open();
      });
    } catch (err) {
      setError(err.message || "Payment could not be completed");
      throw err;
    }
  };

  const addReview = async (payload) => {
    if (!isAuthed) return openAuth("detail");
    await api.addReview(payload);
    const response = await api.reviews(payload.product_id);
    setReviews(response.items || []);
    setNotice("Review submitted.");
  };

  const toggleWishlist = async (productId) => {
    if (!isAuthed) return openAuth("detail");
    const response = await api.toggleWishlist(productId);
    setNotice(response.status === "added" ? "Added to wishlist." : "Removed from wishlist.");
  };

  return (
    <ErrorBoundary>
      <Header query={query} setQuery={setQuery} onOpenCatalog={openCatalog} onOpenAuth={() => openAuth()} onOpenCart={() => setPage("cart")} onOpenOrders={openOrders} onOpenAccount={loadAccount} onOpenDashboard={openDashboard} cartCount={cartCount} authUser={authUser} onLogout={handleLogout} />
      {error ? <div className="status-banner error">{error}</div> : null}
      {notice ? <div className="status-banner success">{notice}</div> : null}

      {page === "auth" ? <AuthPage onLogin={handleLogin} onBack={openCatalog} authUser={authUser} /> : null}
      {page === "home" ? <HomePage featuredProduct={featuredProduct} products={filteredProducts} categories={categories} selectedCategory={selectedCategory} onSelectCategory={setSelectedCategory} onSelectProduct={openProduct} onAddToCart={addToCart} onToggleChat={() => setChatOpen((open) => !open)} loading={loading} query={query} /> : null}
      {page === "cart" ? <CartPage cart={cart} carts={carts} activeCartId={activeCartId} authUser={authUser} onBack={openCatalog} onRemove={removeFromCart} onUpdateQuantity={updateCartQuantity} onProceed={proceedFromCart} onCreateCart={createNamedCart} onSwitchCart={switchCart} onRenameCart={renameActiveCart} onDeleteCart={deleteActiveCart} /> : null}
      {page === "checkout" ? <CheckoutPage cart={cart} authUser={authUser} onBack={() => setPage("cart")} onPlaceOrder={placeOrder} /> : null}
      {page === "orders" ? <OrdersPage orders={orders} onBack={openCatalog} onReorder={async (orderId) => { await api.reorder(orderId); await refreshRemoteCart(); setPage("cart"); }} /> : null}
      {page === "account" ? <AccountPage account={account} authUser={authUser} onBack={openCatalog} onSaveProfile={async (payload) => { setAuthUser(await api.updateProfile(payload)); setNotice("Profile saved."); }} onAddAddress={async (payload) => { await api.addAddress(payload); await loadAccount(); }} onAddPayment={async (payload) => { await api.addPaymentMethod(payload); await loadAccount(); }} onSelectProduct={openProduct} onAddToCart={addToCart} /> : null}
      {page === "seller" ? <SellerDashboard data={sellerData} onBack={openCatalog} onCreateProduct={async (payload) => { await api.sellerCreateProduct(payload); setSellerData(await api.sellerDashboard()); }} onUpdateOrderItem={async (id, status) => { await api.sellerUpdateOrderItem(id, { status }); setSellerData(await api.sellerDashboard()); }} onRespondReview={async (id, response) => { await api.sellerRespondReview(id, { response }); setSellerData(await api.sellerDashboard()); }} /> : null}
      {page === "admin" ? <AdminDashboard data={adminData} onBack={openCatalog} onUpdateUser={async (id, payload) => { await api.adminUpdateUser(id, payload); setAdminData(await api.adminDashboard()); }} onModerateProduct={async (id, status) => { await api.adminModerateProduct(id, { listing_status: status, approval_note: status }); setAdminData(await api.adminDashboard()); }} onRefund={async (id) => { await api.adminRefund(id, { refund_status: "REFUNDED" }); setAdminData(await api.adminDashboard()); }} onResolveComplaint={async (id) => { await api.adminUpdateComplaint(id, { status: "RESOLVED", resolution_note: "Handled by admin" }); setAdminData(await api.adminDashboard()); }} /> : null}
      {page === "detail" ? <ProductDetail product={selectedProduct} reviews={reviews} authUser={authUser} onBack={openCatalog} onAddToCart={addToCart} onAddReview={addReview} onToggleWishlist={toggleWishlist} /> : null}

      <Footer />
      {page !== "auth" ? <AIChatWidget open={chatOpen} setOpen={setChatOpen} products={products} cart={cart} authUser={authUser} /> : null}
    </ErrorBoundary>
  );
}
