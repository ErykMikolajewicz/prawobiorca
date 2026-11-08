from core_service.domain.value_objects.application_templates import ApplicationTemplateStatus


def is_ready_to_publish(status: ApplicationTemplateStatus, instructions: str | None) -> bool:
    return status == ApplicationTemplateStatus.DRAFT and bool((instructions or "").strip())


def is_semantic_search_query(query: str) -> bool:
    return " " in query.lstrip()
