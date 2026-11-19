from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(frozen=True)
class AttemptReservation:
    key: str
    window_start: datetime


@dataclass(frozen=True)
class AttemptLimit:
    max_attempts: int
    window: timedelta

    def get_window_start(self, moment: datetime) -> datetime:
        window_seconds = self.window.total_seconds()
        timestamp = moment.timestamp()
        return datetime.fromtimestamp(timestamp - timestamp % window_seconds, UTC)

    def get_window_end(self, moment: datetime) -> datetime:
        return self.get_window_start(moment) + self.window
