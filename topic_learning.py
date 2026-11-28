import html
import re
import uuid
import streamlit as st
import streamlit.components.v1 as components
from langchain_core.messages import HumanMessage
from llm.model import get_llm
from voice.tts import synthesize_speech


def _focus_topic_input(nonce: int, delay_ms: int = 160):
    """Places the input cursor automatically inside the Topic Learning text input."""
    components.html(
        f"""
        <script>
          (function() {{
            const nonce = "{nonce}";
            const doc = window.parent.document;
            function focusBox() {{
              const inputs = Array.from(
                doc.querySelectorAll('input[type="text"], textarea')
              ).filter((el) => {{
                const rect = el.getBoundingClientRect();
                const label = (el.getAttribute("aria-label") || "").toLowerCase();
                return rect.width > 0 && rect.height > 0 && (
                  label.includes("topic") || label.includes("dictate") || el.placeholder.toLowerCase().includes("topic")
                );
              }});
              if (inputs.length > 0) {{
                const target = inputs[0];
                if (target.dataset.tlFocusedNonce !== nonce || doc.activeElement !== target) {{
                  target.dataset.tlFocusedNonce = nonce;
                  try {{
                    target.focus({{ preventScroll: true }});
                  }} catch (e) {{
                    target.focus();
                  }}
                }}
              }}
            }}
            setTimeout(focusBox, {int(delay_ms)});
            setTimeout(focusBox, {int(delay_ms) + 250});
          }})();
        </script>
        """,
        height=0,
    )


def _build_topic_prompt(
    topic: str,
    depth: str,
    language: str,
    prior_qa: list[dict],
) -> str:
    context_block = ""
    if prior_qa:
        recent = prior_qa[-3:]
        history_lines = "\n".join(
            f"- Learner asked: {item['topic']} | Key point covered: {item['summary_line']}"
            for item in recent
        )
        context_block = f"\nRecent learning context:\n{history_lines}\n"

    return f"""
You are a warm, beginner-friendly voice tutor.
Explain the learner's dictated topic or question in {language} at a "{depth}" level.

Learner's Topic / Question:
"{topic}"
{context_block}
Structure your response clearly using these exact headings:

### 1. Big Picture (In Plain Words)
Explain the core concept simply in 2–3 short sentences without heavy jargon.

### 2. Everyday Analogy & Example
Give one relatable real-world analogy or concrete example that makes it click immediately.

### 3. Key Pointers to Remember
* Give 3 short, scannable bullet points.

### 4. Quick Check for You
Ask one friendly, low-pressure question to test understanding.

Keep the tone encouraging, clear, and easy to follow when read aloud.
"""


def _explain_topic(topic: str, depth: str, language: str, prior_qa: list[dict]) -> tuple[str, bytes | None, str]:
    prompt = _build_topic_prompt(topic=topic, depth=depth, language=language, prior_qa=prior_qa)
    try:
        llm = get_llm(temperature=0.4)
        response = llm.invoke([HumanMessage(content=prompt)])
        explanation = response.content if isinstance(response.content, str) else str(response.content)
        explanation = explanation.strip()
    except Exception:
        explanation = (
            f"### 1. Big Picture (In Plain Words)\n"
            f"**{topic}** is easier to grasp when broken into small pieces. At its core, it solves a specific problem by connecting inputs, logic, and clear outcomes.\n\n"
            f"### 2. Everyday Analogy & Example\n"
            f"Think of it like a well-organized recipe: each step has a clear input, a focused job, and a predictable result.\n\n"
            f"### 3. Key Pointers to Remember\n"
            f"* Start with *what problem* it solves before worrying about edge cases.\n"
            f"* Trace one simple example end to end.\n"
            f"* Connect the concept to a practical project or interview scenario.\n\n"
            f"### 4. Quick Check for You\n"
            f"In your own words, how would you explain **{topic}** to a friend starting out today?"
        )

    spoken_script = re.sub(r"[#*_`>-]+", " ", explanation)
    spoken_script = re.sub(r"\s+", " ", spoken_script).strip()[:1200]

    audio_bytes = None
    mime_type = "audio/wav"
    try:
        audio_bytes, mime = synthesize_speech(spoken_script, language)
        if audio_bytes:
            mime_type = mime or "audio/wav"
    except Exception:
        audio_bytes = None

    return explanation, audio_bytes, mime_type


