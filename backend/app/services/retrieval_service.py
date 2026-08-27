from app.core.config import settings
from app.repositories.chunk_repository import (
    ChunkRepository,
    RetrievedChunk,
    extract_terms,
    reciprocal_rank_fusion,
)
from app.services.embedding_service import EmbeddingService


def rerank_chunks(query: str, chunks: list[RetrievedChunk], limit: int) -> list[RetrievedChunk]:
    terms = extract_terms(query)
    scored: list[tuple[float, RetrievedChunk]] = []
    for chunk in chunks:
        haystack = chunk.content.lower()
        lexical = sum(1 for term in terms if term in haystack) / max(1, len(terms))
        combined = (0.65 * chunk.score) + (0.35 * lexical)
        scored.append((combined, chunk))

    scored.sort(key=lambda item: item[0], reverse=True)
    ranked: list[RetrievedChunk] = []
    for combined, chunk in scored[:limit]:
        chunk.score = round(combined, 4)
        ranked.append(chunk)
    return ranked


class RetrievalService:
    def __init__(
        self,
        chunk_repository: ChunkRepository,
        embedding_service: EmbeddingService,
    ):
        self.chunk_repository = chunk_repository
        self.embedding_service = embedding_service

    async def retrieve(self, meeting_id: str, query: str) -> list[RetrievedChunk]:
        query_embedding = await self.embedding_service.embed_text(query)
        vector_hits = await self.chunk_repository.search_similar(
            meeting_id=meeting_id,
            query_embedding=query_embedding,
            limit=settings.rag_candidate_k,
        )
        keyword_hits = await self.chunk_repository.search_keyword(
            meeting_id=meeting_id,
            query=query,
            limit=settings.rag_candidate_k,
        )

        by_id: dict[str, RetrievedChunk] = {chunk.id: chunk for chunk in keyword_hits}
        for chunk in vector_hits:
            existing = by_id.get(chunk.id)
            if existing is None:
                by_id[chunk.id] = chunk
            else:
                existing.vector_score = max(existing.vector_score, chunk.vector_score)
                existing.retrieval_method = "hybrid"

        rrf = reciprocal_rank_fusion(
            [
                [chunk.id for chunk in vector_hits],
                [chunk.id for chunk in keyword_hits],
            ]
        )
        fused = list(by_id.values())
        for chunk in fused:
            chunk.score = rrf.get(chunk.id, chunk.score)
            if chunk.vector_score and chunk.retrieval_method == "keyword":
                chunk.retrieval_method = "hybrid"

        return rerank_chunks(query, fused, settings.rag_top_k)
