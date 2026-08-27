from inspect import getsource

from app.repositories.chunk_repository import (
    ChunkRepository,
    RetrievedChunk,
    reciprocal_rank_fusion,
)
from app.services.guardrails import filter_cited_chunks


def test_retrieval_design_scopes_by_meeting():
    vector_source = getsource(ChunkRepository.search_similar)
    keyword_source = getsource(ChunkRepository.search_keyword)
    assert "DocumentChunk.meeting_id == meeting_id" in vector_source
    assert "DocumentChunk.meeting_id == meeting_id" in keyword_source


def test_reciprocal_rank_fusion_prefers_shared_hits():
    scores = reciprocal_rank_fusion(
        [
            ["a", "b", "c"],
            ["c", "a", "d"],
        ]
    )
    assert scores["a"] > scores["b"]
    assert scores["c"] > scores["d"]


def test_citation_filter_drops_unknown_chunk_ids():
    retrieved = [
        RetrievedChunk(
            id="chunk-04",
            content="Manish agreed.",
            start_time="00:04:15",
            end_time="00:06:10",
            speakers=["Manish"],
            segment_ids=["s1"],
            score=0.9,
        )
    ]
    kept = filter_cited_chunks(["chunk-04", "missing"], retrieved)
    assert [chunk.id for chunk in kept] == ["chunk-04"]
