from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pathlib import Path
from db import get_db, init_db, fts_manager
from schemas import ChatRequest, ChatResponse, ChatItem, FaqRead
from search import SearchService
from repository import FaqRepository, Seeder

app = FastAPI(title="FAQ Chat")

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    fts_manager.setup()
    seed_path = Path(__file__).parent / "seed_faq.json"
    with next(get_db()) as db:
        repo = FaqRepository(db)
        Seeder(repo).seed_if_empty(seed_path)


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Пустой запрос")
    service = SearchService(db)
    data = service.search_top_k(msg, 3)
    items = [ChatItem(**it) for it in data["results"]]
    return ChatResponse(results=items, used=data["used"])


@app.get("/faqs", response_model=list[FaqRead])
def list_faqs(db: Session = Depends(get_db)):
    rows = FaqRepository(db).list_all()
    return rows
