
import textwrap
import streamlit as st


def _html(markup: str) -> str:
    return textwrap.dedent(markup).strip()


HERO_SAMPLE_HTML = _html(
    """
    <div style="
        background: linear-gradient(135deg, #0B1220 0%, #1E1B4B 55%, #312E81 100%);
        color: #FFFFFF;
        border-radius: 16px;
        padding: 20px;
        border: 1px solid rgba(148, 163, 184, 0.25);
    ">
        <div style="font-size:0.75rem; font-weight:800; letter-spacing:1.2px; color:#93C5FD; margin-bottom:10px;">
            SAMPLE VISUAL PREVIEW • WISPR FLOW + AI
        </div>
        <div style="background:rgba(255,255,255,0.08); border-radius:12px; padding:14px; margin-bottom:12px;">
            <div style="font-size:0.92rem; font-weight:800; color:#FFFFFF; margin-bottom:6px;">
                🤖 "Just speak... I'll handle the rest!"
            </div>
            <div style="font-size:0.82rem; color:#E2E8F0; line-height:1.6;">
                ✓ Mock Interviews &nbsp;•&nbsp; ✓ Topic Learning<br>
                ✓ Guided Tutor &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;•&nbsp; ✓ Performance KPIs
            </div>
        </div>
        <div style="background:rgba(37,99,235,0.22); border:1px solid rgba(147,197,253,0.35); border-radius:12px; padding:12px; text-align:center;">
            <div style="font-size:1.35rem; letter-spacing:3px; color:#93C5FD; font-weight:800;">
                ▮ ▯ ▮ ▯ 🎙️ ▯ ▮ ▯ ▮
            </div>
            <div style="font-size:0.78rem; color:#CBD5E1; margin-top:4px;">
                Sample Voice &amp; Tutor Preview
            </div>
        </div>
    </div>
    """
)