def render_topic_learning_page(voice_answer_component=None):
    defaults = {
        "tl_session_id": f"tl_{uuid.uuid4().hex[:10]}",
        "tl_depth": "Beginner-Friendly",
        "tl_language": st.session_state.get("language", "English"),
        "tl_current_topic": "",
        "tl_current_explanation": "",
        "tl_audio": None,
        "tl_audio_mime": "audio/wav",
        "tl_history": [],
        "tl_nonce": 0,
        "tl_pending_topic": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    st.markdown(
        """
        <div class="studio-topbar">
            <div>
                <h3 style="margin:0; color:#FFFFFF;">📚 Voice-Based Topic Learning</h3>
                <div style="color:#CBD5E1; font-size:0.88rem;">
                    Dictate any topic or question via Wispr Flow • Structured, beginner-friendly explanations
                </div>
            </div>
            <div style="background:rgba(255,255,255,0.14); padding:0.45rem 0.9rem; border-radius:999px; font-size:0.85rem; font-weight:700;">
                Topics Learned: """
        + str(len(st.session_state.tl_history))
        + """
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c_depth, c_lang, c_clear = st.columns([2, 2, 1])
    with c_depth:
        st.session_state.tl_depth = st.selectbox(
            "Explanation Style",
            ["Beginner-Friendly", "Analogy-First", "Step-by-Step Technical", "Interview Prep"],
            index=["Beginner-Friendly", "Analogy-First", "Step-by-Step Technical", "Interview Prep"].index(
                st.session_state.tl_depth
            ),
            key="tl_depth_select",
        )
    with c_lang:
        langs = list(st.session_state.get("_supported_languages", ["English", "Hindi", "Hinglish"]))
        idx = langs.index(st.session_state.tl_language) if st.session_state.tl_language in langs else 0
        st.session_state.tl_language = st.selectbox(
            "Explanation Language",
            langs,
            index=idx,
            key="tl_lang_select",
        )
    with c_clear:
        st.markdown("<div style='height:1.65rem;'></div>", unsafe_allow_html=True)
        if st.button("🧹 Clear", use_container_width=True, key="tl_clear_btn"):
            st.session_state.tl_current_topic = ""
            st.session_state.tl_current_explanation = ""
            st.session_state.tl_audio = None
            st.session_state.tl_history = []
            st.session_state.tl_nonce += 1
            st.rerun()

    st.caption("Quick topics you can click or speak:")
    starter_topics = [
        "How Retrieval-Augmented Generation (RAG) works",
        "REST API vs GraphQL in simple terms",
        "What is a deadlock and how to avoid it",
        "How async/await works in Python",
    ]
    q_cols = st.columns(len(starter_topics))
    for i, sample in enumerate(starter_topics):
        if q_cols[i].button(sample, use_container_width=True, key=f"tl_sample_{i}"):
            st.session_state.tl_pending_topic = sample
            st.rerun()

    left_col, right_col = st.columns([1.05, 1.35], gap="large")

    def _on_topic_enter():
        key = f"tl_dictate_input_{st.session_state.tl_nonce}"
        val = (st.session_state.get(key) or "").strip()
        if val:
            st.session_state.tl_pending_topic = val
            st.session_state[key] = ""

    with left_col:
        st.markdown(
            """
            <div class="split-card split-card-active-user" style="min-height:auto; margin-bottom:0.75rem;">
                <div>
                    <div class="peer-header">
                        <div class="peer-identity">
                            <div class="peer-avatar avatar-user">🎙️</div>
                            <div>
                                <div style="font-weight:800; font-size:1.05rem; color:#0F172A;">Dictate Your Topic</div>
                                <div style="font-size:0.8rem; color:#64748B; font-weight:600;">Wispr Flow Voice Input</div>
                            </div>
                        </div>
                    </div>
                    <div style="font-size:0.85rem; color:#334155;">
                        The cursor is placed in the box automatically. Activate <b>Wispr Flow</b>, speak your topic or question, and press <b>Enter</b> (or click <b>Explain Topic</b>).
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        topic_input_key = f"tl_dictate_input_{st.session_state.tl_nonce}"
        typed_topic = st.text_input(
            "Dictate topic with Wispr Flow and press Enter:",
            placeholder="Speak a topic or question using Wispr Flow...",
            key=topic_input_key,
            on_change=_on_topic_enter,
        )
        _focus_topic_input(st.session_state.tl_nonce)

        if st.button("Explain Topic ➤", type="primary", use_container_width=True, key="tl_submit_btn"):
            candidate_val = (typed_topic or "").strip()
            if candidate_val:
                st.session_state.tl_pending_topic = candidate_val
                st.session_state[topic_input_key] = ""
                st.rerun()

    if st.session_state.tl_pending_topic:
        topic_to_explain = st.session_state.tl_pending_topic
        st.session_state.tl_pending_topic = ""
        with st.spinner(f"Preparing a structured {st.session_state.tl_depth.lower()} explanation..."):
            explanation, audio_bytes, mime = _explain_topic(
                topic=topic_to_explain,
                depth=st.session_state.tl_depth,
                language=st.session_state.tl_language,
                prior_qa=st.session_state.tl_history,
            )
        st.session_state.tl_current_topic = topic_to_explain
        st.session_state.tl_current_explanation = explanation
        st.session_state.tl_audio = audio_bytes
        st.session_state.tl_audio_mime = mime
        st.session_state.tl_nonce += 1

        first_line = next(
            (line.strip("* ") for line in explanation.splitlines() if line.strip() and not line.strip().startswith("#")),
            topic_to_explain,
        )
        st.session_state.tl_history.append(
            {
                "topic": topic_to_explain,
                "depth": st.session_state.tl_depth,
                "explanation": explanation,
                "summary_line": first_line[:140],
            }
        )
        st.rerun()

    with right_col:
        st.markdown('<div class="mi-card">', unsafe_allow_html=True)
        if not st.session_state.tl_current_explanation:
            st.markdown("### Tutor Explanation Stage")
            st.info(
                "The cursor is ready in the input box on the left. Dictate or pick a topic to get a structured breakdown with "
                "**Big Picture**, **Everyday Analogy**, **Key Pointers**, and a **Quick Check**."
            )
        else:
            safe_topic = html.escape(st.session_state.tl_current_topic)
            st.caption(f"Topic • {st.session_state.tl_depth} • {st.session_state.tl_language}")
            st.markdown(f'<div class="question-bubble">“{safe_topic}”</div>', unsafe_allow_html=True)

            if st.session_state.tl_audio:
                st.audio(
                    st.session_state.tl_audio,
                    format=st.session_state.tl_audio_mime,
                    autoplay=True,
                )

            st.markdown(st.session_state.tl_current_explanation)
        st.markdown("</div>", unsafe_allow_html=True)

    if len(st.session_state.tl_history) > 1:
        with st.expander("📖 Previous Topics Explained in This Session", expanded=False):
            for idx, item in enumerate(reversed(st.session_state.tl_history[:-1]), start=1):
                st.markdown(f"**{idx}. {item['topic']}** _({item['depth']})_")
                st.markdown(item["explanation"])
                st.divider()