-- ================================================================
--  Intelligent Laboratory Access Control System
--  Database Schema — Phase 1
--  PostgreSQL 14+
--  psql -U postgres -d lab_access -f schema.sql
-- ================================================================

CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ----------------------------------------------------------------
--  TABLE: labs — one row per physical entrance / edge device
-- ----------------------------------------------------------------
CREATE TABLE labs (
    id          SERIAL          PRIMARY KEY,
    name        VARCHAR(100)    NOT NULL,
    location    VARCHAR(255),
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE users (
    id          SERIAL          PRIMARY KEY,
    full_name   VARCHAR(150)    NOT NULL,
    email       VARCHAR(255)    NOT NULL UNIQUE,
    role        VARCHAR(50)     NOT NULL DEFAULT 'researcher',
    is_active   BOOLEAN         NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE TABLE face_embeddings (
    id          SERIAL      PRIMARY KEY,
    user_id     INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    embedding   FLOAT8[]    NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_embedding_length CHECK (array_length(embedding, 1) = 512)
);

CREATE INDEX idx_face_embeddings_user_id ON face_embeddings(user_id);

CREATE TABLE access_logs (
    id               SERIAL      PRIMARY KEY,
    user_id          INTEGER     REFERENCES users(id) ON DELETE SET NULL,
    lab_id           INTEGER     NOT NULL REFERENCES labs(id) ON DELETE CASCADE,
    outcome          VARCHAR(20) NOT NULL,
    similarity_score FLOAT8,
    latency_ms       FLOAT8,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_outcome CHECK (outcome IN ('ALLOW', 'DENY'))
);

CREATE INDEX idx_access_logs_user_id ON access_logs(user_id);
CREATE INDEX idx_access_logs_lab_id  ON access_logs(lab_id);
CREATE INDEX idx_access_logs_created ON access_logs(created_at DESC);

-- Seed
INSERT INTO labs (name, location)
VALUES ('Lab A - Main Entrance', 'Building 1, Floor 1');