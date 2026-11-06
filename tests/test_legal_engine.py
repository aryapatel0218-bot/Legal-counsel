from __future__ import annotations

import unittest

from src.legal_engine import (
    LegalLearningEngine,
    classify_learner_profile,
    moderate_community_post,
    new_bandit_state,
    recommend_activity,
    update_bandit,
)


class LegalEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.engine = LegalLearningEngine()

    def test_school_question_routes_to_school_topic(self) -> None:
        result = self.engine.answer("Can my school search my phone?")
        self.assertEqual(result.topic_id, "school_rights")
        self.assertGreater(result.routing_score, 0.04)

    def test_immediate_danger_triggers_critical_response(self) -> None:
        result = self.engine.answer("I am in danger right now")
        self.assertEqual(result.safety_level, "critical")
        self.assertEqual(result.topic_id, "safety_support")

    def test_wrongdoing_request_is_blocked(self) -> None:
        result = self.engine.answer("How can I hide evidence?")
        self.assertEqual(result.safety_level, "blocked")
        self.assertEqual(result.topic_id, "safe_alternatives")

    def test_community_post_blocks_contact_information(self) -> None:
        result = moderate_community_post(
            "Please contact me",
            "My phone number is 301-555-0199 and I want private advice.",
        )
        self.assertFalse(result.allowed)
        self.assertTrue(any("phone" in reason.lower() for reason in result.reasons))

    def test_normal_community_post_is_allowed(self) -> None:
        result = moderate_community_post(
            "School handbook question",
            "Where can students usually find a written school discipline policy?",
        )
        self.assertTrue(result.allowed)

    def test_learner_cluster_returns_label(self) -> None:
        result = classify_learner_profile(65, 80, 40, 75)
        self.assertIn(result["label"], {
            "Safety-first planner",
            "Community collaborator",
            "Curious explorer",
        })

    def test_bandit_updates_only_requested_activity(self) -> None:
        state = new_bandit_state()
        activity = recommend_activity(state, epsilon=0.0, seed=1)
        before = dict(state["values"])
        update_bandit(state, activity, 1.0)
        self.assertGreaterEqual(state["values"][activity], before[activity])
        self.assertEqual(state["counts"][activity], 1.0)


if __name__ == "__main__":
    unittest.main()
