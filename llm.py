import asyncio
import logging
import os
import time
from collections import deque
from typing import Optional, Tuple

from google import genai
from google.genai import errors, types

from prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

MODEL_NAME = "gemini-2.5-flash"
MAX_OUTPUT_TOKENS = 768
REQUEST_TIMEOUT_SECONDS = 25
MAX_RETRIES = 3
LOCAL_RPM_LIMIT = int(os.getenv("GEMINI_LOCAL_RPM_LIMIT", "4"))
RPM_WINDOW_SECONDS = 60

RATE_LIMIT_MESSAGE = "⏳ Слишком много запросов – попробуй через минуту."
TEMPORARY_ERROR_MESSAGE = "⚠️ Временный сбой сервиса – попробуй ещё раз через минуту."
GENERIC_ERROR_MESSAGE = "❌ Что-то пошло не так – попробуй ещё раз."

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
_request_times: deque[float] = deque()
_rate_limit_lock = asyncio.Lock()


def _build_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        max_output_tokens=MAX_OUTPUT_TOKENS,
        thinking_config=types.ThinkingConfig(thinking_budget=0),
        http_options=types.HttpOptions(timeout=REQUEST_TIMEOUT_SECONDS * 1000),
    )


def _extract_status_code(exc: Exception) -> Optional[int]:
    for attr in ("status", "code"):
        value = getattr(exc, attr, None)
        if isinstance(value, int):
            return value

    message = str(exc)
    if "429" in message:
        return 429
    if "503" in message:
        return 503
    if "500" in message:
        return 500
    return None


def _classify_error(exc: Exception) -> Tuple[str, bool]:
    status_code = _extract_status_code(exc)
    error_message = str(exc)

    if status_code == 429 or "RESOURCE_EXHAUSTED" in error_message:
        return RATE_LIMIT_MESSAGE, False

    if status_code in {500, 502, 503, 504}:
        return TEMPORARY_ERROR_MESSAGE, True

    if isinstance(exc, (errors.ServerError, asyncio.TimeoutError, TimeoutError)):
        return TEMPORARY_ERROR_MESSAGE, True

    return GENERIC_ERROR_MESSAGE, False


async def _wait_for_local_rate_limit() -> None:
    while True:
        wait_seconds = 0.0

        async with _rate_limit_lock:
            now = time.monotonic()

            while _request_times and now - _request_times[0] >= RPM_WINDOW_SECONDS:
                _request_times.popleft()

            if len(_request_times) < LOCAL_RPM_LIMIT:
                _request_times.append(now)
                return

            wait_seconds = RPM_WINDOW_SECONDS - (now - _request_times[0]) + 0.5

        logger.info(
            "Local Gemini RPM guard engaged: limit=%s waiting_for=%.2fs",
            LOCAL_RPM_LIMIT,
            wait_seconds,
        )
        await asyncio.sleep(max(wait_seconds, 0.5))


async def _request_phrasebook(user_text: str) -> str:
    await _wait_for_local_rate_limit()
    response = await client.aio.models.generate_content(
        model=MODEL_NAME,
        contents=user_text,
        config=_build_config(),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response")

    return response.text


async def generate_phrasebook(user_text: str) -> str:
    """Generate a Serbian phrasebook for the given situation via Gemini API."""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return await _request_phrasebook(user_text)
        except Exception as exc:
            user_message, should_retry = _classify_error(exc)
            status_code = _extract_status_code(exc)

            logger.exception(
                "Gemini API error on attempt %s/%s: type=%s status=%s",
                attempt,
                MAX_RETRIES,
                type(exc).__name__,
                status_code,
            )

            if should_retry and attempt < MAX_RETRIES:
                await asyncio.sleep(attempt)
                continue

            return user_message

    return TEMPORARY_ERROR_MESSAGE
