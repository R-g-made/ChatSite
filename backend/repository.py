from typing import Iterable, List, Optional
from sqlalchemy.orm import Session
from pathlib import Path
import json
from models import Faq
from db import fts_manager


class FaqRepository:
    def __init__(self, session: Session):
        self.session = session

    def count(self) -> int:
        return self.session.query(Faq).count()

    def bulk_insert(self, items: Iterable[dict]):
        objs = []
        for it in items:
            q = (it.get("question") or "").strip()
            a = (it.get("answer") or "").strip()
            t = (it.get("tags") or None)
            objs.append(Faq(question=q, answer=a, tags=(t.strip() or None) if t else None))
        if objs:
            self.session.add_all(objs)
            self.session.commit()

    def list_all(self) -> List[Faq]:
        return self.session.query(Faq).all()

    def list_by_ids(self, ids: List[int]) -> List[Faq]:
        if not ids:
            return []
        rows = self.session.query(Faq).filter(Faq.id.in_(ids)).all()
        order = {v: i for i, v in enumerate(ids)}
        rows.sort(key=lambda r: order.get(r.id, 1_000_000))
        return rows

    def candidate_ids_by_fts(self, query: str, limit: int = 50) -> List[int]:
        return fts_manager.candidate_ids(query, limit)


class Seeder:
    def __init__(self, repo: FaqRepository):
        self.repo = repo

    def seed_if_empty(self, path: Path):
        if self.repo.count() > 0:
            return
        if not path.exists():
            return
        data = []
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            self.repo.bulk_insert(data)
