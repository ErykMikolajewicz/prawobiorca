from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, status

from src.app.dtos.application_templates import (
    ApplicationTemplateData,
    ApplicationTemplateDetailsData,
    ApplicationTemplateRepresentation,
    ApplicationTemplateUploadTarget,
    PublishedApplicationTemplate,
)
from src.app.use_cases.application_templates import (
    AddApplicationTemplate,
    ConfirmApplicationTemplateUpload,
    DeleteApplicationTemplate,
    GetApplicationTemplate,
    GetApplicationTemplateDownloadUrl,
    ListApplicationTemplates,
    ListPublishedApplicationTemplates,
    PublishApplicationTemplate,
    UnpublishApplicationTemplate,
    UpdateApplicationTemplate,
)
from src.domain.exceptions.application_templates import (
    ApplicationTemplateContentNotFound,
    ApplicationTemplateInInvalidState,
    ApplicationTemplateNotFound,
    InvalidApplicationFieldsConfig,
    InvalidApplicationTemplate,
)
from src.domain.exceptions.organizations import OrganizationNotFound
from src.domain.value_objects.organizations import OrganizationFilter
from src.domain.value_objects.users import Caller
from src.framework.dependencies.application_templates import (
    get_add_application_template,
    get_application_template,
    get_application_template_download_url,
    get_confirm_application_template_upload,
    get_delete_application_template,
    get_list_application_templates,
    get_list_published_application_templates,
    get_publish_application_template,
    get_unpublish_application_template,
    get_update_application_template,
)
from src.framework.dependencies.authentication import get_caller
from src.framework.dependencies.organizations import get_organization_filter

application_templates_router = APIRouter(
    tags=["application_templates"],
    prefix="/api",
    responses={
        status.HTTP_401_UNAUTHORIZED: {"description": "Login required!"},
        status.HTTP_403_FORBIDDEN: {"description": "Permission required!"},
    },
)


@application_templates_router.get(
    "/application-templates/published",
    response_model=list[PublishedApplicationTemplate],
    responses={
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Suborganization given without organization!"},
    },
)
async def get_published_application_templates(
    list_published_templates: Annotated[
        ListPublishedApplicationTemplates, Depends(get_list_published_application_templates)
    ],
    caller: Annotated[Caller, Depends(get_caller)],
    organization_filter: Annotated[OrganizationFilter | None, Depends(get_organization_filter)],
) -> list[PublishedApplicationTemplate]:
    return await list_published_templates.execute(caller, organization_filter)


@application_templates_router.get(
    "/application-templates",
    response_model=list[ApplicationTemplateRepresentation],
)
async def get_application_templates(
    list_templates: Annotated[ListApplicationTemplates, Depends(get_list_application_templates)],
    caller: Annotated[Caller, Depends(get_caller)],
) -> list[ApplicationTemplateRepresentation]:
    return await list_templates.execute(caller)


@application_templates_router.get(
    "/application-templates/{templateId}",
    response_model=ApplicationTemplateRepresentation,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
    },
)
async def get_admin_application_template(
    get_template: Annotated[GetApplicationTemplate, Depends(get_application_template)],
    caller: Annotated[Caller, Depends(get_caller)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> ApplicationTemplateRepresentation:
    try:
        return await get_template.execute(caller, template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")


@application_templates_router.post(
    "/application-templates",
    status_code=status.HTTP_201_CREATED,
)
async def add_application_template(
    add_template: Annotated[AddApplicationTemplate, Depends(get_add_application_template)],
    caller: Annotated[Caller, Depends(get_caller)],
    template_data: ApplicationTemplateData,
) -> ApplicationTemplateUploadTarget:
    return await add_template.execute(caller, template_data)


@application_templates_router.post(
    "/application-templates/{templateId}/confirm-upload",
    response_model=ApplicationTemplateRepresentation,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Application template upload already confirmed, or its content not found on storage!"
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Invalid application template!"},
    },
)
async def confirm_application_template_upload(
    confirm_upload: Annotated[ConfirmApplicationTemplateUpload, Depends(get_confirm_application_template_upload)],
    caller: Annotated[Caller, Depends(get_caller)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> ApplicationTemplateRepresentation:
    try:
        return await confirm_upload.execute(caller, template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Application template upload already confirmed!"
        )
    except ApplicationTemplateContentNotFound:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Application template content not found in storage!"
        )
    except InvalidApplicationTemplate as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@application_templates_router.get(
    "/application-templates/{templateId}/download-url",
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
        status.HTTP_409_CONFLICT: {"description": "Application template not uploaded!"},
    },
)
async def get_admin_application_template_download_url(
    get_download_url: Annotated[GetApplicationTemplateDownloadUrl, Depends(get_application_template_download_url)],
    caller: Annotated[Caller, Depends(get_caller)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> str:
    try:
        return await get_download_url.execute(caller, template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application template not uploaded!")


@application_templates_router.put(
    "/application-templates/{templateId}",
    response_model=ApplicationTemplateRepresentation,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template or organization not found!"},
        status.HTTP_409_CONFLICT: {"description": "Only draft application template can be updated!"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "description": "Invalid fields configuration, or suborganization given without organization!"
        },
    },
)
async def update_application_template(
    update_template: Annotated[UpdateApplicationTemplate, Depends(get_update_application_template)],
    caller: Annotated[Caller, Depends(get_caller)],
    template_id: Annotated[UUID, Path(alias="templateId")],
    details_data: ApplicationTemplateDetailsData,
) -> ApplicationTemplateRepresentation:
    try:
        return await update_template.execute(caller, template_id, details_data)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except OrganizationNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only draft application template can be updated!"
        )
    except InvalidApplicationFieldsConfig as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@application_templates_router.post(
    "/application-templates/{templateId}/publish",
    response_model=ApplicationTemplateRepresentation,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Only draft application template with instructions can be published!"
        },
    },
)
async def publish_application_template(
    publish_template: Annotated[PublishApplicationTemplate, Depends(get_publish_application_template)],
    caller: Annotated[Caller, Depends(get_caller)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> ApplicationTemplateRepresentation:
    try:
        return await publish_template.execute(caller, template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft application template with instructions can be published!",
        )


@application_templates_router.post(
    "/application-templates/{templateId}/unpublish",
    response_model=ApplicationTemplateRepresentation,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
        status.HTTP_409_CONFLICT: {"description": "Application template not published!"},
    },
)
async def unpublish_application_template(
    unpublish_template: Annotated[UnpublishApplicationTemplate, Depends(get_unpublish_application_template)],
    caller: Annotated[Caller, Depends(get_caller)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> ApplicationTemplateRepresentation:
    try:
        return await unpublish_template.execute(caller, template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application template not published!")


@application_templates_router.delete(
    "/application-templates/{templateId}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
    },
)
async def delete_application_template(
    delete_template: Annotated[DeleteApplicationTemplate, Depends(get_delete_application_template)],
    caller: Annotated[Caller, Depends(get_caller)],
    template_id: Annotated[UUID, Path(alias="templateId")],
):
    try:
        await delete_template.execute(caller, template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
