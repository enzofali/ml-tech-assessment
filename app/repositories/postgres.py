import uuid
import json
from contextlib import contextmanager
from datetime import datetime, timezone

import psycopg2
import psycopg2.pool

from app.models.transcript import TranscriptAnalysis
from app.ports.repository import AnalysisRepository
from app.metrics import repository_operations_total, repository_size

_CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS transcript_analysis (
    id          UUID        PRIMARY KEY,
    summary     TEXT        NOT NULL,
    action_items JSONB      NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL
)
"""


class PostgresAnalysisRepository(AnalysisRepository):
    def __init__(self, database_url: str) -> None:
        self._pool = psycopg2.pool.ThreadedConnectionPool(1, 10, database_url)
        with self._conn() as conn:
            with conn.cursor() as cur:
                cur.execute(_CREATE_TABLE)

    @contextmanager
    def _conn(self):
        conn = self._pool.getconn()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            self._pool.putconn(conn)

    def _sync_size(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM transcript_analysis")
            repository_size.set(cur.fetchone()[0])

    def save(self, analysis: TranscriptAnalysis) -> None:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO transcript_analysis (id, summary, action_items, created_at)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE
                            SET summary = EXCLUDED.summary,
                                action_items = EXCLUDED.action_items
                        """,
                        (str(analysis.id), analysis.summary, json.dumps(analysis.action_items), analysis.created_at),
                    )
                self._sync_size(conn)
            repository_operations_total.labels(operation="save", result="success").inc()
        except Exception:
            repository_operations_total.labels(operation="save", result="error").inc()
            raise

    def get_by_id(self, id: uuid.UUID) -> TranscriptAnalysis | None:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, summary, action_items, created_at FROM transcript_analysis WHERE id = %s",
                        (str(id),),
                    )
                    row = cur.fetchone()
            result = _row_to_analysis(row) if row else None
            repository_operations_total.labels(operation="get", result="success" if result else "miss").inc()
            return result
        except Exception:
            repository_operations_total.labels(operation="get", result="error").inc()
            raise

    def list_all(self) -> list[TranscriptAnalysis]:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, summary, action_items, created_at FROM transcript_analysis ORDER BY created_at DESC"
                    )
                    rows = cur.fetchall()
            repository_operations_total.labels(operation="list", result="success").inc()
            return [_row_to_analysis(row) for row in rows]
        except Exception:
            repository_operations_total.labels(operation="list", result="error").inc()
            raise

    def delete(self, id: uuid.UUID) -> bool:
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM transcript_analysis WHERE id = %s", (str(id),))
                    deleted = cur.rowcount > 0
                if deleted:
                    self._sync_size(conn)
            result = "success" if deleted else "miss"
            repository_operations_total.labels(operation="delete", result=result).inc()
            return deleted
        except Exception:
            repository_operations_total.labels(operation="delete", result="error").inc()
            raise

    def delete_many(self, ids: list[uuid.UUID]) -> int:
        if not ids:
            return 0
        try:
            with self._conn() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "DELETE FROM transcript_analysis WHERE id = ANY(%s::uuid[])",
                        ([str(i) for i in ids],),
                    )
                    deleted = cur.rowcount
                if deleted:
                    self._sync_size(conn)
            if deleted:
                repository_operations_total.labels(operation="delete", result="success").inc(deleted)
            missed = len(ids) - deleted
            if missed:
                repository_operations_total.labels(operation="delete", result="miss").inc(missed)
            return deleted
        except Exception:
            repository_operations_total.labels(operation="delete", result="error").inc()
            raise


def _row_to_analysis(row: tuple) -> TranscriptAnalysis:
    id_, summary, action_items, created_at = row
    if isinstance(created_at, str):
        created_at = datetime.fromisoformat(created_at)
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    return TranscriptAnalysis(
        id=uuid.UUID(str(id_)),
        summary=summary,
        action_items=action_items if isinstance(action_items, list) else json.loads(action_items),
        created_at=created_at,
    )