def render_home_page(on_navigate):
    st.markdown(
        _html(
            """
            <style>
/* FOOTER */
.vl-footer {
    width: 100%;
    box-sizing: border-box;
    background: linear-gradient(110deg, #090D1A 0%, #172554 55%, #312E81 100%);
    color: #FFFFFF;
    padding: 28px 30px;
    border-radius: 17px;
    margin-top: 20px;
    border: 1px solid rgba(148,163,184,0.2);
}

.vl-footer-heading {
    color: #93C5FD;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 1.2px;
    margin-bottom: 14px;
}

.vl-footer-links {
    display: flex;
    flex-wrap: wrap;
    gap: 9px;
}

.vl-footer a {
    display: inline-block;
    color: #FFFFFF !important;
    text-decoration: none !important;
    border: 1px solid rgba(255,255,255,0.25);
    background: rgba(255,255,255,0.09);
    padding: 9px 15px;
    border-radius: 25px;
    font-size: 0.8rem;
    font-weight: 700;
    transition: all 0.2s ease;
}

.vl-footer a:hover {
    background: rgba(59,130,246,0.4);
    border-color: #93C5FD;
}

.vl-footer-brand {
    text-align: right;
}

.vl-footer-tagline {
    color: #FFFFFF;
    font-size: 1.2rem;
    font-weight: 800;
    font-style: italic;
}

.vl-footer-team {
    color: #93C5FD;
    font-size: 0.8rem;
    font-weight: 800;
    letter-spacing: 3px;
    margin-top: 8px;
}

.vl-footer-divider {
    height: 1px;
    background: rgba(255,255,255,0.15);
    margin: 23px 0 15px 0;
}

.vl-footer-bottom {
    display: flex;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    color: #CBD5E1;
    font-size: 0.72rem;
}

@media(max-width: 650px) {

    .vl-footer-brand {
        text-align: left;
    }

    .vl-footer {
        padding: 22px 18px;
    }
}
.vl-member-role {
    font-size: 13px;
    color: #64748b;
    margin-top: 4px;
}
            .vl-pill-badge {
                display: inline-block;
                background: #EEF2FF;
                color: #4338CA;
                border: 1px solid #C7D2FE;
                padding: 6px 13px;
                border-radius: 30px;
                font-size: 0.78rem;
                font-weight: 750;
                margin-bottom: 14px;
            }

            .vl-hero-title {
                font-size: clamp(2.3rem, 4vw, 3.4rem);
                font-weight: 850;
                line-height: 1.08;
                letter-spacing: -1.5px;
                color: #111827;
                margin-bottom: 12px;
            }

            .vl-hero-pillars {
                color: #4F46E5;
                font-size: 1.05rem;
                font-weight: 750;
                margin-bottom: 13px;
            }

            .vl-hero-sub {
                color: #64748B;
                font-size: 0.98rem;
                line-height: 1.7;
                max-width: 570px;
                margin-bottom: 20px;
            }

            .vl-section-heading {
                font-size: 1.35rem;
                font-weight: 800;
                color: #0F172A;
                margin-bottom: 3px;
            }

            .vl-section-subtitle {
                font-size: 0.85rem;
                color: #64748B;
                margin-bottom: 18px;
            }

            /* Informational feature cards */
            .vl-feature-card {
                min-height: 190px;
                height: 100%;
                padding: 17px;
                border-radius: 15px;
                border: 1px solid #E2E8F0;
                margin-bottom: 10px;
                transition: transform 0.2s ease, box-shadow 0.2s ease;
            }

            .vl-feature-card:hover {
                transform: translateY(-3px);
                box-shadow: 0 8px 20px rgba(15,23,42,0.08);
            }

            .vl-feature-icon {
                font-size: 1.8rem;
                margin-bottom: 12px;
            }

            .vl-feature-title {
                font-size: 0.96rem;
                font-weight: 800;
                color: #0F172A;
                margin-bottom: 7px;
            }

            .vl-feature-desc {
                color: #475569;
                font-size: 0.79rem;
                line-height: 1.55;
                margin-bottom: 13px;
            }

            .vl-feature-tag {
                display: inline-block;
                padding: 4px 9px;
                border-radius: 20px;
                background: rgba(255,255,255,0.75);
                border: 1px solid rgba(148,163,184,0.35);
                color: #334155;
                font-size: 0.68rem;
                font-weight: 750;
            }

            .vl-stack-item {
                text-align: center;
                padding: 14px 8px;
                border-radius: 13px;
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                margin-bottom: 10px;
                min-height: 85px;
            }

            .vl-stack-icon {
                font-size: 1.5rem;
                margin-bottom: 5px;
            }

            .vl-stack-label {
                color: #1E293B;
                font-weight: 750;
                font-size: 0.8rem;
            }

            .vl-member-card {
                display: flex;
                align-items: center;
                gap: 13px;
                background: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 14px;
                padding: 12px;
                margin-bottom: 10px;
            }

            .vl-member-name {
                font-size: 0.94rem;
                font-weight: 800;
                color: #0F172A;
            }

            .vl-member-role {
                font-size: 0.76rem;
                color: #64748B;
                margin-top: 3px;
            }

            .vl-footer {
                background: linear-gradient(110deg, #090D1A, #172554, #312E81);
                color: #FFFFFF;
                padding: 23px 25px;
                border-radius: 17px;
                margin-top: 12px;
            }

            .vl-footer-heading {
                color: #94A3B8;
                font-size: 0.72rem;
                font-weight: 800;
                letter-spacing: 1px;
                margin-bottom: 10px;
            }

            .vl-footer-tagline {
                color: #FFFFFF;
                font-size: 1.12rem;
                font-weight: 800;
                font-style: italic;
            }

            .vl-footer-team {
                color: #93C5FD;
                font-size: 0.78rem;
                font-weight: 800;
                letter-spacing: 2px;
                margin-top: 5px;
            }

            .vl-footer a {
                display: inline-block;
                color: #FFFFFF !important;
                text-decoration: none !important;
                border: 1px solid rgba(255,255,255,0.25);
                background: rgba(255,255,255,0.08);
                padding: 7px 12px;
                border-radius: 25px;
                font-size: 0.78rem;
                font-weight: 700;
                margin: 3px 4px 3px 0;
            }

            .vl-footer a:hover {
                background: rgba(59,130,246,0.35);
            }

            div.stButton > button {
                border-radius: 10px;
                font-weight: 700;
                min-height: 42px;
            }

            @media(max-width: 768px) {
                .vl-hero-title {
                    font-size: 2.4rem;
                }

                .vl-footer {
                    padding: 18px;
                }

                .vl-feature-card {
                    min-height: 160px;
                }
            }
            </style>
            """
        ),
        unsafe_allow_html=True,
    )

    # -------------------------------------------------
    # HERO SECTION
    # -------------------------------------------------
    with st.container(border=True):
        hero_left, hero_right = st.columns([1.05, 1.0], gap="large")

        with hero_left:
            st.markdown(
                _html(
                    """
                    <div class="vl-pill-badge">
                        ✦ AI-POWERED • VOICE-FIRST LEARNING
                    </div>
                    <div class="vl-hero-title">VoiceLearn AI</div>
                    <div class="vl-hero-pillars">
                        Speak &nbsp;•&nbsp; Learn &nbsp;•&nbsp; Practice &nbsp;•&nbsp; Excel
                    </div>
                    <div class="vl-hero-sub">
                        Your personal AI learning companion to master concepts,
                        prepare for interviews, and build confidence — all with
                        the power of <b>Wispr Flow</b> voice input.
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            # Only two primary navigation actions
            b1, b2 = st.columns(2)

            with b1:
                if st.button(
                    "📘 Start Learning",
                    type="primary",
                    use_container_width=True,
                    key="hero_start_btn",
                ):
                    on_navigate("Topic Learning")

            with b2:
                if st.button(
                    "🎙️ Mock Interview",
                    use_container_width=True,
                    key="hero_interview_btn",
                ):
                    on_navigate("Mock Interview")

            if st.button(
                "▶ Watch Demo",
                use_container_width=True,
                key="hero_demo_btn",
            ):
                st.session_state["show_demo_guide"] = not st.session_state.get(
                    "show_demo_guide", False
                )
                st.rerun()

        with hero_right:
            st.markdown(
                HERO_SAMPLE_HTML,
                unsafe_allow_html=True,
            )

    # -------------------------------------------------
    # DEMO GUIDE
    # -------------------------------------------------
    if st.session_state.get("show_demo_guide", False):
        with st.container(border=True):
            st.markdown("### 🎬 Quick Walkthrough")

            st.markdown(
                """
                **1. Topic Learning**

                Open Topic Learning, activate Wispr Flow, and speak a
                question such as *"Explain RAG in simple words"*.

                **2. Mock Interview**

                Start a role-based interview, dictate your answers using
                Wispr Flow, and review your performance report.

                **3. Personalized Learning**

                Learn with structured explanations, practical examples,
                and knowledge checks.
                """
            )

    # -------------------------------------------------
    # KEY FEATURES - INFORMATIONAL ONLY
    # -------------------------------------------------
    st.markdown("")

    with st.container(border=True):
        st.markdown(
            _html(
                """
                <div class="vl-section-heading">Explore VoiceLearn AI</div>
                <div class="vl-section-subtitle">
                    Everything you need to learn, practice, and improve with AI.
                </div>
                """
            ),
            unsafe_allow_html=True,
        )

        feature_data = [
            (
                "🎙️",
                "Mock Interviews",
                "Practice role-based interviews with AI-generated questions, follow-ups, and personalized answer evaluation.",
                "#F3E8FF",
                "VOICE-BASED PRACTICE",
            ),
            (
                "📘",
                "Topic Learning",
                "Explore technical concepts through simple explanations, practical examples, and natural voice interactions.",
                "#DBEAFE",
                "PERSONALIZED LEARNING",
            ),
            (
                "🧠",
                "Guided Tutor",
                "Understand difficult concepts using relatable analogies, knowledge checks, and interactive quizzes.",
                "#D1FAE5",
                "CONCEPT UNDERSTANDING",
            ),
            (
                "📈",
                "Interview Performance",
                "Review your interview performance with scores, feedback, strengths, and areas that need improvement.",
                "#FEF3C7",
                "AI-POWERED INSIGHTS",
            ),
        ]

        feature_cols = st.columns(4, gap="medium")

        for col, item in zip(feature_cols, feature_data):
            icon, title, desc, bg, tag = item

            with col:
                st.markdown(
                    _html(
                        f"""
                        <div class="vl-feature-card" style="background:{bg};">
                            <div class="vl-feature-icon">{icon}</div>
                            <div class="vl-feature-title">{title}</div>
                            <div class="vl-feature-desc">{desc}</div>
                            <span class="vl-feature-tag">{tag}</span>
                        </div>
                        """
                    ),
                    unsafe_allow_html=True,
                )

    # -------------------------------------------------
    # TECH STACK + TEAM
    # -------------------------------------------------
    st.markdown("")

    with st.container(border=True):
        bottom_left, bottom_right = st.columns(
            [1.5, 1.0],
            gap="large",
        )

        with bottom_left:
            st.markdown(
                _html(
                    """
                    <div class="vl-section-heading">⚙️ Tech Stack</div>
                    <div class="vl-section-subtitle">
                        Built with modern and powerful technologies.
                    </div>
                    """
                ),
                unsafe_allow_html=True,
            )

            stack_items = [
                ("🐍", "Python"),
                ("🎈", "Streamlit"),
                ("🕸️", "LangGraph"),
                ("⚡", "FastAPI"),
                ("🚀", "Groq"),
                ("🦙", "Ollama"),
                ("🗄️", "SQLite"),
                ("🎙️", "Wispr Flow"),
            ]

            stack_cols = st.columns(4)

            for idx, (icon, label) in enumerate(stack_items):
                with stack_cols[idx % 4]:
                    st.markdown(
                        _html(
                            f"""
                            <div class="vl-stack-item">
                                <div class="vl-stack-icon">{icon}</div>
                                <div class="vl-stack-label">{label}</div>
                            </div>
                            """
                        ),
                        unsafe_allow_html=True,
                    )

        with bottom_right:
            st.markdown(
                """
                <div class="vl-section-heading">👥 About TEAM SUDO</div>
                <div class="vl-section-subtitle">
                    Building innovative solutions for a smarter tomorrow.
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Venkatesh card
            st.markdown(
                """
                <div class="vl-member-card">
                    <div style="
                        width:52px;
                        height:52px;
                        min-width:52px;
                        border-radius:50%;
                        background:#DBEAFE;
                        border:2px solid #93C5FD;
                        color:#1E3A8A;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        font-weight:800;
                        font-size:1rem;
                        flex-shrink:0;
                    ">AV</div>
                    <div>
                        <div class="vl-member-name">A Venkatesh</div>
                        <div class="vl-member-role">
                            AI &amp; Voice Architecture
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            # Deeksha card
            st.markdown(
                """
                <div class="vl-member-card">
                    <div style="
                        width:52px;
                        height:52px;
                        min-width:52px;
                        border-radius:50%;
                        background:#FCE7F3;
                        border:2px solid #F9A8D4;
                        color:#831843;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        font-weight:800;
                        font-size:1rem;
                        flex-shrink:0;
                    ">D</div>
                    <div>
                        <div class="vl-member-name">Deeksha</div>
                        <div class="vl-member-role">
                            Experience &amp; Learning Flow
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
       

    # -------------------------------------------------
    # FOOTER
    # -------------------------------------------------
        # -------------------------------------------------
    # FOOTER - NATIVE STREAMLIT LAYOUT
    # -------------------------------------------------

    
    # -------------------------------------------------
    # PREMIUM FOOTER - VOICELEARN AI
    # -------------------------------------------------

    st.markdown(
        """
        <style>
        .vl-footer-wrapper {
            background: linear-gradient(135deg, #0B1220, #172554, #312E81);
            border: 1px solid rgba(148,163,184,0.25);
            border-radius: 18px;
            padding: 28px 30px 18px 30px;
            margin-top: 25px;
            color: white;
        }

        .vl-footer-label {
            color: #93C5FD;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 2px;
            margin-bottom: 12px;
        }

        .vl-footer-title {
            color: white;
            font-size: 23px;
            font-weight: 850;
            line-height: 1.4;
        }

        .vl-footer-description {
            color: #CBD5E1;
            font-size: 13px;
            line-height: 1.7;
            margin-top: 8px;
        }

        .vl-footer-team {
            color: #93C5FD;
            font-size: 13px;
            font-weight: 800;
            letter-spacing: 3px;
            margin-top: 12px;
        }

        .vl-footer-divider {
            height: 1px;
            background: rgba(255,255,255,0.16);
            margin: 22px 0 15px 0;
        }

        .vl-footer-copy {
            color: #CBD5E1;
            font-size: 11px;
        }

        div[data-testid="stLinkButton"] a {
            border-radius: 9px !important;
            font-weight: 700 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="vl-footer-wrapper">
            <div class="vl-footer-label">VOICELEARN AI • PROJECT SHOWCASE</div>
            <div class="vl-footer-title">Learn Smarter. Grow Faster.</div>
            <div class="vl-footer-description">
                Your AI-powered learning companion for smarter learning,
                confident interviews and continuous improvement.
            </div>
            <div class="vl-footer-team">— TEAM SUDO —</div>
            <div class="vl-footer-divider"></div>
            <div class="vl-footer-copy">
                © 2026 VoiceLearn AI &nbsp; • &nbsp;
                Built with ❤️ by TEAM SUDO
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Project links below the branding panel
    st.markdown("")

    link1, link2, link3 = st.columns(3, gap="medium")

    with link1:
        st.link_button(
            "💻 GitHub",
            "https://github.com/Venkatesh0610/Wispr-Flow-Hackathon",
            use_container_width=True
        )

    with link2:
        st.link_button(
            "▶ YouTube",
            "https://www.youtube.com/@avenkatesh0610",
            use_container_width=True
        )

    with link3:
        st.link_button(
            "🔗 LinkedIn",
            "https://www.linkedin.com/in/venkatesh-a-400459191/",
            use_container_width=True
        )
