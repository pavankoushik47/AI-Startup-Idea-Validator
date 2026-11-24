
"""
Conversational Startup Advisor Agent.
Provides interactive follow-up advice, business stress-testing, pitch drafting, and strategic guidance based on the validated report.
"""

from typing import List, Dict, Optional
from base_agent import BaseAgent
from models import FullValidationReport
from llm_client import UnifiedLLMClient


class ConversationalAdvisorAgent(BaseAgent):

    def __init__(self, llm_client: Optional[UnifiedLLMClient] = None):
        super().__init__(
            name="StartupAdvisorAgent",
            role="Interactive Founder Advisor & Strategy Consultant",
            llm_client=llm_client
        )

    def answer_query(
        self,
        user_question: str,
        report: FullValidationReport,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:

        self.log(f"Processing founder advisory query: '{user_question}'")

        system_prompt = (
            "You are a seasoned startup advisor speaking directly to the founder. "
            "You have full contextual knowledge of their validated startup idea, "
            "market sizing, competitors, SWOT, MVP roadmap, and GTM strategy. "

            "IMPORTANT INSTRUCTIONS: "
            "1. Answer the founder's latest question directly. "
            "2. Treat every question as a separate task and follow its exact instructions. "
            "3. Do not repeat generic recommendations from previous answers. "
            "4. Use the startup dossier to personalize every response. "
            "5. If asked to write an email, provide a complete ready-to-use email template. "
            "6. If asked for a customer acquisition strategy, provide a practical step-by-step plan. "
            "7. If asked for pricing advice, provide specific pricing approaches. "
            "8. If asked for a pitch deck, provide a suitable slide structure. "
            "9. If asked for examples, give relevant examples. "
            "10. Use bullet points, bold text, and numbered steps where appropriate. "
            "Avoid generic advice and corporate fluff."
        )

        history_context = ""

        if chat_history:
            for turn in chat_history[-4:]:
                history_context += (
                    f"{turn['role'].capitalize()}: "
                    f"{turn['content']}\n"
                )

        user_prompt = (
            f"=== VALIDATED STARTUP DOSSIER ===\n"
            f"Title: {report.structured_idea.title}\n"
            f"Tagline: {report.structured_idea.tagline}\n"
            f"Problem: {report.structured_idea.problem_statement}\n"
            f"Solution: {report.structured_idea.solution_statement}\n"
            f"Domain: {report.structured_idea.industry_domain}\n"
            f"Target Customer: {report.structured_idea.target_customer}\n"
            f"TAM: {report.market_opportunity.tam_estimate} | "
            f"CAGR: {report.market_opportunity.cagr_growth_rate}\n"
            f"Competitors: {', '.join([c.name for c in report.competitor_analysis.competitors])}\n"
            f"White Spaces: {', '.join(report.competitor_analysis.white_space_opportunities[:2])}\n"
            f"Viability Score: {report.composite_viability_score}/100 "
            f"({report.executive_verdict})\n"
            f"MVP Timeline: {report.mvp_recommendation.estimated_build_time_weeks} weeks\n"
            f"First 100 Tactic: "
            f"{report.gtm_strategy.first_100_customers_playbook[0] if report.gtm_strategy.first_100_customers_playbook else ''}\n"
            f"=================================\n\n"

            f"Recent Conversation:\n{history_context}\n"

            f"Founder's LATEST Question:\n{user_question}\n\n"

            f"Answer ONLY the latest question. "
            f"Do not copy or repeat a previous answer unless the founder asks you to.\n\n"

            f"Provide your specific, practical response now:"
        )

        try:
            response = self.llm.generate(
                system_prompt,
                user_prompt,
                temperature=0.7,
                max_tokens=1800
            )

            if not response or not response.strip():
                return (
                    "I couldn't generate a response right now. "
                    "Please try asking your question again."
                )

            return response.strip()

        except Exception as e:

            self.log(f"Advisor LLM error: {e}")

            return (
                f"I couldn't generate a response to your question right now.\n\n"
                f"Your question was: {user_question}\n\n"
                f"Please try again."
            )

    @staticmethod
    def get_starter_prompts() -> List[str]:

        return [
            "How do I acquire my first 10 paying customers with $0 budget?",
            "Write a high-converting cold email template for our primary customer persona.",
            "If the dominant incumbent copies our core feature, how do we defend our position?",
            "Can you outline an 8-slide investor pitch deck structure tailored to this idea?",
            "What should our landing page headline and call-to-action be?"
        ]
