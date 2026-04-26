CREATE TABLE conversations (
    id          TEXT PRIMARY KEY,
    created_at  REAL NOT NULL,
    title       TEXT,
    metadata    TEXT
);

CREATE TABLE runs (
    id                TEXT PRIMARY KEY,
    conversation_id   TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    created_at        REAL NOT NULL,
    completed_at      REAL,
    status            TEXT NOT NULL,
    strategy          TEXT NOT NULL,
    reasoning_model   TEXT NOT NULL,
    evaluator_model   TEXT,
    query             TEXT NOT NULL,
    knobs             TEXT NOT NULL,
    final_answer      TEXT,
    confidence        REAL,
    tokens_used       INTEGER DEFAULT 0,
    elapsed_s         REAL,
    error             TEXT
);

CREATE TABLE events (
    id           TEXT PRIMARY KEY,
    run_id       TEXT NOT NULL REFERENCES runs(id) ON DELETE CASCADE,
    seq          INTEGER NOT NULL,
    ts           REAL NOT NULL,
    type         TEXT NOT NULL,
    payload      TEXT NOT NULL,
    UNIQUE(run_id, seq)
);

CREATE INDEX idx_runs_conv ON runs(conversation_id, created_at DESC);
CREATE INDEX idx_runs_status ON runs(status);
CREATE INDEX idx_events_run_seq ON events(run_id, seq);
