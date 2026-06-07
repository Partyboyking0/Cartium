export default function CategoryRail({ categories, activeCategory, onSelectCategory }) {
  return (
    <div className="category-rail" role="tablist" aria-label="Shop by category">
      {categories.map((category) => (
        <button
          key={category.slug}
          type="button"
          className={category.slug === activeCategory ? "category-chip active" : "category-chip"}
          onClick={() => onSelectCategory(category.slug)}
        >
          <span className="category-name">{category.name}</span>
          <small>{category.count} items</small>
        </button>
      ))}
    </div>
  );
}
