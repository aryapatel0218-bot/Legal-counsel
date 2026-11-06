# UI Migration Notes

The provided UI archive was a React/TanStack/Lovable project using a Legal Counsel design system with soft teal as the primary color, warm coral as the action accent, amber highlights, rounded cards, and the Nova/Voicebox/Chatbox/Minigames/Progress Gavel product model.

For Streamlit Community Cloud reliability, the production runtime does **not** require Node, Vite, React, TanStack, or a second web server. Instead, the supplied visual language and interaction model were reimplemented natively in `streamlit_app.py` using Streamlit widgets plus scoped CSS.

Migrated concepts include:

- Legal Counsel header/product identity
- Nova AI guide identity
- dotted hero surface
- teal/coral/amber design tokens
- rounded feature cards
- mobile phone / Voicebox mockup
- conversation bubbles
- Voicebox workflow
- Chatbox workflow
- Minigame cards and situation questions
- Progress Gavel concept
- privacy/safety callouts
- responsive multi-column layout

The Python legal-learning engine, safety guard, moderation, learner clustering demonstration, and bounded activity recommender remain in `src/legal_engine.py`.


## Streamlit fixed-header compatibility

The root content container now reserves space below Streamlit's fixed application header. This prevents the custom Legal Counsel brand bar from being partially obscured on Community Cloud. Desktop and mobile breakpoints are handled separately, and mobile spacing includes the browser safe-area inset.
