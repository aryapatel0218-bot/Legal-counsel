# Minigames: Next round bug fix and content expansion

## Original problem

The old UI calculated the current question using `cursor % len(questions)`.
The **Getting Help** topic contained just one question, so advancing the cursor
always displayed that same question. Most other topics had only one question too.
The previous answer widget could also retain its selected value on reruns.

## What changed

- Expanded `data/legal_topics.json` to **86 unique scenario questions** across **14 topics**.
- Added `src/quiz_engine.py`, a small Python-only state machine that keeps a
  shuffled question deck, per-topic position, and set number in Streamlit
  `st.session_state`.
- After answering, **Next round** advances to a different question. Completing
  a full set starts a newly shuffled set. The next set's first question is
  guaranteed to differ from the last question of the previous set.
- Every question uses a unique Streamlit radio widget key; the next question
  starts **without a preselected answer**, and previous feedback does not leak.
- **Check answer** remains disabled until an option is selected. Scoring is
  idempotent: the same round cannot add attempts or XP twice.
- Topic switching preserves progress independently for each topic.
- All existing Legal Counsel pages, Nova AI backend, teen-safety disclaimers,
  and author/mentor credits remain in place.

## Manual acceptance test on Streamlit Cloud

1. Deploy the extracted repository with entrypoint `streamlit_app.py`.
2. Open **Minigames**, choose **Getting Help**. It should show `Round 1 of 8`.
3. Choose an answer and click **Check answer**. See the correct/incorrect
   feedback and explanation.
4. Click **Next round**. The screen must show `Round 2 of 8`, a **different
   question**, no preselected answer, and no previous feedback.
5. Complete the remaining questions. The next click after `Round 8 of 8`
   must show `Round 1 of 8 · Set 2` with a different question from round 8.
6. Switch to **School Rights**, advance once, then switch back to **Getting
   Help**. Each topic should retain its own position.
7. Verify that the Progress Gavel counts each submitted answer once.
8. Confirm **Author: Arya Patel** and **Mentor: Dr. Qingyang Xiao** in credits.

## Automated regression tests

From the repository root:

```bash
python -m unittest discover -s tests -v
python -m py_compile streamlit_app.py src/legal_engine.py src/nova_ai.py src/quiz_engine.py
```

`tests/test_quiz_engine.py` validates the bank, distinct question selection,
no-repeat reshuffling, per-topic progress, and once-only scoring.
`tests/test_minigames_ui_flow.py` simulates the real Streamlit UI function's
**Check answer → Next round → new question** flow using lightweight fake
widgets, so it runs without a Streamlit server.

## Editing or adding quiz content

Open `data/legal_topics.json`. Every topic has a `quiz` array. Each question
must have a unique `question`, four `options`, a zero-based integer `answer`
(0–3), and a clear `explanation`. Questions are general educational scenarios,
not jurisdiction-specific legal advice; review content with qualified legal
experts before a public minor-facing launch.

No API key or database is required for Minigames. The optional Gemini/OpenAI
provider is only used for the Nova conversational assistant.
