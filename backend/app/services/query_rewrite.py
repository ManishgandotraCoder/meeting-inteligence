from app.llm.client import LLMClient
from app.llm.prompts import REWRITE_SYSTEM_PROMPT
from app.schemas.chat import ChatHistoryMessage
from app.services.question_router import is_followup


def heuristic_rewrite(question: str, history: list[ChatHistoryMessage]) -> str:
    previous_user = next(
        (item.content for item in reversed(history) if item.role == "user"),
        "",
    )
    if not previous_user:
        return question
    return f"In the context of this previous question: '{previous_user}', {question}"


class QueryRewriteService:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    async def rewrite(
        self,
        question: str,
        history: list[ChatHistoryMessage],
    ) -> str:
        recent = history[-6:]
        if not is_followup(question, len(recent)):
            return question

        history_text = "\n".join(f"{item.role}: {item.content}" for item in recent)
        try:
            result = await self.llm_client.rewrite(
                REWRITE_SYSTEM_PROMPT,
                f"CONVERSATION HISTORY\n{history_text}\n\nLATEST QUESTION\n{question}",
            )
            standalone = result.standalone_question.strip()
            return standalone or heuristic_rewrite(question, recent)
        except Exception:
            return heuristic_rewrite(question, recent)
