from sqlalchemy import Column, Integer, Text, String, DateTime
from sqlalchemy.orm import Mapped
from datetime import datetime
from db import Base


class Faq(Base):
    __tablename__ = "faqs"
    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    question: Mapped[str] = Column(Text, nullable=False)
    answer: Mapped[str] = Column(Text, nullable=False)
    tags: Mapped[str] = Column(String(255), nullable=True)
    created_at: Mapped[datetime] = Column(DateTime, default=datetime.utcnow)
