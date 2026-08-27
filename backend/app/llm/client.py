import json
import re
import time
from typing import TypeVar

from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ValidationError

from app.core.config import settings
from app.core.context import request_id_ctx
from app.core.exceptions import AIProviderError
from app.core.logging import logger
from app.core.tokens import estimate_tokens
from app.llm.prompts import PROMPT_VERSION
from app.schemas.insights import MeetingAnalysisOutput, RagAnswerOutput

T = TypeVar("T", bound=BaseModel)


class RewriteOutput(BaseModel):
    standalone_question: str = Field(min_length=1)


def create_ollama_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        base_url=settings.ollama_base_url,
        api_key="ollama",
        timeout=180.0,
    )


def parse_model_json(content: str, schema: type[T]) -> T:  # noqa: UP047
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return schema.model_validate_json(text)
    except ValidationError:
        return schema.model_validate(json.loads(text))


class LLMClient:
    def __init__(self):
        self.client = create_ollama_client()

    async def answer(self, system_prompt: str, user_prompt: str) -> RagAnswerOutput:
        return await self._parse(system_prompt, user_prompt, RagAnswerOutput)

    async def analyze(self, system_prompt: str, user_prompt: str) -> MeetingAnalysisOutput:
        return await self._parse(system_prompt, user_prompt, MeetingAnalysisOutput)

    async def rewrite(self, system_prompt: str, user_prompt: str) -> RewriteOutput:
        return await self._parse(system_prompt, user_prompt, RewriteOutput)

    async def _parse(self, system_prompt: str, user_prompt: str, schema: type[T]) -> T:
        json_schema = schema.model_json_schema()
        started = time.perf_counter()

        try:
            response = await self.client.chat.completions.create(
                model=settings.chat_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"{system_prompt}\n\n"
                            "Respond with JSON only. Match this schema:\n"
                            f"{json.dumps(json_schema)}"
                        ),
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": json_schema,
                    },
                },
                temperature=0,
            )
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc

        content = response.choices[0].message.content
        if not content:
            raise AIProviderError("Ollama returned an empty response")

        usage = response.usage
        logger.info(
            "llm_completion",
            request_id=request_id_ctx.get(),
            chat_model=settings.chat_model,
            prompt_version=PROMPT_VERSION,
            schema=schema.__name__,
            prompt_tokens=getattr(usage, "prompt_tokens", None),
            completion_tokens=getattr(usage, "completion_tokens", None),
            estimated_input_tokens=estimate_tokens(system_prompt + user_prompt),
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

        try:
            return parse_model_json(content, schema)
        except Exception as exc:
            raise AIProviderError(f"Could not parse model JSON: {exc}") from exc
