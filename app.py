import base64
import html
import uuid
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from config.settings import settings
from database.db import init_db
from database.repository import InterviewRepository
from agent.graph import interview_graph
from voice.tts import synthesize_speech
from report_ui import render_interview_report


# -----------------------------------------------------------------------------
# PAGE + DATABASE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="VoiceLearn AI - Mock Interview",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded"
)
init_db()

# One custom component handles both interviewer audio playback and candidate
# dictation capture. Its frontend is components/voice_input/index.html.
VOICE_INPUT_DIR = Path(__file__).parent / "components" / "voice_input"
voice_answer_component = components.declare_component(
    "voice_answer_idle_submit",
    path=str(VOICE_INPUT_DIR),
)

def apply_interview_layout():
    phase = st.session_state.get("interview_phase", "setup")

    is_live_interview = phase in {
        "interviewer",
        "candidate",
        "processing"
    }

    if is_live_interview:
        st.markdown("""
            <style>
                /* Hide sidebar during interview */
                [data-testid="stSidebar"] {
                    display: none !important;
                }

                /* Hide unnecessary top header space */
                [data-testid="stHeader"] {
                    height: 0rem !important;
                    min-height: 0rem !important;
                }

                /* Use full browser width */
                [data-testid="stAppViewContainer"] {
                    height: 100vh !important;
                    overflow: hidden !important;
                }

                [data-testid="stMain"] {
                    height: 100vh !important;
                    overflow-y: auto !important;
                }

                [data-testid="stMainBlockContainer"] {
                    max-width: 100% !important;
                    width: 100% !important;
                    padding-top: 0.5rem !important;
                    padding-bottom: 0.5rem !important;
                    padding-left: 1.5rem !important;
                    padding-right: 1.5rem !important;
                }

                /* Reduce unnecessary vertical gaps */
                [data-testid="stVerticalBlock"] {
                    gap: 0.5rem !important;
                }

                /* Compact headings */
                h1 {
                    margin-top: 0.2rem !important;
                    margin-bottom: 0.4rem !important;
                }

                h2, h3 {
                    margin-top: 0.2rem !important;
                    margin-bottom: 0.3rem !important;
                }

                /* Remove excess paragraph spacing */
                p {
                    margin-bottom: 0.3rem !important;
                }

                /* Keep buttons compact */
                .stButton {
                    margin-bottom: 0 !important;
                }

                /* Reduce default form spacing */
                [data-testid="stForm"] {
                    padding: 0.5rem !important;
                }

                /* Hide footer */
                footer {
                    visibility: hidden;
                }
            </style>
        """, unsafe_allow_html=True)
