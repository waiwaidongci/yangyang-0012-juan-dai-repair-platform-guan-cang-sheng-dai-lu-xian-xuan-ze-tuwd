CREATE TABLE IF NOT EXISTS archive_exchange_partners (
  slug text PRIMARY KEY,name text NOT NULL, supports_access_copy bool NOT NULL
);
CREATE TABLE IF NOT EXISTS recording_handoffs (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  derivative bigint NOT NULL REFERENCES audio_derivative_checks(id),
  grant_id bigint NOT NULL REFERENCES recording_use_grants(id),
  partner text NOT NULL REFERENCES archive_exchange_partners(slug),
  purpose text NOT NULL, created_by text NOT NULL,
  seal_digest text NOT NULL, credit_text text NOT NULL,
  stage text NOT NULL DEFAULT 'prepared' CHECK(stage IN ('prepared','sent','acknowledged','withdrawn')),
  released_at timestamptz, released_by text, receipt_ref text UNIQUE, received_at timestamptz,
  CHECK ((released_at IS NULL) = (released_by IS NULL)),
  CHECK ((stage IN ('sent','acknowledged')) = (released_at IS NOT NULL)),
  CHECK ((stage='acknowledged') = (receipt_ref IS NOT NULL) AND (receipt_ref IS NULL) = (received_at IS NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS handoff_active_copy ON recording_handoffs(derivative,partner) WHERE stage<>'withdrawn';
