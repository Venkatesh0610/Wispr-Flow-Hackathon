from typing import TypedDict, List

class InterviewState(TypedDict):
    session_id: str
    role: str
    level: str
    language: str
    question_num: int
    max_questions: int
    current_question: str
    user_answer: str
    action: str  # "ask_question" | "followup" | "evaluate" | "summarize"
    transcript: List[dict]
    score: int
    feedback: str
    overall_summary: str
