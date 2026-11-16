-- Database-level integrity tests. Each block must raise or pass as stated.
-- Runs inside one transaction that is rolled back.
\set ON_ERROR_STOP 1
BEGIN;

CREATE FUNCTION pg_temp.expect_error(stmt text, needle text) RETURNS void LANGUAGE plpgsql AS $$
BEGIN
  EXECUTE stmt;
  RAISE EXCEPTION 'EXPECTED ERROR NOT RAISED (%): %', needle, stmt;
EXCEPTION WHEN OTHERS THEN
  IF SQLERRM LIKE 'EXPECTED ERROR NOT RAISED%' THEN RAISE; END IF;
  IF position(needle IN SQLERRM) = 0 THEN
    RAISE EXCEPTION 'wrong error for %: got "%", wanted "%"', stmt, SQLERRM, needle;
  END IF;
END $$;

-- fixtures
INSERT INTO users (id, email, password_hash, age_confirmed_18)
VALUES ('00000000-0000-0000-0000-00000000000a', 'A@Example.com', 'x', true),
       ('00000000-0000-0000-0000-00000000000b', 'b@example.com', 'x', true);
INSERT INTO import_runs (id, source, licence) VALUES ('00000000-0000-0000-0000-0000000000f1', 'demo', 'n/a');
INSERT INTO products (id, slug, name, category, source, source_ref, retrieved_at, is_demo)
VALUES ('00000000-0000-0000-0000-000000000001', 'demo-serum', 'Démo Glow Serum', 'serum', 'demo', 'd1', now(), true);
INSERT INTO product_versions (id, product_id, version_label, raw_ingredients, ingredients_hash, observed_at,
                              completeness, source, source_ref)
VALUES ('00000000-0000-0000-0000-0000000000a1', '00000000-0000-0000-0000-000000000001', 'v1', 'x', '\x01',
        current_date, 1, 'demo', 'd1');
INSERT INTO ingredients (id, inci_name, source) VALUES ('test-a', 'TEST_A', 'fixture');

-- T1 email uniqueness is case-insensitive
SELECT pg_temp.expect_error($$INSERT INTO users (email, password_hash, age_confirmed_18) VALUES ('a@example.com','x',true)$$,
                            'users_email_lower_uq');
-- T2 18+ confirmation is required
SELECT pg_temp.expect_error($$INSERT INTO users (email, password_hash, age_confirmed_18) VALUES ('c@x.com','x',false)$$,
                            'check constraint');
-- T3 unresolved ingredient must have no canonical id and zero confidence (unknown stays unknown)
SELECT pg_temp.expect_error($$INSERT INTO product_ingredients (product_version_id, position, raw_name, ingredient_id, method, confidence, review_status)
  VALUES ('00000000-0000-0000-0000-0000000000a1', 1, 'mystery', 'test-a', 'unresolved', 0, 'needs_review')$$, 'check constraint');
SELECT pg_temp.expect_error($$INSERT INTO product_ingredients (product_version_id, position, raw_name, ingredient_id, method, confidence, review_status)
  VALUES ('00000000-0000-0000-0000-0000000000a1', 1, 'mystery', NULL, 'unresolved', 0.4, 'needs_review')$$, 'check constraint');
INSERT INTO product_ingredients (product_version_id, position, raw_name, ingredient_id, method, confidence, review_status)
  VALUES ('00000000-0000-0000-0000-0000000000a1', 1, 'mystery', NULL, 'unresolved', 0, 'needs_review');
-- T4 only one current version per product
SELECT pg_temp.expect_error($$INSERT INTO product_versions (product_id, version_label, ingredients_hash, observed_at, completeness, source, source_ref)
  VALUES ('00000000-0000-0000-0000-000000000001','v2','\x02',current_date,1,'demo','d1')$$, 'product_versions_one_current');
-- T5 shelf duplicates rejected
INSERT INTO shelf_items (user_id, product_id) VALUES ('00000000-0000-0000-0000-00000000000a', '00000000-0000-0000-0000-000000000001');
SELECT pg_temp.expect_error($$INSERT INTO shelf_items (user_id, product_id) VALUES ('00000000-0000-0000-0000-00000000000a','00000000-0000-0000-0000-000000000001')$$,
                            'shelf_items_pkey');
-- T6 skin analyses cannot be shared
SELECT pg_temp.expect_error($$INSERT INTO shares (token_hash, user_id, target_type, target_id)
  VALUES ('\xaa', '00000000-0000-0000-0000-00000000000a', 'skin_analysis', gen_random_uuid())$$, 'SHARE_REFUSED');
