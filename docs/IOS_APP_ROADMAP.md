# iOS App Roadmap

The Streamlit app is the web prototype. A production iOS app should use a separate native client and a secure Python backend.

## Recommended architecture

```text
SwiftUI iOS client
        |
        | HTTPS JSON requests
        v
Python API service
        |
        |-- legal education engine
        |-- reviewed content store
        |-- moderation service
        |-- authentication and consent controls
        |-- audit and incident logs
        `-- human escalation workflow
```

## Phase 1 - Stabilize the web prototype

- Validate navigation, accessibility, reading level, and teen usability.
- Have qualified reviewers approve every legal-content module.
- Define which data is necessary and which data must never be collected.
- Add content versioning and a reviewer sign-off record.

## Phase 2 - Create a Python API

- Move the core engine into a framework such as FastAPI.
- Expose narrow endpoints for topic routing, educational responses, quizzes, and moderation.
- Add authentication, rate limits, request validation, logging, and abuse prevention.
- Return citations and content-version identifiers with every legal response.

Example response contract:

```json
{
  "topic_id": "digital_privacy",
  "topic_label": "Online Privacy, Social Media, and Digital Safety",
  "plain_language": "...",
  "key_points": ["..."],
  "next_steps": ["..."],
  "jurisdiction": "unverified",
  "content_version": "2026-08-review-1",
  "disclaimer": "Educational information only"
}
```

## Phase 3 - Build the SwiftUI client

- Native navigation, dynamic type, VoiceOver, and low-reading-level modes.
- Text and speech input with a clear permission explanation.
- Local display of safety messages even when the network is unavailable.
- No collection of precise location unless it is necessary, consented to, and protected.
- Parent or guardian controls only after legal and youth-safety review.

## Phase 4 - Safety and release readiness

- Threat modeling and penetration testing.
- Youth privacy and consent review.
- Human moderation and appeals workflow.
- Incident-response playbook.
- App Store privacy disclosures and content ratings.
- Open-source license and third-party asset review.
- Copyright, trademark, and contributor-ownership documentation.

## Important boundary

Do not allow a model or reinforcement-learning loop to rewrite legal rules, emergency instructions, or moderation policy without human review and version control.
