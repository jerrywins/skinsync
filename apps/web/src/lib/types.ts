// Response envelopes that wrap the generated domain types (see api-schema.ts).
import type { ComparisonResult, NormalizedIngredient, RankedAlternative, SkinResult } from "./api";

export type Price = {
  state: "fresh" | "stale" | "unavailable"; label: string; amount?: number; currency?: string;
  seller?: string; source?: string; observed_at?: string; is_test?: boolean;
};
/** Synthetic random prices loaded only in dev/test (`seed-test-prices`); never real. */
export const TEST_PRICE_SOURCE = "synthetic-test";

export type ProductSummary = {
  id: string; slug: string; name: string; brand: string | null; brand_slug: string | null; category: string;
  image_url: string | null; is_demo: boolean; version_id: string | null; completeness: number;
  has_ingredients: boolean; price: Price;
};

export type Page<T> = { items: T[]; total: number; limit: number; offset: number; next_offset: number | null };

export type ProductDetail = {
  id: string; slug: string; name: string; brand: string | null; brand_slug: string | null; category: string;
  market: string | null; image_url: string | null; is_demo: boolean; barcodes: string[];
  provenance: { source: string; source_ref: string; retrieved_at: string; licence: string | null; source_url: string | null };
  current_version: null | { id: string; label: string; observed_at: string; completeness: number; verification: string;
                            has_ingredient_list: boolean; raw_ingredients: string | null; source: string };
  ingredients: { position: number; raw: string; ingredient_id: string | null; inci_name: string | null;
                 function_classes: string[]; method: string; confidence: number; review_status: string;
                 stated_role: string; is_key_active: boolean; name_reviewed: boolean }[];
  unresolved_count: number;
  versions: { id: string; label: string; observed_at: string; completeness: number; is_current: boolean }[];
  prices: Price[];
  indexable: boolean;
};

export type ComparisonSide = {
  product_id: string | null; slug: string | null; name: string; brand: string | null; is_demo: boolean;
  version_id: string; version_label: string; ingredients: NormalizedIngredient[];
};

export type ComparisonEnvelope = {
  id: string | null; result: ComparisonResult; product_a: ComparisonSide; product_b: ComparisonSide;
  saved: boolean | null; outdated: string[]; saveable: boolean; claim_token: string | null;
};

export type AlternativesEnvelope = {
  id: string; saved: boolean; reference: { id: string; slug: string; name: string; brand: string | null;
                                           is_demo: boolean; image_url: string | null };
  results: (RankedAlternative & { slug: string | null; image_url: string | null; category: string | null })[];
  excluded: Record<string, number>; reference_price_state: string; low_identification_confidence: boolean;
  weights: Record<string, number>; mode: string; notes: string[]; candidates_considered: number;
};

export type SkinProduct = {
  product_id: string; slug: string; name: string; brand: string | null; image_url: string | null;
  category: string; observation: string; concern_category: string; observation_confidence: number;
  evidence_strength: string; product_data_confidence: number; matching_ingredients: string[];
  rationale: string; routine_checked: boolean;
};

export type SkinAnalysis = {
  id: string; status: "created" | "validating" | "rejected" | "queued" | "analyzing" | "completed" | "failed";
  skin_type: string; progress: number; error_code: string | null; image_stored: boolean; keep_image: boolean;
  created_at: string; medical_boundary: string; shareable: false; message?: string;
  result?: SkinResult & { products: SkinProduct[]; knowledge_version: string; knowledge_is_demo: boolean };
  model_version?: string; is_demo_model?: boolean; demo_label?: string | null;
};

export type Me = {
  id: string; email: string; role: "registered" | "admin"; email_verified: boolean;
  profile: { skin_type: string | null; preferences: Record<string, unknown> };
  consents: Record<string, boolean>;
};
