import re
import random

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
        "summarize",
    }:
        return {"action": state["action"]}

    ans = state.get("user_answer", "").strip()
    fu_count = state.get("followup_count", 0)
    max_fu = state.get("max_followups", 1)

    if len(ans.split()) < 14 and fu_count < max_fu:
        return {
            "action": "followup",
            "followup_count": fu_count + 1,
        }

    return {
        "action": "evaluate",
        "followup_count": 0,
    }


def route_action(state: InterviewState) -> str:
    return state.get("action", "evaluate")


# --------------------------------------------------
# 2. ASK QUESTION NODE
# --------------------------------------------------

def ask_question_node(state: InterviewState) -> dict:
    role = state.get("role", "Software Engineer")
    level = state.get("level", "Mid-Level")
    language = state.get("language", "English")

    # Interview topics based on role
    role_lower = role.lower()

    if "python" in role_lower or "backend" in role_lower:
        categories = [
            "Python fundamentals",
            "Object-oriented programming",
            "Django and Flask",
            "REST API development",
            "SQL and database optimization",
            "Multithreading and multiprocessing",
            "Debugging and troubleshooting",
            "System design",
            "Performance optimization",
            "Real-world project experience"
        ]
    elif "machine learning" in role_lower or "ml" in role_lower:
        categories = [
            "Machine learning fundamentals",
            "Model evaluation",
            "Feature engineering",
            "Deep learning",
            "NLP",
            "Data preprocessing",
            "Model deployment",
            "MLOps",
            "Real-world ML projects"
        ]
    elif "ai" in role_lower or "genai" in role_lower:
        categories = [
            "LLM fundamentals",
            "RAG architecture",
            "Vector databases",
            "LangChain and LangGraph",
            "Agentic AI",
            "Prompt engineering",
            "LLM evaluation",
            "Model deployment",
            "Real-world GenAI projects"
        ]
    else:
        categories = [
            "Technical fundamentals",
            "Problem solving",
            "System design",
            "Debugging",
            "Performance optimization",
            "Database concepts",
            "Real-world project experience"
        ]

    # Avoid recently used categories when possible
    recent_topics = [
        t.get("question_category")
        for t in state.get("transcript", [])
        if t.get("question_category")
    ]

    available_categories = [
        category for category in categories
        if category not in recent_topics[-3:]
    ]

    if not available_categories:
        available_categories = categories

    selected_category = random.choice(available_categories)

    prior_questions = [
        t.get("question", "").strip()
        for t in state.get("transcript", [])
        if t.get("question")
    ]

    previous_questions = "\n".join(
        f"- {question}" for question in prior_questions
    ) or "None"

    prompt = f"""
You are an experienced technical interviewer conducting
a realistic job interview.

Candidate role: {role}
Experience level: {level}
Interview language: {language}
Selected interview category: {selected_category}

Generate ONE realistic interview question that an interviewer
would commonly ask a candidate during an actual job interview.

Requirements:
1. The question must match the candidate's role and experience.
2. Ask a practical, technically relevant interview question.
3. Prefer scenario-based questions and real-world situations.
4. You may ask conceptual questions where appropriate.
5. Match the difficulty to the candidate's experience level.
6. Do not ask an overly basic question to an experienced candidate.
7. Do not repeat previously asked questions.
8. Do not provide answers, hints, or explanations.
9. Maximum 30 words.
10. Output only the question.

Previously asked questions:
{previous_questions}
"""

    try:
        llm = get_llm(temperature=0.7)
        response = llm.invoke([HumanMessage(content=prompt)])

        q = str(response.content).strip()
        q = re.sub(
            r"^(Interview Question.*?:\s*)",
            "",
            q,
            flags=re.IGNORECASE
        )
        q = q.strip().strip('"').strip("'")

        if not q:
            raise ValueError("Empty question generated")

    except Exception as e:
        print(f"Question generation error: {e}")
        q = (
            f"How would you handle a challenging real-world "
            f"problem related to {selected_category}?"
        )

    return {
        "current_question": q,
        "question_category": selected_category,
        "feedback": "",
        "score": 0,
        "followup_count": 0
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
        response = llm.invoke([HumanMessage(content=prompt)])
        q = response.content.strip()
    except Exception:
        q = (
            "Can you share a specific example or technical "
            "trade-off from your experience?"
        )

    repo = InterviewRepository()
    try:
        repo.create_or_update_session(
            state["session_id"],
            state["role"],
            state["level"],
            state["language"],
        )
        repo.add_turn(
            session_id=state["session_id"],
            question_num=state.get("question_num", 1),
            question=state["current_question"],
            user_answer=state["user_answer"],
            action="followup",
            score=0,
            feedback="Follow-up probe asked.",
        )
    finally:
        repo.close()

    return {
        "current_question": q,
        "feedback": "",
        "score": 0,
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

        "Evaluate the answer based on:\n"
        "1. Technical accuracy\n"
        "2. Relevance to the question\n"
        "3. Clarity\n"
        "4. Practical knowledge\n"
        "5. Depth of explanation\n\n"

        "IMPORTANT SCORING RULES:\n"
        "- If the answer is unrelated to the question, score it 0-1/10.\n"
        "- If the answer is empty or meaningless, score it 0/10.\n"
        "- If the answer only partially addresses the question, "
        "give a proportionate score.\n"
        "- Do not reward grammar alone.\n"
        "- Do not assume technical knowledge not demonstrated.\n"
        "- Evaluate according to the candidate's role and experience level.\n"
        "- Be strict but fair.\n"
        "- Never give a default score of 7.\n\n"

        "Format your response exactly as:\n\n"
        "Score: X/10\n\n"
        "**What went well:** Explain demonstrated strengths.\n\n"
        "**How to improve:** Explain specific improvements.\n\n"
        "**Stronger sample answer:** Provide a technically correct "
        "sample answer.\n"
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        fb = response.content.strip()

        if not fb:
            raise ValueError("Empty evaluation response")

    except Exception as exc:
        print(f"Evaluation LLM error: {exc}")

        fb = (
            "Score: 0/10\n\n"
            "**What went well:** Evaluation could not be completed.\n\n"
            "**How to improve:** Please retry the answer evaluation.\n\n"
            "**Stronger sample answer:** Review the question and "
            "provide a structured technical explanation."
        )

    match = re.search(
        r"Score:\s*(\d+(?:\.\d+)?)\s*/\s*10",
        fb,
        re.IGNORECASE
    )

    score_val = float(match.group(1)) if match else 0.0
    score_val = max(0.0, min(score_val, 10.0))

    repo = InterviewRepository()

    try:
        repo.create_or_update_session(
            state["session_id"],
            state["role"],
            state["level"],
            state["language"],
        )

        repo.add_turn(
            session_id=state["session_id"],
            question_num=state.get("question_num", 1),
            question=state["current_question"],
            user_answer=state["user_answer"],
            action="evaluate",
            score=score_val,
            feedback=fb,
        )

    finally:
        repo.close()

    return {
        "feedback": fb,
        "score": score_val,
        "followup_count": 0,
    }
    

# --------------------------------------------------
# 5. SUMMARIZE NODE
# --------------------------------------------------

def summarize_node(state: InterviewState) -> dict:
    transcript = state.get("transcript", [])

    # Include zero scores so irrelevant or incorrect answers
    # are not excluded from the final average.
    scores = []
    for turn in transcript:
        score = turn.get("score")
        if score is not None:
            try:
                scores.append(max(0.0, min(float(score), 10.0)))
            except (TypeError, ValueError):
                continue

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0
    total_questions = len(scores)

    # Prepare a clean transcript for the LLM.
    formatted_transcript = []
    for index, turn in enumerate(transcript, start=1):
        formatted_transcript.append({
            "question": turn.get("question", "Not available"),
            "candidate_answer": turn.get("answer", turn.get("user_answer", "")),
            "score": turn.get("score", 0),
            "feedback": turn.get("feedback", ""),
        })

    llm = get_llm(temperature=0.2)

    prompt = (
        f"You are a strict but fair senior technical interviewer.\n"
        f"Prepare the final mock interview scorecard for a "
        f"{state['level']} {state['role']} candidate.\n"
        f"{_lang_hint(state['language'])}\n\n"

        f"Average Interview Score: {avg_score}/10\n"
        f"Number of Evaluated Answers: {total_questions}\n"
        f"Interview Transcript:\n{formatted_transcript}\n\n"

        "Generate a concise, professional and evidence-based final "
        "interview scorecard using this exact structure:\n\n"

        "### 1. Overall Readiness\n"
        "- State the candidate's readiness for the target role.\n"
        "- Consider the average score and the quality of answers.\n"
        "- Be honest. Do not give an overly positive assessment.\n\n"

        "### 2. Top 2 Strengths\n"
        "- Mention only strengths demonstrated in the candidate's answers.\n"
        "- If no meaningful strengths were demonstrated, say so.\n\n"

        "### 3. Top 2 Areas of Improvement\n"
        "- Identify the most important technical or communication gaps.\n"
        "- Connect them to the actual interview answers.\n\n"

        "### 4. Recommendations for Improvement\n"
        "- Provide specific actions the candidate should take.\n"
        "- Suggest relevant topics, practical exercises or projects.\n\n"

        "IMPORTANT EVALUATION RULES:\n"
        "1. Base every conclusion on the transcript and individual scores.\n"
        "2. Do not invent skills, experience or strengths.\n"
        "3. If answers are irrelevant, meaningless or empty, reflect "
        "that honestly in the scorecard.\n"
        "4. Do not describe the candidate as technically strong if "
        "the answers do not demonstrate technical knowledge.\n"
        "5. Consider zero scores in the overall assessment.\n"
        "6. Keep the feedback constructive, specific and actionable.\n"
        "7. Do not change or recalculate the supplied average score.\n"
    )

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()

        if not summary:
            raise ValueError("The LLM returned an empty summary.")

    except Exception as exc:
        print(f"Interview summary generation error: {exc}")

        summary = (
            f"### Final Interview Scorecard\n\n"
            f"**Role:** {state['role']}\n\n"
            f"**Level:** {state['level']}\n\n"
            f"**Average Score:** {avg_score}/10\n\n"
            f"**Evaluated Answers:** {total_questions}\n\n"
            "### 1. Overall Readiness\n\n"
            "An AI-generated readiness assessment could not be "
            "completed. Review the individual answer scores and feedback.\n\n"
            "### 2. Top 2 Strengths\n\n"
            "A reliable strengths assessment could not be generated.\n\n"
            "### 3. Top 2 Areas of Improvement\n\n"
            "Review the individual interview feedback to identify "
            "the technical and communication gaps.\n\n"
            "### 4. Recommendations for Improvement\n\n"
            "Practice the interview topics where lower scores were "
            "received and work on explaining technical concepts "
            "with practical examples."
        )

    repo = InterviewRepository()
    try:
        repo.create_or_update_session(
            state["session_id"],
            state["role"],
            state["level"],
            state["language"],
            overall_summary=summary,
        )
    finally:
        repo.close()

    return {"overall_summary": summary}


# --------------------------------------------------
# 6. BUILD LANGGRAPH WORKFLOW
# --------------------------------------------------

def build_interview_graph():
    g = StateGraph(InterviewState)

    g.add_node("decide_action", decide_action_node)
    g.add_node("ask_question", ask_question_node)
    g.add_node("followup", followup_node)
    g.add_node("evaluate", evaluate_node)
    g.add_node("summarize", summarize_node)

    g.add_edge(START, "decide_action")

    g.add_conditional_edges(
        "decide_action",
        route_action,
        {
            "ask_question": "ask_question",
            "followup": "followup",
            "evaluate": "evaluate",
            "summarize": "summarize",
        },
    )

    g.add_edge("ask_question", END)
    g.add_edge("followup", END)
    g.add_edge("evaluate", END)
    g.add_edge("summarize", END)

    return g.compile()


interview_graph = build_interview_graph()