from typing import TypedDict, List

class InterviewState(TypedDict):
    session_id: str
    role: str
    level: str
    language: str
    question_num: int
    max_questions: int
    followup_count: int
    max_followups: int
    current_question: str
    user_answer: str
    action: str
    transcript: List[dict]
    score: float
    feedback: str
    overall_summary: str