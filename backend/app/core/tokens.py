def estimate_tokens(text: str) -> int:
    words = len(text.split())
    return max(1, int(words * 1.3)) if text.strip() else 0
