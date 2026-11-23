from core_service.domain.value_objects.regulations import RegulationPreparationFailureReason


class RegulationsNotPreparedToSearch(Exception):
    def __init__(self, regulations_name: str):
        self.regulations_name = regulations_name


class RegulationAlreadyInitialized(Exception):
    pass


class RegulationPreparationInProgress(Exception):
    pass


class RegulationInInvalidState(Exception):
    pass


class RegulationNotFound(Exception):
    pass


class RegulationContentNotFound(Exception):
    pass


class RegulationDocumentRejected(Exception):
    def __init__(self, reason: RegulationPreparationFailureReason):
        self.reason = reason


class SectionSummariesGenerationInProgress(Exception):
    pass
