import type { ProductDetail, ProductSummary } from "./types";

export function toSummary(d: ProductDetail): ProductSummary {
  return {
    id: d.id, slug: d.slug, name: d.name, brand: d.brand, brand_slug: d.brand_slug, category: d.category,
    image_url: d.image_url, is_demo: d.is_demo, version_id: d.current_version?.id ?? null,
    completeness: d.current_version?.completeness ?? 0, has_ingredients: !!d.current_version?.has_ingredient_list,
    price: d.prices?.[0] ?? { state: "unavailable", label: "Price unavailable" },
  };
}
