from datetime import datetime, timezone
from typing import List, Optional
from database.db import SessionLocal
from database.models import InterviewSession, InterviewTurn

class InterviewRepository:
    def __init__(self):
        self.db = SessionLocal()

    def close(self):
        self.db.close()

    def create_or_update_session(
        self,
        session_id: str,
        role: str,
        level: str = "Mid-Level",
        language: str = "English",
        overall_summary: Optional[str] = None,
    ) -> InterviewSession:
        sess = self.db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()
        if not sess:
            sess = InterviewSession(
                session_id=session_id,
                role=role,
                level=level,
                language=language,
                overall_summary=overall_summary or "",
            )
            self.db.add(sess)
        else:
            sess.role = role
            sess.level = level
            sess.language = language
            if overall_summary is not None:
                sess.overall_summary = overall_summary
            sess.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(sess)
        return sess

    def add_turn(
        self,
        session_id: str,
        question_num: int,
        question: str,
        user_answer: str,
        action: str,
        score: int,
        feedback: str,
    ):
        turn = InterviewTurn(
            session_id=session_id,
            question_num=question_num,
            question=question,
            user_answer=user_answer,
            action=action,
            score=score,
            feedback=feedback,
        )
        self.db.add(turn)
        self.db.commit()

    def get_session(self, session_id: str) -> Optional[InterviewSession]:
        return self.db.query(InterviewSession).filter(InterviewSession.session_id == session_id).first()

    def list_sessions(self, limit: int = 10) -> List[InterviewSession]:
        return (
            self.db.query(InterviewSession)
            .order_by(InterviewSession.updated_at.desc())
            .limit(limit)
            .all()
        )
