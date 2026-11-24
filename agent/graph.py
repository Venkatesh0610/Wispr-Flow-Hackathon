
import re

from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END

from agent.state import InterviewState
from llm.model import get_llm
from database.repository import InterviewRepository


# Supported interview languages
LANGUAGE_HINTS = {
    "English": "Respond in clear, natural English.",
    "Hindi": "Respond in conversational Hindi (Devanagari script) keeping standard technical terms clear.",
    "Hinglish": "Respond in natural Hinglish (Hindi written in Roman script mixed with English tech terms).",
}


def _lang_hint(lang: str) -> str:
    return LANGUAGE_HINTS.get(lang, LANGUAGE_HINTS["English"])


# --------------------------------------------------
# 1. DECIDE ACTION NODE
# --------------------------------------------------

def decide_action_node(state: InterviewState) -> dict:

    if state.get("action") in {
        "ask_question",
        "followup",
        "evaluate",
        "summarize"
    }:
        return {"action": state["action"]}

    ans = state.get("user_answer", "").strip()

    if len(ans.split()) < 14:
        return {"action": "followup"}

    return {"action": "evaluate"}


def route_action(state: InterviewState) -> str:
    return state.get("action", "evaluate")


# --------------------------------------------------
# 2. ASK QUESTION NODE
# --------------------------------------------------


def ask_question_node(state: InterviewState) -> dict:

    q_num = state.get("question_num", 1)
    max_q = state.get("max_questions", 5)

    role = state.get("role", "Software Engineer")
    level = state.get("level", "Mid-Level")
    language = state.get("language", "English")

    prior_qs = [
        t.get("question", "").strip()
        for t in state.get("transcript", [])
        if t.get("question")
    ]

    avoid_block = ""

    if prior_qs:
        formatted_prior = "\n".join(
            [f"- {pq}" for pq in prior_qs]
        )

        avoid_block = (
            f"\nPreviously asked questions:\n{formatted_prior}\n"
            "Do not repeat these questions or topics. "
            "Choose a different practical scenario."
        )

    llm = get_llm(temperature=0.5)

    prompt = f"""
You are an experienced technical interviewer.

Generate exactly ONE short, realistic, scenario-based interview question.

Role: {role}
Level: {level}
Language: {language}

Rules:
- Keep the question between 15 and 25 words.
- Ask only one question at a time.
- Use simple, conversational language.
- Focus on practical, real-world situations.
- Do not include topic names or labels.
- Do not write headings such as "Interview Question" or "Topic".
- Do not include explanations, hints, or expected answers.
- Output ONLY the question that should be spoken aloud.

Avoid repeating previous questions:
{avoid_block}
"""

    try:
        response = llm.invoke([
            HumanMessage(content=prompt)
        ])

        question = response.content.strip()

        # Remove unwanted topic labels if the model generates them
        question = re.sub(
            r"^(Interview Question.*?:\s*)",
            "",
            question,
            flags=re.IGNORECASE
        )

        question = question.strip().strip('"').strip("'")

    except Exception:
        q = (
            f"Can you describe a real technical issue "
            f"you faced while working as a {role} "
            f"and how you resolved it?"
        )

    return {
        "current_question": q,
        "feedback": "",
        "score": 0
    }


# --------------------------------------------------
# 3. FOLLOW-UP NODE
# --------------------------------------------------

def followup_node(state: InterviewState) -> dict:

    llm = get_llm(temperature=0.4)

    prompt = (
        f"You are interviewing a {state['level']} "
        f"{state['role']} candidate.\n"
        f"{_lang_hint(state['language'])}\n"
        f"Current Question: {state['current_question']}\n"
        f"Candidate's Answer: {state['user_answer']}\n\n"
        "Ask ONE focused follow-up question to explore "
        "their reasoning, technical understanding, "
        "or request a specific real-world example."
    )

    try:
        response = llm.invoke([
            HumanMessage(content=prompt)
        ])

        q = response.content.strip()

    except Exception:
        q = (
            "Can you share a specific example or technical "
            "trade-off from your experience?"
        )

    # Save follow-up interaction
    repo = InterviewRepository()

    try:
        repo.create_or_update_session(
            state["session_id"],
            state["role"],
            state["level"],
            state["language"]
        )

        repo.add_turn(
            session_id=state["session_id"],
            question_num=state.get("question_num", 1),
            question=state["current_question"],
            user_answer=state["user_answer"],
            action="followup",
            score=0,
            feedback="Follow-up probe asked."
        )

    finally:
        repo.close()

    return {
        "current_question": q,
        "feedback": "",
        "score": 0
    }


# --------------------------------------------------
# 4. EVALUATE ANSWER NODE
# --------------------------------------------------

