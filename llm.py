import logging
import os

from google import genai
from google.genai import types

from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])


async def generate_phrasebook(user_text: str) -> str:
    """Generate a Serbian phrasebook for the given situation via Gemini API."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=user_text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=2048,
            ),
        )
        return response.text
    except Exception as exc:
        error_message = str(exc)
        if "429" in error_message or "RESOURCE_EXHAUSTED" in error_message:
            logger.warning("Rate limit hit: %s", error_message)
            return "⏳ Слишком много запросов – попробуй через минуту."
        logger.error("Gemini API error: %s", error_message)
        return "❌ Что-то пошло не так – попробуй ещё раз."
