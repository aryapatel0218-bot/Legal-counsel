from __future__ import annotations

import json
import math
import random
import re
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parents[1]
TOPICS_PATH = BASE_DIR / "data" / "legal_topics.json"


@lru_cache(maxsize=1)
def load_topics() -> dict[str, dict[str, Any]]:
    """Load the reviewed local topic library."""
    return json.loads(TOPICS_PATH.read_text(encoding="utf-8"))


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


@dataclass(frozen=True)
class SafetyAssessment:
    level: str
    category: str
    message: str


@dataclass(frozen=True)
class GuideResponse:
    topic_id: str
    topic_label: str
    routing_score: float
    safety_level: str
    safety_category: str
    plain_language: str
    key_points: list[str]
    next_steps: list[str]
    jurisdiction_note: str
    disclaimer: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModerationResult:
    allowed: bool
    reasons: list[str]
    support_message: str = ""


class TopicRouter:
    """Transparent TF-IDF topic router for a small, reviewed knowledge base."""

    def __init__(self, topics: dict[str, dict[str, Any]]):
        self.topic_ids = list(topics.keys())
        corpus: list[str] = []
        for topic in topics.values():
            corpus.append(
                " ".join(
                    [
                        topic["label"],
                        topic["summary"],
                        " ".join(topic.get("keywords", [])),
                        " ".join(topic.get("example_questions", [])),
                    ]
                )
            )
        self.vectorizer = TfidfVectorizer(
            lowercase=True,
            stop_words="english",
            ngram_range=(1, 2),
            sublinear_tf=True,
        )
        self.topic_matrix = self.vectorizer.fit_transform(corpus)

    def route(self, question: str) -> tuple[str, float]:
        # Legal-domain terms outrank noisy generic word overlap (e.g. "work"
        # in "How does inheritance work?"). Keep this rule deterministic.
        if "estate_inheritance" in self.topic_ids and re.search(
            r"\b(?:inherit(?:ance|ed|ing)?|probate|deed|heirs?|bequeath|"
            r"pass(?:ing)? down (?:a |the )?(?:home|house|property)|hand(?:ing)? down|"
            r"estate planning|living trust|will and testament|step[ -]?up in basis)\b",
            question,
            flags=re.IGNORECASE,
        ):
            return "estate_inheritance", 1.0
        if "patents_inventions" in self.topic_ids and re.search(
            r"\b(?:patents?|invent(?:ion|or|ors)?)\b", question, re.I
        ):
            return "patents_inventions", 1.0
        if "housing_renters" in self.topic_ids and re.search(
            r"\b(?:landlord|renter|rental|tenant|lease|evict(?:ion|ed)?|"
            r"security deposit|rent increase|apartment)\b", question, re.I
        ):
            return "housing_renters", 1.0
        query = self.vectorizer.transform([question])
        scores = cosine_similarity(query, self.topic_matrix)[0]
        best_index = int(np.argmax(scores))
        best_score = float(scores[best_index])
        if not question.strip() or best_score < 0.045:
            return "general_rights", best_score
        return self.topic_ids[best_index], best_score


