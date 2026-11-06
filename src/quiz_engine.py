"""Pure, Streamlit-independent state machine for multi-round legal learning quizzes.

Each topic receives a shuffled deck of distinct reviewed questions. Completing the
last round starts a new shuffled set; the next question is never the same as the
one just completed, provided the topic has at least two questions.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any, MutableMapping


@dataclass(frozen=True)
class QuizRound:
    topic_id: str
    question_index: int
    round_number: int
    total_rounds: int
    set_number: int
    key: str


def shuffled_order(
    question_count: int,
    *,
    previous_last: int | None = None,
    rng: random.Random | None = None,
) -> list[int]:
    """Create a permutation and avoid an immediate repeat across deck boundaries."""
    if question_count < 1:
        raise ValueError("A quiz topic needs at least one question")
    order = list(range(question_count))
    (rng or random.SystemRandom()).shuffle(order)
    if len(order) > 1 and order[0] == previous_last:
        order[0], order[1] = order[1], order[0]
    return order


def current_round(
    state: MutableMapping[str, Any],
    topic_id: str,
    question_count: int,
    *,
    rng: random.Random | None = None,
) -> QuizRound:
    """Get a stable current round across Streamlit reruns and topic switches."""
    if not topic_id:
        raise ValueError("topic_id cannot be blank")
    if question_count < 1:
        raise ValueError("Quiz topic has no questions")

    orders = state.setdefault("quiz_orders", {})
    positions = state.setdefault("quiz_positions", {})
    cycles = state.setdefault("quiz_cycles", {})
    order = orders.get(topic_id)
    if not isinstance(order, list) or sorted(order) != list(range(question_count)):
        order = shuffled_order(question_count, rng=rng)
        orders[topic_id] = order
        positions[topic_id] = 0
        cycles[topic_id] = 1

    position = positions.get(topic_id, 0)
    if not isinstance(position, int) or not 0 <= position < question_count:
        position = 0
        positions[topic_id] = 0
    cycle = cycles.get(topic_id, 1)
    if not isinstance(cycle, int) or cycle < 1:
        cycle = 1
        cycles[topic_id] = 1
    question_index = order[position]
    return QuizRound(
        topic_id=topic_id,
        question_index=question_index,
        round_number=position + 1,
        total_rounds=question_count,
        set_number=cycle,
        key=f"{topic_id}:set{cycle}:round{position + 1}:question{question_index}",
    )


def advance_round(
    state: MutableMapping[str, Any],
    topic_id: str,
    question_count: int,
    *,
    rng: random.Random | None = None,
) -> QuizRound:
    """Advance exactly one round; reshuffle on wrap without repeating last question."""
    if question_count < 2:
        raise ValueError("Next round requires at least two different questions")
    before = current_round(state, topic_id, question_count, rng=rng)
    if before.round_number < question_count:
        state["quiz_positions"][topic_id] = before.round_number
    else:
        state["quiz_orders"][topic_id] = shuffled_order(
            question_count, previous_last=before.question_index, rng=rng
        )
        state["quiz_positions"][topic_id] = 0
        state["quiz_cycles"][topic_id] = before.set_number + 1
    after = current_round(state, topic_id, question_count, rng=rng)
    if after.question_index == before.question_index:
        raise AssertionError("Next round must select a different question")
    return after


def submit_answer(
    state: MutableMapping[str, Any],
    round_info: QuizRound,
    selected_option: int,
    correct_option: int,
    options: list[str],
    explanation: str,
) -> bool:
    """Record one attempt per round. Return True only for a new submission."""
    if not 0 <= selected_option < len(options):
        raise ValueError("A valid answer choice must be selected")
    if not 0 <= correct_option < len(options):
        raise ValueError("The question has an invalid answer index")
    feedback = state.setdefault("quiz_feedback_by_round", {})
    if round_info.key in feedback:
        return False
    correct = selected_option == correct_option
    feedback[round_info.key] = {
        "correct": correct,
        "explanation": explanation,
        "correct_option": options[correct_option],
    }
    state["quiz_attempts"] = state.get("quiz_attempts", 0) + 1
    state["quiz_correct"] = state.get("quiz_correct", 0) + int(correct)
    return True
