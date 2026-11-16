-- Users may explicitly keep their skin photo; default is delete-after-analysis (NFR-08).
ALTER TABLE skin_analyses ADD COLUMN keep_image boolean NOT NULL DEFAULT false;
-- Guests poll their own label scan with a token; only its hash is stored.
ALTER TABLE ocr_results ADD COLUMN guest_token_hash bytea;
