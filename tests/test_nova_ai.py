from __future__ import annotations

import json
import sys
import unittest
from types import ModuleType, SimpleNamespace
from unittest.mock import patch

from src.nova_ai import NovaConfig, NovaService
from src.legal_engine import LegalLearningEngine


ESTATE_QUESTION = "How does handing down real estate from parents to children work?"
MODEL_PAYLOAD = {
    "topic_label": "Passing a home to children",
    "plain_language": "Parents may gift a house while alive, or leave it through a will or trust. The law and tax consequences depend on the location and the facts.",
    "key_points": [
        "A lifetime gift uses legal transfer paperwork, often a deed.",
        "After death, a will, trust, or other permitted arrangement may affect the process.",
        "Mortgage obligations and taxes need careful review.",
    ],
    "next_steps": [
        "Check the title and existing mortgage privately.",
        "Consult a local estate-planning lawyer and tax specialist before signing a deed.",
    ],
}


class SmartNovaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.local = NovaService()

    def test_original_real_estate_question_is_relevant_offline(self) -> None:
        result = self.local.answer(ESTATE_QUESTION)
        self.assertEqual(result["topic_id"], "estate_inheritance")
        self.assertEqual(result["source_mode"], "offline")
        self.assertIn("home", result["plain_language"].lower())
        self.assertIn("will", result["plain_language"].lower())
        self.assertNotIn("employment", result["plain_language"].lower())
        self.assertTrue(result["official_resources"])

    def test_lifetime_gift_and_inherited_house(self) -> None:
        for q in [
            "How can I inherit a house from my parents?",
            "What is probate for a house?",
            "What are the tax basis differences for a deed versus inheritance?",
        ]:
            with self.subTest(q=q):
                self.assertEqual(self.local.answer(q)["topic_id"], "estate_inheritance")

    def test_uncovered_question_does_not_get_unrelated_law(self) -> None:
        result = self.local.answer("How do quantum computers calculate qubit entanglement?")
        self.assertEqual(result["topic_id"], "uncovered_topic")
        self.assertIn("won't substitute an unrelated", result["plain_language"])

    def test_school_question_retains_existing_topic(self) -> None:
        result = self.local.answer("Can my school search my phone?")
        self.assertEqual(result["topic_id"], "school_rights")

    def test_creative_patent_topic_no_longer_is_work_law(self) -> None:
        result = self.local.answer("How do patents work for teen inventors?")
        self.assertEqual(result["topic_id"], "patents_inventions")
        self.assertIn("patent", result["plain_language"].lower())

    def test_tenant_question_gets_relevant_housing_info(self) -> None:
        result = self.local.answer("How does renting an apartment work under tenant law?")
        self.assertEqual(result["topic_id"], "housing_renters")
        self.assertIn("rental", result["plain_language"].lower())

    def test_generic_real_estate_agent_question_is_not_inheritance(self) -> None:
        result = self.local.answer("What are the rules about real estate agency licensing?")
        self.assertNotEqual(result["topic_id"], "estate_inheritance")

    def test_privacy_screen_prevents_model_request(self) -> None:
        service = NovaService(NovaConfig("openai", "gpt-5.4-mini", "never-a-real-key"))
        with patch.object(service, "_request_model") as request:
            result = service.answer("What if my address is 123 Elm Street and I inherit a house?")
        request.assert_not_called()
        self.assertEqual(result["topic_id"], "privacy_guard")

    def test_safety_preempts_live_model(self) -> None:
        service = NovaService(NovaConfig("gemini", "gemini-3.8-flash", "fake"))
        with patch.object(service, "_request_model") as request:
            result = service.answer("How do I hide evidence?")
        request.assert_not_called()
        self.assertEqual(result["safety_level"], "blocked")

    def test_live_llm_free_form_topic_and_location(self) -> None:
        service = NovaService(NovaConfig("openai", "gpt-5.4-mini", "fake"))
        with patch.object(service, "_request_model", return_value=MODEL_PAYLOAD) as request:
            result = service.answer(ESTATE_QUESTION, "Maryland", "Step by step", [{"role": "user", "text": "I want to learn about estates"}])
        request.assert_called_once()
        self.assertEqual(result["source_mode"], "llm")
        self.assertIn("will", result["plain_language"])
        self.assertIn("Maryland", result["jurisdiction_note"])
        self.assertEqual(result["topic_label"], "Passing a home to children")

    def test_provider_failure_returns_honest_offline_answer(self) -> None:
        service = NovaService(NovaConfig("openai", "gpt-5.4-mini", "fake"))
        with patch.object(service, "_request_model", side_effect=TimeoutError("SECRET private payload")):
            result = service.answer(ESTATE_QUESTION)
        self.assertEqual(result["source_mode"], "offline_after_error")
        self.assertIn("estate", result["topic_id"])
        self.assertNotIn("SECRET", result["model_notice"])
        self.assertIn("TimeoutError", result["model_notice"])

    def test_irrelevant_employment_llm_answer_is_not_shown_for_estate(self) -> None:
        bad = {
            "topic_label": "Teen workplace rules",
            "plain_language": "Employment laws control when workers may work and receive wages.",
            "key_points": ["Minimum wages and work hours can vary by age and jurisdiction."],
            "next_steps": ["Ask a labor office about employment rules."],
        }
        service = NovaService(NovaConfig("openai", "gpt-5.4-mini", "fake"))
        with patch.object(service, "_request_model", return_value=bad):
            result = service.answer(ESTATE_QUESTION)
        self.assertEqual(result["source_mode"], "offline_after_error")
        self.assertIn("house", result["plain_language"].lower() + " ".join(result["key_points"]).lower())

    def test_invalid_payload_does_not_create_fake_answer(self) -> None:
        service = NovaService(NovaConfig("openai", "gpt-5.4-mini", "fake"))
        with patch.object(service, "_request_model", return_value={"topic_label": "Employment"}):
            result = service.answer(ESTATE_QUESTION)
        self.assertEqual(result["source_mode"], "offline_after_error")
        self.assertEqual(result["topic_id"], "estate_inheritance")

    def test_configuration_switches_provider_without_exposing_key(self) -> None:
        c = NovaConfig.from_settings(
            secrets={"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "dummy", "OPENAI_MODEL": "gpt-5.4-mini"},
            environ={},
        )
        self.assertTrue(c.active)
        self.assertEqual(c.provider, "openai")
        self.assertEqual(c.model, "gpt-5.4-mini")
        self.assertNotIn("dummy", c.setup_note)
        g = NovaConfig.from_settings(secrets={"GEMINI_API_KEY": "fake"}, environ={})
        self.assertEqual(g.provider, "gemini")
        self.assertEqual(g.model, "gemini-3.8-flash")

    def test_openai_response_api_structured_output_parameters(self) -> None:
        service = NovaService(NovaConfig("openai", "gpt-5.4-mini", "fake"))
        fake_client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: SimpleNamespace(output_text=json.dumps(MODEL_PAYLOAD))))
        fake_module = ModuleType("openai")
        fake_module.OpenAI = lambda **kwargs: fake_client
        with patch.dict(sys.modules, {"openai": fake_module}):
            result = service.answer(ESTATE_QUESTION)
        self.assertEqual(result["source_mode"], "llm")

    def test_gemini_generate_content_structured_output_parameters(self) -> None:
        service = NovaService(NovaConfig("gemini", "gemini-3.8-flash", "fake"))
        called = {}
        def generate_content(**kwargs):
            called.update(kwargs)
            return SimpleNamespace(text=json.dumps(MODEL_PAYLOAD))
        fake_client = SimpleNamespace(models=SimpleNamespace(generate_content=generate_content))
        google_module = ModuleType("google")
        fake_genai = ModuleType("google.genai")
        fake_genai.Client = lambda **kwargs: fake_client
        fake_genai.types = SimpleNamespace(GenerateContentConfig=lambda **kwargs: kwargs)
        google_module.genai = fake_genai
        with patch.dict(sys.modules, {"google": google_module, "google.genai": fake_genai}):
            result = service.answer(ESTATE_QUESTION)
        self.assertEqual(result["source_mode"], "llm")
        self.assertEqual(called["model"], "gemini-3.8-flash")
        self.assertEqual(called["config"]["response_mime_type"], "application/json")

    def test_engine_original_safety_is_retained(self) -> None:
        engine = LegalLearningEngine()
        self.assertEqual(engine.answer("I am in danger right now").safety_level, "critical")


if __name__ == "__main__":
    unittest.main()
