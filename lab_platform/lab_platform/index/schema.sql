CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    run_type TEXT NOT NULL,
    pipeline TEXT NOT NULL,
    job_kind TEXT,
    status TEXT NOT NULL,
    operator TEXT NOT NULL,
    project_id TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    device_ids TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id TEXT PRIMARY KEY,
    artifact_type TEXT NOT NULL,
    lifecycle_status TEXT NOT NULL,
    producer_run_id TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    FOREIGN KEY (producer_run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS run_artifact_links (
    run_id TEXT NOT NULL,
    artifact_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    PRIMARY KEY (run_id, artifact_id, relation),
    FOREIGN KEY (run_id) REFERENCES runs(id),
    FOREIGN KEY (artifact_id) REFERENCES artifacts(artifact_id)
);

CREATE TABLE IF NOT EXISTS resource_locks (
    lock_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    holder_run_id TEXT NOT NULL,
    acquired_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    PRIMARY KEY (lock_type, resource_id),
    FOREIGN KEY (holder_run_id) REFERENCES runs(id)
);

CREATE INDEX IF NOT EXISTS idx_runs_type_status ON runs(run_type, status);
CREATE INDEX IF NOT EXISTS idx_artifacts_type ON artifacts(artifact_type);
CREATE INDEX IF NOT EXISTS idx_links_run ON run_artifact_links(run_id);
