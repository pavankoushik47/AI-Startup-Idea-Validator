
"""
Unified LLM Client supporting Google Gemini, Groq, OpenAI,
and heuristic fallback.

Optimized with reusable API clients and execution-time logging.
"""

import os
import json
import re
import time
from typing import Dict, Any, Optional


# Load API keys from the project's .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


class UnifiedLLMClient:

    def __init__(
        self,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.provider = (
            provider or os.getenv("LLM_PROVIDER", "groq")
        ).lower()

        self.model = model
        self.api_key = api_key

        # Reusable API clients
        self.groq_client = None
        self.gemini_client = None
        self.openai_session = None

        self._init_client()

    def _init_client(self):

        if self.provider == "auto":
            self.provider = os.getenv(
                "LLM_PROVIDER", "groq"
            ).lower()

        # Default models
        if not self.model:
            if self.provider == "gemini":
                self.model = "gemini-3.8-flash"

            elif self.provider == "groq":
                self.model = "openai/gpt-oss-20b"

            elif self.provider == "openai":
                self.model = "gpt-4o-mini"

            else:
                self.model = "heuristic-v1"

        # Initialize Groq once
        if self.provider == "groq":

            from groq import Groq

            key = self.api_key or os.getenv("GROQ_API_KEY")

            if not key:
                raise ValueError(
                    "GROQ_API_KEY is missing from .env"
                )

            self.groq_client = Groq(
                api_key=key,
                timeout=30.0,
                max_retries=0
            )

        # Initialize Gemini once
        elif self.provider == "gemini":

            from google import genai

            key = (
                self.api_key
                or os.getenv("GEMINI_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
            )

            if not key:
                raise ValueError(
                    "No Gemini API key available"
                )

            self.gemini_client = genai.Client(
                api_key=key
            )

        # Initialize reusable OpenAI session
        elif self.provider == "openai":

            import requests

            key = self.api_key or os.getenv("OPENAI_API_KEY")

            if not key:
                raise ValueError(
                    "No OpenAI API key available"
                )

            self.openai_session = requests.Session()

            self.openai_session.headers.update({
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json"
            })

        print(
            f"[LLM Client] Selected provider: {self.provider}"
        )

        print(
            f"[LLM Client] Selected model: {self.model}"
        )

    # ---------------------------------------------------------
    # MAIN GENERATION METHOD
    # ---------------------------------------------------------

    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.4,
        max_tokens: int = 2500
    ) -> str:

        start_time = time.perf_counter()

        try:

            if self.provider == "gemini":

                result = self._call_gemini(
                    system_prompt,
                    user_prompt,
                    temperature,
                    max_tokens
                )

            elif self.provider == "groq":

                result = self._call_groq(
                    system_prompt,
                    user_prompt,
                    temperature,
                    max_tokens
                )

            elif self.provider == "openai":

                result = self._call_openai(
                    system_prompt,
                    user_prompt,
                    temperature,
                    max_tokens
                )

            else:

                result = self._call_heuristic(
                    system_prompt,
                    user_prompt
                )

            elapsed = time.perf_counter() - start_time

            print(
                f"[LLM Timing] {self.provider} generation "
                f"completed in {elapsed:.2f} seconds."
            )

            return result

        except Exception as error:

            elapsed = time.perf_counter() - start_time

            print(
                f"[LLM Client ERROR] {self.provider} failed "
                f"after {elapsed:.2f} seconds: {error}"
            )

            print(
                "[LLM Client] Switching to heuristic fallback."
            )

            return self._call_heuristic(
                system_prompt,
                user_prompt
            )

    # ---------------------------------------------------------
    # GEMINI
    # ---------------------------------------------------------

    def _call_gemini(
        self,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens
    ):

        from google.genai import types

        response = self.gemini_client.models.generate_content(
            model=self.model,
            contents=(
                f"System instructions:\n{system_prompt}\n\n"
                f"User request:\n{user_prompt}"
            ),
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
        )

        if not response.text:
            raise ValueError(
                "Gemini returned an empty response"
            )

        return response.text

    # ---------------------------------------------------------
    # GROQ
    # ---------------------------------------------------------

    def _call_groq(
        self,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens
    ):

        if self.groq_client is None:
            raise ValueError(
                "Groq client is not initialized"
            )

        response = self.groq_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            model=self.model,
            temperature=temperature,
            max_tokens=max_tokens
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError(
                "Groq returned an empty response"
            )

        return content

    # ---------------------------------------------------------
    # OPENAI
    # ---------------------------------------------------------

    def _call_openai(
        self,
        system_prompt,
        user_prompt,
        temperature,
        max_tokens
    ):

        if self.openai_session is None:
            raise ValueError(
                "OpenAI session is not initialized"
            )

        url = "https://api.openai.com/v1/chat/completions"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }

        response = self.openai_session.post(
            url,
            json=payload,
            timeout=30
        )

        response.raise_for_status()

        content = response.json()["choices"][0]["message"]["content"]

        if not content:
            raise ValueError(
                "OpenAI returned an empty response"
            )

        return content

    # ---------------------------------------------------------
    # HEURISTIC FALLBACK
    # ---------------------------------------------------------

    def _call_heuristic(
        self,
        system_prompt,
        user_prompt
    ):

        from heuristic_engine import generate_heuristic_response

        return generate_heuristic_response(
            system_prompt,
            user_prompt
        )

    # ---------------------------------------------------------
    # JSON EXTRACTION
    # ---------------------------------------------------------

    @staticmethod
    def extract_json(text: str) -> Dict[str, Any]:

        text = text.strip()

        if "```json" in text:

            text = (
                text.split("```json", 1)[1]
                .split("```", 1)[0]
                .strip()
            )

        elif "```" in text:

            text = (
                text.split("```", 1)[1]
                .split("```", 1)[0]
                .strip()
            )

        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1:

            json_str = text[start:end + 1]

            # Remove trailing commas before } or ]
            json_str = re.sub(
                r",\s*([}\]])",
                r"\1",
                json_str
            )

            try:
                return json.loads(json_str)

            except Exception:
                pass

        try:

            return json.loads(text)

        except Exception as error:

            return {
                "raw_text": text,
                "error": f"JSON parsing failed: {error}"
            }
