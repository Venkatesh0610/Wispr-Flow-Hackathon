import uuid
import streamlit as st
from config.settings import settings
from database.db import init_db
from database.repository import InterviewRepository
from llm.model import get_llm
from agent.graph import interview_graph
from voice.tts import synthesize_speech

st.set_page_config(page_title=settings.APP_NAME, page_icon="🎤", layout="wide")
init_db()

st.markdown(
    """
    <style>
    .stApp { background-color: #F8FAFC; color: #0F172A; }
    [data-testid="stSidebar"] { background-color: #EEF2FF; border-right: 1px solid #CBD5E1; }
    .mi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 14px;
        padding: 1.25rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.05);
    }
    .mi-q-card {
        background-color: #EEF2FF;
        border-left: 5px solid #4F46E5;
        border-radius: 12px;
        padding: 1.15rem 1.25rem;
        margin-bottom: 1rem;
    }
    .mi-wispr {
        background: linear-gradient(90deg, rgba(79,70,229,0.10) 0%, rgba(37,99,235,0.08) 100%);
        border: 1px solid #6366F1;
        border-radius: 12px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
        color: #1E1B4B;
        font-size: 0.92rem;
    }
    .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #0F172A !important;
        border: 2px solid #4F46E5 !important;
        border-radius: 12px !important;
        font-size: 1.02rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

defaults = {
    "session_id": f"int_{uuid.uuid4().hex[:10]}",
    "role": "Software Engineer",
    "level": "Mid-Level",
    "language": "English",
    "question_num": 1,
    "max_questions": 5,
    "current_question": "",
    "active_audio": None,
    "active_audio_mime": "",
    "feedback": "",
    "overall_summary": "",
    "chat_log": [],      # List of {"role": "interviewer" | "candidate", "text": str, "meta": str}
    "transcript": [],    # Structured turn records
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

def ask_new_question(q_num: int, is_first: bool = False):
    res = interview_graph.invoke(
        {
            "session_id": st.session_state.session_id,
            "role": st.session_state.role,
            "level": st.session_state.level,
            "language": st.session_state.language,
            "question_num": q_num,
            "max_questions": st.session_state.max_questions,
            "current_question": "",
            "user_answer": "",
            "action": "ask_question",
            "transcript": st.session_state.transcript,
            "score": 0,
            "feedback": "",
            "overall_summary": "",
        }
    )
    q_text = res["current_question"]
    st.session_state.current_question = q_text
    st.session_state.feedback = ""
    label = f"Question {q_num}" if is_first else f"Question {q_num} of {st.session_state.max_questions}"
    st.session_state.chat_log.append({"role": "interviewer", "text": q_text, "meta": label})
    audio_bytes, mime = synthesize_speech(q_text, st.session_state.language)
    st.session_state.active_audio = audio_bytes
    st.session_state.active_audio_mime = mime

def begin_session(role: str):
    st.session_state.role = role
    st.session_state.session_id = f"int_{uuid.uuid4().hex[:10]}"
    st.session_state.question_num = 1
    st.session_state.feedback = ""
    st.session_state.overall_summary = ""
    st.session_state.chat_log = []
    st.session_state.transcript = []
    with st.spinner("Interviewer is preparing your first question..."):
        ask_new_question(1, is_first=True)
    st.rerun()

with st.sidebar:
    st.markdown(f"## 🎤 {settings.APP_NAME}")
    try:
        get_llm().invoke("Hi")
        st.caption(f"🟢 Groq Online ({settings.GROQ_MODEL})")
    except Exception:
        st.caption("🟡 Demo Fallback Mode")
    st.caption(f"🔊 TTS Engine: {settings.TTS_ENGINE}")
    st.divider()

    st.session_state.role = st.text_input("Target Role", st.session_state.role)
    st.session_state.level = st.selectbox(
        "Experience Level",
        settings.EXPERIENCE_LEVELS,
        index=settings.EXPERIENCE_LEVELS.index(st.session_state.level),
    )
    st.session_state.language = st.selectbox(
        "Interview Language",
        settings.SUPPORTED_LANGUAGES,
        index=settings.SUPPORTED_LANGUAGES.index(st.session_state.language),
    )
    st.session_state.max_questions = st.slider("Number of Questions", 2, 8, st.session_state.max_questions)

    if st.button("🚀 Start New Interview", type="primary", use_container_width=True):
        begin_session(st.session_state.role)

    st.divider()
    st.markdown("### Past Interviews")
    repo = InterviewRepository()
    try:
        past = repo.list_sessions(limit=5)
    finally:
        repo.close()
    for p in past:
        st.caption(f"• **{p.role}** ({p.level} • {p.language})")

st.title("🎤 Conversational Mock Interview")
st.caption(settings.TAGLINE)

if not st.session_state.current_question:
    st.info("Pick a role or click **Start New Interview** in the sidebar. The AI will ask the first question, you will answer, and the conversation will continue automatically.")
    cols = st.columns(4)
    for i, r in enumerate(settings.SUGGESTED_ROLES):
        if cols[i].button(f"Start: {r}", use_container_width=True):
            begin_session(r)
else:
    st.progress(
        st.session_state.question_num / st.session_state.max_questions,
        text=f"Question {st.session_state.question_num} of {st.session_state.max_questions} • {st.session_state.role} ({st.session_state.level})",
    )

    # Ongoing AI -> User -> AI Conversation Stream
    for msg in st.session_state.chat_log:
        if msg["role"] == "interviewer":
            with st.chat_message("assistant"):
                st.caption(msg["meta"])
                st.markdown(msg["text"])
        else:
            with st.chat_message("user"):
                st.markdown(msg["text"])

    # Audio playback for the latest interviewer question/follow-up
    if st.session_state.active_audio:
        st.audio(st.session_state.active_audio, format=st.session_state.active_audio_mime, autoplay=True)

    # Active Question Prompt Card & Answer Input
    st.markdown(
        f'<div class="mi-q-card"><b>Current Question to Answer:</b><br><span style="font-size:1.05rem;">{st.session_state.current_question}</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="mi-wispr">🎙️ <b>Your Turn to Answer:</b> Click inside the box below, dictate with Wispr Flow '
        '(or type), and submit. If your answer is brief, the AI asks a follow-up; once answered, it evaluates and continues.</div>',
        unsafe_allow_html=True,
    )

    with st.form("live_interview_form", clear_on_submit=True):
        answer_input = st.text_area(
            "Dictate your answer with Wispr Flow:",
            placeholder="Speak your answer naturally, review it, then submit…",
            height=120,
        )
        col_a, col_b = st.columns(2)
        submit_ans = col_a.form_submit_button("Submit Answer & Continue ➤", type="primary", use_container_width=True)
        eval_now = col_b.form_submit_button("Evaluate & Move On", use_container_width=True)

        if (submit_ans or eval_now) and answer_input.strip():
            spoken_ans = answer_input.strip()
            st.session_state.chat_log.append({"role": "candidate", "text": spoken_ans, "meta": "You"})

            with st.spinner("Interviewer is responding to your answer..."):
                res = interview_graph.invoke(
                    {
                        "session_id": st.session_state.session_id,
                        "role": st.session_state.role,
                        "level": st.session_state.level,
                        "language": st.session_state.language,
                        "question_num": st.session_state.question_num,
                        "max_questions": st.session_state.max_questions,
                        "current_question": st.session_state.current_question,
                        "user_answer": spoken_ans,
                        "action": "evaluate" if eval_now else "",
                        "transcript": st.session_state.transcript,
                        "score": 0,
                        "feedback": "",
                        "overall_summary": "",
                    }
                )

            action_taken = res.get("action", "evaluate")
            st.session_state.transcript.append(
                {
                    "question_num": st.session_state.question_num,
                    "question": st.session_state.current_question,
                    "user_answer": spoken_ans,
                    "action": action_taken,
                    "score": res.get("score", 0),
                    "feedback": res.get("feedback", ""),
                }
            )

            if action_taken == "followup":
                # Follow-up question becomes the active question so the user answers it next
                followup_q = res["current_question"]
                st.session_state.current_question = followup_q
                st.session_state.feedback = ""
                st.session_state.chat_log.append({"role": "interviewer", "text": followup_q, "meta": "Follow-Up Question"})
                audio_bytes, mime = synthesize_speech(followup_q, st.session_state.language)
                st.session_state.active_audio = audio_bytes
                st.session_state.active_audio_mime = mime
            else:
                fb = res.get("feedback", "")
                st.session_state.feedback = fb
                st.session_state.chat_log.append({"role": "interviewer", "text": fb, "meta": "Evaluation & Feedback"})
                # Automatically advance to the next main question if questions remain
                if st.session_state.question_num < st.session_state.max_questions:
                    st.session_state.question_num += 1
                    ask_new_question(st.session_state.question_num, is_first=False)

            st.rerun()

    if st.session_state.question_num >= st.session_state.max_questions and st.session_state.feedback and not st.session_state.overall_summary:
        if st.button("🏁 Finish Interview & Generate Final Scorecard", type="primary"):
            with st.spinner("Generating final scorecard..."):
                res = interview_graph.invoke(
                    {
                        "session_id": st.session_state.session_id,
                        "role": st.session_state.role,
                        "level": st.session_state.level,
                        "language": st.session_state.language,
                        "question_num": st.session_state.question_num,
                        "max_questions": st.session_state.max_questions,
                        "current_question": "",
                        "user_answer": "",
                        "action": "summarize",
                        "transcript": st.session_state.transcript,
                        "score": 0,
                        "feedback": "",
                        "overall_summary": "",
                    }
                )
                st.session_state.overall_summary = res.get("overall_summary", "")
            st.rerun()

    if st.session_state.overall_summary:
        st.success("Interview Completed! Here is your final scorecard:")
        st.markdown(f'<div class="mi-card">{st.session_state.overall_summary}</div>', unsafe_allow_html=True)
