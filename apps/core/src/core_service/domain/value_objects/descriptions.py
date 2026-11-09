from enum import StrEnum


class DescriptionStatus(StrEnum):
    NOT_REQUESTED = "NOT_REQUESTED"
    IN_PROGRESS = "IN_PROGRESS"
    GENERATED = "GENERATED"
    FAILED = "FAILED"
