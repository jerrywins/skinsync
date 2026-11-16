-- SkinSync initial schema (PostgreSQL 16). Spec: SkinSync §8, SkinIQ §97-101.
-- Design rules enforced here, not just in application code:
--   * provenance on catalogue rows (source, source_ref, retrieved_at)            NFR-09
--   * comparisons bind to product_version ids + knowledge_version                 principle 1.2.5
--   * confidence and evidence strength are separate columns                       principle 1.2.3
--   * skin analyses can never be shared (trigger)                                 FR-19
--   * deleting a user cascades to every personal row                              FR-20
--   * only one published, non-demo knowledge version is "current" at a time


CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;
CREATE EXTENSION IF NOT EXISTS pgcrypto;  -- gen_random_uuid()

-- unaccent() is STABLE; an IMMUTABLE wrapper is needed to use it in indexes.
CREATE OR REPLACE FUNCTION f_unaccent(text) RETURNS text
  LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
  AS $$ SELECT public.unaccent('public.unaccent', $1) $$;

-- ---------------------------------------------------------------- enums
CREATE TYPE user_role          AS ENUM ('registered', 'admin');
CREATE TYPE evidence_strength  AS ENUM ('high', 'moderate', 'limited', 'insufficient', 'unknown');
CREATE TYPE confidence_level   AS ENUM ('high', 'moderate', 'low');
CREATE TYPE knowledge_status   AS ENUM ('draft', 'in_review', 'published', 'retired');
CREATE TYPE compat_status      AS ENUM ('no_notable_interaction', 'caution', 'strong_caution',
                                        'insufficient_evidence', 'data_incomplete');
CREATE TYPE rule_severity      AS ENUM ('info', 'caution', 'strong_caution');
CREATE TYPE norm_method        AS ENUM ('exact', 'alias_component', 'fuzzy', 'unresolved', 'manual');
CREATE TYPE review_status      AS ENUM ('auto_accepted', 'needs_review', 'confirmed', 'rejected');
CREATE TYPE job_status         AS ENUM ('queued', 'processing', 'completed', 'failed', 'cancelled');
CREATE TYPE skin_status        AS ENUM ('created', 'validating', 'rejected', 'queued', 'analyzing',
                                        'completed', 'failed');
CREATE TYPE share_target       AS ENUM ('comparison', 'product', 'alternative_search', 'routine', 'skin_analysis');
CREATE TYPE flag_status        AS ENUM ('open', 'resolved', 'dismissed');

