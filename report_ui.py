import re
import streamlit as st

FILLER_WORDS = ("um", "uh", "like", "basically", "actually", "literally", "well")


def _count_filler_words(text: str) -> tuple[int, dict[str, int]]:
    tokens = re.findall(r"\b[a-zA-Z']+\b", (text or "").lower())
    counts: dict[str, int] = {}
    total = 0
    for fw in FILLER_WORDS:
        c = tokens.count(fw)
        if c > 0:
            counts[fw] = c
            total += c
    return total, counts


def _estimate_wpm(text: str, duration_sec: float | None = None) -> int:
    words = len((text or "").split())
    if words == 0:
        return 0
    # Fallback ~135 wpm baseline if duration isn't tracked, or compute from elapsed seconds
    if duration_sec and duration_sec > 2:
        return max(30, min(260, int(round((words / duration_sec) * 60))))
    return max(75, min(195, int(round(words * 2.2))))


def _score_ring_svg(score_10: float, label: str = "SCORE", sub: str = "GOOD") -> str:
    pct = max(0.0, min(100.0, (score_10 / 10.0) * 100.0))
    radius = 42
    circumference = 2 * 3.14159 * radius
    dash_offset = circumference * (1.0 - pct / 100.0)
    color = "#10B981" if score_10 >= 7.5 else ("#D97706" if score_10 >= 5.0 else "#EF4444")

    return f"""
    <div style="display:flex; flex-direction:column; align-items:center; justify-content:center;">
      <svg width="112" height="112" viewBox="0 0 112 112">
        <circle cx="56" cy="56" r="{radius}" fill="none" stroke="#E2E8F0" stroke-width="9" />
        <circle cx="56" cy="56" r="{radius}" fill="none" stroke="{color}" stroke-width="9"
                stroke-linecap="round"
                stroke-dasharray="{circumference:.1f}"
                stroke-dashoffset="{dash_offset:.1f}"
                transform="rotate(-90 56 56)" />
      </svg>
      <div style="margin-top:-78px; text-align:center; line-height:1.15;">
        <div style="font-size:0.65rem; font-weight:800; color:#64748B; letter-spacing:0.06em;">{label}</div>
        <div style="font-size:1.35rem; font-weight:800; color:#0F172A;">{score_10:.1f}</div>
        <div style="font-size:0.65rem; font-weight:800; color:{color}; text-transform:uppercase;">{sub}</div>
      </div>
      <div style="height:26px;"></div>
    </div>
    """


def _extract_section(markdown_text: str, headings: list[str], default_text: str) -> str:
    if not markdown_text:
        return default_text
    pattern = r"(?i)(?:\*\*|###?\s*)?(?:" + "|".join(re.escape(h) for h in headings) + r")(?:\*\*)?\s*:?\s*(.+?)(?=(?:\n(?:\*\*|###?\s*)?[A-Z][A-Za-z\s]{2,30}(?:\*\*)?\s*:)|\Z)"
    m = re.search(pattern, markdown_text, flags=re.DOTALL)
    if m:
        cleaned = m.group(1).strip()
        if cleaned:
            return cleaned
    return default_text


