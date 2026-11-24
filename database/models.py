from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey
from database.db import Base

def utcnow():
    return datetime.now(timezone.utc)

class InterviewSession(Base):
    __tablename__ = "interview_sessions"
    session_id = Column(String, primary_key=True)
    role = Column(String, nullable=False)
    level = Column(String, default="Mid-Level")
    language = Column(String, default="English")
    overall_summary = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

class InterviewTurn(Base):
    __tablename__ = "interview_turns"
    turn_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("interview_sessions.session_id"), index=True)
    question_num = Column(Integer, default=1)
    question = Column(Text, nullable=False)
    user_answer = Column(Text, nullable=False)
    action = Column(String, default="evaluate")
    score = Column(Integer, default=0)
    feedback = Column(Text, default="")
    created_at = Column(DateTime, default=utcnow)