-- T7 skin uploads must be encrypted
SELECT pg_temp.expect_error($$INSERT INTO uploads (purpose, object_key, sha256, byte_size, encrypted, delete_after)
  VALUES ('skin_image','k1','h',10,false, now())$$, 'check constraint');
-- T8 knowledge: cannot publish a rule without evidence; cannot publish fixture evidence as real
INSERT INTO knowledge_versions (id) VALUES ('kv-test');
INSERT INTO interaction_rules (code, knowledge_version, interaction_type, severity, side_a, side_b,
  mechanism_summary, practical_guidance, explanation_template)
  VALUES ('R1','kv-test','redundancy','caution','[]','[]','m','g','t');
SELECT pg_temp.expect_error($$UPDATE knowledge_versions SET status='published', published_at=now() WHERE id='kv-test'$$,
                            'PUBLISH_BLOCKED: rule without evidence');
INSERT INTO evidence_records (id, knowledge_version, claim, source_type, citation, strength)
  VALUES ('E1','kv-test','c','fixture','FIXTURE','moderate');
INSERT INTO rule_evidence VALUES ('kv-test','R1','E1');
SELECT pg_temp.expect_error($$UPDATE knowledge_versions SET status='published', published_at=now() WHERE id='kv-test'$$,
                            'PUBLISH_BLOCKED: fixture evidence');
-- T9 published knowledge is immutable; only one real version may be published
INSERT INTO knowledge_versions (id) VALUES ('kv-real');
UPDATE knowledge_versions SET status='published', published_at=now() WHERE id='kv-real';
SELECT pg_temp.expect_error($$INSERT INTO interaction_rules (code, knowledge_version, interaction_type, severity, side_a, side_b,
  mechanism_summary, practical_guidance, explanation_template) VALUES ('R2','kv-real','redundancy','caution','[]','[]','m','g','t')$$,
  'KNOWLEDGE_IMMUTABLE');
SELECT pg_temp.expect_error($$INSERT INTO concern_mappings VALUES ('kv-real','visible_shine','c','{x}','r','{E1}')$$,
                            'KNOWLEDGE_IMMUTABLE');
INSERT INTO knowledge_versions (id) VALUES ('kv-real-2');
SELECT pg_temp.expect_error($$UPDATE knowledge_versions SET status='published', published_at=now() WHERE id='kv-real-2'$$,
                            'knowledge_one_published_real');
-- T10 a guest comparison cannot be marked saved
SELECT pg_temp.expect_error($$INSERT INTO comparisons (product_version_a, product_version_b, knowledge_version, engine_version,
  status, confidence, evidence_strength, completeness, result, saved)
  VALUES ('00000000-0000-0000-0000-0000000000a1','00000000-0000-0000-0000-0000000000a1','kv-real','e',
          'data_incomplete',0,'unknown',0,'{}',true)$$, 'check constraint');
-- T11 audit log is append-only
INSERT INTO audit_log (action) VALUES ('test');
SELECT pg_temp.expect_error($$DELETE FROM audit_log$$, 'AUDIT_APPEND_ONLY');
-- T12 typo-tolerant, accent-insensitive product search uses the trigram index
DO $$ BEGIN
  IF NOT EXISTS (SELECT 1 FROM products WHERE f_unaccent(lower(name)) % f_unaccent(lower('demo glw serum'))) THEN
    RAISE EXCEPTION 'trigram search did not match a misspelled query';
  END IF;
END $$;
-- T13 FR-20: deleting a user removes every personal row
INSERT INTO routines (id, user_id, name, time_of_day) VALUES (gen_random_uuid(), '00000000-0000-0000-0000-00000000000a', 'AM', 'morning');
INSERT INTO consents (user_id, purpose, policy_version, granted) VALUES ('00000000-0000-0000-0000-00000000000a','terms','1',true);
DELETE FROM users WHERE id = '00000000-0000-0000-0000-00000000000a';
DO $$ BEGIN
  IF EXISTS (SELECT 1 FROM shelf_items WHERE user_id = '00000000-0000-0000-0000-00000000000a')
     OR EXISTS (SELECT 1 FROM routines WHERE user_id = '00000000-0000-0000-0000-00000000000a')
     OR EXISTS (SELECT 1 FROM consents WHERE user_id = '00000000-0000-0000-0000-00000000000a') THEN
    RAISE EXCEPTION 'personal rows survived account deletion';
  END IF;
END $$;

SELECT 'ALL SCHEMA TESTS PASSED';
ROLLBACK;