# -----------------------------------------------------------------------------
# STYLES
# -----------------------------------------------------------------------------

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', system-ui, sans-serif;
    }

    /* Main application background */
    .stApp {
        background: linear-gradient(135deg, #F1F5F9 0%, #EAF1FB 55%, #F0FDFA 100%);
        color: #0F172A;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0B1220 0%, #172554 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    [data-testid="stSidebar"] * {
        color: #527aa3 !important;
    }

    [data-testid="stSidebar"] .stCaption {
        color: #94A3B8 !important;
    }

    /* Top header */
    .studio-topbar {
        background: linear-gradient(120deg, #0B1220 0%, #172554 65%, #1E40AF 100%);
        color: #FFFFFF;
        border-radius: 16px;
        padding: 1rem 1.3rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.6rem;
        box-shadow: 0 8px 24px -10px rgba(15,23,42,0.35);
    }

    /* Interviewer and candidate cards */
    .split-card {
        background: #FFFFFF;
        border: 1.5px solid #DCE5F0;
        border-radius: 18px;
        padding: 1rem;
        min-height: 240px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: 0 6px 20px -10px rgba(15,23,42,0.12);
        transition: all 0.2s ease;
    }

    .split-card-active-ai {
        border-color: #2563EB;
        box-shadow: 0 0 0 3px rgba(37,99,235,0.12),
                    0 10px 24px -12px rgba(37,99,235,0.3);
    }

    .split-card-active-user {
        border-color: #0D9488;
        box-shadow: 0 0 0 3px rgba(13,148,136,0.12),
                    0 10px 24px -12px rgba(13,148,136,0.3);
    }

    .split-card-processing {
        border-color: #D97706;
        box-shadow: 0 0 0 3px rgba(217,119,6,0.12);
    }

    /* Participant header */
    .peer-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 0.7rem;
        gap: 0.5rem;
    }

    .peer-identity {
        display: flex;
        align-items: center;
        gap: 0.7rem;
    }

    .peer-avatar {
        width: 42px;
        height: 42px;
        border-radius: 13px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
        color: #FFFFFF;
        flex-shrink: 0;
    }

    .avatar-ai {
        background: linear-gradient(135deg, #2563EB, #1D4ED8);
    }

    .avatar-user {
        background: linear-gradient(135deg, #0D9488, #0F766E);
    }

    /* Audio wave animation */
    .wave-box {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        height: 26px;
        padding: 0 6px;
    }

    .wave-bar {
        width: 4px;
        height: 8px;
        border-radius: 999px;
        background: #94A3B8;
        opacity: 0.45;
    }

    .wave-active-ai .wave-bar {
        background: #2563EB;
        opacity: 1;
        animation: eqBounce 0.9s infinite ease-in-out;
    }

    .wave-active-user .wave-bar {
        background: #0D9488;
        opacity: 1;
        animation: eqBounce 0.8s infinite ease-in-out;
    }

    .wave-bar:nth-child(2) { animation-delay: 0.15s; }
    .wave-bar:nth-child(3) { animation-delay: 0.30s; }
    .wave-bar:nth-child(4) { animation-delay: 0.45s; }
    .wave-bar:nth-child(5) { animation-delay: 0.60s; }

    @keyframes eqBounce {
        0%, 100% { height: 6px; }
        50% { height: 24px; }
    }

    /* Interview question */
    .question-bubble {
        background: #EFF6FF;
        border-left: 4px solid #2563EB;
        border-radius: 0 12px 12px 0;
        padding: 0.8rem 1rem;
        font-size: 0.96rem;
        font-weight: 600;
        line-height: 1.45;
        color: #172554;
        margin: 0.4rem 0 0.7rem 0;
    }

    /* Processing state */
    .processing-banner {
        background: linear-gradient(110deg, #FFFBEB 0%, #FEF3C7 100%);
        border: 1px solid #F59E0B;
        border-radius: 13px;
        padding: 0.8rem 1rem;
        margin: 0.5rem 0 0.7rem 0;
        color: #78350F;
    }

    /* Information banner */
    .info-banner {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: 12px;
        padding: 0.7rem 0.9rem;
        color: #1E40AF;
        margin: 0.4rem 0 0.7rem 0;
    }

    /* Feedback card */
    .mi-card {
        background: #FFFFFF;
        border: 1px solid #DCE5F0;
        border-radius: 14px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.7rem;
    }

    /* Answer input */
    .stTextArea textarea {
        background: #FFFFFF !important;
        color: #0F172A !important;
        border: 1.5px solid #2563EB !important;
        border-radius: 11px !important;
        font-size: 0.9rem !important;
        line-height: 1.45 !important;
    }

    .stTextArea textarea:focus {
        border-color: #0D9488 !important;
        box-shadow: 0 0 0 2px rgba(13,148,136,0.12) !important;
    }

    /* Buttons */
    div.stButton > button,
    div.stFormSubmitButton > button {
        border-radius: 10px;
        font-weight: 700;
        border: none;
        transition: all 0.2s ease;
    }

    div.stButton > button[kind="primary"],
    div.stFormSubmitButton > button[kind="primary"] {
        background: linear-gradient(120deg, #2563EB, #1D4ED8);
        color: #FFFFFF;
    }

    div.stButton > button[kind="primary"]:hover {
        background: linear-gradient(120deg, #1D4ED8, #1E40AF);
        box-shadow: 0 4px 12px rgba(37,99,235,0.25);
    }

    /* Compact typography and spacing */
    h1, h2, h3 {
        color: #0F172A;
    }

    [data-testid="stCaptionContainer"] {
        color: #64748B;
    }

    /* Live interview compact layout */
    @media (max-height: 850px) {
        .split-card {
            min-height: 190px;
            padding: 0.8rem;
        }

        .question-bubble {
            font-size: 0.88rem;
            padding: 0.65rem 0.8rem;
        }

        .peer-avatar {
            width: 36px;
            height: 36px;
            font-size: 1rem;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)



# -----------------------------------------------------------------------------
# SESSION STATE
# interview_phase: setup | interviewer | candidate | processing | completed
# -----------------------------------------------------------------------------
defaults = {
    "session_id": f"int_{uuid.uuid4().hex[:10]}",
    "role": "Software Engineer",
    "level": "Mid-Level",
    "language": "English",
    "question_num": 1,
    "main_questions_asked": 0,
    "max_questions": 3,
    "followup_count": 0,
    "max_followups": 1,
    "is_followup_turn": False,
    "current_question": "",
    "active_audio": None,
    "active_audio_mime": "audio/wav",
    "audio_playing": False,
    "feedback": "",
    "overall_summary": "",
    "interview_ended": False,
    "interview_phase": "setup",
    "processing_stage": "",
    "chat_log": [],
    "transcript": [],
    "force_eval_next": False,
    "pending_answer": "",
    "turn_nonce": 0,
    "last_auto_submit_token": "",
    "last_error": "",
}

if "show_extra_panels" not in st.session_state:
    st.session_state.show_extra_panels = False

apply_interview_layout()
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def _safe_index(options, selected):
    try:
        return list(options).index(selected)
    except (ValueError, TypeError):
        return 0


def _wave_html(active_class=""):
    class_name = f"wave-box {active_class}".strip()
    bars = "".join('<span class="wave-bar"></span>' for _ in range(5))
    return f'<div class="{class_name}">{bars}</div>'


def _set_phase(phase, processing_stage=""):
    st.session_state.interview_phase = phase
    st.session_state.processing_stage = processing_stage


def _graph_input(action, question_num=None, user_answer=""):
    return {
        "session_id": st.session_state.session_id,
        "role": st.session_state.role,
        "level": st.session_state.level,
        "language": st.session_state.language,
        "question_num": question_num or st.session_state.question_num,
        "max_questions": st.session_state.max_questions,
        "followup_count": st.session_state.followup_count,
        "max_followups": st.session_state.max_followups,
        "current_question": st.session_state.current_question,
        "user_answer": user_answer,
        "action": action,
        "transcript": st.session_state.transcript,
        "score": 0,
        "feedback": "",
        "overall_summary": "",
    }


# -----------------------------------------------------------------------------
# INTERVIEW ACTIONS
# -----------------------------------------------------------------------------
def ask_new_question(q_num: int):
    st.session_state.followup_count = 0
    st.session_state.is_followup_turn = False
    st.session_state.feedback = ""
    st.session_state.turn_nonce += 1
    st.session_state.current_question = ""
    st.session_state.active_audio = None
    _set_phase("processing", "Preparing your next interview question...")

    result = interview_graph.invoke(_graph_input("ask_question", question_num=q_num))
    question_text = str(result.get("current_question", "")).strip()
    if not question_text:
        raise ValueError("The interviewer did not return a question.")

    st.session_state.question_num = q_num
    st.session_state.main_questions_asked = q_num
    st.session_state.current_question = question_text
    st.session_state.chat_log.append(
        {
            "role": "interviewer",
            "text": question_text,
            "meta": f"Question {q_num} of {st.session_state.max_questions}",
        }
    )

    try:
        audio_bytes, mime_type = synthesize_speech(
            question_text, st.session_state.language
        )
        if not audio_bytes:
            raise ValueError("The TTS engine returned empty audio.")
        st.session_state.active_audio = audio_bytes
        st.session_state.active_audio_mime = mime_type or "audio/wav"
        st.session_state.audio_playing = True
        _set_phase("interviewer")
    except Exception as exc:
        # Keep the text question available and skip directly to candidate input.
        st.session_state.active_audio = None
        st.session_state.audio_playing = False
        st.session_state.last_error = f"Text-to-speech was unavailable: {exc}"
        _set_phase("candidate")


def begin_session(role: str):
    st.session_state.role = role
    st.session_state.session_id = f"int_{uuid.uuid4().hex[:10]}"
    st.session_state.question_num = 1
    st.session_state.main_questions_asked = 0
    st.session_state.followup_count = 0
    st.session_state.is_followup_turn = False
    st.session_state.feedback = ""
    st.session_state.overall_summary = ""
    st.session_state.interview_ended = False
    st.session_state.interview_phase = "processing"
    st.session_state.processing_stage = "Starting your interview..."
    st.session_state.chat_log = []
    st.session_state.transcript = []
    st.session_state.force_eval_next = False
    st.session_state.last_error = ""
    st.session_state.turn_nonce += 1

    try:
        ask_new_question(1)
    except Exception as exc:
        st.session_state.last_error = f"Could not start the interview: {exc}"
        _set_phase("setup")
    st.rerun()


def generate_final_report():
    _set_phase("processing", "Preparing your final interview scorecard...")
    result = interview_graph.invoke(
        {
            "session_id": st.session_state.session_id,
            "role": st.session_state.role,
            "level": st.session_state.level,
            "language": st.session_state.language,
            "question_num": st.session_state.main_questions_asked,
            "max_questions": st.session_state.max_questions,
            "followup_count": 0,
            "max_followups": st.session_state.max_followups,
            "current_question": "",
            "user_answer": "",
            "action": "summarize",
            "transcript": st.session_state.transcript,
            "score": 0,
            "feedback": "",
            "overall_summary": "",
        }
    )
    st.session_state.overall_summary = result.get("overall_summary", "")
    st.session_state.interview_ended = True
    st.session_state.active_audio = None
    st.session_state.audio_playing = False
    _set_phase("completed")


def process_answer(spoken_answer: str, force_eval: bool = False):
    spoken_answer = spoken_answer.strip()
    if not spoken_answer:
        st.warning("Please dictate or type an answer before submitting.")
        return

    st.session_state.chat_log.append(
        {"role": "candidate", "text": spoken_answer, "meta": "Your answer"}
    )
    st.session_state.pending_answer = ""
    _set_phase("processing", "Sending your answer to the AI interviewer...")

    try:
        with st.status(
            "AI interviewer is reviewing your answer...",
            expanded=True,
        ) as status:
            status.write("Your answer has been received.")
            status.write("Evaluating the response against the interview question.")
            result = interview_graph.invoke(
                _graph_input(
                    "evaluate" if force_eval else "",
                    user_answer=spoken_answer,
                )
            )
            status.write("Preparing the interviewer's next turn.")
            status.update(
                label="Response processed",
                state="complete",
                expanded=False,
            )

        action_taken = result.get("action", "evaluate")
        st.session_state.followup_count = result.get(
            "followup_count", st.session_state.followup_count
        )

        st.session_state.transcript.append(
            {
                "question_num": st.session_state.question_num,
                "question": st.session_state.current_question,
                "user_answer": spoken_answer,
                "action": action_taken,
                "score": result.get("score", 0),
                "feedback": result.get("feedback", ""),
            }
        )

        if action_taken == "followup":
            followup_question = str(result.get("current_question", "")).strip()
            if not followup_question:
                raise ValueError("The interviewer returned an empty follow-up question.")

            st.session_state.current_question = followup_question
            st.session_state.is_followup_turn = True
            st.session_state.feedback = ""
            st.session_state.turn_nonce += 1
            st.session_state.chat_log.append(
                {
                    "role": "interviewer",
                    "text": followup_question,
                    "meta": f"Follow-up on Question {st.session_state.question_num}",
                }
            )
            try:
                audio_bytes, mime_type = synthesize_speech(
                    followup_question, st.session_state.language
                )
                if not audio_bytes:
                    raise ValueError("The TTS engine returned empty audio.")
                st.session_state.active_audio = audio_bytes
                st.session_state.active_audio_mime = mime_type or "audio/wav"
                st.session_state.audio_playing = True
                _set_phase("interviewer")
            except Exception as exc:
                st.session_state.active_audio = None
                st.session_state.audio_playing = False
                st.session_state.last_error = f"Follow-up audio unavailable: {exc}"
                _set_phase("candidate")

        else:
            feedback = result.get("feedback", "")
            st.session_state.feedback = feedback
            st.session_state.followup_count = 0
            st.session_state.is_followup_turn = False
            st.session_state.chat_log.append(
                {
                    "role": "interviewer",
                    "text": feedback,
                    "meta": (
                        f"Evaluation • Question {st.session_state.question_num} "
                        f"of {st.session_state.max_questions}"
                    ),
                }
            )

            if st.session_state.main_questions_asked < st.session_state.max_questions:
                next_question_num = st.session_state.main_questions_asked + 1
                ask_new_question(next_question_num)
            else:
                generate_final_report()

    except Exception as exc:
        st.session_state.last_error = f"We couldn't process that answer: {exc}"
        _set_phase("candidate")
        st.error(st.session_state.last_error)


def reset_to_settings():
    st.session_state.current_question = ""
    st.session_state.active_audio = None
    st.session_state.audio_playing = False
    st.session_state.feedback = ""
    st.session_state.interview_ended = False
    st.session_state.interview_phase = "setup"
    st.session_state.transcript = []
    st.session_state.chat_log = []
    st.rerun()


# -----------------------------------------------------------------------------
# SIDEBAR SETTINGS
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(f"## 🎙️ {settings.APP_NAME}")
    model_label = getattr(
        settings,
        "GROQ_MODEL",
        getattr(settings, "OLLAMA_MODEL", "Configured LLM"),
    )
    st.caption(f"🤖 Model: {model_label}")
    st.caption(f"🔊 Voice: {settings.TTS_ENGINE}")
    st.divider()

    st.session_state.role = st.text_input(
        "Target Role", value=st.session_state.role
    )
    st.session_state.level = st.selectbox(
        "Experience Level",
        settings.EXPERIENCE_LEVELS,
        index=_safe_index(settings.EXPERIENCE_LEVELS, st.session_state.level),
    )
    st.session_state.language = st.selectbox(
        "Interview Language",
        settings.SUPPORTED_LANGUAGES,
        index=_safe_index(settings.SUPPORTED_LANGUAGES, st.session_state.language),
    )
    st.session_state.max_questions = st.slider(
        "Number of Questions",
        min_value=1,
        max_value=8,
        value=int(st.session_state.max_questions),
    )

    st.divider()
    st.markdown("### 🎤 Wispr Flow setup")
    st.caption(
        "After the interviewer finishes speaking, the answer field is focused automatically. "
        "Activate Wispr Flow with your normal shortcut. The app submits after 5 seconds without new text."
    )

    if st.button(
        "🚀 Start Mock Interview",
        type="primary",
        use_container_width=True,
    ):
        begin_session(st.session_state.role)

    st.divider()
    st.markdown("### Recent Sessions")
    try:
        repository = InterviewRepository()
        try:
            recent_sessions = repository.list_sessions(limit=5)
        finally:
            repository.close()
        if recent_sessions:
            for session in recent_sessions:
                st.caption(
                    f"• **{session.role}** ({session.level} • {session.language})"
                )
        else:
            st.caption("No previous sessions yet.")
    except Exception as exc:
        st.caption(f"Session history unavailable: {exc}")


# -----------------------------------------------------------------------------
# MAIN HEADER
# -----------------------------------------------------------------------------
current_question_number = min(
    st.session_state.main_questions_asked,
    st.session_state.max_questions,
)

st.markdown(
    f"""
    <div class="studio-topbar">
        <div>
            <h3 style="margin:0; color:#FFFFFF;">🎙️ Live Interview Room</h3>
            <div style="color:#CBD5E1; font-size:0.88rem;">
                {html.escape(str(st.session_state.role))} •
                {html.escape(str(st.session_state.level))} •
                {html.escape(str(st.session_state.language))}
            </div>
        </div>
        <div style="background:rgba(255,255,255,0.14); padding:0.45rem 0.9rem; border-radius:999px; font-size:0.85rem; font-weight:700;">
            Question {current_question_number} / {st.session_state.max_questions}
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# -----------------------------------------------------------------------------
# SETUP / REPORT / LIVE INTERVIEW
# -----------------------------------------------------------------------------
if st.session_state.interview_phase == "setup" and not st.session_state.interview_ended:
    st.markdown('<div class="mi-card">', unsafe_allow_html=True)
    st.markdown("### Ready to Start Your Mock Interview?")
    st.write(
        f"You will complete **{st.session_state.max_questions}** dynamically generated "
        "interview questions. Listen to each question, dictate your response using "
        "Wispr Flow, and submit it for AI evaluation."
    )
    st.markdown("</div>", unsafe_allow_html=True)

    suggested_roles = list(settings.SUGGESTED_ROLES)
    if suggested_roles:
        columns = st.columns(min(4, len(suggested_roles)))
        for index, suggested_role in enumerate(suggested_roles):
            if columns[index % len(columns)].button(
                f"Start: {suggested_role}",
                use_container_width=True,
                key=f"suggested_role_{index}",
            ):
                begin_session(suggested_role)

elif st.session_state.interview_ended or st.session_state.interview_phase == "completed":
    render_interview_report(
        role=st.session_state.role,
        level=st.session_state.level,
        language=st.session_state.language,
        max_questions=st.session_state.max_questions,
        overall_summary=st.session_state.overall_summary,
        transcript=st.session_state.transcript,
        on_restart=lambda: begin_session(st.session_state.role),
        on_change_settings=reset_to_settings,
    )

else:
    # Full-width state banner: this appears above both speaker panels.
    phase = st.session_state.interview_phase
    if phase == "processing":
        st.markdown(
            f"""
            <div class="processing-banner">
                <div style="font-size:1.02rem; font-weight:800;">⚙️ AI Interviewer is working</div>
                <div style="font-size:0.9rem; margin-top:0.25rem;">
                    {html.escape(st.session_state.processing_stage or 'Please wait...')}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    elif phase == "interviewer":
        st.markdown(
            '<div class="info-banner">🔊 <b>Interviewer turn:</b> Listen to the question. '
            'The candidate panel will activate automatically when the audio ends.</div>',
            unsafe_allow_html=True,
        )
    elif phase == "candidate":
        st.success("Your turn — the answer field will focus automatically. Activate Wispr Flow with your usual shortcut.")

    if st.session_state.last_error:
        st.warning(st.session_state.last_error)
        st.session_state.last_error = ""

    # Process a submitted answer at page level (not inside either speaker column),
    # so the processing status spans the full interview workspace.
    if phase == "processing" and st.session_state.pending_answer:
        answer_to_process = st.session_state.pending_answer
        force_eval = bool(st.session_state.force_eval_next)
        st.session_state.force_eval_next = False
        process_answer(answer_to_process, force_eval=force_eval)
        st.rerun()

    is_processing = phase == "processing"
    is_interviewer_turn = phase == "interviewer" and bool(st.session_state.audio_playing)
    is_candidate_turn = phase == "candidate"

    left_col, right_col = st.columns(2, gap="large")

    # -------------------------------------------------------------------------
    # INTERVIEWER PANEL
    # -------------------------------------------------------------------------
    with left_col:
        ai_card_class = (
            "split-card split-card-active-ai"
            if is_interviewer_turn
            else "split-card"
        )
        ai_status = (
            "🔊 Question ready — listen to the interviewer"
            if is_interviewer_turn
            else "Interviewer"
        )
        turn_label = (
            f"Follow-up • Question {st.session_state.question_num}"
            if st.session_state.is_followup_turn
            else f"Question {st.session_state.main_questions_asked} of {st.session_state.max_questions}"
        )
        safe_question = html.escape(str(st.session_state.current_question))

        st.markdown(
            f"""
            <div class="{ai_card_class}">
                <div>
                    <div class="peer-header">
                        <div class="peer-identity">
                            <div class="peer-avatar avatar-ai">👔</div>
                            <div>
                                <div style="font-weight:800; font-size:1.05rem; color:#0F172A;">Alex • Interviewer</div>
                                <div style="font-size:0.8rem; color:#64748B; font-weight:600;">{turn_label}</div>
                            </div>
                        </div>
                        {_wave_html('wave-active-ai' if is_interviewer_turn else '')}
                    </div>
                    <div style="font-size:0.82rem; font-weight:700; color:#4338CA; margin-bottom:0.35rem;">{ai_status}</div>
                    <div class="question-bubble">“{safe_question}”</div>
                </div>
                <div style="font-size:0.82rem; color:#64748B;">
                    Listen to the question. You can replay the audio if needed.
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_interviewer_turn and st.session_state.active_audio:
            audio_b64 = base64.b64encode(st.session_state.active_audio).decode("utf-8")
            audio_result = voice_answer_component(
                mode="interviewer",
                audio_base64=audio_b64,
                audio_mime=st.session_state.active_audio_mime,
                idle_seconds=5,
                key=f"voice_interaction_{st.session_state.turn_nonce}",
                default=None,
                height=110,
            )
            if (
                isinstance(audio_result, dict)
                and audio_result.get("event") == "audio_finished"
                and st.session_state.audio_playing
            ):
                st.session_state.audio_playing = False
                _set_phase("candidate")
                st.rerun()
        elif not st.session_state.active_audio:
            st.caption("Audio is unavailable for this question. Read the question above; your answer panel is ready.")

    # -------------------------------------------------------------------------
    # CANDIDATE PANEL + WISPR FLOW INPUT
    # -------------------------------------------------------------------------
    with right_col:
        if is_processing:
            candidate_card_class = "split-card split-card-processing"
            candidate_status = "⚙️ Your answer is being processed"
            candidate_wave = ""
        elif is_candidate_turn:
            candidate_card_class = "split-card split-card-active-user"
            candidate_status = "🟢 Your turn — Wispr Flow dictation is ready"
            candidate_wave = "wave-active-user"
        else:
            candidate_card_class = "split-card"
            candidate_status = "⏳ Waiting for the interviewer"
            candidate_wave = ""

        st.markdown(
            f"""
            <div class="{candidate_card_class}">
                <div>
                    <div class="peer-header">
                        <div class="peer-identity">
                            <div class="peer-avatar avatar-user">🧑🏽‍💻</div>
                            <div>
                                <div style="font-weight:800; font-size:1.05rem; color:#0F172A;">You • Candidate</div>
                                <div style="font-size:0.8rem; color:#64748B; font-weight:600;">Wispr Flow Dictation</div>
                            </div>
                        </div>
                        {_wave_html(candidate_wave)}
                    </div>
                    <div style="font-size:0.9rem; font-weight:700; color:#0F172A;">{candidate_status}</div>
                    <div style="font-size:0.83rem; color:#475569; margin-top:0.6rem;">
                        The answer box is focused automatically. Activate Wispr Flow using your normal shortcut and speak naturally.
                        After 5 seconds without new dictated text, your answer is submitted automatically.
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if is_candidate_turn:
            st.markdown(
                """
                <div class="info-banner">
                    <b>🎙️ Automatic voice capture</b><br>
                    Your answer field is focused automatically. Start Wispr Flow with your usual shortcut.
                    When no new text arrives for <b>5 seconds</b>, the answer is submitted to the interviewer.
                </div>
                """,
                unsafe_allow_html=True,
            )

            component_result = voice_answer_component(
                mode="candidate",
                idle_seconds=5,
                placeholder="Your answer will appear here as Wispr Flow dictates... You can also type naturally.",
                key=f"voice_interaction_{st.session_state.turn_nonce}",
                default=None,
                height=180,
            )

            if (
                isinstance(component_result, dict)
                and component_result.get("event") == "answer_submitted"
            ):
                auto_answer = str(component_result.get("text", "")).strip()
                submit_token = str(component_result.get("token", ""))
                if (
                    auto_answer
                    and submit_token
                    and submit_token != st.session_state.last_auto_submit_token
                ):
                    st.session_state.last_auto_submit_token = submit_token
                    st.session_state.pending_answer = auto_answer
                    st.session_state.force_eval_next = False
                    _set_phase(
                        "processing",
                        "Your answer was captured. AI interviewer is evaluating it...",
                    )
                    st.rerun()
                elif not auto_answer:
                    st.warning("No answer text was captured. Please try dictating again.")
        else:
            st.info(
                "The candidate input activates automatically after the interviewer finishes asking the question."
            )

    # -------------------------------------------------------------------------
    # FULL-WIDTH PROGRESS + LATEST FEEDBACK
    # -------------------------------------------------------------------------
    # -------------------------------------------------------------------------
# FULL-WIDTH PROGRESS + LATEST FEEDBACK
# -------------------------------------------------------------------------

col1, col2 = st.columns([8, 1])

with col2:
    if st.button(
        "📊 Details"
        if not st.session_state.show_extra_panels
        else "❌ Hide",
        use_container_width=True,
    ):
        st.session_state.show_extra_panels = (
            not st.session_state.show_extra_panels
        )
        st.rerun()

if st.session_state.show_extra_panels:

    st.markdown("### Interview progress")

    progress_value = min(
        1.0,
        st.session_state.main_questions_asked /
        max(1, st.session_state.max_questions),
    )

    st.progress(
        progress_value,
        text=(
            f"Main questions: "
            f"{st.session_state.main_questions_asked} "
            f"of {st.session_state.max_questions}"
        ),
    )

    if st.session_state.feedback:
        with st.container(border=True):
            st.markdown("### Latest answer evaluation")
            st.markdown(st.session_state.feedback)

    with st.expander(
        "📜 Interview transcript",
        expanded=False
    ):
        if not st.session_state.chat_log:
            st.caption(
                "Your interview conversation will appear here."
            )
        else:
            for message in st.session_state.chat_log:
                role = (
                    "assistant"
                    if message.get("role") == "interviewer"
                    else "user"
                )

                with st.chat_message(role):
                    st.caption(message.get("meta", ""))
                    st.markdown(message.get("text", ""))

    with st.expander(
        "🛠️ Troubleshooting Wispr Flow",
        expanded=False
    ):
        st.markdown(
            """
            1. Wait until the interviewer finishes speaking.
            2. Activate Wispr Flow.
            3. Confirm text appears.
            4. Auto-submit occurs after 5 seconds.
            """
        )