class SafetyGuard:
    """Rule-based safety layer that always runs before topic routing."""

    IMMEDIATE_PATTERNS = [
        r"\bi am in danger right now\b",
        r"\bsomeone is trying to hurt me\b",
        r"\bsomeone has a weapon\b",
        r"\bi am being followed\b",
        r"\bi was kidnapped\b",
        r"\bthere is a shooting\b",
        r"\bhelp me escape an attacker\b",
    ]
    SELF_HARM_PATTERNS = [
        r"\bi want to die\b",
        r"\bi want to kill myself\b",
        r"\bi am going to hurt myself\b",
        r"\bself harm right now\b",
    ]
    ABUSE_OR_EXPLOITATION_PATTERNS = [
        r"\bbeing abused\b",
        r"\bmy parent hits me\b",
        r"\ban adult asked me for nudes\b",
        r"\bthreaten(?:ing)? to leak (?:my )?(?:nude|private|intimate)\b",
        r"\bblackmail(?:ing)? me with (?:a )?(?:photo|video|image)\b",
        r"\bsextortion\b",
    ]
    WRONGDOING_PATTERNS = [
        r"\bhow (?:do|can) i hide evidence\b",
        r"\bhow (?:do|can) i avoid the police\b",
        r"\bhow (?:do|can) i get away with\b",
        r"\bdelete evidence without getting caught\b",
        r"\bhow to hack\b",
        r"\bhow to blackmail\b",
        r"\bhow to dox\b",
    ]

    @staticmethod
    def _matches(text: str, patterns: Iterable[str]) -> bool:
        return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)

    def assess(self, question: str) -> SafetyAssessment:
        text = question.strip()
        if self._matches(text, self.SELF_HARM_PATTERNS):
            return SafetyAssessment(
                level="critical",
                category="self_harm",
                message=(
                    "This sounds like an immediate safety situation. Move toward a safe place and contact "
                    "local emergency services or a trusted adult who can stay with you now. This educational "
                    "app cannot provide crisis care."
                ),
            )
        if self._matches(text, self.IMMEDIATE_PATTERNS):
            return SafetyAssessment(
                level="critical",
                category="immediate_danger",
                message=(
                    "Your immediate safety comes first. Move toward a safer location if possible and contact "
                    "local emergency services or a trusted adult who can act now. Do not rely on this app during "
                    "an emergency."
                ),
            )
        if self._matches(text, self.ABUSE_OR_EXPLOITATION_PATTERNS):
            return SafetyAssessment(
                level="high",
                category="abuse_or_exploitation",
                message=(
                    "You should not handle abuse, exploitation, blackmail, or threats alone. Preserve evidence "
                    "without forwarding harmful content, stop engaging when safe, and tell a trusted adult or "
                    "qualified local authority promptly. Use emergency services when danger is immediate."
                ),
            )
        if self._matches(text, self.WRONGDOING_PATTERNS):
            return SafetyAssessment(
                level="blocked",
                category="wrongdoing_or_evasion",
                message=(
                    "I cannot help hide evidence, evade authorities, hack accounts, dox people, or harm someone. "
                    "I can explain lawful options such as preserving records, getting a trusted adult, correcting "
                    "a mistake, or contacting a qualified lawyer."
                ),
            )
        return SafetyAssessment(level="standard", category="none", message="")


