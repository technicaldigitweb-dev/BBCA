-- ============================================================================
-- Buy Box Check Automation - history schema PROPOSAL
--
-- STATUS: NOT APPLIED. This file has not been executed against any database.
-- Running it requires the `history_write_approved` gate plus DBA action, and a
-- decision on which database it belongs in (see "Placement" below).
--
-- Until then all history is written to local SQLite (automation/state/buy_box_history.db),
-- which carries the same logical schema.
-- ============================================================================

-- Placement ------------------------------------------------------------------
-- Candidates considered:
--   ledsone            read-only for this project (tech_user); warehouse, not app state
--   ph_dashboard       holds the PH Dashboard app's own tables; reachable here only
--                      through the read-only MCP tool, so no write path exists today
-- Recommendation: a dedicated `buy_box` schema in ph_dashboard, because the ASIN spine
-- and the existing scheduler/run-log tables already live there. Needs owner approval.

CREATE SCHEMA IF NOT EXISTS buy_box;

-- One row per execution -------------------------------------------------------
CREATE TABLE IF NOT EXISTS buy_box.check_run (
    run_id              text        PRIMARY KEY,
    mode                text        NOT NULL
                                    CHECK (mode IN ('full_daily','manual_single','manual_full')),
    source              text,
    started_at          timestamptz NOT NULL,
    finished_at         timestamptz,
    status              text        NOT NULL
                                    CHECK (status IN ('running','completed',
                                                      'completed_with_errors','failed')),
    total_eligible      integer     NOT NULL DEFAULT 0,
    checked             integer     NOT NULL DEFAULT 0,
    buy_box_yes         integer     NOT NULL DEFAULT 0,
    buy_box_no          integer     NOT NULL DEFAULT 0,
    not_verified        integer     NOT NULL DEFAULT 0,
    check_error         integer     NOT NULL DEFAULT 0,
    reason_unknown      integer     NOT NULL DEFAULT 0,
    failed_requests     integer     NOT NULL DEFAULT 0,
    skipped             integer     NOT NULL DEFAULT 0,
    detail              text
);

-- One row per checked record per run -----------------------------------------
-- The PK is what makes a re-run idempotent: re-running the SAME run_id upserts,
-- while a NEW run_id always adds rows, which is what preserves daily history.
CREATE TABLE IF NOT EXISTS buy_box.check_history (
    run_id              text        NOT NULL REFERENCES buy_box.check_run(run_id)
                                    ON DELETE CASCADE,
    asin                text        NOT NULL,
    sku                 text,
    seller_account      text        NOT NULL,
    seller_id           text,
    marketplace         text        NOT NULL,
    buy_box_status      text        NOT NULL
                                    CHECK (buy_box_status IN ('YES','NO',
                                                              'NOT VERIFIED','CHECK ERROR')),
    official_reason     text,
    possible_reason     jsonb       NOT NULL DEFAULT '[]'::jsonb,
    stock_quantity      integer,
    listing_status      text,
    evidence_source     text,
    -- three DISTINCT timestamps; never substitute one for another
    source_observed_at  timestamptz,    -- when the source observed the fact
    checked_at          timestamptz,    -- when this run executed the check
    live_verified_at    timestamptz,    -- only set for genuinely live verification
    error_code          text,
    verification_status text            CHECK (verification_status IN
                                               ('historical','live','unavailable','error')),
    detail              text,
    PRIMARY KEY (run_id, asin, seller_account, marketplace)
);

CREATE INDEX IF NOT EXISTS ix_bbh_grain   ON buy_box.check_history (asin, seller_account, marketplace);
CREATE INDEX IF NOT EXISTS ix_bbh_checked ON buy_box.check_history (checked_at DESC);
CREATE INDEX IF NOT EXISTS ix_bbh_status  ON buy_box.check_history (buy_box_status)
                                            WHERE buy_box_status = 'NO';

-- Alert de-duplication --------------------------------------------------------
CREATE TABLE IF NOT EXISTS buy_box.alert_sent (
    alert_key       text        PRIMARY KEY,
    run_id          text        REFERENCES buy_box.check_run(run_id) ON DELETE CASCADE,
    asin            text        NOT NULL,
    seller_account  text        NOT NULL,
    marketplace     text        NOT NULL,
    channel         text,
    dry_run         boolean     NOT NULL DEFAULT true,
    sent_at         timestamptz NOT NULL DEFAULT now(),
    payload         jsonb
);

-- Convenience view: newest result per grain ----------------------------------
CREATE OR REPLACE VIEW buy_box.latest_result AS
SELECT DISTINCT ON (asin, seller_account, marketplace) *
FROM buy_box.check_history
ORDER BY asin, seller_account, marketplace, checked_at DESC;

-- Rollback --------------------------------------------------------------------
-- DROP VIEW  IF EXISTS buy_box.latest_result;
-- DROP TABLE IF EXISTS buy_box.alert_sent;
-- DROP TABLE IF EXISTS buy_box.check_history;
-- DROP TABLE IF EXISTS buy_box.check_run;
-- DROP SCHEMA IF EXISTS buy_box;
