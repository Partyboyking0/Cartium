import { CategoryRail, HeroPanel, ProductCard, SectionHeader } from "../components";

export default function HomePage({
  featuredProduct,
  products,
  categories,
  selectedCategory,
  onSelectCategory,
  onSelectProduct,
  onAddToCart,
  onToggleChat,
  loading,
  query,
}) {
  const activeCategory = categories.find((item) => item.slug === selectedCategory)?.name || "All";
  const heading = selectedCategory === "all" ? "Popular picks" : `${activeCategory} picks`;
  const subtitle = query.trim()
    ? `Showing results for \"${query.trim()}\" across the current catalog.`
    : "Fresh catalog highlights with clear pricing, ratings, and quick actions.";

  return (
    <main className="page-wrap">
      <HeroPanel
        product={featuredProduct}
        categoryCount={Math.max(categories.length - 1, 1)}
        onSelectProduct={onSelectProduct}
        onAddToCart={onAddToCart}
      />

      <section className="surface">
        <CategoryRail categories={categories} activeCategory={selectedCategory} onSelectCategory={onSelectCategory} />
      </section>

      <section className="surface section-block">
        <SectionHeader
          eyebrow="Storefront"
          title={heading}
          subtitle={subtitle}
          actionLabel="Ask shopping assistant"
          onAction={onToggleChat}
        />

        {loading ? (
          <div className="empty-state">Loading products...</div>
        ) : products.length ? (
          <div className="product-grid">
            {products.map((product) => (
              <ProductCard
                key={product.id}
                product={product}
                onSelectProduct={onSelectProduct}
                onAddToCart={onAddToCart}
              />
            ))}
          </div>
        ) : (
          <div className="empty-state">No products match this search yet. Try a brand, category, or broader term.</div>
        )}
      </section>
    </main>
  );
}
