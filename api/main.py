import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from config.settings import settings
from database.db import init_db
from database.repository import InterviewRepository
from llm.model import get_llm
from agent.graph import interview_graph

init_db()

app = FastAPI(title=f"{settings.APP_NAME} API", version="0.2.0")

class StartInterviewReq(BaseModel):
    role: str = Field(..., examples=["Software Engineer"])
    level: str = Field(default="Mid-Level")
    language: str = Field(default="English")
    max_questions: int = Field(default=5, ge=1, le=10)

class AnswerReq(BaseModel):
    session_id: str
    role: str
    level: str = "Mid-Level"
    language: str = "English"
    question_num: int = 1
    max_questions: int = 5
    current_question: str
    user_answer: str
    force_evaluate: bool = False

@app.get("/health")
def health():
    try:
        get_llm().invoke("Hi")
        groq_online = True
    except Exception:
        groq_online = False

    return {
        "status": "ok",
        "groq_online": groq_online,
        "model": settings.GROQ_MODEL
    }

@app.post("/interview/start")
def start_interview(req: StartInterviewReq):
    session_id = f"int_{uuid.uuid4().hex[:10]}"
    res = interview_graph.invoke(
        {
            "session_id": session_id,
            "role": req.role,
            "level": req.level,
            "language": req.language,
            "question_num": 1,
            "max_questions": req.max_questions,
            "current_question": "",
            "user_answer": "",
            "action": "ask_question",
            "transcript": [],
            "score": 0,
            "feedback": "",
            "overall_summary": "",
        }
    )
    return {"session_id": session_id, "question": res["current_question"]}

@app.post("/interview/answer")
def submit_answer(req: AnswerReq):
    res = interview_graph.invoke(
        {
            "session_id": req.session_id,
            "role": req.role,
            "level": req.level,
            "language": req.language,
            "question_num": req.question_num,
            "max_questions": req.max_questions,
            "current_question": req.current_question,
            "user_answer": req.user_answer,
            "action": "evaluate" if req.force_evaluate else "",
            "transcript": [],
            "score": 0,
            "feedback": "",
            "overall_summary": "",
        }
    )
    return {
        "session_id": req.session_id,
        "action": res.get("action"),
        "next_question": res.get("current_question") if res.get("action") == "followup" else None,
        "score": res.get("score", 0),
        "feedback": res.get("feedback", ""),
    }

@app.get("/interview/{session_id}")
def get_interview(session_id: str):
    repo = InterviewRepository()
    try:
        sess = repo.get_session(session_id)
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        turns = repo.get_turns(session_id)
    finally:
        repo.close()
    return {
        "session_id": sess.session_id,
        "role": sess.role,
        "level": sess.level,
        "language": sess.language,
        "overall_summary": sess.overall_summary,
        "turns": [
            {
                "question_num": t.question_num,
                "question": t.question,
                "user_answer": t.user_answer,
                "score": t.score,
                "feedback": t.feedback,
            }
            for t in turns
        ],
    }
