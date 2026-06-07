export const defaultChatMessages = [
  { role: "assistant", content: "Hi. I can help you compare products, scan categories, and review your cart." },
];

const currencyFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
  maximumFractionDigits: 0,
});

export function formatCurrency(value) {
  return currencyFormatter.format(Number(value) || 0);
}

export function formatCount(value) {
  return Number(value || 0).toLocaleString("en-IN");
}

export function getDiscountPercent(product) {
  if (!product?.mrp || !product?.price || product.mrp <= product.price) return 0;
  return Math.round(((product.mrp - product.price) / product.mrp) * 100);
}

export function buildFallbackImage(product) {
  const safeBrand = (product?.brand || "Featured").replace(/[<&>]/g, "");
  const safeTitle = (product?.title || "Featured product").replace(/[<&>]/g, "");
  const svg = `
    <svg xmlns="http://www.w3.org/2000/svg" width="900" height="640" viewBox="0 0 900 640">
      <defs>
        <linearGradient id="hero" x1="0" x2="1" y1="0" y2="1">
          <stop offset="0%" stop-color="#1d4ed8" />
          <stop offset="100%" stop-color="#06b6d4" />
        </linearGradient>
      </defs>
      <rect width="900" height="640" rx="40" fill="url(#hero)" />
      <circle cx="730" cy="130" r="92" fill="rgba(255,255,255,0.12)" />
      <circle cx="200" cy="520" r="150" fill="rgba(255,255,255,0.10)" />
      <rect x="64" y="72" width="772" height="496" rx="34" fill="rgba(15,23,42,0.18)" stroke="rgba(255,255,255,0.18)" />
      <text x="112" y="190" fill="#ffffff" font-size="42" font-family="Arial, Helvetica, sans-serif" font-weight="700">${safeBrand}</text>
      <text x="112" y="270" fill="#eff6ff" font-size="28" font-family="Arial, Helvetica, sans-serif">${safeTitle}</text>
      <text x="112" y="340" fill="#dbeafe" font-size="24" font-family="Arial, Helvetica, sans-serif">Product image coming soon</text>
    </svg>`;

  return `data:image/svg+xml;charset=UTF-8,${encodeURIComponent(svg)}`;
}

export function uniqueCategories(products) {
  const counts = new Map();
  for (const product of products) {
    const slug = product.category_slug || "misc";
    const existing = counts.get(slug) || { slug, name: product.category || "Misc", count: 0 };
    existing.count += 1;
    counts.set(slug, existing);
  }

  return [
    { slug: "all", name: "All", count: products.length },
    ...Array.from(counts.values()).sort((a, b) => a.name.localeCompare(b.name)),
  ];
}

export function cartSummary(cart) {
  const items = cart.reduce((total, item) => total + item.quantity, 0);
  const subtotal = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
  const mrpTotal = cart.reduce((sum, item) => sum + item.mrp * item.quantity, 0);
  return {
    items,
    subtotal,
    mrpTotal,
    savings: Math.max(0, mrpTotal - subtotal),
  };
}

function findBudget(text) {
  const match = text.match(/under\s+(\d[\d,]*)|below\s+(\d[\d,]*)|(\d[\d,]*)\s*(budget|rs|inr)/i);
  const raw = match?.[1] || match?.[2] || match?.[3];
  return raw ? Number(raw.replace(/,/g, "")) : null;
}

export function buildAssistantReply(input, products, cart) {
  const text = input.trim().toLowerCase();
  if (!text) return "Ask about a category, a budget, or what is already in your cart.";

  if (text.includes("cart") || text.includes("checkout")) {
    const summary = cartSummary(cart);
    if (!summary.items) {
      return "Your cart is empty right now. Add a couple of products and I can help you compare totals.";
    }
    return `You have ${summary.items} item${summary.items > 1 ? "s" : ""} worth ${formatCurrency(summary.subtotal)} in the cart, with savings of ${formatCurrency(summary.savings)} versus MRP.`;
  }

  const budget = findBudget(text);
  let matches = [...products];

  for (const product of products) {
    const categoryText = `${product.category} ${product.category_slug}`.toLowerCase();
    if (text.includes(product.brand.toLowerCase()) || text.includes(categoryText) || text.includes(product.title.toLowerCase())) {
      matches = products.filter((item) => {
        const haystack = `${item.brand} ${item.title} ${item.category} ${item.category_slug}`.toLowerCase();
        return haystack.includes(product.brand.toLowerCase()) || haystack.includes(product.category_slug.toLowerCase());
      });
      break;
    }
  }

  if (budget) {
    matches = matches.filter((item) => item.price <= budget);
  }

  matches.sort((a, b) => b.rating - a.rating || a.price - b.price);

  if (!matches.length) {
    return "I could not find a close match. Try asking for a category like electronics or mobiles, or give me a budget.";
  }

  const picks = matches.slice(0, 3).map((product) => `${product.title} at ${formatCurrency(product.price)} with ${product.rating} stars`).join("; ");

  if (text.includes("compare") && matches.length >= 2) {
    const [first, second] = matches;
    return `${first.title} is ${formatCurrency(first.price)} with ${first.rating} stars, while ${second.title} is ${formatCurrency(second.price)} with ${second.rating} stars. Pick ${first.title} for the better rating and ${second.title} if you want the alternate price point.`;
  }

  return `Here are the strongest matches I found: ${picks}.`;
}