class LegalLearningEngine:
    """Teen-friendly legal education engine with bounded behavior."""

    DISCLAIMER = (
        "Educational information only. This is not legal advice, does not create a lawyer-client relationship, "
        "and may not reflect the law where you live."
    )

    def __init__(self, topics: dict[str, dict[str, Any]] | None = None):
        self.topics = topics or load_topics()
        self.router = TopicRouter(self.topics)
        self.safety = SafetyGuard()

    def answer(self, question: str, jurisdiction: str = "") -> GuideResponse:
        question = question.strip()
        assessment = self.safety.assess(question)

        jurisdiction_clean = re.sub(r"\s+", " ", jurisdiction.strip())[:80]
        if jurisdiction_clean:
            jurisdiction_note = (
                f"You entered '{jurisdiction_clean}'. The app does not verify local law, so use this only as a "
                "starting point and check an official source or qualified professional in that location."
            )
        else:
            jurisdiction_note = (
                "Laws vary by country, state, age, school type, and the facts. Add a location only when useful, "
                "and do not enter a home address or other private information."
            )

        if assessment.level == "critical":
            return GuideResponse(
                topic_id="safety_support",
                topic_label="Immediate Safety Support",
                routing_score=1.0,
                safety_level=assessment.level,
                safety_category=assessment.category,
                plain_language=assessment.message,
                key_points=[
                    "Move toward a safer place when you can do so safely.",
                    "Contact local emergency services or a trusted adult who can act now.",
                    "Do not depend on an educational app during a crisis.",
                ],
                next_steps=[
                    "Use a phone or nearby person to get real-world help.",
                    "Stay with a safe person when possible.",
                    "Share only the information responders need to help you.",
                ],
                jurisdiction_note=jurisdiction_note,
                disclaimer=self.DISCLAIMER,
            )

        if assessment.level == "blocked":
            return GuideResponse(
                topic_id="safe_alternatives",
                topic_label="Safe and Lawful Alternatives",
                routing_score=1.0,
                safety_level=assessment.level,
                safety_category=assessment.category,
                plain_language=assessment.message,
                key_points=[
                    "Do not destroy, alter, or hide possible evidence.",
                    "Do not threaten, impersonate, hack, or expose private information.",
                    "A trusted adult or qualified lawyer can help you choose a lawful next step.",
                ],
                next_steps=[
                    "Stop the risky action.",
                    "Preserve a factual record.",
                    "Tell a trusted adult and get qualified help for a real case.",
                ],
                jurisdiction_note=jurisdiction_note,
                disclaimer=self.DISCLAIMER,
            )

        topic_id, score = self.router.route(question)
        topic = self.topics[topic_id]
        plain_language = topic["summary"]
        key_points = list(topic["key_points"])
        next_steps = list(topic["next_steps"])

        if assessment.level == "high":
            plain_language = assessment.message + " " + plain_language
            key_points = [
                "Do not manage a serious safety issue alone.",
                "Preserve evidence without reposting or forwarding harmful material.",
            ] + key_points[:2]
            next_steps = [
                "Tell a trusted adult or qualified local authority promptly.",
                "Use emergency services when danger is immediate.",
            ] + next_steps[:2]

        return GuideResponse(
            topic_id=topic_id,
            topic_label=topic["label"],
            routing_score=score,
            safety_level=assessment.level,
            safety_category=assessment.category,
            plain_language=plain_language,
            key_points=key_points,
            next_steps=next_steps,
            jurisdiction_note=jurisdiction_note,
            disclaimer=self.DISCLAIMER,
        )


EMAIL_PATTERN = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?<!\d)(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}(?!\d)")
ADDRESS_PATTERN = re.compile(
    r"\b\d{1,6}\s+[A-Za-z0-9.'-]+(?:\s+[A-Za-z0-9.'-]+){0,4}\s+"
    r"(?:street|st|road|rd|avenue|ave|lane|ln|drive|dr|court|ct|boulevard|blvd|way)\b",
    re.IGNORECASE,
)


def moderate_community_post(title: str, body: str) -> ModerationResult:
    """Block high-risk or identifying content before a demo post is stored in session."""
    text = f"{title}\n{body}".strip()
    reasons: list[str] = []
    support_message = ""

    if len(title.strip()) < 4 or len(body.strip()) < 12:
        reasons.append("Add a clear title and enough context for a useful discussion.")
    if len(title) > 120 or len(body) > 1200:
        reasons.append("Keep the title under 120 characters and the post under 1,200 characters.")
    if EMAIL_PATTERN.search(text) or PHONE_PATTERN.search(text) or ADDRESS_PATTERN.search(text):
        reasons.append("Remove email addresses, phone numbers, and street addresses.")
    if re.search(r"\b(?:i will|we will|going to)\s+(?:kill|hurt|attack|shoot|stab)\b", text, re.IGNORECASE):
        reasons.append("Threats of violence cannot be posted.")
        support_message = "If anyone is in immediate danger, contact local emergency services or a trusted adult now."
    if re.search(r"\b(?:nude|intimate image|sextortion|sexual abuse)\b", text, re.IGNORECASE):
        reasons.append("Sensitive exploitation details should not be posted in a public teen forum.")
        support_message = (
            "Preserve evidence without forwarding it and tell a trusted adult or qualified local authority. "
            "Use emergency services if danger is immediate."
        )
    if re.search(r"\b(?:buy|sell)\s+(?:drugs|fake id|stolen)\b", text, re.IGNORECASE):
        reasons.append("Requests to buy or sell illegal or stolen items are not allowed.")
    if re.search(r"\b(?:dox|hack|blackmail)\s+(?:them|him|her|someone)\b", text, re.IGNORECASE):
        reasons.append("Requests to dox, hack, or blackmail someone are not allowed.")

    return ModerationResult(allowed=not reasons, reasons=reasons, support_message=support_message)


