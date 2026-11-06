"""Smoke-test the real Streamlit Minigames function without a browser/server.

The test extracts the UI function from its source and supplies lightweight fake
widgets. This verifies the Check answer -> Next round -> new question flow even
in environments where the Streamlit package cannot be installed.
"""
from __future__ import annotations

import ast
import html
import unittest
from pathlib import Path
from typing import Any

from src.legal_engine import get_quiz, load_topics
from src.quiz_engine import advance_round, current_round, submit_answer


class SessionState(dict):
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError as exc:
            raise AttributeError(key) from exc

    def __setattr__(self, key, value):
        self[key] = value


class RerunRequested(Exception):
    pass


class FakeColumn:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


class FakeStreamlit:
    def __init__(self):
        self.session_state = SessionState(
            quiz_attempts=0,
            quiz_correct=0,
            quiz_feedback_by_round={},
            question_history=[],
            topics_opened=[],
            topic_counts={},
        )
        self.clicked = None
        self.radio_index = 1
        self.radio_calls = []
        self.buttons = []
        self.markdowns = []
        self.alerts = []
        self.topic = "Getting Help"

    def columns(self, *args, **kwargs):
        count = args[0] if isinstance(args[0], int) else len(args[0])
        return [FakeColumn() for _ in range(count)]

    def selectbox(self, label, options, **kwargs):
        assert self.topic in options
        return self.topic

    def markdown(self, body, **kwargs):
        self.markdowns.append(body)

    def radio(self, label, options, **kwargs):
        self.radio_calls.append(kwargs)
        return None if kwargs.get("disabled") else self.radio_index

    def button(self, label, **kwargs):
        self.buttons.append((label, kwargs))
        return label == self.clicked and not kwargs.get("disabled", False)

    def success(self, message):
        self.alerts.append(("success", message))

    def error(self, message):
        self.alerts.append(("error", message))

    def info(self, message):
        self.alerts.append(("info", message))

    def caption(self, message):
        pass

    def progress(self, value):
        pass

    def rerun(self):
        raise RerunRequested()

    def reset_run(self, clicked=None):
        self.clicked = clicked
        self.radio_calls.clear()
        self.buttons.clear()
        self.markdowns.clear()
        self.alerts.clear()


def load_ui_function(st):
    source = Path(__file__).resolve().parents[1] / "streamlit_app.py"
    module = ast.parse(source.read_text(encoding="utf-8"))
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == "render_minigames")
    isolated = ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[]))
    namespace = {
        "Any": Any,
        "st": st,
        "get_quiz": get_quiz,
        "current_round": current_round,
        "advance_round": advance_round,
        "submit_answer": submit_answer,
        "section_intro": lambda *a, **kw: None,
        "feature_card": lambda *a, **kw: None,
        "render_footer": lambda *a, **kw: None,
        "record_topic": lambda *a, **kw: None,
        "esc": html.escape,
    }
    exec(compile(isolated, str(source), "exec"), namespace)
    return namespace["render_minigames"]


class MinigamesUIFlowTests(unittest.TestCase):
    def test_check_answer_then_next_round_displays_new_question_and_clears_answer(self):
        st = FakeStreamlit()
        render = load_ui_function(st)
        topics = load_topics()
        first = current_round(st.session_state, "general_rights", 8)
        first_question = get_quiz("general_rights")[first.question_index]["question"]

        st.reset_run(clicked="Check answer")
        with self.assertRaises(RerunRequested):
            render(topics)
        self.assertEqual(st.session_state.quiz_attempts, 1)
        self.assertEqual(len(st.session_state.quiz_feedback_by_round), 1)

        st.reset_run(clicked="Next round")
        with self.assertRaises(RerunRequested):
            render(topics)
        second = current_round(st.session_state, "general_rights", 8)
        self.assertNotEqual(first.question_index, second.question_index)
        self.assertEqual(second.round_number, 2)

        st.reset_run()
        st.radio_index = None
        render(topics)
        self.assertTrue(any("Round 2 of 8" in part for part in st.markdowns))
        self.assertTrue(any(get_quiz("general_rights")[second.question_index]["question"] in part for part in st.markdowns))
        self.assertFalse(any(first_question in part for part in st.markdowns))
        self.assertEqual(st.radio_calls[-1]["index"], None)
        self.assertFalse(st.radio_calls[-1]["disabled"])
        self.assertEqual(st.session_state.quiz_attempts, 1)
        self.assertEqual(st.alerts, [])  # Old feedback does not leak to the new round.
        check = next(kw for label, kw in st.buttons if label == "Check answer")
        self.assertTrue(check["disabled"])  # User must choose an answer again.


if __name__ == "__main__":
    unittest.main()
