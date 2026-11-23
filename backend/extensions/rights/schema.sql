CREATE TABLE IF NOT EXISTS recording_use_grants (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  reel text NOT NULL REFERENCES acetate_reels(code),
  instrument_ref text NOT NULL UNIQUE,
  access_scope text NOT NULL CHECK(access_scope IN ('internal','partner','public')),
  begins date NOT NULL, expires date NOT NULL,
  credit_line text NOT NULL, documented_by text NOT NULL,
  stage text NOT NULL DEFAULT 'draft' CHECK(stage IN ('draft','approved','revoked')),
  approved_by text, revoked_by text, revoke_note text,
  CHECK (expires >= begins),
  CHECK ((stage IN ('approved','revoked')) = (approved_by IS NOT NULL)),
  CHECK ((stage='revoked') = (revoked_by IS NOT NULL) AND (revoked_by IS NULL) = (revoke_note IS NULL))
);
CREATE INDEX IF NOT EXISTS grants_by_recording ON recording_use_grants(reel,access_scope,stage);
