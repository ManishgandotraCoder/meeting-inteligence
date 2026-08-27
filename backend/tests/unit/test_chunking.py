from app.models.transcript import TranscriptSegment
from app.services.chunking_service import ChunkingService


def segment(i: int, speaker: str, text: str):
    return TranscriptSegment(
        id=f"s{i}",
        meeting_id="meeting-123",
        speaker=speaker,
        start_time=f"00:00:{i:02d}",
        text=text,
        sequence_number=i,
    )


def test_chunking_preserves_whole_segments():
    segments = [
        segment(1, "Sarah", "Release is Friday."),
        segment(2, "John", "I own the API."),
        segment(3, "Mike", "Stripe migration is a risk."),
    ]

    chunks = ChunkingService(
        target_tokens=30,
        max_tokens=40,
        overlap_tokens=8,
        short_transcript_tokens=1,
    ).chunk(
        segments,
        meeting_id="meeting-123",
    )

    assert chunks
    assert all(chunk.segment_ids for chunk in chunks)
    assert any("John" in chunk.content for chunk in chunks)
    assert chunks[0].meeting_id == "meeting-123"
    assert chunks[0].speakers


def test_chunking_never_splits_a_speaker_turn():
    long_text = "This is one complete decision about shipping payments next Friday. " * 40
    chunks = ChunkingService(
        target_tokens=20,
        max_tokens=25,
        overlap_tokens=5,
        short_transcript_tokens=1,
    ).chunk(
        [segment(1, "Manish", long_text)],
        meeting_id="meeting-123",
    )

    assert len(chunks) == 1
    assert chunks[0].segment_ids == ["s1"]
    assert chunks[0].speakers == ["Manish"]


def test_short_transcript_stays_one_chunk():
    segments = [
        segment(1, "Rahul", "We should wait."),
        segment(2, "Manish", "Agreed, we wait."),
    ]
    chunks = ChunkingService(short_transcript_tokens=2000).chunk(segments, "meeting-123")

    assert len(chunks) == 1
    assert chunks[0].start_time == "00:00:01"
    assert "Rahul" in chunks[0].speakers and "Manish" in chunks[0].speakers


def test_chunks_include_overlap():
    segments = [
        segment(i, "Speaker", f"Turn number {i} with extra words for size.")
        for i in range(1, 8)
    ]
    chunks = ChunkingService(
        target_tokens=25,
        max_tokens=35,
        overlap_tokens=12,
        short_transcript_tokens=20,
    ).chunk(
        segments,
        "meeting-123",
    )

    assert len(chunks) >= 2
    first_ids = set(chunks[0].segment_ids)
    second_ids = set(chunks[1].segment_ids)
    assert first_ids & second_ids
