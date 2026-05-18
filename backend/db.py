from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine
from typing import List
import re

DB_URL = "sqlite:///./faq.db"
engine: Engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class FtsManager:
    def __init__(self, engine: Engine):
        self.engine = engine
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    def setup(self):
        try:
            with self.engine.begin() as conn:
                conn.execute(
                    text(
                        "CREATE VIRTUAL TABLE IF NOT EXISTS faq_fts USING fts5("
                        "question, answer, tags, content='faqs', content_rowid='id'"
                        ")"
                    )
                )
                conn.execute(text("DROP TRIGGER IF EXISTS faq_ai"))
                conn.execute(text("DROP TRIGGER IF EXISTS faq_ad"))
                conn.execute(text("DROP TRIGGER IF EXISTS faq_au"))
                conn.execute(
                    text(
                        "CREATE TRIGGER faq_ai AFTER INSERT ON faqs BEGIN "
                        "INSERT INTO faq_fts(rowid, question, answer, tags) "
                        "VALUES (new.id, new.question, new.answer, new.tags); END;"
                    )
                )
                conn.execute(
                    text(
                        "CREATE TRIGGER faq_ad AFTER DELETE ON faqs BEGIN "
                        "INSERT INTO faq_fts(faq_fts, rowid, question, answer, tags) "
                        "VALUES('delete', old.id, old.question, old.answer, old.tags); END;"
                    )
                )
                conn.execute(
                    text(
                        "CREATE TRIGGER faq_au AFTER UPDATE ON faqs BEGIN "
                        "INSERT INTO faq_fts(faq_fts, rowid, question, answer, tags) "
                        "VALUES('delete', old.id, old.question, old.answer, old.tags); "
                        "INSERT INTO faq_fts(rowid, question, answer, tags) "
                        "VALUES (new.id, new.question, new.answer, new.tags); END;"
                    )
                )
            self._enabled = True
        except Exception:
            self._enabled = False

    def _fts_query(self, query: str) -> str:
        words = [w for w in re.findall(r"\w+", query.lower()) if len(w) > 2]
        if not words:
            return ""
        parts = [f"{w}*" for w in words[:6]]
        return " OR ".join(parts)

    def candidate_ids_with_scores(self, query: str, limit: int = 50) -> List[tuple]:
        if not self._enabled:
            return []
        q = self._fts_query(query)
        if not q:
            return []
        try:
            with self.engine.begin() as conn:
                rows = conn.execute(
                    text(
                        "SELECT rowid, -bm25(faq_fts, 10.0, 1.0, 5.0) as score "
                        "FROM faq_fts "
                        "WHERE faq_fts MATCH :q "
                        "ORDER BY score DESC "
                        "LIMIT :lim"
                    ),
                    {"q": q, "lim": limit},
                ).fetchall()
            return [(int(r[0]), float(r[1])) for r in rows]
        except Exception:
            return []

    def candidate_ids(self, query: str, limit: int = 50) -> List[int]:
        res = self.candidate_ids_with_scores(query, limit)
        return [r[0] for r in res]


fts_manager = FtsManager(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    from . import models

    Base.metadata.create_all(bind=engine)
    fts_manager.setup()
