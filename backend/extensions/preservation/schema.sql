CREATE TABLE IF NOT EXISTS reel_capture_profiles (
  reel text PRIMARY KEY REFERENCES acetate_reels(code),
  target_seconds numeric NOT NULL CHECK(target_seconds > 0),
  target_channels smallint NOT NULL CHECK(target_channels IN (1,2))
);
CREATE TABLE IF NOT EXISTS audio_derivative_checks (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  card bigint NOT NULL REFERENCES conservation_cards(id),
  kind text NOT NULL CHECK(kind IN ('master','access')),
  filename text NOT NULL, expected_digest text NOT NULL, measured_digest text NOT NULL,
  duration_seconds numeric NOT NULL CHECK(duration_seconds > 0),
  sample_rate integer NOT NULL CHECK(sample_rate > 0),
  channels smallint NOT NULL CHECK(channels IN (1,2)),
  clipped_frames integer NOT NULL CHECK(clipped_frames >= 0),
  recorded_by text NOT NULL,
  stage text NOT NULL DEFAULT 'queued' CHECK(stage IN ('queued','accepted','failed')),
  review_by text, failed_rules text[] NOT NULL DEFAULT '{}',
  UNIQUE(card,filename),
  CHECK ((stage='queued') = (review_by IS NULL)),
  CHECK ((stage='failed') = (cardinality(failed_rules) > 0))
);