LEARNER_TRAINING = np.array(
    [
        [35, 85, 20, 55], [42, 90, 25, 60], [50, 78, 30, 58], [47, 82, 35, 65],
        [65, 45, 82, 70], [72, 40, 90, 75], [60, 55, 88, 68], [70, 50, 80, 72],
        [82, 55, 45, 92], [88, 50, 35, 95], [75, 62, 48, 90], [90, 42, 30, 88],
    ],
    dtype=float,
)


def classify_learner_profile(
    quiz_confidence: int,
    exploration: int,
    discussion_interest: int,
    safety_awareness: int,
) -> dict[str, Any]:
    """Demonstrate K-means clustering without storing identity or demographic data."""
    scaler = StandardScaler()
    training_scaled = scaler.fit_transform(LEARNER_TRAINING)
    model = KMeans(n_clusters=3, random_state=42, n_init=20)
    labels = model.fit_predict(training_scaled)

    user = np.array([[quiz_confidence, exploration, discussion_interest, safety_awareness]], dtype=float)
    cluster_id = int(model.predict(scaler.transform(user))[0])
    centers = scaler.inverse_transform(model.cluster_centers_)
    center = centers[cluster_id]

    if center[3] >= 82:
        label = "Safety-first planner"
        suggestion = "Review a real-life scenario, then practice identifying the safest next step."
    elif center[2] >= center[1]:
        label = "Community collaborator"
        suggestion = "Use a moderated discussion prompt and compare several respectful viewpoints."
    else:
        label = "Curious explorer"
        suggestion = "Open a new topic card, ask a follow-up question, and finish with a short quiz."

    return {
        "cluster_id": cluster_id,
        "label": label,
        "suggestion": suggestion,
        "center": {
            "quiz_confidence": round(float(center[0]), 1),
            "exploration": round(float(center[1]), 1),
            "discussion_interest": round(float(center[2]), 1),
            "safety_awareness": round(float(center[3]), 1),
        },
        "training_cluster_sizes": {
            str(i): int(np.sum(labels == i)) for i in sorted(set(labels.tolist()))
        },
    }


ACTIVITIES = [
    "Ask the Rights Guide",
    "Take a mini-game",
    "Read a topic card",
    "Review safety steps",
]


def new_bandit_state() -> dict[str, dict[str, float]]:
    return {
        "counts": {activity: 0.0 for activity in ACTIVITIES},
        "values": {activity: 0.5 for activity in ACTIVITIES},
    }


def recommend_activity(
    state: dict[str, dict[str, float]],
    epsilon: float = 0.12,
    seed: int | None = None,
) -> str:
    """Epsilon-greedy recommendation. It may change activities, never legal or safety content."""
    rng = random.Random(seed)
    if rng.random() < epsilon:
        return rng.choice(ACTIVITIES)
    best_value = max(state["values"].values())
    best = [name for name, value in state["values"].items() if math.isclose(value, best_value)]
    return sorted(best)[0]


def update_bandit(
    state: dict[str, dict[str, float]],
    activity: str,
    reward: float,
) -> dict[str, dict[str, float]]:
    if activity not in ACTIVITIES:
        raise ValueError(f"Unknown activity: {activity}")
    reward = max(0.0, min(1.0, float(reward)))
    count = state["counts"].get(activity, 0.0) + 1.0
    old_value = state["values"].get(activity, 0.5)
    new_value = old_value + (reward - old_value) / count
    state["counts"][activity] = count
    state["values"][activity] = new_value
    return state


def get_quiz(topic_id: str) -> list[dict[str, Any]]:
    topics = load_topics()
    return list(topics[topic_id].get("quiz", []))
