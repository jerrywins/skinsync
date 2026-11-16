export const STATUS = {
  no_notable_interaction: { tone: "clear", short: "No notable interaction found", icon: "check" },
  caution: { tone: "caution", short: "Potential interaction: caution", icon: "alert" },
  strong_caution: { tone: "strong", short: "Strong caution", icon: "stop" },
  insufficient_evidence: { tone: "unknown", short: "Insufficient evidence", icon: "question" },
  data_incomplete: { tone: "unknown", short: "Data incomplete", icon: "gap" },
} as const;
export type StatusKey = keyof typeof STATUS;

export const STRENGTH_LABEL: Record<string, string> = {
  high: "High", moderate: "Moderate", limited: "Limited", insufficient: "Insufficient", unknown: "Unknown",
};

export const CONFIDENCE_LABEL: Record<string, string> = { high: "High", moderate: "Moderate", low: "Low" };

export function pct(x: number | null | undefined): string {
  return x == null ? "–" : `${Math.round(x * 100)}%`;
}

export function inr(amount?: number, currency = "INR"): string {
  if (amount == null) return "Price unavailable";
  return new Intl.NumberFormat("en-IN", { style: "currency", currency, maximumFractionDigits: 0 }).format(amount);
}

export function date(iso?: string | null): string {
  if (!iso) return "";
  return new Intl.DateTimeFormat("en-IN", { day: "numeric", month: "short", year: "numeric" }).format(new Date(iso));
}

export const CATEGORY_LABEL: Record<string, string> = {
  sunscreen: "Sunscreen", serum: "Serum", face_mask: "Face mask", exfoliant: "Exfoliant", eye_care: "Eye care",
  cleanser: "Cleanser", toner: "Toner", moisturizer: "Moisturizer", lip_care: "Lip care", hand_care: "Hand care",
  body_care: "Body care", face_care: "Face care",
};

export const SKIN_TYPES = [
  { id: "dry", label: "Dry" }, { id: "oily", label: "Oily" }, { id: "combination", label: "Combination" },
  { id: "normal", label: "Normal" }, { id: "sensitive", label: "Sensitive or easily irritated" },
  { id: "unsure", label: "I'm not sure" },
] as const;

export const MODE_LABEL: Record<string, string> = {
  similar: "Similar formula", cheaper: "Cheaper", premium: "Premium", ingredient_focused: "Ingredient-focused",
  routine_compatible: "Fits my routine", sensitive_preference: "Matches my preferences",
};

export const EXCLUDE_LABEL: Record<string, string> = {
  duplicate_or_reference: "duplicates of your product", user_excluded: "products you excluded",
  missing_ingredient_data: "products without an ingredient list", different_category: "products in other categories",
  avoided_brand: "brands you avoid", contains_avoided_ingredient: "products with ingredients you avoid",
  conflicts_with_routine: "products that conflict with your routine", price_not_comparable: "products without a current comparable price",
  not_cheaper: "products that are not cheaper", not_premium: "products that are not pricier",
  missing_target_ingredients: "products without your target ingredients", too_dissimilar: "products too different in formula",
};
