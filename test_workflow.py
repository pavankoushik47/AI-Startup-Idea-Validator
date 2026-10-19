"""Run: python test_workflow.py   (live tests need GEMINI_API_KEY and TAVILY_API_KEY in .env)"""
import json
import unittest
from unittest.mock import patch, MagicMock
from orchestrator import run_pipeline

SAMPLE_IDEAS = [
    {"description": "An app that gives rural students affordable AI tutoring in regional languages over WhatsApp.",
     "industry": "EdTech", "target_customers": "Rural school students and parents", "details": ""},
    {"description": "A subscription service that delivers personalised diabetic-friendly meal kits to urban households.",
     "industry": "HealthTech", "target_customers": "Urban adults managing diabetes", "details": ""},
    {"description": "A marketplace connecting small farmers directly with restaurants to cut middlemen and waste.",
     "industry": "AgriTech", "target_customers": "Small farmers and local restaurants", "details": ""},
]

FAKE_IDEA = {"problem_statement": "p", "proposed_solution": "s", "target_customers": "t",
             "industry": "i", "key_features": ["f"]}


class OfflineTests(unittest.TestCase):
    def test_missing_inputs(self):
        r = run_pipeline({"description": "", "industry": "", "target_customers": ""})
        self.assertEqual(r["status"], "invalid_input")
        self.assertEqual(len(r["errors"]), 3)

    @patch("orchestrator.extract_idea", side_effect=ValueError("The AI returned invalid JSON."))
    def test_llm_failure(self, _):
        r = run_pipeline(SAMPLE_IDEAS[0])
        self.assertEqual(r["status"], "extraction_failed")

    @patch("orchestrator.extract_idea", return_value={"industry": "x"})
    def test_missing_keys_in_llm_json(self, _):
        self.assertEqual(run_pipeline(SAMPLE_IDEAS[0])["status"], "extraction_failed")

    @patch("orchestrator.extract_idea", return_value=FAKE_IDEA)
    def test_search_failure(self, _):
        client = MagicMock()
        client.search.side_effect = RuntimeError("API down")
        r = run_pipeline(SAMPLE_IDEAS[0], search_client=client)
        self.assertIn(r["status"], ("partial", "search_failed"))
        self.assertIsNotNone(r["structured_idea"])

    @patch("orchestrator.extract_idea", return_value=FAKE_IDEA)
    def test_happy_path(self, _):
        client = MagicMock()
        client.search.return_value = {"results": [{"title": "T", "url": "http://x", "content": "c"}]}
        r = run_pipeline(SAMPLE_IDEAS[0], search_client=client)
        self.assertEqual(r["status"], "ok")


def live_run():
    out = []
    for form in SAMPLE_IDEAS:
        r = run_pipeline(form)
        print(f"\n[{form['industry']}] status={r['status']} errors={r['errors']}")
        out.append({"input": form, "output": r})
    with open("test_results.json", "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)
    print("\nSaved test_results.json")


if __name__ == "__main__":
    unittest.main(exit=False, verbosity=2)
    live_run()
