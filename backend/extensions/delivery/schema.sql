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
  stage text NOT NULL DEFAULT 'prepared',
  released_at timestamptz, released_by text, receipt_ref text UNIQUE, received_at timestamptz,
  recalled_at timestamptz, returned_at timestamptz,
  reissue_of bigint REFERENCES recording_handoffs(id),
  CONSTRAINT handoff_stage_values CHECK(stage IN ('prepared','sent','recalling','acknowledged','returned','withdrawn')),
  CONSTRAINT handoff_release_pair CHECK ((released_at IS NULL) = (released_by IS NULL)),
  CONSTRAINT handoff_release_stage CHECK ((stage IN ('sent','recalling','acknowledged','returned')) = (released_at IS NOT NULL)),
  CONSTRAINT handoff_ack_receipt CHECK ((stage<>'acknowledged' OR receipt_ref IS NOT NULL) AND (receipt_ref IS NULL) = (received_at IS NULL)),
  CONSTRAINT handoff_return_trail CHECK ((stage='returned') = (returned_at IS NOT NULL) AND (returned_at IS NULL OR recalled_at IS NOT NULL))
);
-- 既有库的幂等迁移：补列、换约束、换部分索引
ALTER TABLE recording_handoffs ADD COLUMN IF NOT EXISTS recalled_at timestamptz;
ALTER TABLE recording_handoffs ADD COLUMN IF NOT EXISTS returned_at timestamptz;
ALTER TABLE recording_handoffs ADD COLUMN IF NOT EXISTS reissue_of bigint REFERENCES recording_handoffs(id);
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS recording_handoffs_stage_check;
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS recording_handoffs_check;
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS recording_handoffs_check1;
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS recording_handoffs_check2;
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS handoff_stage_values;
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS handoff_release_pair;
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS handoff_release_stage;
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS handoff_ack_receipt;
ALTER TABLE recording_handoffs DROP CONSTRAINT IF EXISTS handoff_return_trail;
ALTER TABLE recording_handoffs ADD CONSTRAINT handoff_stage_values CHECK(stage IN ('prepared','sent','recalling','acknowledged','returned','withdrawn'));
ALTER TABLE recording_handoffs ADD CONSTRAINT handoff_release_pair CHECK ((released_at IS NULL) = (released_by IS NULL));
ALTER TABLE recording_handoffs ADD CONSTRAINT handoff_release_stage CHECK ((stage IN ('sent','recalling','acknowledged','returned')) = (released_at IS NOT NULL));
ALTER TABLE recording_handoffs ADD CONSTRAINT handoff_ack_receipt CHECK ((stage<>'acknowledged' OR receipt_ref IS NOT NULL) AND (receipt_ref IS NULL) = (received_at IS NULL));
ALTER TABLE recording_handoffs ADD CONSTRAINT handoff_return_trail CHECK ((stage='returned') = (returned_at IS NOT NULL) AND (returned_at IS NULL OR recalled_at IS NOT NULL));
DROP INDEX IF EXISTS handoff_active_copy;
-- 在途与已交付的清单占用副本；已退回、已撤单后可重新建档
CREATE UNIQUE INDEX handoff_active_copy ON recording_handoffs(derivative,partner) WHERE stage IN ('prepared','sent','recalling','acknowledged');
-- 每张退回清单只允许开立一张补发单
CREATE UNIQUE INDEX IF NOT EXISTS handoff_reissue_once ON recording_handoffs(reissue_of) WHERE reissue_of IS NOT NULL;
-- 伙伴离线回执事实表：签收与退回两条事实都保留，receipt_ref 幂等
CREATE TABLE IF NOT EXISTS handoff_receipts (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  handoff bigint NOT NULL REFERENCES recording_handoffs(id),
  kind text NOT NULL CHECK(kind IN ('acknowledgement','return')),
  receipt_ref text NOT NULL UNIQUE,
  verified_digest text NOT NULL,
  signed_at timestamptz NOT NULL,
  recorded_by text NOT NULL,
  recorded_at timestamptz NOT NULL DEFAULT now(),
  disputed bool NOT NULL DEFAULT false,
  dispute_note text,
  CHECK (disputed = (dispute_note IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS receipts_by_handoff ON handoff_receipts(handoff,id);
