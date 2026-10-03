from enum import StrEnum


class ApplicationType(StrEnum):
    OTHER = "OTHER"
    DIPLOMA_DEADLINE_EXTENSION = "DIPLOMA_DEADLINE_EXTENSION"


class ApplicationGenerationStatus(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    GENERATED = "GENERATED"
    FAILED = "FAILED"