def render_interview_report(
    role: str,
    level: str,
    language: str,
    max_questions: int,
    overall_summary: str,
    transcript: list[dict],
    on_restart,
    on_change_settings,
):
    eval_turns = [t for t in transcript if t.get("action") == "evaluate"]
    scores = [float(t.get("score", 0)) for t in eval_turns if float(t.get("score", 0)) > 0]
    avg_10 = round(sum(scores) / len(scores), 1) if scores else 7.0
    overall_pct = int(round((avg_10 / 10.0) * 100))
    domain_100 = int(round(min(100, max(0, avg_10 * 10))))

    strengths_md = _extract_section(
        overall_summary,
        ["Top 2 Strengths", "Strengths", "What went well"],
        "Clear structure and willingness to walk through real scenarios.",
    )
    weaknesses_md = _extract_section(
        overall_summary,
        ["Top 2 Areas of Improvement", "Weakness", "Weaknesses", "How to improve"],
        "Add more concrete metrics, trade-offs, and concise examples when answering.",
    )
    insights_md = _extract_section(
        overall_summary,
        ["Recommendations for Improvement", "Pro Insights", "Next Steps"],
        "Structure answers with Context → Action → Impact and keep pauses intentional.",
    )

    st.markdown(
        """
        <style>
        .rep-dark-banner {
            background: linear-gradient(135deg, #071312 0%, #0D2622 60%, #111827 100%);
            color: #F8FAFC;
            border-radius: 20px;
            padding: 1.5rem 1.75rem;
            margin-bottom: 1.25rem;
            border: 1px solid rgba(16, 185, 129, 0.25);
        }
        .rep-kpi-dark {
            background: #102421;
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 16px;
            padding: 1.15rem;
            text-align: center;
            color: #F8FAFC;
            height: 100%;
        }
        .rep-q-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 20px;
            padding: 1.5rem;
            margin-bottom: 1.25rem;
            box-shadow: 0 10px 25px -12px rgba(15, 23, 42, 0.08);
        }
        .rep-metric-tile {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 1.1rem;
            height: 100%;
        }
        .filler-chip {
            display: inline-block;
            background: #F1F5F9;
            border: 1px solid #CBD5E1;
            color: #334155;
            border-radius: 999px;
            padding: 0.15rem 0.6rem;
            font-size: 0.78rem;
            font-weight: 700;
            margin: 0.2rem 0.25rem 0 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Top Actionable Feedback & Main KPIs Section (inspired by second reference)
    st.markdown(
        f"""
        <div class="rep-dark-banner">
            <div style="font-size:0.78rem; text-transform:uppercase; letter-spacing:0.08em; color:#34D399; font-weight:800;">
                Interview Completed • {role} ({level} • {language})
            </div>
            <h2 style="margin:0.25rem 0; color:#FFFFFF;">Actionable Feedback &amp; Performance KPIs</h2>
            <div style="color:#CBD5E1; font-size:0.92rem;">
                Completed all <b>{max_questions}</b> selected questions. Review your overall readiness, domain score, and per-question metrics below.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    fb_col, kpi1_col, kpi2_col = st.columns([1.35, 0.85, 0.85], gap="medium")

    with fb_col:
        with st.expander("👍 Strengths", expanded=True):
            st.markdown(strengths_md)
        with st.expander("⚠️ Areas to Improve (Weaknesses)", expanded=True):
            st.markdown(weaknesses_md)
        with st.expander("⚡ Pro Insights & Action Pointers", expanded=False):
            st.markdown(insights_md)

    with kpi1_col:
        st.markdown(
            f"""
            <div class="rep-kpi-dark">
                <div style="font-weight:700; font-size:0.95rem; margin-bottom:0.65rem;">Overall Score</div>
                <div style="font-size:2.3rem; font-weight:800; color:#10B981;">{overall_pct}%</div>
                <div style="font-size:0.8rem; color:#94A3B8; margin-top:0.35rem;">Avg {avg_10}/10 across {len(eval_turns)} Q(s)</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with kpi2_col:
        st.markdown(
            f"""
            <div class="rep-kpi-dark">
                <div style="font-weight:700; font-size:0.95rem; margin-bottom:0.65rem;">Domain Knowledge</div>
                <div style="font-size:2.3rem; font-weight:800; color:#38BDF8;">{domain_100}<span style="font-size:1rem; color:#94A3B8;">/100</span></div>
                <div style="font-size:0.8rem; color:#94A3B8; margin-top:0.35rem;">Role alignment &amp; depth</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Per-Question Analysis & Speaking Metrics")

    # Per-Question Breakdown Cards (inspired by first reference)
    for idx, turn in enumerate(transcript, start=1):
        q_text = turn.get("question", "")
        ans_text = turn.get("user_answer", "")
        fb_text = turn.get("feedback", "")
        q_score = float(turn.get("score", 0))
        q_num = turn.get("question_num", idx)
        is_fu = turn.get("action") == "followup"

        sub_tag = "STRONG" if q_score >= 8.0 else ("GOOD" if q_score >= 6.0 else ("PROBE" if is_fu else "NEEDS WORK"))
        wpm = _estimate_wpm(ans_text, turn.get("duration_sec"))
        filler_total, filler_map = _count_filler_words(ans_text)

        expected_match = re.search(
            r"(?i)(?:\*\*Stronger sample answer:\*\*|Stronger sample answer:)\s*(.+)",
            fb_text,
            flags=re.DOTALL,
        )
        expected_ans = expected_match.group(1).strip() if expected_match else ""

        st.markdown('<div class="rep-q-card">', unsafe_allow_html=True)
        main_q_col, ring_col = st.columns([2.5, 1], gap="large")

        with main_q_col:
            q_header = f"Question {q_num} (Follow-Up)" if is_fu else f"Question {q_num}"
            st.caption(q_header)
            st.markdown(f"#### {q_text}")

            st.markdown("**Your response**")
            st.write(ans_text or "_No response recorded._")

            if fb_text:
                st.markdown("**Our feedback**")
                st.markdown(fb_text)

        with ring_col:
            st.markdown("<div style='text-align:center; font-weight:700; color:#0F172A;'>Question Score</div>", unsafe_allow_html=True)
            st.markdown(_score_ring_svg(q_score, label="SCORE", sub=sub_tag), unsafe_allow_html=True)

        if expected_ans:
            with st.expander("💡 Expected / Stronger Sample Answer"):
                st.markdown(expected_ans)

        # 3 Bottom KPI Cards per Question (Speaking Speed, Filler Words, Response Depth)
        m1, m2, m3 = st.columns(3, gap="medium")

        with m1:
            pace_badge = "Target Pace" if 120 <= wpm <= 160 else ("Speak faster" if wpm < 120 else "Slow down slightly")
            st.markdown(
                f"""
                <div class="rep-metric-tile">
                    <div style="font-weight:700; font-size:0.9rem; color:#0F172A; margin-bottom:0.4rem;">⚡ Speaking Speed</div>
                    <div style="font-size:1.65rem; font-weight:800; color:#0F172A;">{wpm} <span style="font-size:0.82rem; font-weight:500; color:#64748B;">words / min</span></div>
                    <div style="margin-top:0.35rem; font-size:0.78rem; font-weight:700; color:#047857;">{pace_badge}</div>
                    <div style="font-size:0.74rem; color:#64748B; margin-top:0.25rem;">Target 120–160 words / min</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m2:
            chips_html = "".join(
                f'<span class="filler-chip">{k}: {v}</span>' for k, v in filler_map.items()
            ) or '<span style="font-size:0.78rem; color:#64748B;">None detected</span>'
            st.markdown(
                f"""
                <div class="rep-metric-tile">
                    <div style="font-weight:700; font-size:0.9rem; color:#0F172A; margin-bottom:0.4rem;">💬 Filler Words</div>
                    <div style="font-size:1.65rem; font-weight:800; color:#0F172A;">{filler_total} <span style="font-size:0.82rem; font-weight:500; color:#64748B;">detected</span></div>
                    <div style="font-size:0.72rem; font-weight:700; color:#64748B; margin-top:0.35rem; text-transform:uppercase;">Words you used</div>
                    <div>{chips_html}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with m3:
            word_len = len(ans_text.split())
            depth_label = "Detailed" if word_len >= 35 else ("Moderate" if word_len >= 15 else "Brief")
            st.markdown(
                f"""
                <div class="rep-metric-tile">
                    <div style="font-weight:700; font-size:0.9rem; color:#0F172A; margin-bottom:0.4rem;">📏 Answer Depth</div>
                    <div style="font-size:1.65rem; font-weight:800; color:#0F172A;">{word_len} <span style="font-size:0.82rem; font-weight:500; color:#64748B;">words</span></div>
                    <div style="margin-top:0.35rem; font-size:0.78rem; font-weight:700; color:#4338CA;">{depth_label} Response</div>
                    <div style="font-size:0.74rem; color:#64748B; margin-top:0.25rem;">Includes examples &amp; reasoning</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)

    c1, c2 = st.columns(2)
    if c1.button("🔄 Start Another Mock Interview", type="primary", use_container_width=True):
        on_restart()
    if c2.button("⚙️ Change Role / Settings", use_container_width=True):
        on_change_settings()