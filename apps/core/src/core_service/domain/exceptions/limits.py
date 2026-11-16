class UsageLimitExceeded(Exception):
    def __init__(self, is_anonymous: bool, retry_after_seconds: int):
        super().__init__()
        self.is_anonymous = is_anonymous
        self.retry_after_seconds = retry_after_seconds


class TooManyAttempts(Exception):
    def __init__(self, retry_after_seconds: int):
        super().__init__()
        self.retry_after_seconds = retry_after_seconds
