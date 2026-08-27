import re
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chunk import DocumentChunk

STOPWORDS = {
    "a",
    "an",
    "the",
    "is",
    "was",
    "were",
    "are",
    "what",
    "who",
    "when",
    "where",
    "why",
    "how",
    "did",
    "does",
    "do",
    "of",
    "in",
    "to",
    "for",
    "and",
    "or",
    "on",
    "at",
    "by",
    "with",
    "from",
    "about",
    "this",
    "that",
    "these",
    "those",
}


@dataclass(slots=True)
class ChunkCreate:
    content: str
    embedding: list[float]
    start_time: str | None
    end_time: str | None
    speakers: list[str]
    segment_ids: list[str]


@dataclass(slots=True)
class RetrievedChunk:
    id: str
    content: str
    start_time: str | None
    end_time: str | None
    speakers: list[str]
    segment_ids: list[str]
    score: float
    vector_score: float = 0.0
    retrieval_method: str = "vector"


def extract_terms(query: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z0-9_-]{2,}", query.lower())
    return [token for token in tokens if token not in STOPWORDS][:8]


def reciprocal_rank_fusion(ranked_id_lists: list[list[str]], k: int = 60) -> dict[str, float]:
    scores: dict[str, float] = {}
    for ranked in ranked_id_lists:
        for rank, chunk_id in enumerate(ranked, start=1):
            scores[chunk_id] = scores.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return scores


class ChunkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def bulk_create(
        self,
        meeting_id: str,
        chunks: list[ChunkCreate],
    ) -> list[DocumentChunk]:
        rows = [
            DocumentChunk(
                id=str(uuid4()),
                meeting_id=meeting_id,
                content=item.content,
                embedding=item.embedding,
                start_time=item.start_time,
                end_time=item.end_time,
                speakers=item.speakers,
                segment_ids=item.segment_ids,
            )
            for item in chunks
        ]
        self.db.add_all(rows)
        await self.db.flush()
        return rows

    def _to_retrieved(
        self,
        chunk: DocumentChunk,
        score: float,
        vector_score: float,
        method: str,
    ) -> RetrievedChunk:
        return RetrievedChunk(
            id=chunk.id,
            content=chunk.content,
            start_time=chunk.start_time,
            end_time=chunk.end_time,
            speakers=list(chunk.speakers or []),
            segment_ids=list(chunk.segment_ids or []),
            score=score,
            vector_score=vector_score,
            retrieval_method=method,
        )

    async def search_similar(
        self,
        meeting_id: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[RetrievedChunk]:
        distance = DocumentChunk.embedding.cosine_distance(query_embedding)
        stmt = (
            select(DocumentChunk, distance.label("distance"))
            .where(DocumentChunk.meeting_id == meeting_id)
            .order_by(distance)
            .limit(limit)
        )
        result = await self.db.execute(stmt)

        return [
            self._to_retrieved(
                chunk,
                score=max(0.0, 1.0 - float(distance_value)),
                vector_score=max(0.0, 1.0 - float(distance_value)),
                method="vector",
            )
            for chunk, distance_value in result.all()
        ]

    async def search_keyword(
        self,
        meeting_id: str,
        query: str,
        limit: int,
    ) -> list[RetrievedChunk]:
        terms = extract_terms(query)
        if not terms:
            return []

        tsv = func.to_tsvector("english", DocumentChunk.content)
        tsquery = func.plainto_tsquery("english", " ".join(terms))
        rank = func.ts_rank_cd(tsv, tsquery)

        stmt = (
            select(DocumentChunk, rank.label("rank"))
            .where(DocumentChunk.meeting_id == meeting_id)
            .where(tsv.op("@@")(tsquery))
            .order_by(rank.desc())
            .limit(limit)
        )
        rows = (await self.db.execute(stmt)).all()
        if rows:
            return [
                self._to_retrieved(
                    chunk,
                    score=float(rank_value or 0.0),
                    vector_score=0.0,
                    method="keyword",
                )
                for chunk, rank_value in rows
            ]

        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.meeting_id == meeting_id)
            .where(or_(*[DocumentChunk.content.ilike(f"%{term}%") for term in terms]))
            .limit(limit)
        )
        chunks = list((await self.db.execute(stmt)).scalars())
        return [
            self._to_retrieved(chunk, score=0.4, vector_score=0.0, method="keyword")
            for chunk in chunks
        ]
