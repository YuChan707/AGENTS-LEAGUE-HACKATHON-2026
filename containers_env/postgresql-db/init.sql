-- ============================================================================
-- OnLooker schema for Azure Database for PostgreSQL / Supabase.
--
-- One table per persisted entity. Rich/nested structures are stored as JSONB;
-- the keys you actually filter/join on are typed columns with indexes.
--
-- IDEMPOTENT: every statement uses IF NOT EXISTS, so it is safe to run this
-- file as many times as you want (deploys, re-runs) without errors.
--
-- Apply it to Azure/Supabase with:
--     python containers_env/postgresql-db/apply_schema.py
-- (reads DATABASE_POOL_URL / DATABASE_URL from the environment).
--
-- NOTE on Dapr: the Dapr state-store components (*/components/statestore.yaml)
-- auto-create their OWN key/value tables (ingestor_locations,
-- processor_audience_specs, backend_sessions). Those are a generic key->JSON
-- cache. The tables below are the QUERYABLE, per-entity relational storage.
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;   -- provides gen_random_uuid()

-- ============================================================================
-- RAW DATA (data_ingestor) — real US Census stats per New York zip_code
-- ============================================================================
CREATE TABLE IF NOT EXISTS locations (
    location_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    zip_code          text UNIQUE,
    country           text NOT NULL DEFAULT 'US',
    state             text,
    city              text,
    latitude          double precision,
    longitude         double precision,
    total_population  integer,
    statistics        jsonb,            -- LocationStatistics (income, ethnicity_distribution, age_ranges, ...)
    last_updated      date,
    created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_locations_zip        ON locations (zip_code);
CREATE INDEX IF NOT EXISTS idx_locations_state_city ON locations (state, city);
CREATE INDEX IF NOT EXISTS idx_locations_stats_gin  ON locations USING gin (statistics);

CREATE TABLE IF NOT EXISTS demographic_groups (
    group_id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id       uuid REFERENCES locations (location_id) ON DELETE CASCADE,
    group_name        text NOT NULL,
    min_age           integer,
    max_age           integer,
    gender            text CHECK (gender IS NULL OR gender IN ('male','female','non_binary','other')),
    ethnicity         text,
    education_level   text,
    income_bracket    text CHECK (income_bracket IS NULL OR income_bracket IN ('low','lower_middle','middle','upper_middle','high')),
    median_income     integer,
    population_size   integer,
    population_share  double precision,
    created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_demographic_groups_location ON demographic_groups (location_id);

-- ============================================================================
-- SYNTHETIC BEHAVIOR MODEL (data_processor)
-- ============================================================================

-- Statistical behavior model: one BehaviorFormula per metric, per location.
CREATE TABLE IF NOT EXISTS behavior_formulas (
    formula_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id       uuid REFERENCES locations (location_id) ON DELETE CASCADE,
    zip_code          text,
    metric            text NOT NULL,
    baseline          double precision,
    combination_rule  text CHECK (combination_rule IS NULL OR combination_rule IN ('multiplicative','additive','weighted_average')),
    modifiers         jsonb NOT NULL DEFAULT '[]'::jsonb,   -- FactorModifier[]
    expression        text,
    output_min        double precision DEFAULT 0.0,
    output_max        double precision DEFAULT 1.0,
    sample_size       integer,
    confidence        double precision,
    generated_by      text DEFAULT 'llm',
    created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_behavior_formulas_location ON behavior_formulas (location_id);
CREATE INDEX IF NOT EXISTS idx_behavior_formulas_metric   ON behavior_formulas (metric);

-- Audience groups oriented to a field/topic (technology, entertainment,
-- education, health, finance, politics, family).
CREATE TABLE IF NOT EXISTS field_behavior_groups (
    group_id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id            uuid REFERENCES locations (location_id) ON DELETE CASCADE,
    zip_code               text,
    group_name             text NOT NULL,
    field_domain           text NOT NULL CHECK (field_domain IN ('technology','education','finance','politics','entertainment','family','health')),
    description            text,
    typical_min_age        integer,
    typical_max_age        integer,
    typical_income_bracket text,
    profile                jsonb,   -- dominant_values, platforms, decision_drivers, objections, criteria, jargon_tolerance
    behavior_formulas      jsonb,   -- BehaviorFormula[]
    generated_by           text DEFAULT 'llm',
    created_at             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_field_groups_location ON field_behavior_groups (location_id);
CREATE INDEX IF NOT EXISTS idx_field_groups_field    ON field_behavior_groups (field_domain);

-- Varied audience groups: a group defined by a COMBINATION of factors, with its
-- behavior levels as RANGES (min/expected/max) = the audience output scores.
CREATE TABLE IF NOT EXISTS group_behavior_profiles (
    profile_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id       uuid REFERENCES locations (location_id) ON DELETE CASCADE,
    zip_code          text,
    group_name        text NOT NULL,
    min_age           integer,
    max_age           integer,
    gender            text CHECK (gender IS NULL OR gender IN ('male','female','non_binary','other')),
    ethnicity         text,
    income_bracket    text CHECK (income_bracket IS NULL OR income_bracket IN ('low','lower_middle','middle','upper_middle','high')),
    education_level   text,
    field_domain      text,
    behavior_ranges   jsonb NOT NULL DEFAULT '[]'::jsonb,   -- MetricRange[] (min/expected/max scores)
    formulas          jsonb,                                -- BehaviorFormula[] backing the ranges
    confidence        double precision,
    generated_by      text DEFAULT 'llm',
    created_at        timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_group_profiles_location   ON group_behavior_profiles (location_id);
CREATE INDEX IF NOT EXISTS idx_group_profiles_field      ON group_behavior_profiles (field_domain);
CREATE INDEX IF NOT EXISTS idx_group_profiles_ranges_gin ON group_behavior_profiles USING gin (behavior_ranges);

-- Consolidated audience spec per location (the persisted output of the processor).
CREATE TABLE IF NOT EXISTS audience_specs (
    spec_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id        uuid REFERENCES locations (location_id) ON DELETE CASCADE,
    zip_code           text UNIQUE,
    location_label     text,
    n_field_groups     integer,
    n_audience_groups  integer,
    audience_scores    jsonb,   -- {metric: {expected_avg, min, max, n_groups}}
    spec               jsonb,   -- full consolidated payload
    created_at         timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audience_specs_zip        ON audience_specs (zip_code);
CREATE INDEX IF NOT EXISTS idx_audience_specs_scores_gin ON audience_specs USING gin (audience_scores);

-- ============================================================================
-- ACTIONABLE AUDIENCE + PRODUCT EVALUATION (dtos/data_processors)
-- ============================================================================
CREATE TABLE IF NOT EXISTS audience_segments (
    segment_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    label                   text NOT NULL,
    location_id             uuid REFERENCES locations (location_id) ON DELETE SET NULL,
    demographic_group_id    uuid,
    psychographic_group_id  uuid,
    behavioral_group_id     uuid,
    particularity_ids       jsonb,
    estimated_reach         integer,
    confidence              double precision,
    created_at              timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_audience_segments_location ON audience_segments (location_id);

CREATE TABLE IF NOT EXISTS project_assets (
    asset_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name                text NOT NULL,
    asset_type          text CHECK (asset_type IS NULL OR asset_type IN ('document','presentation','spreadsheet','pdf','other')),
    summary             text,
    language            text,
    target_segment_ids  jsonb,
    source_uri          text,
    created_at          timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS reaction_profiles (
    reaction_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    asset_id               uuid REFERENCES project_assets (asset_id) ON DELETE CASCADE,
    segment_id             uuid,
    section                text,
    sentiment_score        double precision,
    comprehension_score    double precision,
    cultural_fit_score     double precision,
    engagement_likelihood  double precision,
    metric_scores          jsonb,
    factor_attribution     jsonb,
    applied_formula_ids    jsonb,
    strengths              jsonb,
    risks                  jsonb,
    recommendations        jsonb,
    confidence             double precision,
    generated_by           text DEFAULT 'llm',
    created_at             timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reaction_profiles_asset   ON reaction_profiles (asset_id);
CREATE INDEX IF NOT EXISTS idx_reaction_profiles_segment ON reaction_profiles (segment_id);

-- ============================================================================
-- BACKEND OPERATIONAL TABLES (mirror backend/models/database.py; init_db()
-- also creates these via SQLAlchemy — both paths are idempotent).
-- ============================================================================
CREATE TABLE IF NOT EXISTS audiences (
    id                   varchar(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    persona_type         text NOT NULL,
    region               text NOT NULL,
    focus_area           text NOT NULL,
    demographic_data     jsonb,
    behavioral_profile   jsonb,
    group_label          text,
    group_size_estimate  integer DEFAULT 0,
    created_at           timestamptz DEFAULT now()
);

CREATE TABLE IF NOT EXISTS sessions (
    id            varchar(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    audience_id   varchar(36),
    persona_type  text NOT NULL,
    region        text NOT NULL,
    focus_area    text NOT NULL,
    status        text DEFAULT 'active',
    started_at    timestamptz DEFAULT now(),
    completed_at  timestamptz
);
CREATE INDEX IF NOT EXISTS idx_sessions_audience ON sessions (audience_id);

CREATE TABLE IF NOT EXISTS analytics (
    id                 serial PRIMARY KEY,
    session_id         varchar(36) NOT NULL,
    recorded_at        timestamptz DEFAULT now(),
    engagement_level   double precision DEFAULT 0.0,
    sentiment_score    double precision DEFAULT 0.0,
    attention_score    double precision DEFAULT 0.0,
    conviction_level   double precision DEFAULT 0.0,
    objection_count    integer DEFAULT 0,
    decision_readiness double precision DEFAULT 0.0,
    risk_perception    double precision DEFAULT 0.0,
    pace_wpm           integer DEFAULT 0,
    filler_count       integer DEFAULT 0,
    clarity_score      double precision DEFAULT 0.0
);
CREATE INDEX IF NOT EXISTS idx_analytics_session ON analytics (session_id);

CREATE TABLE IF NOT EXISTS ingestion_events (
    id           serial PRIMARY KEY,
    session_id   varchar(36),
    source       text NOT NULL,
    event_type   text NOT NULL,
    raw_payload  jsonb NOT NULL,
    processed    boolean DEFAULT false,
    ingested_at  timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_ingestion_events_session ON ingestion_events (session_id);

CREATE TABLE IF NOT EXISTS reports (
    id           varchar(36) PRIMARY KEY DEFAULT gen_random_uuid()::text,
    session_id   varchar(36) NOT NULL,
    report_type  text NOT NULL,
    summary      jsonb,
    file_url     text,
    created_at   timestamptz DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_reports_session ON reports (session_id);