def evaluate_node(state: InterviewState) -> dict:

    llm = get_llm(temperature=0.2)

    prompt = (
        f"You are evaluating a {state['level']} "
        f"{state['role']} candidate.\n"
        f"{_lang_hint(state['language'])}\n\n"

        f"Interview Question: {state['current_question']}\n"
        f"Candidate Answer: {state['user_answer']}\n\n"

        "Evaluate the candidate based on technical accuracy, "
        "relevance, clarity, practical knowledge, and depth.\n\n"

        "Format your response cleanly as:\n\n"

        "Score: X/10\n"
        "**What went well:** Explain the strengths.\n"
        "**How to improve:** Explain specific improvements.\n"
        "**Stronger sample answer:** Provide a better sample answer."
    )

    try:
        response = llm.invoke([
            HumanMessage(content=prompt)
        ])

        fb = response.content.strip()

    except Exception:
        fb = (
            "Score: 7/10\n\n"
            "**What went well:** Solid initial thought.\n\n"
            "**How to improve:** Add concrete examples, "
            "technical details, and measurable outcomes.\n\n"
            "**Stronger sample answer:** Explain the problem, "
            "your approach, and the results."
        )

    # Extract score
    match = re.search(r"Score:\s*(\d+(?:\.\d+)?)", fb)

    score_val = float(match.group(1)) if match else 7

    score_val = max(0, min(score_val, 10))

    # Save evaluation in database
    repo = InterviewRepository()

    try:
        repo.create_or_update_session(
            state["session_id"],
            state["role"],
            state["level"],
            state["language"]
        )

        repo.add_turn(
            session_id=state["session_id"],
            question_num=state.get("question_num", 1),
            question=state["current_question"],
            user_answer=state["user_answer"],
            action="evaluate",
            score=score_val,
            feedback=fb
        )

    finally:
        repo.close()

    return {
        "feedback": fb,
        "score": score_val
    }


# --------------------------------------------------
# 5. SUMMARIZE NODE
# --------------------------------------------------

def summarize_node(state: InterviewState) -> dict:

    transcript = state.get("transcript", [])

    scores = [
        t["score"]
        for t in transcript
        if t.get("score", 0) > 0
    ]

    avg_score = (
        round(sum(scores) / len(scores), 1)
        if scores else 0
    )

    llm = get_llm(temperature=0.3)

    prompt = (
        f"Summarize this mock interview for a "
        f"{state['level']} {state['role']} candidate.\n"
        f"{_lang_hint(state['language'])}\n\n"

        f"Average Interview Score: {avg_score}/10\n"
        f"Interview Transcript: {transcript}\n\n"

        "Generate a concise and professional final interview "
        "scorecard covering:\n\n"

        "1. Overall Readiness\n"
        "2. Top 2 Strengths\n"
        "3. Top 2 Areas of Improvement\n"
        "4. Recommendations for Improvement\n\n"

        "Keep the feedback practical and actionable."
    )

    try:
        response = llm.invoke([
            HumanMessage(content=prompt)
        ])

        summary = response.content.strip()

    except Exception:
        summary = (
            f"### Final Interview Scorecard\n\n"
            f"**Role:** {state['role']}\n\n"
            f"**Average Score:** {avg_score}/10\n\n"
            "**Top Strengths:** Clear communication "
            "and structured answers.\n\n"
            "**Areas of Improvement:** Practice technical "
            "depth and explaining trade-offs.\n\n"
            "**Next Steps:** Work on real-world examples "
            "and measurable outcomes."
        )

    # Save final scorecard
    repo = InterviewRepository()

    try:
        repo.create_or_update_session(
            state["session_id"],
            state["role"],
            state["level"],
            state["language"],
            overall_summary=summary
        )

    finally:
        repo.close()

    return {
        "overall_summary": summary
    }


# --------------------------------------------------
# 6. BUILD LANGGRAPH WORKFLOW
# --------------------------------------------------

def build_interview_graph():

    g = StateGraph(InterviewState)

    # Register nodes
    g.add_node("decide_action", decide_action_node)
    g.add_node("ask_question", ask_question_node)
    g.add_node("followup", followup_node)
    g.add_node("evaluate", evaluate_node)
    g.add_node("summarize", summarize_node)

    # Starting point
    g.add_edge(START, "decide_action")

    # Conditional routing
    g.add_conditional_edges(
        "decide_action",
        route_action,
        {
            "ask_question": "ask_question",
            "followup": "followup",
            "evaluate": "evaluate",
            "summarize": "summarize"
        }
    )

    # End nodes
    g.add_edge("ask_question", END)
    g.add_edge("followup", END)
    g.add_edge("evaluate", END)
    g.add_edge("summarize", END)

    return g.compile()


# --------------------------------------------------
# 7. INITIALIZE INTERVIEW GRAPH
# --------------------------------------------------

interview_graph = build_interview_graph()
