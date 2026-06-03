from typing import List, Dict, Any
from sqlalchemy.orm import Session
from rapidfuzz import fuzz
import re
from models import Faq
from repository import FaqRepository
from db import fts_manager


class FuzzyRanker:
    def __init__(self):
        ...

    def _words(self, s: str) -> set:
        return {w for w in re.findall(r"\w+", (s or "").lower()) if len(w) > 2}

    def score(self, message: str, faq: Faq) -> float:
        r = fuzz.token_set_ratio(message or "", faq.question or "")
        msg = self._words(message)
        q = self._words(faq.question or "")
        t = self._words(faq.tags or "")
        overlap_q = len(msg & q)
        overlap_t = len(msg & t)
        return float(r) + 2.0 * overlap_q + 5.0 * overlap_t


class SearchService:
    def __init__(self, session: Session):
        self.repo = FaqRepository(session)
        self.ranker = FuzzyRanker()

    def search_top_k(self, message: str, k: int = 3) -> Dict[str, Any]:
        candidates = fts_manager.candidate_ids_with_scores(message, 50)
        bm25_scores = {cid: score for cid, score in candidates}
        ids = [cid for cid, _ in candidates]
        
        if ids:
            faqs = self.repo.list_by_ids(ids)
        else:
            faqs = self.repo.list_all()
            
        scored = []
        for f in faqs:
            fuzzy_score = self.ranker.score(message, f)
            bm25_val = bm25_scores.get(f.id, 0.0)
            # Bm25 + fuzzy
            final_score = fuzzy_score + 5.0 * bm25_val
            scored.append((final_score, f))
            
        scored.sort(key=lambda x: x[0], reverse=True)
        top = [{
            "id": f.id,
            "question": f.question,
            "answer": f.answer,
            "tags": f.tags,
            "score": round(s, 3)
        } for s, f in scored[:k]]
        
        used = {"fts5": fts_manager.enabled, "bm25": True, "fuzzy": "rapidfuzz"}
        return {"results": top, "used": used}
