from src.domain.value_objects.application_templates import ApplicationTemplateStatus


def is_ready_to_publish(status: ApplicationTemplateStatus, instructions: str | None) -> bool:
    return status == ApplicationTemplateStatus.DRAFT and bool((instructions or "").strip())
