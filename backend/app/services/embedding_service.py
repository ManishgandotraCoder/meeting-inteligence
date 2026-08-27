from app.core.config import settings
from app.core.exceptions import AIProviderError
from app.llm.client import create_ollama_client


class EmbeddingService:
    def __init__(self):
        self.client = create_ollama_client()

    async def embed_text(self, text: str) -> list[float]:
        vectors = await self.embed_many([text])
        return vectors[0]

    async def embed_many(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        try:
            response = await self.client.embeddings.create(
                model=settings.embedding_model,
                input=texts,
            )
        except Exception as exc:
            raise AIProviderError(str(exc)) from exc

        return [item.embedding for item in response.data]
