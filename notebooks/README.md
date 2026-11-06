# Colab notebook compatibility

`Teen_Law_App_Colab_Prototype.ipynb` is the earlier teaching/prototype notebook illustrating local NLP, ML, quiz, and safety concepts. The deployed Streamlit app now uses **`src/nova_ai.py`** for optional Gemini/OpenAI conversational AI and **`src/legal_engine.py`** for routing, lessons, moderation, clustering, and safe fallbacks. The older notebook remains as a learning artifact and is not the Streamlit entrypoint.

To use a model in Google Colab, follow `docs/SMART_NOVA_SETUP.md`; do not paste real API credentials into a notebook that you intend to publish publicly.
