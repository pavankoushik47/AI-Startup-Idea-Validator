"""Milestone 1 orchestration: idea form -> LLM extraction -> Tavily search."""
import os
from dotenv import load_dotenv

from idea_extractor import extract_idea
from tavily_search import search_startup_idea

load_dotenv()

REQUIRED_KEYS = ["problem_statement", "proposed_solution", "target_customers", "industry", "key_features"]


def validate_input(form: dict) -> list:
    """Return a list of error messages (empty list = valid)."""
    errors = []
    if len((form.get("description") or "").strip()) < 20:
        errors.append("Idea description is required (at least 20 characters).")
    if not (form.get("industry") or "").strip():
        errors.append("Industry is required.")
    if not (form.get("target_customers") or "").strip():
        errors.append("Target customers are required.")
    return errors


def build_idea_text(form: dict) -> str:
    parts = [
        f"Idea: {form['description'].strip()}",
        f"Industry: {form['industry'].strip()}",
        f"Target customers: {form['target_customers'].strip()}",
    ]
    if (form.get("details") or "").strip():
        parts.append(f"Additional details: {form['details'].strip()}")
    return "\n".join(parts)


def run_pipeline(form: dict, search_client=None) -> dict:
    """Run the Milestone 1 workflow. Never raises; errors are returned in the result."""
    result = {"status": "ok", "errors": [], "structured_idea": None, "search_results": None}

    errors = validate_input(form)
    if errors:
        result.update(status="invalid_input", errors=errors)
        return result

    # Step 1: structured extraction
    try:
        idea = extract_idea(build_idea_text(form))
        if not isinstance(idea, dict):
            raise ValueError("LLM did not return a JSON object.")
        missing = [k for k in REQUIRED_KEYS if k not in idea]
        if missing:
            raise ValueError(f"LLM response missing keys: {missing}")
        result["structured_idea"] = idea
    except Exception as e:
        result.update(status="extraction_failed", errors=[f"Idea extraction failed: {e}"])
        return result

    # Step 2: web search
    try:
        if search_client is None:
            key = os.getenv("TAVILY_API_KEY")
            if not key:
                raise ValueError("TAVILY_API_KEY is missing.")
            from tavily import TavilyClient
            search_client = TavilyClient(api_key=key)
        query_text = f"{idea['proposed_solution']} for {form['industry'].strip()}"
        result["search_results"] = search_startup_idea(query_text, search_client)
        if not any(result["search_results"].values()):
            result.update(status="partial", errors=["Search returned no results."])
    except Exception as e:
        result.update(status="search_failed", errors=[f"Web search failed: {e}"])
    return result
