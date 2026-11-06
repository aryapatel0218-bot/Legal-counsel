# Smarter Nova: Gemini / OpenAI Setup and Verification

## What changed

The previous build answered by selecting one of a small set of prepared lessons using TF-IDF. That is not generative AI: the sentence "How does handing down real estate from parents to children work?" produced an unrelated teen-employment answer because its highest text similarity was only 16%.

The new build uses this priority order:

1. **Safety and privacy screen**: emergencies, wrongdoing, exploitation and contact details are not sent to the model.
2. **Real conversational AI**: if enabled in Streamlit secrets and opted into by the user, the app sends the current question, optional state/country, answer-style preference and up to six short prior turns to **Gemini 3.8 Flash** (Google) or **GPT-5.4 Mini** (OpenAI). It expects structured JSON containing a direct explanation, key ideas and next steps.
3. **Offline reviewed lessons**: without a key, without opt-in, or if the AI service fails, the app uses curated explanations. A new home-inheritance lesson covers deeds, gifts, wills, trusts, probate, mortgages, and general US gift/inheritance basis differences. It explicitly declines questions with no matching offline lesson instead of displaying unrelated content.

No live government-law lookup or factual legal verification is implemented. Language models can still make mistakes. Always verify jurisdiction-specific rules with official sources or a qualified professional.

## Configure Google Gemini (typically easiest if you use Google Colab)

1. Sign in to [Google AI Studio](https://aistudio.google.com/) with the account that should own API usage.
2. Create a Gemini API key for an eligible Google project. Confirm allowed models, usage quotas, privacy/data-use terms and any billing requirements. **Free-tier access depends on your account, chosen model and Google’s current rules; it is not guaranteed.**
3. Open [Streamlit Community Cloud](https://share.streamlit.io/) and choose your deployed Legal Counsel app.
4. Open **App settings -> Secrets** (or select **Advanced settings -> Secrets** when creating a new app).
5. Paste this TOML **with your actual key** (never into GitHub):

   ```toml
   LLM_PROVIDER = "gemini"
   GEMINI_API_KEY = "YOUR_REAL_GEMINI_KEY"
   GEMINI_MODEL = "gemini-3.8-flash"
   ```

6. Save the secrets and reboot/redeploy the app if it has not picked up the change.
7. Visit **Chatbox**, confirm it says "Enhanced Nova AI: Gemini", tick the privacy opt-in, then ask:

   `How does handing down real estate from parents to children work?`

8. A correct general educational response should discuss methods such as **lifetime gift/deed versus post-death will/trust/probate**, plus ownership, loan/tax issues and jurisdiction differences. It should **not** discuss teen jobs or wage rules.

If AI Studio does not allow `gemini-3.8-flash` for your account, choose a **currently available model ID listed in AI Studio** and change `GEMINI_MODEL` in Streamlit secrets. Do not silently assume any old model alias will still work.

## Alternatively configure OpenAI

1. Create an API key in your [OpenAI Platform dashboard](https://platform.openai.com/api-keys). API usage may require billing; ChatGPT subscriptions are separate from API billing.
2. In Streamlit app **Settings -> Secrets**, instead paste:

   ```toml
   LLM_PROVIDER = "openai"
   OPENAI_API_KEY = "YOUR_REAL_OPENAI_KEY"
   OPENAI_MODEL = "gpt-5.4-mini"
   ```

3. Save, then visit Chatbox and verify the label shows the OpenAI model. Tick the privacy opt-in before asking a question.

The system allows `LLM_PROVIDER = "auto"` to choose Gemini if `GEMINI_API_KEY` is present, otherwise OpenAI if `OPENAI_API_KEY` is present, otherwise offline. Explicitly choosing a provider helps avoid accidentally using the wrong key. Model names are owner-configurable.

## Update the existing GitHub and Streamlit app

Existing intended destinations:

- GitHub: https://github.com/qxiao2ub/Teen-Rights-Law-App
- Streamlit: https://teen-rights-law.streamlit.app/

1. Extract the ZIP on your Windows PC.
2. Upload **every file and folder inside the ZIP**, not the ZIP itself, to the **root** of the existing GitHub repository on the deployed branch (usually `main`). Replace the old `streamlit_app.py`, `src/`, `data/`, `requirements.txt`, tests, and docs.
3. In the GitHub website UI, commit the changes. If editing via Git Bash, follow the repository's usual `git add`, `git commit`, and `git push` workflow instead.
4. Streamlit Community Cloud typically redeploys after the GitHub branch updates. Confirm your deployment still points to **`streamlit_app.py`**.
5. Streamlit Cloud secrets are configured **separately**; GitHub files cannot transmit an API key into the app by themselves.
6. Confirm the UI looks the same, that the top navigation is not covered, that old mini-games and community screens remain usable, and that the new real estate question returns a relevant answer.

## Security, expense, and teen privacy

- Never put `GEMINI_API_KEY`, `OPENAI_API_KEY` or `secrets.toml` with real keys into GitHub, a screenshot, or chat history. GitHub will not keep a committed key secret. Rotate a compromised key immediately.
- The live model provider receives the user's question and recent conversation **only after** an explicit checkbox opt-in. The app screens common email addresses, phone numbers and street addresses, but **this does not identify every kind of sensitive information**. Avoid collecting identifiable minors' data.
- The app keeps chat history in **Streamlit session state** for the current session. External API providers may retain/process submitted prompts according to their respective terms and your account settings. This prototype is not a complete youth privacy / COPPA compliance program.
- A *per-browser-session* limit of 25 enhanced requests reduces casual repeated use but **is not real server-side rate limiting**. Public apps need provider-side quotas/spending controls, abuse prevention, and privacy/legal review before wide release to minors.
- The K-means and bandit features are learning-demo components. They do **not** train the Gemini/OpenAI model on user conversations or guarantee it improves autonomously.
- All answers are educational; current jurisdictional law is **not verified**. Estate and tax planning require qualified local advice for real situations.
- If there is a provider quota issue, wrong model ID, missing key, or temporary outage, the app shows a warning and uses the limited offline knowledge base. It does not fake a successful live AI answer.

## Debugging tips

- **"Reviewed lesson mode"**: secrets absent/invalid or intentionally set to offline; confirm `LLM_PROVIDER` and the corresponding provider key in Streamlit settings.
- **"Your question was not sent"**: select the privacy opt-in checkbox to enable live AI; otherwise the offline answer is expected.
- **"AI service could not respond"**: verify API access, model ID, model availability, billing/quota, and provider status. Full private provider errors are intentionally not shown to visitors.
- **"No relevant lesson"**: an unsupported question in offline mode. Configure a live model or expand `data/legal_topics.json` with a reviewed lesson and tests.
- **After GitHub push, no change**: verify the correct branch, the repo root contains `streamlit_app.py` and the Streamlit app is pointed to that branch.

Useful documentation:

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- https://ai.google.dev/gemini-api/docs/generate-content/text-generation
- https://developers.openai.com/api/docs/guides/structured-outputs
- https://www.irs.gov/publications/p559
- https://www.irs.gov/publications/p551
