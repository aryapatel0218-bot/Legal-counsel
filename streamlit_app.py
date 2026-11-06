from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from src.nova_ai import NovaConfig, NovaService
from src.quiz_engine import advance_round, current_round, submit_answer

from src.legal_engine import (
    ACTIVITIES,
    LegalLearningEngine,
    classify_learner_profile,
    get_quiz,
    load_topics,
    moderate_community_post,
    new_bandit_state,
    recommend_activity,
    update_bandit,
)

st.set_page_config(
    page_title="Legal Counsel — Know Your Rights with Nova",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Streamlit-native recreation of the supplied Legal Counsel React/TanStack design.
st.markdown(
    r"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&family=Outfit:wght@500;600;700&display=swap');

    :root {
      --lc-bg: #f7fcfb;
      --lc-fg: #243c45;
      --lc-card: #ffffff;
      --lc-primary: #55aeb0;
      --lc-primary-soft: #e4f5f3;
      --lc-primary-deep: #315f69;
      --lc-secondary: #edf7f6;
      --lc-muted: #6f8288;
      --lc-accent: #e67f58;
      --lc-accent-soft: #fff0e8;
      --lc-highlight: #e7c75c;
      --lc-border: #dcebea;
      --lc-danger: #c84141;
      --lc-radius: 22px;
    }

    html, body, [class*="css"] { font-family: 'Figtree', sans-serif; }
    h1, h2, h3, h4, .lc-display { font-family: 'Outfit', sans-serif !important; letter-spacing: -0.02em; }
    .stApp { background: var(--lc-bg); color: var(--lc-fg); }

    /*
      Streamlit's application header is fixed above the page content on
      Community Cloud. Reserve enough vertical space so the Legal Counsel
      brand bar never renders underneath that header, including on phones
      with a safe-area inset.
    */
    [data-testid="stAppViewBlockContainer"],
    .block-container {
      max-width: 1160px;
      padding-top: calc(5.25rem + env(safe-area-inset-top)) !important;
      padding-bottom: 3.5rem;
    }
    header[data-testid="stHeader"] {
      min-height: 3.75rem;
      background: rgba(247,252,251,.96);
      border-bottom: 1px solid rgba(220,235,234,.78);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      z-index: 1000;
    }
    #MainMenu, footer { visibility: hidden; }
    div[data-testid="stToolbar"] { visibility: hidden; height: 0; }

    /* Top brand bar */
    .lc-topbar {
      position: relative; z-index: 1; min-height: 56px;
      display:flex; align-items:center; gap:12px; padding: 10px 2px 8px;
      border-bottom: 1px solid var(--lc-border); margin-bottom: 8px;
    }
    .lc-logo {
      width:38px; height:38px; border-radius:13px; background:var(--lc-primary);
      display:inline-flex; align-items:center; justify-content:center; color:white; font-size:20px;
      box-shadow: 0 8px 20px rgba(49,95,105,.12);
    }
    .lc-brand {font-family:'Outfit',sans-serif; font-size:19px; font-weight:700; color:var(--lc-fg);}
    .lc-tagline {margin-left:auto; font-size:12px; color:var(--lc-muted);}

    /* Horizontal radio navigation */
    div[role="radiogroup"] { gap: .3rem !important; flex-wrap: wrap !important; }
    div[role="radiogroup"] label {
      background:#fff; border:1px solid var(--lc-border); border-radius:999px;
      padding:.32rem .75rem !important; transition:.15s ease; box-shadow:none;
    }
    div[role="radiogroup"] label:hover { border-color: var(--lc-primary); transform: translateY(-1px); }
    div[role="radiogroup"] label:has(input:checked) { background:var(--lc-primary-soft); border-color:var(--lc-primary); }
    div[role="radiogroup"] label p { font-size:.88rem !important; font-weight:600; color:var(--lc-primary-deep); }
    div[role="radiogroup"] [data-testid="stMarkdownContainer"] { margin: 0; }

    .surface-grid {
      background-image: radial-gradient(circle at 1px 1px, rgba(85,174,176,.18) 1px, transparent 0);
      background-size: 22px 22px;
    }
    .lc-hero {
      margin-top:1rem; padding: 3.2rem 3rem; border:1px solid var(--lc-border); border-radius:34px;
      background-color:rgba(255,255,255,.74); box-shadow:0 18px 60px rgba(49,95,105,.08);
    }
    .lc-eyebrow {
      display:inline-flex; align-items:center; gap:7px; border-radius:999px; background:var(--lc-accent-soft);
      padding:6px 11px; font-size:12px; font-weight:700; text-transform:uppercase; letter-spacing:.06em;
    }
    .lc-hero h1 { font-size:clamp(2.5rem,6vw,4.2rem); line-height:1.02; margin:18px 0 14px; }
    .lc-primary-text { color:var(--lc-primary); }
    .lc-lead { color:var(--lc-muted); font-size:1.08rem; line-height:1.7; max-width:720px; }
    .lc-stats { display:flex; gap:30px; flex-wrap:wrap; margin-top:28px; }
    .lc-stat strong {display:block; font-family:'Outfit'; font-size:1.55rem; color:var(--lc-primary-deep);}
    .lc-stat span {font-size:.78rem; color:var(--lc-muted);}

    .lc-section { margin-top: 2.5rem; }
    .lc-section-title {font-size:2.1rem; margin:.4rem 0 .3rem;}
    .lc-section-sub {max-width:760px;color:var(--lc-muted);line-height:1.6;margin-bottom:1.1rem;}
    .lc-pill {display:inline-block;padding:5px 11px;background:var(--lc-primary-soft);color:var(--lc-primary-deep);border-radius:999px;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.07em;}

    .lc-card {
      border:1px solid var(--lc-border); background:var(--lc-card); border-radius:26px;
      padding:1.35rem; height:100%; box-shadow:0 8px 28px rgba(49,95,105,.045);
    }
    .lc-card h3 { margin:.5rem 0 .35rem; font-size:1.16rem; }
    .lc-card p {color:var(--lc-muted);line-height:1.55;font-size:.92rem;}
    .lc-icon {
      width:44px;height:44px;border-radius:16px;background:var(--lc-primary-soft);color:var(--lc-primary-deep);
      display:flex;align-items:center;justify-content:center;font-size:21px;
    }
    .lc-phone {
      max-width:380px; margin: 1.2rem auto; border:8px solid #315f69; border-radius:42px;
      background:#fff; padding:22px; box-shadow:0 24px 60px rgba(26,60,70,.20);
    }
    .lc-notch { width:64px;height:6px;background:#dce5e5;border-radius:99px;margin:0 auto 18px; }
    .lc-wave {display:flex;align-items:end;justify-content:center;gap:7px;height:80px;margin:14px 0;}
    .lc-wave span {width:8px;border-radius:99px;background:var(--lc-primary);display:block;animation:pulse 1.4s ease-in-out infinite alternate;}
    @keyframes pulse { from {opacity:.45;transform:scaleY(.75)} to {opacity:1;transform:scaleY(1.05)} }
    .bubble-user {margin-left:auto;max-width:85%;width:fit-content;background:var(--lc-primary);color:white;border-radius:18px 18px 5px 18px;padding:10px 13px;font-size:.88rem;}
    .bubble-ai {margin-top:10px;max-width:92%;width:fit-content;background:var(--lc-secondary);border-radius:18px 18px 18px 5px;padding:10px 13px;font-size:.88rem;}
    .lc-button-look {display:block;text-align:center;margin-top:18px;background:var(--lc-accent);color:white;border-radius:999px;padding:11px;font-weight:700;}

    .lc-callout {border-radius:22px;padding:1rem 1.1rem;background:var(--lc-accent-soft);border:1px solid #f3d7c9;line-height:1.55;}
    .lc-safety {border-radius:20px;padding:1rem 1.1rem;background:#fff8e6;border:1px solid #ead59a;border-left:5px solid var(--lc-highlight);}
    .lc-answer {border-radius:22px;padding:1.1rem 1.2rem;background:#fff;border:1px solid var(--lc-border);box-shadow:0 7px 22px rgba(49,95,105,.05);}
    .lc-answer.urgent {background:#fff5f3;border-color:#ebc6bf;border-left:5px solid var(--lc-accent);}
    .lc-answer h3 {margin-top:0;}
    .lc-muted {color:var(--lc-muted);font-size:.9rem;}
    .lc-chip {display:inline-block;border:1px solid var(--lc-border);background:#fff;border-radius:999px;padding:5px 10px;margin:3px;font-size:.78rem;color:var(--lc-primary-deep);}

    /* Native widgets */
    .stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] button {
      border-radius:999px !important; font-weight:700 !important; border:1px solid var(--lc-border) !important;
    }
    .stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {
      background:var(--lc-accent) !important;color:white !important;border-color:var(--lc-accent) !important;
    }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea, [data-testid="stSelectbox"] > div > div {
      border-radius:18px !important;
    }
    div[data-testid="stMetric"] {border:1px solid var(--lc-border);border-radius:20px;padding:.85rem 1rem;background:#fff;}
    div[data-testid="stExpander"] {border:1px solid var(--lc-border);border-radius:20px;background:#fff;}
    div[data-testid="stProgressBar"] > div > div { background:var(--lc-primary) !important; }
    [data-testid="stAlert"] {border-radius:18px;}

    .lc-footer {margin-top:3.5rem;padding:2rem 0 1rem;border-top:1px solid var(--lc-border);color:var(--lc-muted);font-size:.82rem;}
    .lc-credit {margin-top:.65rem;color:var(--lc-fg);font-weight:600;}
    .lc-gavel {font-size:3.4rem;text-align:center;margin:.5rem 0;filter:drop-shadow(0 10px 10px rgba(231,199,92,.16));}
    .lc-level {font-family:'Outfit';font-weight:700;color:var(--lc-primary-deep);}

    @media (max-width: 700px) {
      [data-testid="stAppViewBlockContainer"],
      .block-container {
        padding-top: calc(4.75rem + env(safe-area-inset-top)) !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
      }
      .lc-hero {padding:2rem 1.35rem;border-radius:26px;}
      .lc-tagline {display:none;}
      .lc-section-title {font-size:1.7rem;}
    }
    </style>
    """,
    unsafe_allow_html=True,
)

NAV_ITEMS = ["Home", "Voicebox", "Chatbox", "Minigames", "Learn", "Community", "Progress", "Features"]


def esc(value: Any) -> str:
    return html.escape(str(value))


@st.cache_resource
def get_engine() -> LegalLearningEngine:
    return LegalLearningEngine()


@st.cache_data
def get_topics() -> dict[str, dict[str, Any]]:
    return load_topics()


def get_nova_service() -> NovaService:
    """Read secrets at runtime; never hardcode or reveal provider API keys."""
    try:
        secrets = dict(st.secrets)
    except Exception:
        secrets = {}
    return NovaService(NovaConfig.from_settings(secrets=secrets), engine=get_engine())


def ai_mode_notice(nova: NovaService) -> None:
    if nova.config.active:
        text = (
            f"<strong>Enhanced Nova AI:</strong> {esc(nova.config.provider.title())} / "
            f"{esc(nova.config.model)}. AI explanations can be wrong. "
            "Questions are sent to this third-party AI provider only after you opt in. "
            "Do not enter private personal information."
        )
    else:
        text = (
            "<strong>Reviewed lesson mode:</strong> No external AI model is configured. "
            "Nova answers covered topics locally and explicitly tells you when a question "
            "is outside its offline knowledge base. The app owner can activate a stronger "
            "Gemini or OpenAI model using Streamlit secrets."
        )
    st.markdown(f'<div class="lc-callout">{text}</div>', unsafe_allow_html=True)
    if nova.config.active:
        st.checkbox(
            "I understand my question will be sent to the selected AI provider for an educational answer; I will not include identifying information.",
            value=False,
            key="external_ai_opt_in",
        )


def safe_answer(nova: NovaService, question: str, jurisdiction: str, style: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    if nova.config.active and not st.session_state.get("external_ai_opt_in", False):
        # Explicit non-consent: never send the question to the provider.
        local = NovaService(config=NovaConfig(), engine=get_engine())
        result = local.answer(question, jurisdiction, style, history or [])
        result["model_notice"] = "Your question was not sent to an AI provider. Check the privacy box above to use the enhanced model."
        return result
    # Lightweight session limit to discourage uncontrolled public API spending.
    # This is NOT a network-wide rate limit; owners should also set quotas.
    if nova.config.active:
        if st.session_state.get("ai_requests", 0) >= 25:
            local = NovaService(config=NovaConfig(), engine=get_engine())
            result = local.answer(question, jurisdiction, style, history or [])
            result["model_notice"] = "This browser session reached its 25-question AI budget. Showing the offline response."
            return result
        st.session_state.ai_requests = st.session_state.get("ai_requests", 0) + 1
    return nova.answer(question, jurisdiction, style, history or [])


def recent_chat_context() -> list[dict[str, str]]:
    context: list[dict[str, str]] = []
    for message in st.session_state.chat_history[-6:]:
        if message["role"] == "user":
            context.append({"role": "user", "text": message["text"]})
        elif message["role"] == "assistant":
            context.append({"role": "assistant", "text": message["result"]["plain_language"]})
    return context


def init_state() -> None:
    defaults: dict[str, Any] = {
        "page": "Home",
        "question_history": [],
        "chat_history": [],
        "ai_requests": 0,
        "last_voice_answer": None,
        "topic_counts": {},
        "topics_opened": [],
        "quiz_attempts": 0,
        "quiz_correct": 0,
        "quiz_orders": {},
        "quiz_positions": {},
        "quiz_cycles": {},
        "quiz_feedback_by_round": {},
        "community_posts": [
            {
                "title": "How do I check whether a school rule is written down?",
                "body": "Start with the student handbook, then ask which policy applies and who can explain the review process.",
                "topic": "School Rights",
            },
            {
                "title": "What should I save after an online purchase?",
                "body": "Keep the receipt, product description, seller messages, and refund or cancellation terms.",
                "topic": "Contracts and Money",
            },
        ],
        "community_posts_created": 0,
        "bandit": new_bandit_state(),
        "recommended_activity": "Ask the Rights Guide",
        "recommendation_feedback": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def record_topic(topic_id: str) -> None:
    if topic_id in {"safety_support", "safe_alternatives", "uncovered_topic", "privacy_guard"}:
        return
    st.session_state.topic_counts[topic_id] = st.session_state.topic_counts.get(topic_id, 0) + 1
    if topic_id not in st.session_state.topics_opened:
        st.session_state.topics_opened.append(topic_id)


def log_result(result: dict[str, Any]) -> None:
    st.session_state.question_history.append(
        {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "topic": result["topic_label"],
            "topic_id": result["topic_id"],
            "safety_level": result["safety_level"],
            "routing_score": round(float(result["routing_score"]), 3),
            "answer_mode": result.get("source_mode", "offline"),
        }
    )
    record_topic(result["topic_id"])


def answer_for_speech(result: dict[str, Any]) -> str:
    parts = [result["topic_label"], result["plain_language"], *result["key_points"], *result["next_steps"]]
    return re.sub(r"\s+", " ", " ".join(parts)).strip()


def speak(text: str) -> None:
    payload = json.dumps(text)
    components.html(
        f"""
        <script>
        const msg = new SpeechSynthesisUtterance({payload});
        msg.rate = 0.96;
        msg.pitch = 1.02;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(msg);
        </script>
        """,
        height=1,
    )


def top_navigation() -> str:
    st.markdown(
        """
        <div class="lc-topbar">
          <div class="lc-logo">⚖</div>
          <div class="lc-brand">Legal Counsel</div>
          <div class="lc-tagline">Know your rights. Ask Nova. Practice safely.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    current = st.session_state.page if st.session_state.page in NAV_ITEMS else "Home"
    page = st.radio(
        "Navigation",
        NAV_ITEMS,
        index=NAV_ITEMS.index(current),
        horizontal=True,
        label_visibility="collapsed",
        key="nav_radio",
    )
    st.session_state.page = page
    return page


def section_intro(eyebrow: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="lc-section">
          <span class="lc-pill">{esc(eyebrow)}</span>
          <h2 class="lc-section-title">{esc(title)}</h2>
          <p class="lc-section-sub">{esc(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def feature_card(icon: str, title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="lc-card">
          <div class="lc-icon">{icon}</div>
          <h3>{esc(title)}</h3>
          <p>{esc(body)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_footer() -> None:
    st.markdown(
        """
        <div class="lc-footer">
          <strong>Legal Counsel</strong> gives general legal information and learning support, not legal advice.
          Laws vary by location, age, setting, and facts. For a real legal problem, use a qualified local attorney or legal-aid service.
          <div class="lc-credit">Author: Arya Patel &nbsp;•&nbsp; Mentor: Dr. Qingyang Xiao</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_result(result: dict[str, Any], show_speech: bool = True) -> None:
    urgent = result["safety_level"] in {"critical", "high", "blocked"}
    css = "lc-answer urgent" if urgent else "lc-answer"
    points = "".join(f"<li>{esc(x)}</li>" for x in result["key_points"])
    steps = "".join(f"<li>{esc(x)}</li>" for x in result["next_steps"])
    st.markdown(
        f"""
        <div class="{css}">
          <span class="lc-pill">Nova · {esc(result['topic_label'])}</span>
          <h3 style="margin-top:.8rem">{esc(result['plain_language'])}</h3>
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:16px;margin-top:16px">
            <div><strong>Key ideas</strong><ul>{points}</ul></div>
            <div><strong>Possible next steps</strong><ul>{steps}</ul></div>
          </div>
          <p class="lc-muted"><strong>Location note:</strong> {esc(result['jurisdiction_note'])}</p>
          <p class="lc-muted">{esc(result['disclaimer'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if result.get("model_label"):
        st.caption(esc(result["model_label"]))
    if result.get("model_notice"):
        st.warning(result["model_notice"])
    if result.get("source_mode") == "offline":
        st.caption("Topic matching is a retrieval hint, not legal accuracy or confidence. Verify local rules.")
    if result.get("official_resources"):
        st.markdown("**Official materials for independent verification** (not live citations for AI output):")
        for item in result["official_resources"]:
            st.markdown(f'- [{item["title"]}]({item["url"]})')
    if show_speech and st.button("🔊 Hear Nova read this answer", use_container_width=True):
        speak(answer_for_speech(result))


def render_home(topics: dict[str, dict[str, Any]]) -> None:
    c1, c2 = st.columns([1.35, 0.8], gap="large", vertical_alignment="center")
    with c1:
        st.markdown(
            """
            <div class="lc-hero surface-grid">
              <span class="lc-eyebrow">✦ Meet Nova</span>
              <h1>Know your rights<br><span class="lc-primary-text">before you need them.</span></h1>
              <p class="lc-lead">Legal Counsel is a teen-friendly legal learning app. Ask Nova in everyday language, explore common rights topics, and make the ideas stick with short scenario-based games.</p>
              <div class="lc-stats">
                <div class="lc-stat"><strong>Plain</strong><span>teen-friendly explanations</span></div>
                <div class="lc-stat"><strong>Private</strong><span>session-first prototype</span></div>
                <div class="lc-stat"><strong>Practical</strong><span>real-life learning scenarios</span></div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        bars = [18, 34, 52, 70, 44, 62, 28, 48, 22]
        spans = "".join(
            f'<span style="height:{h}px;animation-delay:{i*90}ms"></span>' for i, h in enumerate(bars)
        )
        st.markdown(
            f"""
            <div class="lc-phone">
              <div class="lc-notch"></div>
              <div class="lc-muted"><strong>Nova · Voicebox</strong></div>
              <div class="lc-wave">{spans}</div>
              <div class="bubble-user">Can my school search my backpack?</div>
              <div class="bubble-ai">The answer depends on the school, location, and facts. I can explain the general framework and what to check next.</div>
              <div class="lc-button-look">🎙 Hold to talk</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="lc-safety"><strong>Good to know:</strong> this prototype teaches general legal concepts. It does not replace a lawyer, emergency service, school safeguarding process, or other qualified local help.</div>',
        unsafe_allow_html=True,
    )

    section_intro("The core four", "Four ways to actually learn this stuff", "Each space has one job, so the app feels more like a guide than a textbook.")
    cols = st.columns(4)
    cards = [
        ("🎙", "Voicebox", "Record a question, enter a transcript, and hear Nova read the educational response aloud."),
        ("💬", "Chatbox", "Ask questions in plain English and receive structured, safety-screened learning guidance."),
        ("🎮", "Minigames", "Practice with reviewed scenario questions and instant explanations."),
        ("⚖", "Progress Gavel", "Watch your session progress grow as you explore, ask, and practice."),
    ]
    for col, card in zip(cols, cards):
        with col:
            feature_card(*card)

    section_intro("Explore", "Popular rights topics", "Start with a general topic, then use Chatbox for a more specific educational question.")
    topic_ids = list(topics)[:8]
    for start in range(0, len(topic_ids), 4):
        cols = st.columns(4)
        for col, topic_id in zip(cols, topic_ids[start:start+4]):
            topic = topics[topic_id]
            with col:
                feature_card("📚", topic["short_label"], topic["summary"])

    render_footer()


def render_chatbox(nova: NovaService) -> None:
    section_intro("Chatbox", "Type it, and Nova explains it", "Ask about a right, rule, or situation without posting names, addresses, school identifiers, account credentials, or other private information.")

    ai_mode_notice(nova)

    # Conversation visual from supplied design.
    st.markdown(
        '<div class="lc-card"><div class="lc-icon">💬</div><h3>Nova</h3><p>Hey — I’m Nova. Ask a general question about rights at school, online, at work, or in everyday life. I’ll keep it in plain language.</p></div>',
        unsafe_allow_html=True,
    )

    for item in st.session_state.chat_history[-8:]:
        if item["role"] == "user":
            st.markdown(f'<div class="bubble-user" style="margin-top:10px">{esc(item["text"])}</div>', unsafe_allow_html=True)
        else:
            result = item["result"]
            st.markdown(f'<div class="bubble-ai"><strong>Nova:</strong> {esc(result["plain_language"])}</div>', unsafe_allow_html=True)

    starters = [
        "Can my school search my phone?",
        "What should I save if someone threatens me online?",
        "What does a contract mean if I am under 18?",
        "How does handing down real estate from parents to children work?",
    ]
    st.caption("Try a starter: " + "  ·  ".join(starters))

    with st.form("chat_form", clear_on_submit=True):
        question = st.text_input("Ask Nova a question", placeholder="Example: Can my school search my phone?")
        c1, c2 = st.columns([1, 1])
        with c1:
            jurisdiction = st.text_input("State or country (optional)", placeholder="Example: Maryland")
        with c2:
            reading = st.selectbox("Answer style", ["Quick and clear", "Step by step", "Key ideas first"])
        submitted = st.form_submit_button("Send to Nova", type="primary", use_container_width=True)

    if submitted:
        if len(question.strip()) < 5:
            st.error("Please enter a complete question without private information.")
        else:
            result = safe_answer(nova, question, jurisdiction, reading, recent_chat_context())
            result["reading_style"] = reading
            log_result(result)
            st.session_state.chat_history.append({"role": "user", "text": question.strip()})
            st.session_state.chat_history.append({"role": "assistant", "result": result})
            st.rerun()

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "assistant":
        render_result(st.session_state.chat_history[-1]["result"])

    c1, c2, c3 = st.columns(3)
    with c1: feature_card("📖", "Plain-English structure", "General rule, key ideas, safer next steps, and a reminder to verify local law.")
    with c2: feature_card("🔒", "Privacy-aware", "The interface warns against entering identifying or sensitive information.")
    with c3: feature_card("🛟", "Safety mode", "High-risk questions are redirected toward trusted adults, qualified services, or emergency support.")
    render_footer()


def render_voicebox(nova: NovaService) -> None:
    section_intro("Voicebox", "Ask out loud. Hear Nova answer.", "The Streamlit version keeps the supplied Voicebox look while using a reliable free-cloud workflow: capture audio, enter/confirm the transcript, then hear the answer through your browser’s text-to-speech.")

    ai_mode_notice(nova)
    c1, c2 = st.columns([1.05, .95], gap="large")
    with c1:
        st.markdown(
            """
            <div class="lc-phone">
              <div class="lc-notch"></div>
              <div class="lc-muted"><strong>Nova · Voicebox</strong></div>
              <div class="lc-wave"><span style="height:20px"></span><span style="height:45px"></span><span style="height:66px"></span><span style="height:38px"></span><span style="height:58px"></span><span style="height:28px"></span><span style="height:50px"></span></div>
              <div class="bubble-user">Ask the way you would ask a friend.</div>
              <div class="bubble-ai">I’ll explain the general legal idea, point out what can vary by location, and flag when real-world help matters.</div>
              <div class="lc-button-look">🎙 Voice question</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with c2:
        audio = st.audio_input("Record your question")
        if audio is not None:
            st.success("Recording captured in this session. For privacy and reliability, this open-source build does not automatically send the audio to a third-party transcription service.")
        with st.form("voice_form"):
            transcript = st.text_area("Voice transcript / question", placeholder="Example: What should I do if someone is impersonating me online?", height=110)
            jurisdiction = st.text_input("State or country (optional)", placeholder="Example: Maryland")
            go = st.form_submit_button("Ask Nova", type="primary", use_container_width=True)
        if go:
            if len(transcript.strip()) < 5:
                st.error("Enter or confirm the spoken question first.")
            else:
                result = safe_answer(nova, transcript, jurisdiction, "Quick and clear")
                log_result(result)
                st.session_state.last_voice_answer = result
        if st.session_state.last_voice_answer:
            render_result(st.session_state.last_voice_answer)

    st.markdown('<div class="lc-callout"><strong>Voice privacy:</strong> audio is not automatically transcribed or sent to an AI provider. Only your confirmed typed transcript is submitted when you explicitly opt in to enhanced Nova AI. Browser speech synthesis can read the answer aloud.</div>', unsafe_allow_html=True)
    render_footer()


def render_minigames(topics: dict[str, dict[str, Any]]) -> None:
    section_intro("Minigames", "Learning your rights, minus the textbook", "Short scenario questions use the reviewed local topic library and explain the answer immediately.")
    cols = st.columns(4)
    modes = [
        ("🧩", "Situation Match", "Choose the safest or strongest response to a realistic situation."),
        ("⏱", "Vocab Sprint", "Build familiarity with legal terms using plain definitions."),
        ("✨", "Topic Challenge", "Practice different reviewed questions in a shuffled set."),
        ("🏆", "Progress Gavel", "Each completed question contributes to your session progress."),
    ]
    for col, item in zip(cols, modes):
        with col:
            feature_card(*item)

    quiz_topics = {t["short_label"]: tid for tid, t in topics.items() if t.get("quiz")}
    label = st.selectbox("Choose a topic", list(quiz_topics))
    topic_id = quiz_topics[label]
    questions = get_quiz(topic_id)
    round_info = current_round(st.session_state, topic_id, len(questions))
    q = questions[round_info.question_index]
    round_key = round_info.key  # Unique across questions, topics, and shuffled sets.
    feedback = st.session_state.quiz_feedback_by_round.get(round_key)

    c1, c2 = st.columns([1.2, .8], gap="large")
    with c1:
        st.markdown(
            f'<div class="lc-card"><span class="lc-pill">Round {round_info.round_number} of '
            f'{round_info.total_rounds} · Set {round_info.set_number}</span>'
            f'<h3 style="margin-top:.8rem">{esc(q["question"])}</h3></div>',
            unsafe_allow_html=True,
        )
        # index=None forces a fresh, unselected answer for each new question.
        # Including the round key in the widget key prevents old choices from
        # reappearing after the user clicks Next round or changes topic.
        choice = st.radio(
            "Choose one answer",
            range(len(q["options"])),
            format_func=lambda i: q["options"][i],
            index=None,
            key=f"quiz_choice_{round_key}",
            disabled=feedback is not None,
        )
        if feedback is None:
            if st.button(
                "Check answer",
                type="primary",
                use_container_width=True,
                disabled=choice is None,
                key=f"quiz_check_{round_key}",
            ):
                # Award XP/accuracy once per question, not on every rerun or
                # repeated button press. A new set can be scored again.
                is_new_attempt = submit_answer(
                    st.session_state,
                    round_info,
                    selected_option=choice,
                    correct_option=q["answer"],
                    options=q["options"],
                    explanation=q["explanation"],
                )
                if is_new_attempt:
                    record_topic(topic_id)
                st.rerun()
        else:
            if feedback["correct"]:
                st.success("Correct — " + feedback["explanation"])
            else:
                st.error("Not quite. Best answer: " + feedback["correct_option"])
                st.info(feedback["explanation"])
            if len(questions) > 1:
                if st.button("Next round", use_container_width=True, key=f"quiz_next_{round_key}"):
                    # Always moves to a different question. The final round
                    # reshuffles a new set without repeating the last item.
                    advance_round(st.session_state, topic_id, len(questions))
                    st.rerun()
            else:
                st.info("This topic has one reviewed question. More rounds are coming soon.")

        st.caption(
            f"{len(questions)} different questions in this topic · "
            "Questions reshuffle after each set."
        )
    with c2:
        attempts = st.session_state.quiz_attempts
        accuracy = st.session_state.quiz_correct / attempts if attempts else 0
        xp = min(1600, len(st.session_state.question_history) * 80 + attempts * 120 + len(st.session_state.topics_opened) * 50)
        st.markdown('<div class="lc-card"><div class="lc-icon">⚖</div><h3>Progress Gavel</h3><p>Your learning activity fills the gavel during this browser session.</p><div class="lc-gavel">🔨</div></div>', unsafe_allow_html=True)
        st.progress(min(xp / 1600, 1.0))
        st.caption(f"{xp:,} XP · {attempts} questions · {accuracy:.0%} accuracy")

    render_footer()


def render_learn(topics: dict[str, dict[str, Any]]) -> None:
    section_intro("Learn", "The law in everyday language", "Browse the reviewed topic library before asking Nova a follow-up question.")
    label_to_id = {t["label"]: tid for tid, t in topics.items()}
    label = st.selectbox("Choose a topic", list(label_to_id))
    topic_id = label_to_id[label]
    topic = topics[topic_id]
    record_topic(topic_id)

    st.markdown(f'<div class="lc-card"><span class="lc-pill">{esc(topic["short_label"])}</span><h2>{esc(topic["label"])}</h2><p>{esc(topic["summary"])}</p></div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### What to understand")
        for item in topic["key_points"]: st.markdown(f"- {item}")
    with c2:
        st.markdown("### Safer next steps")
        for item in topic["next_steps"]: st.markdown(f"- {item}")
    st.markdown(f'<div class="lc-callout"><strong>Common myth:</strong> {esc(topic["myth"])}</div>', unsafe_allow_html=True)
    st.markdown("### Questions to explore")
    for q in topic["example_questions"]: st.markdown(f'<span class="lc-chip">{esc(q)}</span>', unsafe_allow_html=True)
    st.caption("Jurisdiction-specific content should be reviewed by a qualified legal/content reviewer before publication.")
    render_footer()


def render_community(topics: dict[str, dict[str, Any]]) -> None:
    section_intro("Community", "Share ideas without oversharing", "A session-only forum prototype demonstrates pre-post moderation. It does not publish to the internet or persist after the session.")
    st.markdown('<div class="lc-safety"><strong>Privacy rule:</strong> do not post names, phone numbers, email addresses, street addresses, account details, intimate images, or identifying information about another teen.</div>', unsafe_allow_html=True)

    with st.form("community_form", clear_on_submit=True):
        title = st.text_input("Discussion title", max_chars=120)
        topic = st.selectbox("Topic", [t["short_label"] for t in topics.values()])
        body = st.text_area("Post", max_chars=1200, height=110)
        submitted = st.form_submit_button("Safety check and post", type="primary", use_container_width=True)
    if submitted:
        result = moderate_community_post(title, body)
        if result.allowed:
            st.session_state.community_posts.insert(0, {"title": title.strip(), "body": body.strip(), "topic": topic})
            st.session_state.community_posts_created += 1
            st.success("This post passed the prototype safety check and was added to this session.")
        else:
            st.error("This post was not added.")
            for reason in result.reasons: st.markdown(f"- {reason}")
            if result.support_message: st.warning(result.support_message)

    st.markdown("### Session discussions")
    for post in st.session_state.community_posts:
        st.markdown(
            f'<div class="lc-card" style="margin-bottom:12px"><span class="lc-pill">{esc(post["topic"])}</span><h3>{esc(post["title"])}</h3><p>{esc(post["body"])}</p><div class="lc-muted">Anonymous participant · verify legal claims before relying on them.</div></div>',
            unsafe_allow_html=True,
        )
    render_footer()


def render_progress(topics: dict[str, dict[str, Any]]) -> None:
    section_intro("Progress Gavel", "One visual for what you’ve explored", "Progress is session-only in this open-source prototype. No account or long-term profile is required.")
    attempts = st.session_state.quiz_attempts
    accuracy = st.session_state.quiz_correct / attempts if attempts else 0
    xp = min(1600, len(st.session_state.question_history) * 80 + attempts * 120 + len(st.session_state.topics_opened) * 50 + st.session_state.community_posts_created * 40)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Questions asked", len(st.session_state.question_history))
    c2.metric("Topics explored", len(st.session_state.topics_opened))
    c3.metric("Quiz accuracy", f"{accuracy:.0%}")
    c4.metric("Session XP", xp)

    st.markdown('<div class="lc-card"><div class="lc-icon">⚖</div><h3>Progress Gavel</h3><p>From Rights Rookie to Know-Your-Rights Pro.</p></div>', unsafe_allow_html=True)
    st.progress(min(xp / 1600, 1.0))
    level = "Rights Rookie" if xp < 400 else "Case Builder" if xp < 900 else "Know-Your-Rights Pro" if xp < 1500 else "Rights Advocate"
    st.markdown(f'<div class="lc-level">Current level: {esc(level)}</div>', unsafe_allow_html=True)

    if st.session_state.topic_counts:
        rows = [{"Topic": topics[k]["short_label"], "Interactions": v} for k, v in st.session_state.topic_counts.items() if k in topics]
        st.bar_chart(pd.DataFrame(rows).set_index("Topic"))

    section_intro("Learning AI", "Preference clustering without sensitive demographics", "This demonstration clusters learning preferences only; it does not use race, religion, health, precise location, or other sensitive personal traits.")
    a, b = st.columns(2)
    with a:
        quiz_confidence = st.slider("Quiz confidence", 0, 100, 60)
        exploration = st.slider("Interest in new topics", 0, 100, 70)
    with b:
        discussion_interest = st.slider("Interest in moderated discussion", 0, 100, 55)
        safety_awareness = st.slider("Safety/privacy awareness", 0, 100, 80)
    profile = classify_learner_profile(quiz_confidence, exploration, discussion_interest, safety_awareness)
    st.success(f"Learning style: {profile['label']}")
    st.write(profile["suggestion"])

    section_intro("Adaptive practice", "Bounded reinforcement-learning demo", "The bandit may choose which learning activity to suggest. It cannot rewrite legal content, safety messages, or moderation rules.")
    if st.button("Recommend my next activity", type="primary"):
        st.session_state.recommended_activity = recommend_activity(st.session_state.bandit)
        st.session_state.recommendation_feedback = ""
    activity = st.session_state.recommended_activity
    st.info("Nova suggests: " + activity)
    g, n = st.columns(2)
    if g.button("Helpful", use_container_width=True):
        update_bandit(st.session_state.bandit, activity, 1.0)
        st.session_state.recommendation_feedback = "Thanks — the activity preference was updated."
    if n.button("Not helpful yet", use_container_width=True):
        update_bandit(st.session_state.bandit, activity, 0.0)
        st.session_state.recommendation_feedback = "Thanks — the activity preference was updated."
    if st.session_state.recommendation_feedback: st.caption(st.session_state.recommendation_feedback)

    export = {
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "questions_asked": len(st.session_state.question_history),
        "topics_explored": [topics[t]["short_label"] for t in st.session_state.topics_opened if t in topics],
        "quiz_attempts": attempts,
        "quiz_correct": st.session_state.quiz_correct,
        "community_posts_created": st.session_state.community_posts_created,
        "question_history_without_question_text": st.session_state.question_history,
        "activity_values": st.session_state.bandit,
    }
    st.download_button("Download session progress (JSON)", json.dumps(export, indent=2), "legal_counsel_progress.json", "application/json", use_container_width=True)
    render_footer()


def render_features() -> None:
    section_intro("App rundown", "Every part of Legal Counsel", "The migrated Streamlit build keeps the uploaded UI’s clean spaces and teen-friendly visual language while connecting them to the Python legal-learning prototype.")
    items = [
        ("🏠", "Home", "A focused starting point with the product message, core modes, and topic discovery."),
        ("🎙", "Voicebox", "Audio capture, transcript confirmation, safety-screened response, and browser read-aloud."),
        ("💬", "Chatbox", "Context-aware Nova with optional Gemini 3.8 Flash or GPT-5.4 Mini, plus a reviewed offline knowledge base."),
        ("🎮", "Minigames", "Reviewed scenario questions with instant explanations and progress tracking."),
        ("⚖", "Progress Gavel", "Session XP, topic activity, learning-preference clustering, and adaptive activity suggestions."),
        ("👥", "Community", "Session-only discussion mockup with privacy and safety moderation before a post is accepted."),
        ("📍", "Location awareness", "Optional state/country context with no unsupported claim of verified current law."),
        ("🏡", "Home inheritance", "Learn about gifting a house, wills, trusts, probate, deeds, mortgages, and potential tax consequences."),
        ("🧠", "Smarter Nova", "Structured LLM educational answers, recent context, privacy screening, safety-first routing, and no irrelevant topic fallback."),
        ("🔒", "Safety first", "No login is required; risky questions and unsafe community content are redirected or blocked."),
    ]
    for start in range(0, len(items), 4):
        cols = st.columns(4)
        for col, item in zip(cols, items[start:start+4]):
            with col: feature_card(*item)

    section_intro("Project credits", "Built for teen legal literacy", "The author credit is shown here and in the footer; it is not used as the product or assistant name.")
    c1, c2 = st.columns(2)
    with c1: feature_card("✍", "Author", "Arya Patel")
    with c2: feature_card("🎓", "Mentor", "Dr. Qingyang Xiao")

    st.markdown(
        """
        <div class="lc-safety"><strong>Important limitation:</strong> Nova explains general legal concepts and learning steps. It is not a lawyer and should not be used as a substitute for emergency services, mandated reporting channels, or advice from a qualified attorney who knows the jurisdiction and facts.</div>
        """,
        unsafe_allow_html=True,
    )
    render_footer()


def main() -> None:
    init_state()
    nova = get_nova_service()
    topics = get_topics()
    page = top_navigation()

    if page == "Home": render_home(topics)
    elif page == "Voicebox": render_voicebox(nova)
    elif page == "Chatbox": render_chatbox(nova)
    elif page == "Minigames": render_minigames(topics)
    elif page == "Learn": render_learn(topics)
    elif page == "Community": render_community(topics)
    elif page == "Progress": render_progress(topics)
    else: render_features()


if __name__ == "__main__":
    main()