-- ---------------------------------------------------------------- users & auth
CREATE TABLE users (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  email              text NOT NULL CHECK (length(email) BETWEEN 3 AND 320),
  email_lower        text GENERATED ALWAYS AS (lower(email)) STORED,
  password_hash      text NOT NULL,                     -- argon2id encoded string
  role               user_role NOT NULL DEFAULT 'registered',
  email_verified_at  timestamptz,
  age_confirmed_18   boolean NOT NULL CHECK (age_confirmed_18),
  created_at         timestamptz NOT NULL DEFAULT now(),
  updated_at         timestamptz NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX users_email_lower_uq ON users (email_lower);

CREATE TABLE profiles (
  user_id        uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  skin_type      text CHECK (skin_type IN ('dry','oily','combination','normal','sensitive','unsure')),
  preferences    jsonb NOT NULL DEFAULT '{}'::jsonb,   -- budget, avoided brands/ingredients...
  updated_at     timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE consents (
  id              bigserial PRIMARY KEY,
  user_id         uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  purpose         text NOT NULL CHECK (purpose IN ('terms', 'skin_image_processing', 'analytics')),
  policy_version  text NOT NULL,
  granted         boolean NOT NULL,
  recorded_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX consents_user_idx ON consents (user_id, purpose, recorded_at DESC);

-- Rotating refresh tokens; a reused token revokes its whole family.
CREATE TABLE refresh_tokens (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  family_id    uuid NOT NULL,
  token_hash   bytea NOT NULL UNIQUE,                 -- sha256 of the secret; secret never stored
  issued_at    timestamptz NOT NULL DEFAULT now(),
  expires_at   timestamptz NOT NULL,
  used_at      timestamptz,
  revoked_at   timestamptz
);
CREATE INDEX refresh_tokens_family_idx ON refresh_tokens (family_id);

CREATE TABLE auth_tokens (                            -- email verification / password reset
  token_hash   bytea PRIMARY KEY,
  user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  purpose      text NOT NULL CHECK (purpose IN ('verify_email', 'reset_password')),
  expires_at   timestamptz NOT NULL,
  used_at      timestamptz
);

-- ---------------------------------------------------------------- catalogue
CREATE TABLE import_runs (
  id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source        text NOT NULL,                        -- 'openbeautyfacts' | 'team_csv' | 'demo'
  licence       text NOT NULL,                        -- e.g. 'ODbL-1.0'
  started_at    timestamptz NOT NULL DEFAULT now(),
  finished_at   timestamptz,
  counts        jsonb NOT NULL DEFAULT '{}'::jsonb     -- read/skipped/inserted/updated/failed
);

CREATE TABLE brands (
  id      bigserial PRIMARY KEY,
  name    text NOT NULL,
  slug    text NOT NULL UNIQUE
);

CREATE TABLE products (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  slug             text NOT NULL UNIQUE,
  name             text NOT NULL CHECK (length(name) BETWEEN 1 AND 300),
  brand_id         bigint REFERENCES brands(id),
  category         text NOT NULL,
  category_parent  text,
  market           text,                                 -- ISO country / region where known
  image_url        text,                                 -- remote reference only, never re-hosted
  is_demo          boolean NOT NULL DEFAULT false,       -- demo records are labelled everywhere
  source           text NOT NULL,
  source_ref       text NOT NULL,
  import_run_id    uuid REFERENCES import_runs(id),
  retrieved_at     timestamptz NOT NULL,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (source, source_ref)
);
CREATE INDEX products_name_trgm ON products USING gin (f_unaccent(lower(name)) gin_trgm_ops);
CREATE INDEX products_category_idx ON products (category);
CREATE INDEX products_brand_idx ON products (brand_id);

CREATE TABLE product_identifiers (
  product_id  uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  kind        text NOT NULL CHECK (kind IN ('ean13', 'upc', 'ean8', 'other')),
  value       text NOT NULL,
  PRIMARY KEY (kind, value)
);
CREATE INDEX product_identifiers_product_idx ON product_identifiers (product_id);

CREATE TABLE product_versions (
  id                 uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id         uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  version_label      text NOT NULL,
  raw_ingredients    text,                               -- exactly as received; NULL = no list
  ingredients_hash   bytea,                              -- new version only when the text changes
  observed_at        date NOT NULL,
  market             text,
  completeness       numeric(5,4) NOT NULL CHECK (completeness BETWEEN 0 AND 1),
  verification       text NOT NULL DEFAULT 'unverified'
                     CHECK (verification IN ('unverified', 'imported', 'verified')),
  notes              text,
  source             text NOT NULL,
  source_ref         text NOT NULL,
  is_current         boolean NOT NULL DEFAULT true,
  created_at         timestamptz NOT NULL DEFAULT now(),
  UNIQUE (product_id, ingredients_hash)
);
CREATE UNIQUE INDEX product_versions_one_current ON product_versions (product_id) WHERE is_current;

CREATE TABLE ingredients (
  id                text PRIMARY KEY,                    -- canonical slug
  inci_name         text NOT NULL UNIQUE,
  function_classes  text[] NOT NULL DEFAULT '{}',        -- empty = unknown, never guessed
  considerations    text,
  is_demo           boolean NOT NULL DEFAULT false,
  source            text NOT NULL,
  reviewed_by       uuid REFERENCES users(id) ON DELETE SET NULL,
  reviewed_at       timestamptz
);
CREATE INDEX ingredients_inci_trgm ON ingredients USING gin (f_unaccent(lower(inci_name)) gin_trgm_ops);

CREATE TABLE ingredient_aliases (
  alias_key      text PRIMARY KEY,                       -- normalize_key(alias)
  ingredient_id  text NOT NULL REFERENCES ingredients(id) ON DELETE CASCADE,
  alias          text NOT NULL
);
CREATE INDEX ingredient_aliases_trgm ON ingredient_aliases USING gin (alias_key gin_trgm_ops);

CREATE TABLE product_ingredients (
  product_version_id  uuid NOT NULL REFERENCES product_versions(id) ON DELETE CASCADE,
  position            int  NOT NULL CHECK (position >= 1),
  raw_name            text NOT NULL,
  ingredient_id       text REFERENCES ingredients(id),   -- NULL = unresolved (unknown stays unknown)
  method              norm_method NOT NULL,
  confidence          numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  review_status       review_status NOT NULL,
  stated_role         text NOT NULL DEFAULT 'listed' CHECK (stated_role IN ('listed', 'may_contain')),
  concentration_pct   numeric(6,3),
  is_key_active       boolean NOT NULL DEFAULT false,
  PRIMARY KEY (product_version_id, position),
  CHECK ((ingredient_id IS NULL) = (method = 'unresolved')),
  CHECK (method <> 'unresolved' OR confidence = 0)
);
CREATE INDEX product_ingredients_ingredient_idx ON product_ingredients (ingredient_id);
CREATE INDEX product_ingredients_review_idx ON product_ingredients (review_status) WHERE review_status = 'needs_review';

CREATE TABLE price_observations (
  id            bigserial PRIMARY KEY,
  product_id    uuid NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  amount        numeric(12,2) NOT NULL CHECK (amount > 0),
  currency      char(3) NOT NULL,
  seller        text NOT NULL,
  country       text,
  source        text NOT NULL,
  available     boolean NOT NULL DEFAULT true,
  observed_at   timestamptz NOT NULL
);
CREATE INDEX price_observations_latest_idx ON price_observations (product_id, currency, observed_at DESC);

-- ---------------------------------------------------------------- knowledge
CREATE TABLE knowledge_versions (
  id             text PRIMARY KEY,
  status         knowledge_status NOT NULL DEFAULT 'draft',
  is_demo        boolean NOT NULL DEFAULT false,
  notes          text,
  created_by     uuid REFERENCES users(id) ON DELETE SET NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  published_by   uuid REFERENCES users(id) ON DELETE SET NULL,
  published_at   timestamptz,
  retired_at     timestamptz,
  CHECK (status <> 'published' OR published_at IS NOT NULL)
);
-- Exactly one current real version; the labelled demo version is kept separate.
CREATE UNIQUE INDEX knowledge_one_published_real
  ON knowledge_versions ((true)) WHERE status = 'published' AND NOT is_demo;

CREATE TABLE evidence_records (
  id                 text NOT NULL,
  knowledge_version  text NOT NULL REFERENCES knowledge_versions(id) ON DELETE CASCADE,
  claim              text NOT NULL,
  source_type        text NOT NULL CHECK (source_type IN ('regulatory','peer_reviewed','professional_guidance',
                                                          'manufacturer','expert_curated','fixture')),
  citation           text NOT NULL,
  strength           evidence_strength NOT NULL,
  publication_date   date,
  retrieved_at       date,
  reviewer           text,
  notes              text,
  PRIMARY KEY (knowledge_version, id)
);

CREATE TABLE interaction_rules (
  code                  text NOT NULL,
  knowledge_version     text NOT NULL REFERENCES knowledge_versions(id) ON DELETE CASCADE,
  interaction_type      text NOT NULL,
  severity              rule_severity NOT NULL,
  side_a                jsonb NOT NULL,
  side_b                jsonb NOT NULL,
  mechanism_summary     text NOT NULL,
  practical_guidance    text NOT NULL,
  explanation_template  text NOT NULL,
  review_status         text NOT NULL DEFAULT 'reviewed',
  last_reviewed         date,
  PRIMARY KEY (knowledge_version, code)
);

CREATE TABLE rule_evidence (
  knowledge_version  text NOT NULL,
  rule_code          text NOT NULL,
  evidence_id        text NOT NULL,
  PRIMARY KEY (knowledge_version, rule_code, evidence_id),
  FOREIGN KEY (knowledge_version, rule_code) REFERENCES interaction_rules(knowledge_version, code) ON DELETE CASCADE,
  FOREIGN KEY (knowledge_version, evidence_id) REFERENCES evidence_records(knowledge_version, id) ON DELETE CASCADE
);

CREATE TABLE concern_mappings (
  knowledge_version   text NOT NULL REFERENCES knowledge_versions(id) ON DELETE CASCADE,
  observation         text NOT NULL,
  concern_category    text NOT NULL,
  ingredient_classes  text[] NOT NULL CHECK (cardinality(ingredient_classes) >= 1),
  intended_role       text NOT NULL,
  evidence_ids        text[] NOT NULL CHECK (cardinality(evidence_ids) >= 1),
  PRIMARY KEY (knowledge_version, observation, concern_category)
);

-- A version cannot be published while any rule lacks evidence (SC-05, UC12).
CREATE OR REPLACE FUNCTION knowledge_publish_guard() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.status = 'published' AND OLD.status IS DISTINCT FROM 'published' THEN
    IF EXISTS (
      SELECT 1 FROM interaction_rules r
      WHERE r.knowledge_version = NEW.id
        AND NOT EXISTS (SELECT 1 FROM rule_evidence e
                        WHERE e.knowledge_version = r.knowledge_version AND e.rule_code = r.code)
    ) THEN
      RAISE EXCEPTION 'PUBLISH_BLOCKED: rule without evidence in %', NEW.id USING ERRCODE = 'check_violation';
    END IF;
    IF NOT NEW.is_demo AND EXISTS (
      SELECT 1 FROM evidence_records WHERE knowledge_version = NEW.id AND source_type = 'fixture'
    ) THEN
      RAISE EXCEPTION 'PUBLISH_BLOCKED: fixture evidence in non-demo version %', NEW.id USING ERRCODE = 'check_violation';
    END IF;
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER knowledge_publish_guard BEFORE UPDATE OF status ON knowledge_versions
  FOR EACH ROW EXECUTE FUNCTION knowledge_publish_guard();

-- Published knowledge is immutable: change it by publishing a new version.
CREATE OR REPLACE FUNCTION knowledge_immutable_guard() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE kv text := COALESCE(NEW.knowledge_version, OLD.knowledge_version);
BEGIN
  IF EXISTS (SELECT 1 FROM knowledge_versions WHERE id = kv AND status IN ('published', 'retired')) THEN
    RAISE EXCEPTION 'KNOWLEDGE_IMMUTABLE: % is published or retired', kv USING ERRCODE = 'check_violation';
  END IF;
  RETURN COALESCE(NEW, OLD);
END $$;
CREATE TRIGGER rules_immutable BEFORE INSERT OR UPDATE OR DELETE ON interaction_rules
  FOR EACH ROW EXECUTE FUNCTION knowledge_immutable_guard();
CREATE TRIGGER evidence_immutable BEFORE INSERT OR UPDATE OR DELETE ON evidence_records
  FOR EACH ROW EXECUTE FUNCTION knowledge_immutable_guard();
CREATE TRIGGER rule_evidence_immutable BEFORE INSERT OR UPDATE OR DELETE ON rule_evidence
  FOR EACH ROW EXECUTE FUNCTION knowledge_immutable_guard();
CREATE TRIGGER concern_mappings_immutable BEFORE INSERT OR UPDATE OR DELETE ON concern_mappings
  FOR EACH ROW EXECUTE FUNCTION knowledge_immutable_guard();

-- ---------------------------------------------------------------- results
CREATE TABLE comparisons (
  id                    uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id               uuid REFERENCES users(id) ON DELETE CASCADE,   -- NULL = guest, unsaved
  product_version_a     uuid NOT NULL REFERENCES product_versions(id),
  product_version_b     uuid NOT NULL REFERENCES product_versions(id),
  knowledge_version     text NOT NULL REFERENCES knowledge_versions(id),
  engine_version        text NOT NULL,
  status                compat_status NOT NULL,
  confidence            numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  evidence_strength     evidence_strength NOT NULL,
  completeness          numeric(5,4) NOT NULL CHECK (completeness BETWEEN 0 AND 1),
  result                jsonb NOT NULL,                                -- canonical engine output
  saved                 boolean NOT NULL DEFAULT false,
  created_at            timestamptz NOT NULL DEFAULT now(),
  CHECK (NOT saved OR user_id IS NOT NULL)
);
CREATE INDEX comparisons_user_idx ON comparisons (user_id, created_at DESC) WHERE user_id IS NOT NULL;
CREATE INDEX comparisons_cache_idx ON comparisons (product_version_a, product_version_b, knowledge_version, engine_version);

CREATE TABLE comparison_findings (
  comparison_id      uuid NOT NULL REFERENCES comparisons(id) ON DELETE CASCADE,
  ordinal            int  NOT NULL,
  type               text NOT NULL,
  severity           rule_severity NOT NULL,
  rule_code          text,
  confidence         numeric(5,4) NOT NULL,
  evidence_strength  evidence_strength NOT NULL,
  explanation        text NOT NULL,
  PRIMARY KEY (comparison_id, ordinal)
);

CREATE TABLE uploads (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id        uuid REFERENCES users(id) ON DELETE CASCADE,
  purpose        text NOT NULL CHECK (purpose IN ('skin_image', 'label_image')),
  object_key     text NOT NULL UNIQUE,         -- random key in a private bucket; never user-supplied
  sha256         text NOT NULL,
  byte_size      int NOT NULL CHECK (byte_size > 0),
  encrypted      boolean NOT NULL,
  created_at     timestamptz NOT NULL DEFAULT now(),
  delete_after   timestamptz NOT NULL,          -- retention: enforced by the cleanup job
  CHECK (purpose <> 'skin_image' OR encrypted)
);
CREATE INDEX uploads_retention_idx ON uploads (delete_after);

CREATE TABLE skin_analyses (
  id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id         uuid REFERENCES users(id) ON DELETE CASCADE,
  guest_token_hash bytea,                        -- lets a guest poll their own job, nothing else
  upload_id       uuid REFERENCES uploads(id) ON DELETE SET NULL,
  skin_type       text NOT NULL,
  status          skin_status NOT NULL DEFAULT 'created',
  rejection_code  text,
  model_version   text,
  is_demo_model   boolean,
  knowledge_version text REFERENCES knowledge_versions(id),
  result          jsonb,
  consent_id      bigint REFERENCES consents(id) ON DELETE SET NULL,
  created_at      timestamptz NOT NULL DEFAULT now(),
  completed_at    timestamptz,
  CHECK (user_id IS NOT NULL OR guest_token_hash IS NOT NULL),
  CHECK (status <> 'completed' OR (model_version IS NOT NULL AND is_demo_model IS NOT NULL))
);
CREATE INDEX skin_analyses_user_idx ON skin_analyses (user_id, created_at DESC);

CREATE TABLE skin_observations (
  analysis_id     uuid NOT NULL REFERENCES skin_analyses(id) ON DELETE CASCADE,
  characteristic  text NOT NULL,
  confidence      numeric(5,4) NOT NULL CHECK (confidence BETWEEN 0 AND 1),
  severity        text NOT NULL,
  PRIMARY KEY (analysis_id, characteristic)
);

CREATE TABLE recommendations (
  analysis_id             uuid NOT NULL REFERENCES skin_analyses(id) ON DELETE CASCADE,
  rank                    int NOT NULL,
  observation             text NOT NULL,
  concern_category        text NOT NULL,
  product_id              uuid REFERENCES products(id) ON DELETE SET NULL,
  observation_confidence  numeric(5,4) NOT NULL,
  evidence_strength       evidence_strength NOT NULL,
  rationale               text NOT NULL,
  PRIMARY KEY (analysis_id, rank)
);

CREATE TABLE alternative_searches (
  id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id             uuid REFERENCES users(id) ON DELETE CASCADE,
  reference_product   uuid NOT NULL REFERENCES products(id),
  reference_version   uuid NOT NULL REFERENCES product_versions(id),
  mode                text NOT NULL CHECK (mode IN ('similar','cheaper','premium','ingredient_focused',
                                                    'routine_compatible','sensitive_preference')),
  constraints         jsonb NOT NULL DEFAULT '{}'::jsonb,
  result              jsonb NOT NULL,
  saved               boolean NOT NULL DEFAULT false,
  created_at          timestamptz NOT NULL DEFAULT now(),
  CHECK (NOT saved OR user_id IS NOT NULL)
);

CREATE TABLE product_alternatives (
  search_id    uuid NOT NULL REFERENCES alternative_searches(id) ON DELETE CASCADE,
  rank         int NOT NULL,
  product_id   uuid NOT NULL REFERENCES products(id),
  score        numeric(6,4) NOT NULL,
  dimensions   jsonb NOT NULL,
  PRIMARY KEY (search_id, rank)
);

-- ---------------------------------------------------------------- shelf & routines
CREATE TABLE shelf_items (
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id  uuid NOT NULL REFERENCES products(id),
  status      text NOT NULL DEFAULT 'owned' CHECK (status IN ('owned', 'wishlist')),
  note        text CHECK (length(note) <= 1000),
  added_at    timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, product_id)                  -- duplicates rejected by the database
);

CREATE TABLE routines (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name         text NOT NULL CHECK (length(name) BETWEEN 1 AND 120),
  time_of_day  text NOT NULL CHECK (time_of_day IN ('morning', 'evening')),
  is_active    boolean NOT NULL DEFAULT true,
  created_at   timestamptz NOT NULL DEFAULT now(),
  updated_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX routines_user_idx ON routines (user_id);

CREATE TABLE routine_items (
  routine_id   uuid NOT NULL REFERENCES routines(id) ON DELETE CASCADE,
  step_order   int  NOT NULL CHECK (step_order >= 1),
  product_id   uuid NOT NULL REFERENCES products(id),
  step_kind    text,                                 -- cleanser / treatment / serum / ...
  frequency    text CHECK (length(frequency) <= 60),
  note         text CHECK (length(note) <= 1000),
  PRIMARY KEY (routine_id, step_order) DEFERRABLE INITIALLY DEFERRED   -- reorder in one transaction
);

-- ---------------------------------------------------------------- OCR, jobs
CREATE TABLE ocr_results (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  upload_id        uuid REFERENCES uploads(id) ON DELETE SET NULL,
  user_id          uuid REFERENCES users(id) ON DELETE CASCADE,
  raw_text         text NOT NULL,
  mean_confidence  numeric(5,2) NOT NULL,
  engine           text NOT NULL,
  status           text NOT NULL CHECK (status IN ('pending_review', 'auto_extracted', 'confirmed', 'rejected')),
  corrected_text   text,
  created_at       timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE jobs (
  id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  type           text NOT NULL CHECK (type IN ('skin_analysis', 'ocr', 'obf_import', 'retention_cleanup')),
  user_id        uuid REFERENCES users(id) ON DELETE CASCADE,
  target_id      uuid,
  status         job_status NOT NULL DEFAULT 'queued',
  idempotency_key text UNIQUE,
  retry_count    int NOT NULL DEFAULT 0 CHECK (retry_count <= 5),
  error_code     text,
  progress       smallint NOT NULL DEFAULT 0 CHECK (progress BETWEEN 0 AND 100),
  created_at     timestamptz NOT NULL DEFAULT now(),
  started_at     timestamptz,
  completed_at   timestamptz
);
CREATE INDEX jobs_status_idx ON jobs (status, created_at) WHERE status IN ('queued', 'processing');

-- ---------------------------------------------------------------- sharing
CREATE TABLE shares (
  token_hash   bytea PRIMARY KEY,                    -- sha256 of the URL token
  user_id      uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  target_type  share_target NOT NULL,
  target_id    uuid NOT NULL,
  created_at   timestamptz NOT NULL DEFAULT now(),
  revoked_at   timestamptz
);
CREATE INDEX shares_user_idx ON shares (user_id);

-- Skin analyses are private by default and cannot be shared through the ordinary path (FR-19).
CREATE OR REPLACE FUNCTION shares_no_skin() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.target_type = 'skin_analysis' THEN
    RAISE EXCEPTION 'SHARE_REFUSED: skin analyses are private' USING ERRCODE = 'check_violation';
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER shares_no_skin BEFORE INSERT OR UPDATE ON shares FOR EACH ROW EXECUTE FUNCTION shares_no_skin();

-- ---------------------------------------------------------------- governance & analytics
CREATE TABLE data_quality_flags (
  id            bigserial PRIMARY KEY,
  target_type   text NOT NULL CHECK (target_type IN ('product', 'product_version', 'ingredient',
                                                     'product_ingredient', 'ocr_result', 'price', 'evidence')),
  target_ref    text NOT NULL,
  reason        text NOT NULL CHECK (reason IN ('missing_ingredient_list', 'unknown_ingredient', 'fuzzy_match',
                                                'duplicate_product', 'stale_price', 'low_ocr_confidence',
                                                'conflicting_evidence', 'missing_evidence', 'user_report',
                                                'incomplete_source')),
  source        text NOT NULL,                       -- who/what raised it
  details       jsonb NOT NULL DEFAULT '{}'::jsonb,
  status        flag_status NOT NULL DEFAULT 'open',
  raised_by     uuid REFERENCES users(id) ON DELETE SET NULL,
  resolved_by   uuid REFERENCES users(id) ON DELETE SET NULL,
  created_at    timestamptz NOT NULL DEFAULT now(),
  resolved_at   timestamptz
);
CREATE INDEX dq_flags_open_idx ON data_quality_flags (status, created_at) WHERE status = 'open';

CREATE TABLE audit_log (
  id           bigserial PRIMARY KEY,
  actor_id     uuid,                                 -- kept (not FK) so history survives deletion
  action       text NOT NULL,
  target       text,
  old_value    jsonb,
  new_value    jsonb,
  reason       text,
  request_id   text,
  occurred_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX audit_log_time_idx ON audit_log (occurred_at DESC);

-- Append-only audit log.
CREATE OR REPLACE FUNCTION audit_append_only() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'AUDIT_APPEND_ONLY' USING ERRCODE = 'check_violation'; END $$;
CREATE TRIGGER audit_no_update BEFORE UPDATE OR DELETE ON audit_log FOR EACH ROW EXECUTE FUNCTION audit_append_only();

CREATE TABLE analytics_events (                      -- funnel events only; no PII, no skin data
  id           bigserial PRIMARY KEY,
  name         text NOT NULL CHECK (name ~ '^[a-z_]{3,60}$'),
  session_id   text,                                  -- random, non-identifying
  route        text,
  metadata     jsonb NOT NULL DEFAULT '{}'::jsonb CHECK (pg_column_size(metadata) < 2048),
  occurred_at  timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX analytics_events_name_time ON analytics_events (name, occurred_at);

