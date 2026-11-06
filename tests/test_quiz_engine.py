"""Regression tests for the Minigames 'Next round' bug and quiz content."""
from __future__ import annotations

import random
import unittest

from src.legal_engine import get_quiz, load_topics
from src.quiz_engine import advance_round, current_round, shuffled_order, submit_answer


class QuizBankTests(unittest.TestCase):
    def test_every_topic_has_multiple_distinct_reviewed_questions(self) -> None:
        topics = load_topics()
        self.assertEqual(len(topics), 14)
        for topic_id, topic in topics.items():
            with self.subTest(topic=topic_id):
                questions = get_quiz(topic_id)
                self.assertGreaterEqual(len(questions), 6)
                seen = set()
                for q in questions:
                    self.assertIsInstance(q["question"], str)
                    self.assertGreater(len(q["question"]), 12)
                    self.assertNotIn(q["question"].casefold(), seen)
                    seen.add(q["question"].casefold())
                    self.assertEqual(len(q["options"]), 4)
                    self.assertEqual(len(set(q["options"])), 4)
                    self.assertIsInstance(q["answer"], int)
                    self.assertIn(q["answer"], range(4))
                    self.assertGreater(len(q["explanation"]), 20)

    def test_getting_help_has_more_than_one_question(self) -> None:
        questions = get_quiz("general_rights")
        self.assertEqual(len(questions), 8)
        self.assertIn("legal-looking problem", questions[0]["question"])


class QuizRoundTests(unittest.TestCase):
    def test_first_next_round_changes_the_actual_question(self) -> None:
        questions = get_quiz("general_rights")
        state: dict = {}
        first = current_round(state, "general_rights", len(questions), rng=random.Random(11))
        next_round = advance_round(state, "general_rights", len(questions), rng=random.Random(12))
        self.assertNotEqual(first.question_index, next_round.question_index)
        self.assertNotEqual(questions[first.question_index]["question"], questions[next_round.question_index]["question"])
        self.assertEqual((first.round_number, next_round.round_number), (1, 2))
        self.assertNotEqual(first.key, next_round.key)

    def test_each_set_has_all_unique_questions_then_reshuffles(self) -> None:
        questions = get_quiz("general_rights")
        n = len(questions)
        state: dict = {}
        seen = []
        for i in range(n):
            round_info = current_round(state, "general_rights", n, rng=random.Random(2))
            self.assertEqual(round_info.round_number, i + 1)
            self.assertEqual(round_info.set_number, 1)
            seen.append(round_info.question_index)
            if i < n - 1:
                advance_round(state, "general_rights", n, rng=random.Random(i + 5))
        self.assertEqual(set(seen), set(range(n)))
        last_question = seen[-1]
        after = advance_round(state, "general_rights", n, rng=random.Random(20))
        self.assertEqual(after.round_number, 1)
        self.assertEqual(after.set_number, 2)
        self.assertNotEqual(after.question_index, last_question)
        self.assertEqual(set(state["quiz_orders"]["general_rights"]), set(range(n)))

    def test_next_round_never_repeats_immediately_in_any_topic(self) -> None:
        for topic_id, topic in load_topics().items():
            count = len(topic["quiz"])
            with self.subTest(topic=topic_id):
                state: dict = {}
                previous = current_round(state, topic_id, count, rng=random.Random(0))
                for step in range(count * 3):
                    current = advance_round(state, topic_id, count, rng=random.Random(step))
                    self.assertNotEqual(previous.question_index, current.question_index)
                    previous = current

    def test_rerun_does_not_advance_and_topic_switch_keeps_progress(self) -> None:
        state: dict = {}
        help_first = current_round(state, "general_rights", 8, rng=random.Random(3))
        self.assertEqual(help_first, current_round(state, "general_rights", 8))
        school_first = current_round(state, "school_rights", 6, rng=random.Random(4))
        self.assertEqual(school_first, current_round(state, "school_rights", 6))
        self.assertEqual(help_first, current_round(state, "general_rights", 8))
        advance_round(state, "school_rights", 6, rng=random.Random(6))
        self.assertEqual(help_first, current_round(state, "general_rights", 8))

    def test_no_immediate_repeat_even_with_identity_shuffle(self) -> None:
        class NoShuffle:
            def shuffle(self, items):
                pass
        self.assertEqual(shuffled_order(3, previous_last=0, rng=NoShuffle()), [1, 0, 2])

    def test_answer_scored_once_and_new_round_is_unanswered(self) -> None:
        state: dict = {}
        r1 = current_round(state, "general_rights", 8, rng=random.Random(9))
        self.assertTrue(submit_answer(state, r1, 1, 1, ["a", "b", "c", "d"], "Explanation"))
        self.assertFalse(submit_answer(state, r1, 1, 1, ["a", "b", "c", "d"], "Explanation"))
        self.assertEqual(state["quiz_attempts"], 1)
        self.assertEqual(state["quiz_correct"], 1)
        r2 = advance_round(state, "general_rights", 8, rng=random.Random(10))
        self.assertNotIn(r2.key, state["quiz_feedback_by_round"])
        self.assertTrue(submit_answer(state, r2, 0, 1, ["a", "b", "c", "d"], "Explanation"))
        self.assertEqual(state["quiz_attempts"], 2)
        self.assertEqual(state["quiz_correct"], 1)
        self.assertEqual(state["quiz_feedback_by_round"][r2.key]["correct_option"], "b")

    def test_invalid_answer_and_one_question_advance_are_rejected(self) -> None:
        state: dict = {}
        r = current_round(state, "general_rights", 8, rng=random.Random(1))
        with self.assertRaises(ValueError):
            submit_answer(state, r, -1, 1, ["a", "b"], "Explanation")
        with self.assertRaises(ValueError):
            advance_round({}, "only_one", 1)

    def test_changing_question_count_rebuilds_deck(self) -> None:
        state: dict = {}
        current_round(state, "general_rights", 8, rng=random.Random(1))
        after = current_round(state, "general_rights", 6, rng=random.Random(1))
        self.assertEqual(after.total_rounds, 6)
        self.assertEqual(after.round_number, 1)
        self.assertEqual(set(state["quiz_orders"]["general_rights"]), set(range(6)))


if __name__ == "__main__":
    unittest.main()
