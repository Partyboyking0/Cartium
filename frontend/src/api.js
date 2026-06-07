const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

let authToken = localStorage.getItem("cartium-token") || "";

export function setAuthToken(token) {
  authToken = token || "";
  if (authToken) {
    localStorage.setItem("cartium-token", authToken);
  } else {
    localStorage.removeItem("cartium-token");
  }
}

export function getAuthToken() {
  return authToken;
}

async function request(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (authToken) {
    headers.Authorization = `Bearer ${authToken}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let message = "";
    try {
      const error = await response.json();
      message = error.detail || JSON.stringify(error);
    } catch {
      message = await response.text();
    }
    throw new Error(message || `Request failed with ${response.status}`);
  }

  return response.status === 204 ? null : response.json();
}

const json = (body, method = "POST") => ({ method, body: JSON.stringify(body) });

export const api = {
  health: () => request("/api/health"),
  products: (params = {}) => {
    const query = new URLSearchParams(params).toString();
    return request(`/api/products${query ? `?${query}` : ""}`);
  },
  product: (id) => request(`/api/products/${id}`),

  signup: (payload) => request("/api/auth/signup", json(payload)),
  login: (payload) => request("/api/auth/login", json(payload)),
  oauth: (payload) => request("/api/auth/oauth", json(payload)),
  me: () => request("/api/auth/me"),
  logout: () => request("/api/auth/logout", { method: "POST" }),

  cart: (cartId) => request(`/api/cart${cartId ? `?cart_id=${cartId}` : ""}`),
  cartList: () => request("/api/cart/carts"),
  createCart: (payload) => request("/api/cart/carts", json(payload)),
  renameCart: (cartId, payload) => request(`/api/cart/carts/${cartId}`, json(payload, "PATCH")),
  activateCart: (cartId) => request(`/api/cart/carts/${cartId}/activate`, { method: "PATCH" }),
  deleteCart: (cartId) => request(`/api/cart/carts/${cartId}`, { method: "DELETE" }),
  addCart: (payload) => request("/api/cart", json(payload)),
  updateCart: (itemId, payload) => request(`/api/cart/${itemId}`, json(payload, "PATCH")),
  removeCart: (itemId) => request(`/api/cart/${itemId}`, { method: "DELETE" }),
  clearCart: (cartId) => request(`/api/cart${cartId ? `?cart_id=${cartId}` : ""}`, { method: "DELETE" }),

  profile: () => request("/api/account/profile"),
  updateProfile: (payload) => request("/api/account/profile", json(payload, "PATCH")),
  addresses: () => request("/api/account/addresses"),
  addAddress: (payload) => request("/api/account/addresses", json(payload)),
  updateAddress: (id, payload) => request(`/api/account/addresses/${id}`, json(payload, "PATCH")),
  paymentMethods: () => request("/api/account/payment-methods"),
  addPaymentMethod: (payload) => request("/api/account/payment-methods", json(payload)),
  wishlist: () => request("/api/account/wishlist"),
  toggleWishlist: (productId) => request(`/api/account/wishlist/${productId}`, { method: "POST" }),
  recentlyViewed: () => request("/api/account/recently-viewed"),

  checkout: (payload) => request("/api/orders/checkout", json(payload)),
  createRazorpayOrder: (payload) => request("/api/orders/razorpay/create", json(payload)),
  verifyRazorpayPayment: (payload) => request("/api/orders/razorpay/verify", json(payload)),
  orders: () => request("/api/orders"),
  reorder: (orderId) => request(`/api/orders/${orderId}/reorder`, { method: "POST" }),
  complaint: (payload) => request("/api/orders/complaints", json(payload)),

  reviews: (productId) => request(`/api/reviews/product/${productId}`),
  addReview: (payload) => request("/api/reviews", json(payload)),

  chat: (payload) => request("/api/ai/chat", json(payload)),
  chatHistory: () => request("/api/ai/history"),
  clearChatHistory: () => request("/api/ai/history", { method: "DELETE" }),

  sellerDashboard: () => request("/api/seller/dashboard"),
  sellerCreateProduct: (payload) => request("/api/seller/products", json(payload)),
  sellerUpdateProduct: (id, payload) => request(`/api/seller/products/${id}`, json(payload, "PATCH")),
  sellerDeleteProduct: (id) => request(`/api/seller/products/${id}`, { method: "DELETE" }),
  sellerUpdateOrderItem: (id, payload) => request(`/api/seller/orders/items/${id}/status`, json(payload, "PATCH")),
  sellerRespondReview: (id, payload) => request(`/api/seller/reviews/${id}/response`, json(payload)),

  adminDashboard: () => request("/api/admin/dashboard"),
  adminUpdateUser: (id, payload) => request(`/api/admin/users/${id}`, json(payload, "PATCH")),
  adminModerateProduct: (id, payload) => request(`/api/admin/products/${id}/moderation`, json(payload, "PATCH")),
  adminRemoveProduct: (id) => request(`/api/admin/products/${id}`, { method: "DELETE" }),
  adminRefund: (id, payload) => request(`/api/admin/transactions/${id}/refund`, json(payload, "PATCH")),
  adminUpdateComplaint: (id, payload) => request(`/api/admin/complaints/${id}`, json(payload, "PATCH")),
};
