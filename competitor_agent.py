
"""
Competitor Discovery and Comparison Agent.
Analyzes competitors dynamically for different startup industries.
"""

from typing import Optional, List

from base_agent import BaseAgent
from models import (
    StructuredIdea,
    WebSearchIntelligence,
    MarketOpportunity,
    CompetitorAnalysis,
    Competitor
)
from llm_client import UnifiedLLMClient


class CompetitorAnalysisAgent(BaseAgent):

    def __init__(
        self,
        llm_client: Optional[UnifiedLLMClient] = None
    ):
        super().__init__(
            name="CompetitorAnalysisAgent",
            role="Competitor Discovery & Gap Analysis",
            llm_client=llm_client
        )

    @staticmethod
    def _to_bool(value):
        """Convert verified feature values into booleans.
        Unknown or unverified values are omitted.
        """
        if isinstance(value, bool):
            return value

        if isinstance(value, (int, float)):
            return bool(value)

        if isinstance(value, str):
            value = value.strip().lower()

            if value in ("true", "yes", "available", "supported", "1"):
                return True

            if value in ("false", "no", "unavailable", "not supported", "0"):
                return False

        return None

    @classmethod
    def _clean_feature_matrix(cls, matrix):
        """Keep only valid boolean feature comparisons."""

        if not isinstance(matrix, dict):
            return {}

        cleaned = {}

        for feature, competitor_values in matrix.items():

            if not isinstance(competitor_values, dict):
                continue

            cleaned_values = {}

            for competitor_name, value in competitor_values.items():

                boolean_value = cls._to_bool(value)

                # Do not treat unverified information as False.
                if boolean_value is not None:
                    cleaned_values[str(competitor_name)] = boolean_value

            if cleaned_values:
                cleaned[str(feature)] = cleaned_values

        return cleaned

    def run(
        self,
        idea: StructuredIdea,
        search_data: WebSearchIntelligence,
        market: MarketOpportunity
    ) -> CompetitorAnalysis:

        self.log(f"Analyzing competitors for: {idea.title}")

        search_results = search_data.results or []

        search_context = "\n\n".join(
            [
                f"Title: {r.title}\n"
                f"Domain: {r.source_domain}\n"
                f"URL: {r.url}\n"
                f"Information: {r.snippet[:400]}"
                for r in search_results[:12]
            ]
        )

        if not search_context.strip():
            search_context = "No live search results were provided."

        market_summary = (
            search_data.market_signals_summary or ""
        )[:1000]

        system_prompt = """
You are a professional startup competitor research analyst.

Analyze only the startup idea provided.

Rules:
1. Identify real commercial products and companies.
2. Focus on competitors solving the same or closely related problem.
3. Distinguish Direct, Indirect and Substitute competitors.
4. Use the supplied search evidence.
5. Never invent prices, market shares or statistics.
6. If a fact is not verified, say Not publicly verified.
7. Do not return unrelated companies.
8. Do not return an empty list if relevant competitors
   are clearly identified in the evidence.
9. Provide useful market gaps specific to the startup.
10. Do not use information from another startup.

IMPORTANT FEATURE MATRIX RULE:
Every feature matrix value MUST be true or false.
If a competitor's feature cannot be verified, omit that
competitor's value for that feature.
Never write "Not publicly verified" inside the feature matrix.

Return valid JSON only:

{
    "market_saturation_level": "Low, Moderate, High, or Unknown",
    "competitors": [
        {
            "name": "Company or product name",
            "competitor_type": "Direct, Indirect, or Substitute",
            "description": "Relevant product description",
            "strengths": ["Strength"],
            "weaknesses": ["Weakness or Not publicly verified"],
            "pricing_model": "Verified price or Not publicly verified",
            "estimated_market_position": "Unknown unless verified"
        }
    ],
    "feature_matrix": {
        "Personalized Recommendations": {
            "Competitor Name": true
        }
    },
    "white_space_opportunities": ["Specific market gap"],
    "defensibility_moat": "Potential competitive advantage"
}
"""

        user_prompt = f"""
STARTUP:
{idea.title}

PROBLEM:
{idea.problem_statement}

SOLUTION:
{idea.solution_statement}

TARGET CUSTOMERS:
{idea.target_customer}

INDUSTRY:
{idea.industry_domain}

VALUE PROPOSITION:
{idea.core_value_prop}

MARKET RESEARCH:
{market_summary}

SEARCH RESULTS:
{search_context}

Find relevant competitors for this exact startup.

Include real companies supported by the evidence.
Explain their relevant offerings and limitations.
Identify opportunities that this startup could explore.

Return JSON only.
"""

        data = {}

        try:
            data = self.execute_structured_prompt(
                system_prompt,
                user_prompt,
                temperature=0.1
            )

            if not isinstance(data, dict):
                data = {}

        except Exception as error:
            self.log(f"LLM competitor analysis failed: {error}")

        # Create competitor objects.
        competitors: List[Competitor] = []

        raw_competitors = data.get("competitors", [])

        if isinstance(raw_competitors, list):

            for item in raw_competitors[:8]:

                if not isinstance(item, dict):
                    continue

                name = str(item.get("name", "")).strip()

                if not name:
                    continue

                competitor_type = str(
                    item.get("competitor_type", "Indirect")
                ).strip().title()

                if competitor_type not in [
                    "Direct", "Indirect", "Substitute"
                ]:
                    competitor_type = "Indirect"

                strengths = item.get("strengths", [])
                weaknesses = item.get("weaknesses", [])

                if not isinstance(strengths, list):
                    strengths = []

                if not isinstance(weaknesses, list):
                    weaknesses = []

                try:
                    competitors.append(
                        Competitor(
                            name=name,
                            competitor_type=competitor_type,
                            description=str(
                                item.get(
                                    "description",
                                    "Relevant product offering requires further verification."
                                )
                            ),
                            strengths=[
                                str(x) for x in strengths
                            ] or ["Not publicly verified"],
                            weaknesses=[
                                str(x) for x in weaknesses
                            ] or ["Not publicly verified"],
                            pricing_model=str(
                                item.get(
                                    "pricing_model",
                                    "Not publicly verified"
                                )
                            ),
                            estimated_market_position=str(
                                item.get(
                                    "estimated_market_position",
                                    "Unknown"
                                )
                            )
                        )
                    )

                except Exception as error:
                    self.log(
                        f"Could not process competitor {name}: {error}"
                    )

        # Remove duplicate names.
        unique_competitors = []
        seen = set()

        for competitor in competitors:

            key = competitor.name.lower()

            if key not in seen:
                seen.add(key)
                unique_competitors.append(competitor)

        competitors = unique_competitors

        # Market saturation.
        saturation = str(
            data.get("market_saturation_level", "Unknown")
        ).strip().title()

        if saturation not in [
            "Low", "Moderate", "High", "Unknown"
        ]:
            saturation = "Unknown"

        if not competitors:
            saturation = "Unknown"

        # Clean feature matrix to ensure all values are booleans.
        feature_matrix = self._clean_feature_matrix(
            data.get("feature_matrix", {})
        )

        # White-space opportunities.
        white_space = data.get(
            "white_space_opportunities", []
        )

        if not isinstance(white_space, list):
            white_space = []

        white_space = [
            str(item).strip()
            for item in white_space
            if str(item).strip()
        ]

        if not white_space:
            white_space = [
                (
                    "Validate whether existing solutions adequately "
                    f"address the problem: {idea.problem_statement}"
                ),
                (
                    "Explore how the proposed solution can offer "
                    f"distinct value to {idea.target_customer}."
                ),
                (
                    "Test customer demand and willingness to pay "
                    "through interviews and a pilot program."
                )
            ]

        # Defensibility.
        defensibility = data.get("defensibility_moat", "")

        if not isinstance(defensibility, str) or not defensibility.strip():
            defensibility = (
                "The startup could build a competitive advantage "
                "through differentiated features, customer trust, "
                "continuous product improvement and strong customer "
                "relationships. These advantages require validation."
            )

        self.log(
            f"Competitor analysis completed. "
            f"Competitors found: {len(competitors)}"
        )

        return CompetitorAnalysis(
            competitors=competitors,
            market_saturation_level=saturation,
            feature_matrix=feature_matrix,
            white_space_opportunities=white_space,
            defensibility_moat=defensibility
        )
