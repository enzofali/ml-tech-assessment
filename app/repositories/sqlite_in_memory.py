import uuid
import sqlite3
import json
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
                action_items TEXT NOT NULL
            )
            """
        )

    def save(self, analysis: TranscriptAnalysis) -> None:
        self._conn.execute(
            "INSERT INTO transcript_analysis (id, summary, action_items) VALUES (?, ?, ?)",
            (str(analysis.id), analysis.summary, json.dumps(analysis.action_items)),
        )
        self._conn.commit()

    def get_by_id(self, id: uuid.UUID) -> TranscriptAnalysis | None:
        row = self._conn.execute(
            "SELECT id, summary, action_items FROM transcript_analysis WHERE id = ?",
            (str(id),),
        ).fetchone()

        if row is None:
            return None

        return TranscriptAnalysis(
            id=uuid.UUID(row[0]),
            summary=row[1],
            action_items=json.loads(row[2]),
        )
