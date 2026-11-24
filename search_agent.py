
"""
Web Search and Data Retrieval Agent.
Retrieves startup-specific market intelligence
using Tavily and DDGS fallback.
"""

import os
import re
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional, Tuple
from urllib.parse import urlparse, urlunparse

from base_agent import BaseAgent
from models import StructuredIdea, WebSearchIntelligence, SearchResultItem
from llm_client import UnifiedLLMClient


class WebSearchAgent(BaseAgent):

    def __init__(
        self,
        tavily_api_key: Optional[str] = None,
        llm_client: Optional[UnifiedLLMClient] = None
    ):
        super().__init__(
            name="WebSearchAgent",
            role="Live Market Data & Competitor Intelligence Retrieval",
            llm_client=llm_client
        )

        self.tavily_api_key = (
            tavily_api_key or os.getenv("TAVILY_API_KEY")
        )

    # ---------------------------------------------------------
    # MAIN AGENT
    # ---------------------------------------------------------

    def run(self, idea: StructuredIdea) -> WebSearchIntelligence:

        self.log(f"Initiating market research for: {idea.title}")

        queries = self._generate_search_queries(idea)

        self.log(
            f"Generated {len(queries)} startup-specific queries."
        )

        raw_results: List[SearchResultItem] = []

        # Execute independent searches concurrently.
        with ThreadPoolExecutor(max_workers=4) as executor:
            search_batches = executor.map(
                self._execute_search_query,
                queries
            )

            for batch in search_batches:
                raw_results.extend(batch)

        self.log(
            f"Retrieved {len(raw_results)} raw search results."
        )

        unique_results = self._remove_duplicates(raw_results)

        relevant_results = self._filter_relevant_results(
            idea,
            unique_results
        )

        final_results = relevant_results[:8]

        self.log(
            f"Selected {len(final_results)} market research results."
        )

        summary, stats = self._synthesize_search_results(
            idea,
            final_results
        )

        return WebSearchIntelligence(
            queries_executed=queries,
            results=final_results,
            market_signals_summary=summary,
            real_world_stats=stats
        )

    # ---------------------------------------------------------
    # SEARCH QUERY GENERATION
    # ---------------------------------------------------------

    def _generate_search_queries(
        self,
        idea: StructuredIdea
    ) -> List[str]:

        industry = str(idea.industry_domain or "").strip()
        problem = str(idea.problem_statement or "").strip()
        solution = str(idea.solution_statement or "").strip()
        customers = str(idea.target_customer or "").strip()

        def shorten(value, limit=10):
            return " ".join(value.split()[:limit])

        queries = [
            f"{shorten(solution)} competitors and platforms India",
            f"{shorten(problem)} market demand research India",
            f"{shorten(solution)} companies offering similar solutions India",
            f"{shorten(customers)} needs and challenges {industry}",
            f"{industry} market trends and customer adoption India"
        ]

        cleaned = []
        seen = set()

        for query in queries:
            query = re.sub(r"\s+", " ", query).strip()

            if query and query.lower() not in seen:
                seen.add(query.lower())
                cleaned.append(query)

        return cleaned

    # ---------------------------------------------------------
    # SEARCH EXECUTION
    # ---------------------------------------------------------

    def _execute_search_query(
        self,
        query: str,
        max_results: int = 3
    ) -> List[SearchResultItem]:

        items: List[SearchResultItem] = []

        # Tavily search
        if self.tavily_api_key:
            try:
                from tavily import TavilyClient

                client = TavilyClient(
                    api_key=self.tavily_api_key
                )

                response = client.search(
                    query=query,
                    search_depth="basic",
                    max_results=max_results
                )

                for result in response.get("results", []):

                    url = result.get("url") or ""

                    snippet = (
                        result.get("content")
                        or result.get("snippet")
                        or ""
                    )

                    if not url or len(snippet.strip()) < 70:
                        continue

                    domain = (
                        urlparse(url).netloc.replace("www.", "")
                    )

                    items.append(
                        SearchResultItem(
                            title=result.get("title") or "Search Result",
                            url=url,
                            snippet=snippet,
                            query_used=query,
                            source_domain=domain
                        )
                    )

                if items:
                    self.log(
                        f"Tavily returned {len(items)} results."
                    )
                    return items

            except Exception as error:
                self.log(f"Tavily search failed: {error}")

        # DDGS fallback
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            with DDGS(timeout=5) as ddgs:

                results = list(
                    ddgs.text(
                        query,
                        max_results=max_results
                    )
                )

                for result in results:

                    url = (
                        result.get("href")
                        or result.get("link")
                        or result.get("url")
                        or ""
                    )

                    snippet = (
                        result.get("body")
                        or result.get("snippet")
                        or result.get("abstract")
                        or result.get("text")
                        or ""
                    )

                    if not url or len(snippet.strip()) < 70:
                        continue

                    domain = (
                        urlparse(url).netloc.replace("www.", "")
                    )

                    items.append(
                        SearchResultItem(
                            title=result.get("title") or "Search Result",
                            url=url,
                            snippet=snippet,
                            query_used=query,
                            source_domain=domain
                        )
                    )

                if items:
                    self.log(
                        f"DDGS returned {len(items)} results."
                    )

        except Exception as error:
            self.log(f"DDGS search failed: {error}")

        return items

    # ---------------------------------------------------------
    # DUPLICATE AND LOW-QUALITY RESULT REMOVAL
    # ---------------------------------------------------------

    def _remove_duplicates(
        self,
        results: List[SearchResultItem]
    ) -> List[SearchResultItem]:

        seen_urls = set()
        seen_titles = set()
        cleaned = []

        for result in results:

            url = str(result.url or "").strip()

            if not url:
                continue

            parsed = urlparse(url)

            clean_url = urlunparse((
                parsed.scheme,
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                "",
                "",
                ""
            )).lower()

            title_key = re.sub(
                r"[^a-z0-9]+",
                " ",
                str(result.title or "").lower()
            ).strip()

            if clean_url in seen_urls:
                continue

            if title_key and title_key in seen_titles:
                continue

            if self._is_low_quality_page(result):
                continue

            seen_urls.add(clean_url)

            if title_key:
                seen_titles.add(title_key)

            cleaned.append(result)

        return cleaned

    def _is_low_quality_page(
        self,
        result: SearchResultItem
    ) -> bool:

        url = str(result.url or "").lower()
        title = str(result.title or "").lower()
        snippet = str(result.snippet or "").lower()

        unwanted_patterns = [
            "alternatives-competitors",
            "/alternatives/",
            "alternatives and competitors",
            "compare-",
            "/comparison/",
            "top-10-alternatives",
            "best-alternatives",
            "competitors-and-alternatives"
        ]

        combined = url + " " + title

        if any(pattern in combined for pattern in unwanted_patterns):
            return True

        if len(snippet.strip()) < 70:
            return True

        return False

    # ---------------------------------------------------------
    # STARTUP-SPECIFIC RELEVANCE FILTER
    # ---------------------------------------------------------

    def _filter_relevant_results(
        self,
        idea: StructuredIdea,
        results: List[SearchResultItem]
    ) -> List[SearchResultItem]:

        if not results:
            return []

        industry = str(idea.industry_domain or "").lower()
        problem = str(idea.problem_statement or "")
        solution = str(idea.solution_statement or "")
        customers = str(idea.target_customer or "")
        title = str(idea.title or "")

        stop_words = {
            "the", "and", "for", "with", "from", "that", "this",
            "their", "they", "them", "your", "into", "using",
            "uses", "use", "are", "was", "were", "has", "have",
            "had", "can", "will", "would", "could", "should",
            "about", "which", "what", "when", "where", "while",
            "through", "also", "more", "most", "many", "some",
            "such", "than", "then", "been", "being", "other",
            "new", "based", "system", "platform", "solution",
            "solutions", "company", "companies", "business",
            "businesses", "india", "indian", "startup", "startups",
            "provides", "offers", "helps", "make"
        }

        def extract_words(value):

            words = re.findall(
                r"[a-zA-Z0-9]+",
                str(value).lower()
            )

            return {
                word for word in words
                if len(word) >= 3 and word not in stop_words
            }

        problem_words = extract_words(problem)
        solution_words = extract_words(solution)
        customer_words = extract_words(customers)
        title_words = extract_words(title)
        industry_words = extract_words(industry)

        industry_aliases = {
            "edtech": {
                "education", "educational", "learning", "students",
                "schools", "teaching", "tutoring", "academic",
                "personalized", "curriculum", "assessment"
            },
            "healthtech": {
                "healthcare", "health", "medical", "clinic",
                "clinics", "patients", "hospital", "hospitals"
            },
            "fintech": {
                "finance", "financial", "banking", "payments",
                "payment", "lending", "insurance"
            },
            "agritech": {
                "agriculture", "farming", "farmers", "crops",
                "farm", "agricultural"
            },
            "foodtech": {
                "food", "restaurant", "restaurants", "kitchen",
                "meals", "delivery", "cooking"
            },
            "ecommerce": {
                "retail", "shopping", "online", "marketplace",
                "commerce", "buyers", "sellers"
            }
        }

        alias_words = set()
        normalized_industry = industry.replace(" ", "")

        for key, aliases in industry_aliases.items():

            if key in normalized_industry:
                alias_words.update(aliases)

        ranked_results = []

        for result in results:

            title_text = str(result.title or "").lower()
            snippet_text = str(result.snippet or "").lower()

            result_words = extract_words(
                title_text + " " + snippet_text
            )

            solution_match = len(
                solution_words & result_words
            )

            problem_match = len(
                problem_words & result_words
            )

            customer_match = len(
                customer_words & result_words
            )

            industry_match = len(
                industry_words & result_words
            )

            alias_match = len(
                alias_words & result_words
            )

            title_match = len(
                title_words & result_words
            )

            score = (
                solution_match * 4
                + problem_match * 3
                + customer_match * 2
                + industry_match * 3
                + alias_match * 2
                + title_match
            )

            ranked_results.append((score, result))

        ranked_results.sort(
            key=lambda item: item[0],
            reverse=True
        )

        relevant = [
            result
            for score, result in ranked_results
            if score >= 3
        ]

        return relevant

    # ---------------------------------------------------------
    # MARKET INTELLIGENCE SYNTHESIS
    # ---------------------------------------------------------

    def _synthesize_search_results(
        self,
        idea: StructuredIdea,
        results: List[SearchResultItem]
    ) -> Tuple[str, List[str]]:

        if not results:

            return (
                "Relevant live market evidence could not be found "
                "for this startup idea. The available search results "
                "were insufficient. Please try again when web "
                "search is available.",
                []
            )

        snippets_text = "\n\n".join(
            [
                f"Title: {result.title}\n"
                f"Website: {result.source_domain}\n"
                f"URL: {result.url}\n"
                f"Information: {result.snippet[:350]}"
                for result in results[:6]
            ]
        )

        system_prompt = """
You are a professional market research analyst.

Analyze live web search evidence for the exact startup idea.

STRICT RULES:

1. Use only information supported by the supplied sources.
2. Never invent market size, growth rates, prices or statistics.
3. Do not treat search titles as verified facts.
4. Do not include unrelated companies as competitors.
5. A competitor must offer a product or service relevant
   to the proposed solution.
6. Distinguish direct competitors from indirect alternatives.
7. Do not repeat companies or market signals.
8. Ignore generic alternatives and comparison pages.
9. If evidence is weak, clearly state that.
10. Do not assume evidence applies to India unless
    the source supports that location.
11. Do not reuse information from another startup.

Write a concise professional market intelligence summary.

Return a JSON object:
{
    "summary": "Evidence-based market research summary"
}
"""

        user_prompt = f"""
CURRENT STARTUP IDEA

Title: {idea.title}
Problem: {idea.problem_statement}
Proposed solution: {idea.solution_statement}
Target customers: {idea.target_customer}
Industry: {idea.industry_domain}

LIVE SEARCH EVIDENCE

{snippets_text}

Explain:
- Relevant market demand
- Customer needs and problems
- Industry trends
- Relevant products and companies
- Business opportunities
- Limitations in available evidence

Only include claims supported by the supplied sources.
Do not include companies simply because they belong
to the same broad industry.
"""

        summary = ""

        try:

            data = self.execute_structured_prompt(
                system_prompt,
                user_prompt,
                temperature=0.1
            )

            if isinstance(data, dict):

                summary = (
                    data.get("summary")
                    or data.get("market_signals_summary")
                    or ""
                )

            elif isinstance(data, str):
                summary = data.strip()

            if isinstance(summary, str):
                summary = summary.strip()
            else:
                summary = ""

            if summary:
                self.log(
                    "Startup-specific market intelligence generated."
                )

        except Exception as error:

            self.log(
                f"Market summary generation failed: {error}"
            )

        if not summary:

            summary = (
                "Relevant web sources were retrieved, but the AI "
                "could not generate a reliable market summary. "
                "Please review the source links."
            )

        stats = self._extract_market_data_points(results)

        return summary, stats

    # ---------------------------------------------------------
    # MARKET DATA EXTRACTION
    # ---------------------------------------------------------

    def _extract_market_data_points(
        self,
        results: List[SearchResultItem]
    ) -> List[str]:

        stats = []

        meaningful_indicators = [
            "%", "million", "billion", "thousand",
            "crore", "lakh", "cagr", "revenue",
            "market size", "market value", "market growth",
            "growth rate", "users", "customers", "students",
            "schools", "hospitals", "clinics", "locations",
            "countries", "investment", "funding", "adoption",
            "₹", "$"
        ]

        for result in results:

            snippet = str(result.snippet or "").strip()
            title = str(result.title or "").strip()

            if not re.search(r"\d", snippet):
                continue

            lower_snippet = snippet.lower()

            has_market_context = any(
                indicator in lower_snippet
                for indicator in meaningful_indicators
            )

            if not has_market_context:
                continue

            sentences = re.split(r'(?<=[.!?])\s+', snippet)

            for sentence in sentences:
                sentence = sentence.strip()

                if (
                    len(sentence) >= 25
                    and len(sentence) <= 260
                    and re.search(r'\d', sentence)
                    and any(
                        indicator in sentence.lower()
                        for indicator in meaningful_indicators
                    )
                ):
                    stats.append(
                        f"{sentence} (Source: {title} - {result.url})"
                    )
                    break

            if len(stats) >= 4:
                break

        return stats
