from enum import StrEnum


class ApplicationGenerationStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    GENERATED = "GENERATED"
    FAILED = "FAILED"
