class MeetingNotFoundError(Exception):
    pass


class InvalidTranscriptError(Exception):
    pass


class AIProviderError(Exception):
    pass


class MeetingNotReadyError(Exception):
    pass


class RateLimitExceededError(Exception):
    pass
