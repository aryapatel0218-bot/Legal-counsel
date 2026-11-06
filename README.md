# Legal Counsel — Teen Legal Learning App

**Legal Counsel** is an open-source, teen-friendly legal education prototype built in Python and Streamlit. The interface in this repository is a Streamlit-native migration of the supplied Legal Counsel UI design, preserving its soft teal/coral visual system, **Nova** assistant, Voicebox, Chatbox, Minigames, and Progress Gavel concepts while connecting them to the existing Python legal-learning and safety engine.

> **Educational use only.** This app provides general legal information and learning support, not legal advice. Laws vary by jurisdiction, age, setting, and facts. Serious or real-world cases should be handled with a qualified local attorney, legal-aid organization, trusted adult, or emergency service as appropriate.

## Credits

- **Author:** Arya Patel
- **Mentor:** Dr. Qingyang Xiao

The author's first name is used only in the required project credit. It is not the app name, assistant name, or product branding.

## Streamlit Community Cloud

The repository is ready for Streamlit Community Cloud with the entrypoint in the repository root:

```text
streamlit_app.py
```

Deployment steps:

1. Upload the contents of this repository to GitHub.
2. In Streamlit Community Cloud, create a new app from that GitHub repository.
3. Choose the desired branch (usually `main`).
4. Set **Main file path** to `streamlit_app.py`.
5. Deploy. **No API key is required to open the app and access its offline reviewed legal lessons.** To enable **real conversational AI answers**, configure Gemini or OpenAI in **Streamlit App settings → Secrets**. See [`docs/SMART_NOVA_SETUP.md`](docs/SMART_NOVA_SETUP.md).

### Cloud-header layout fix

The app reserves responsive space below Streamlit Community Cloud's fixed header, so the **Legal Counsel** logo, product name, and navigation remain fully visible instead of being covered at the top of the page. The spacing also accounts for mobile browser safe-area insets.

## Local launch

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Activate real conversational AI (required for broad questions)

The app runs without a key, but **offline mode can only explain topics covered by the reviewed lesson library**. To answer open-ended questions with a real LLM, open your deployed Streamlit app's **Settings → Secrets** and add either:

**Option A: Google Gemini (AI Studio key)**

```toml
LLM_PROVIDER = "gemini"
GEMINI_API_KEY = "YOUR_PRIVATE_API_KEY"
GEMINI_MODEL = "gemini-3.8-flash"
```

**Option B: OpenAI (API key)**

```toml
LLM_PROVIDER = "openai"
OPENAI_API_KEY = "YOUR_PRIVATE_API_KEY"
OPENAI_MODEL = "gpt-5.4-mini"
```

**Never commit real API keys to GitHub.** Model availability, usage limits and charges vary by account and provider; the model may also produce incorrect legal explanations. Users must tick the privacy opt-in in Chatbox/Voicebox before a question is sent externally.

For illustrated owner instructions, testing checks, and cost/privacy caveats, see **[`docs/SMART_NOVA_SETUP.md`](docs/SMART_NOVA_SETUP.md)**.

## Minigames update — Next round now works

The previous **Getting Help** topic had only one question, so the old modulo-based
cursor kept displaying the same question after **Next round**. This release
replaces that behavior with a tested shuffled-question deck:

- **86 reviewed questions across 14 legal-learning topics**; Getting Help now has 8 distinct questions, and every other topic has at least 6.
- **Check answer → Next round** advances to a *different* question, with a fresh, unselected answer and cleared feedback.
- Each topic displays **Round X of N · Set Y**. After completing the set, a new shuffled set starts, without immediately repeating the last question.
- Switching topics keeps each topic's place; repeated clicks/reruns do not count an answer twice.
- No AI key or database is needed for these local mini-games. The original legal-safety notices and author/mentor credits are retained.

For the code change, testing steps, and content-editing guide, see [`docs/MINIGAMES_FIX.md`](docs/MINIGAMES_FIX.md).

## Main features

- Home experience modeled on the supplied UI design
- **Nova Voicebox**: browser audio capture, transcript confirmation, and browser text-to-speech answer playback
- **Nova Chatbox**: privacy-opt-in conversational LLM answers via Google Gemini (`gemini-3.8-flash`) **or** OpenAI (`gpt-5.4-mini`), with brief multi-turn context and structured explanations; chat history held in temporary Streamlit session memory
- **Offline fallback**: a reviewed topic library including home inheritance/estate planning; no misleading answer when the best text match is irrelevant
- Safety screening for urgent or unsafe requests and common contact details before an external LLM call
- Legal topic learning cards
- Scenario-based minigames with 86 questions, shuffled rounds, fresh answer selection, and once-only scoring
- Progress Gavel, session XP, and topic activity
- K-means learning-preference demonstration using non-sensitive features
- Bounded reinforcement-learning activity recommender
- Session-only moderated teen community prototype
- Optional state/country context with clear jurisdiction warnings
- Exportable session progress

## Repository structure

```text
.
├── streamlit_app.py              # Streamlit Cloud entrypoint + migrated UI
├── requirements.txt              # Runtime dependencies
├── requirements-dev.txt          # Development/test dependencies
├── src/
│   ├── legal_engine.py           # NLP router, safety guard, moderation, ML/RL demos
│   ├── nova_ai.py                # Gemini/OpenAI model adapters, structured answer validation, offline fallback
│   └── quiz_engine.py            # Reliable shuffled multi-round quiz state machine
├── data/
│   └── legal_topics.json         # Reviewed educational topic/quiz content
├── notebooks/
│   └── Teen_Law_App_Colab_Prototype.ipynb
├── tests/
│   ├── test_legal_engine.py
│   └── test_nova_ai.py
├── docs/
├── .streamlit/config.toml
├── .streamlit/secrets.toml.example # template only; real secrets never committed
├── .github/workflows/tests.yml
├── start_windows.bat              # Optional Windows local launch helper
├── LICENSE
├── SECURITY.md
└── CODE_OF_CONDUCT.md
```

## Voice design note

The app intentionally avoids requiring a paid speech API. Streamlit's browser audio capture can collect a voice question, while the user confirms/types the transcript before it is processed by the local engine. Nova's answer can then be read aloud through the browser's speech-synthesis capability. A production iOS/web release can add an on-device or privacy-reviewed speech-to-text model.

## Privacy and teen-safety design

- No login is required in the prototype.
- Learning history is kept in Streamlit session state and is not designed as a persistent teen profile.
- External AI requests require explicit on-screen opt-in; the selected cloud model provider will receive the submitted question and short conversation context. Review provider data policies and youth protection obligations before a public minor-facing launch.
- App model responses are **not** verified against live statutes or official government websites. Verify legal details with trustworthy current sources.
- A light per-session API request limit is **not** a substitute for real deployment-wide rate limiting and billing quotas.
- Community posts are screened for common PII and high-risk content before being added to the session.
- K-means clustering uses learning-preference scores, not sensitive demographic attributes.
- Reinforcement learning is limited to selecting learning activities; it cannot alter legal/safety content.

See `SECURITY.md`, `CODE_OF_CONDUCT.md`, and `docs/CONTENT_REVIEW_CHECKLIST.md` before extending the app.

## Validation

Run `python -m unittest discover -s tests -v`. The smart-Nova upgrade has **24 unit tests**, including a regression test for home-inheritance questions and mocked provider adapters; a live API connection requires the owner's own credentials. See [`docs/VALIDATION_REPORT.md`](docs/VALIDATION_REPORT.md).
