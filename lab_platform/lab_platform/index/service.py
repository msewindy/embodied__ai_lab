from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..config import LabConfig
from ..models import ArtifactRecord, LockRecord, Pipeline, RunRecord, RunStatus


class IndexService:
    """SQLite 索引服务 — 骨架期真实实现。"""

    def __init__(self, config: LabConfig) -> None:
        self._config = config
        self._db_path = config.index_db

    def initialize(self) -> None:
        schema = (Path(__file__).parent / "schema.sql").read_text(encoding="utf-8")
        with self._connect() as conn:
            conn.executescript(schema)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def register_run(self, record: RunRecord) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (
                    id, run_type, pipeline, job_kind, status, operator, project_id,
                    storage_path, device_ids, metadata_json, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.run_id,
                    record.run_type,
                    record.pipeline.value,
                    record.job_kind,
                    record.status.value,
                    record.operator,
                    record.project_id,
                    record.storage_path,
                    json.dumps(record.device_ids),
                    json.dumps(record.metadata),
                    ts,
                    ts,
                ),
            )

    def patch_run(self, run_id: str, **fields) -> None:
        allowed = {"status", "metadata", "job_kind"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            row = conn.execute("SELECT metadata_json FROM runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise KeyError(f"run not found: {run_id}")
            meta = json.loads(row["metadata_json"] or "{}")
            if "metadata" in updates:
                meta.update(updates.pop("metadata"))
            sets = ["updated_at=?"]
            vals: list = [ts]
            if "status" in updates:
                sets.append("status=?")
                vals.append(
                    updates["status"].value
                    if isinstance(updates["status"], RunStatus)
                    else updates["status"]
                )
            if meta:
                sets.append("metadata_json=?")
                vals.append(json.dumps(meta))
            vals.append(run_id)
            conn.execute(f"UPDATE runs SET {', '.join(sets)} WHERE id=?", vals)

    def get_run(self, run_id: str) -> RunRecord | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        return self._row_to_run(row) if row else None

    def list_runs(
        self,
        run_type: str | None = None,
        status: RunStatus | None = None,
        limit: int = 50,
    ) -> list[RunRecord]:
        q = "SELECT * FROM runs WHERE 1=1"
        params: list = []
        if run_type:
            q += " AND run_type=?"
            params.append(run_type)
        if status:
            q += " AND status=?"
            params.append(status.value)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(q, params).fetchall()
        return [self._row_to_run(r) for r in rows]

    def register_artifact(self, record: ArtifactRecord) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO artifacts (
                    artifact_id, artifact_type, lifecycle_status, producer_run_id,
                    storage_path, metadata_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.artifact_id,
                    record.artifact_type,
                    record.lifecycle_status,
                    record.producer_run_id,
                    record.storage_path,
                    json.dumps(record.metadata),
                    ts,
                ),
            )

    def patch_artifact(self, artifact_id: str, **fields) -> None:
        if "lifecycle_status" not in fields and "metadata" not in fields:
            return
        with self._connect() as conn:
            row = conn.execute(
                "SELECT metadata_json FROM artifacts WHERE artifact_id=?", (artifact_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"artifact not found: {artifact_id}")
            meta = json.loads(row["metadata_json"] or "{}")
            if "metadata" in fields:
                meta.update(fields["metadata"])
            if "lifecycle_status" in fields:
                conn.execute(
                    "UPDATE artifacts SET lifecycle_status=?, metadata_json=? WHERE artifact_id=?",
                    (fields["lifecycle_status"], json.dumps(meta), artifact_id),
                )
            else:
                conn.execute(
                    "UPDATE artifacts SET metadata_json=? WHERE artifact_id=?",
                    (json.dumps(meta), artifact_id),
                )

    def get_artifact(self, artifact_id: str) -> ArtifactRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM artifacts WHERE artifact_id=?", (artifact_id,)
            ).fetchone()
        return self._row_to_artifact(row) if row else None

    def list_artifacts(
        self, artifact_type: str | None = None, limit: int = 50
    ) -> list[ArtifactRecord]:
        q = "SELECT * FROM artifacts"
        params: list = []
        if artifact_type:
            q += " WHERE artifact_type=?"
            params.append(artifact_type)
        q += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(q, params).fetchall()
        return [self._row_to_artifact(r) for r in rows]

    def link_run_artifact(self, run_id: str, artifact_id: str, relation: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO run_artifact_links (run_id, artifact_id, relation)
                VALUES (?, ?, ?)
                """,
                (run_id, artifact_id, relation),
            )

    def get_lineage(self, run_id: str) -> dict:
        run = self.get_run(run_id)
        if not run:
            return {}
        with self._connect() as conn:
            links = conn.execute(
                "SELECT * FROM run_artifact_links WHERE run_id=?", (run_id,)
            ).fetchall()
        upstream, downstream = [], []
        for link in links:
            art = self.get_artifact(link["artifact_id"])
            item = {"artifact_id": link["artifact_id"], "relation": link["relation"]}
            if art:
                item["type"] = art.artifact_type
            if link["relation"] == "upstream":
                upstream.append(item)
            else:
                downstream.append(item)
        return {
            "run_id": run_id,
            "run_type": run.run_type,
            "status": run.status.value,
            "upstream": upstream,
            "downstream": downstream,
        }

    def acquire_locks(
        self, run_id: str, locks: list[tuple[str, str]], ttl_seconds: int
    ) -> list[LockRecord]:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(seconds=ttl_seconds)
        acquired: list[LockRecord] = []
        with self._connect() as conn:
            device_locks_requested = [
                rid for lt, rid in locks if lt == "device_lock"
            ]
            if device_locks_requested:
                z_dyn = set(self._z_dyn_devices())
                z_dyn_requested = [d for d in device_locks_requested if d in z_dyn]
                if z_dyn_requested:
                    active = conn.execute(
                        """
                        SELECT resource_id FROM resource_locks
                        WHERE lock_type='device_lock'
                        """
                    ).fetchall()
                    active_z = {r["resource_id"] for r in active if r["resource_id"] in z_dyn}
                    new_z = set(z_dyn_requested) - active_z
                    if len(active_z) + len(new_z) > 2:
                        raise ResourceConflictError(
                            f"Z-DYN concurrent limit (2) exceeded: "
                            f"active={sorted(active_z)}, requested={z_dyn_requested}"
                        )
            for lock_type, resource_id in locks:
                try:
                    conn.execute(
                        """
                        INSERT INTO resource_locks (
                            lock_type, resource_id, holder_run_id, acquired_at, expires_at
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            lock_type,
                            resource_id,
                            run_id,
                            now.isoformat(),
                            expires.isoformat(),
                        ),
                    )
                except sqlite3.IntegrityError as e:
                    raise ResourceConflictError(
                        f"lock held: {lock_type}/{resource_id}"
                    ) from e
                acquired.append(
                    LockRecord(
                        lock_type=lock_type,
                        resource_id=resource_id,
                        holder_run_id=run_id,
                        acquired_at=now.isoformat(),
                        expires_at=expires.isoformat(),
                    )
                )
        return acquired

    def release_locks(self, run_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM resource_locks WHERE holder_run_id=?", (run_id,)
            )

    def list_active_locks(self, zone: str | None = None) -> list[LockRecord]:
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM resource_locks").fetchall()
        locks = [
            LockRecord(
                lock_type=r["lock_type"],
                resource_id=r["resource_id"],
                holder_run_id=r["holder_run_id"],
                acquired_at=r["acquired_at"],
                expires_at=r["expires_at"],
            )
            for r in rows
        ]
        if zone != "Z-DYN":
            return locks
        z_devices = set(self._z_dyn_devices())
        return [l for l in locks if l.resource_id in z_devices or l.resource_id == "Z-DYN"]

    def _z_dyn_devices(self) -> list[str]:
        import yaml

        cap_path = self._config.registry_dir / "device_capabilities.yaml"
        if not cap_path.exists():
            return []
        data = yaml.safe_load(cap_path.read_text(encoding="utf-8")) or {}
        return [
            did
            for did, d in (data.get("devices") or {}).items()
            if d.get("zone") == "Z-DYN"
        ]

    @staticmethod
    def _row_to_run(row: sqlite3.Row) -> RunRecord:
        return RunRecord(
            run_id=row["id"],
            run_type=row["run_type"],
            pipeline=Pipeline(row["pipeline"]),
            status=RunStatus(row["status"]),
            operator=row["operator"],
            project_id=row["project_id"],
            storage_path=row["storage_path"],
            device_ids=json.loads(row["device_ids"] or "[]"),
            job_kind=row["job_kind"],
            metadata=json.loads(row["metadata_json"] or "{}"),
        )

    @staticmethod
    def _row_to_artifact(row: sqlite3.Row) -> ArtifactRecord:
        return ArtifactRecord(
            artifact_id=row["artifact_id"],
            artifact_type=row["artifact_type"],
            lifecycle_status=row["lifecycle_status"],
            producer_run_id=row["producer_run_id"],
            storage_path=row["storage_path"],
            metadata=json.loads(row["metadata_json"] or "{}"),
        )


class ResourceConflictError(Exception):
    pass
