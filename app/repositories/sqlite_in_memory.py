import uuid
import sqlite3
import json
from datetime import datetime, timezone
from app.models.transcript import TranscriptAnalysis
from app.ports.repository import AnalysisRepository


class SQLiteInMemoryAnalysisRepository(AnalysisRepository):
    def __init__(self) -> None:
        self._conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE transcript_analysis (
                id TEXT PRIMARY KEY,
                summary TEXT NOT NULL,
                action_items TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

    def save(self, analysis: TranscriptAnalysis) -> None:
        self._conn.execute(
            "INSERT INTO transcript_analysis (id, summary, action_items, created_at) VALUES (?, ?, ?, ?)",
            (str(analysis.id), analysis.summary, json.dumps(analysis.action_items), analysis.created_at.isoformat()),
        )
        self._conn.commit()

    def get_by_id(self, id: uuid.UUID) -> TranscriptAnalysis | None:
        row = self._conn.execute(
            "SELECT id, summary, action_items, created_at FROM transcript_analysis WHERE id = ?",
            (str(id),),
        ).fetchone()
        if row is None:
            return None
        return self._row_to_analysis(row)

    def list_all(self) -> list[TranscriptAnalysis]:
        rows = self._conn.execute(
            "SELECT id, summary, action_items, created_at FROM transcript_analysis ORDER BY created_at DESC"
        ).fetchall()
        return [self._row_to_analysis(row) for row in rows]

    def delete(self, id: uuid.UUID) -> bool:
        cursor = self._conn.execute(
            "DELETE FROM transcript_analysis WHERE id = ?", (str(id),)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    def delete_many(self, ids: list[uuid.UUID]) -> int:
        if not ids:
            return 0
        placeholders = ",".join("?" * len(ids))
        cursor = self._conn.execute(
            f"DELETE FROM transcript_analysis WHERE id IN ({placeholders})",
            [str(i) for i in ids],
        )
        self._conn.commit()
        return cursor.rowcount

    @staticmethod
    def _row_to_analysis(row: tuple) -> TranscriptAnalysis:
        return TranscriptAnalysis(
            id=uuid.UUID(row[0]),
            summary=row[1],
            action_items=json.loads(row[2]),
            created_at=datetime.fromisoformat(row[3]),
        )
