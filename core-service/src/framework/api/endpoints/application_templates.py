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
from src.framework.dependencies.authentication import require_admin, require_logged_user

application_templates_router = APIRouter(tags=["application_templates"], prefix="/api")


@application_templates_router.get(
    "/application-templates",
    response_model=list[PublishedApplicationTemplate],
    dependencies=(Depends(require_logged_user),),
)
async def get_published_application_templates(
    list_published_templates: Annotated[
        ListPublishedApplicationTemplates, Depends(get_list_published_application_templates)
    ],
) -> list[PublishedApplicationTemplate]:
    return await list_published_templates.execute()


@application_templates_router.get(
    "/admin/application-templates",
    response_model=list[ApplicationTemplateRepresentation],
    dependencies=(Depends(require_admin),),
)
async def get_application_templates(
    list_templates: Annotated[ListApplicationTemplates, Depends(get_list_application_templates)],
) -> list[ApplicationTemplateRepresentation]:
    return await list_templates.execute()


@application_templates_router.get(
    "/admin/application-templates/{templateId}",
    response_model=ApplicationTemplateRepresentation,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
    },
)
async def get_admin_application_template(
    get_template: Annotated[GetApplicationTemplate, Depends(get_application_template)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> ApplicationTemplateRepresentation:
    try:
        return await get_template.execute(template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")


@application_templates_router.post(
    "/admin/application-templates",
    dependencies=(Depends(require_admin),),
    status_code=status.HTTP_201_CREATED,
)
async def add_application_template(
    add_template: Annotated[AddApplicationTemplate, Depends(get_add_application_template)],
    template_data: ApplicationTemplateData,
) -> ApplicationTemplateUploadTarget:
    return await add_template.execute(template_data)


@application_templates_router.post(
    "/admin/application-templates/{templateId}/confirm-upload",
    response_model=ApplicationTemplateRepresentation,
    dependencies=(Depends(require_admin),),
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
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> ApplicationTemplateRepresentation:
    try:
        return await confirm_upload.execute(template_id)
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
    "/admin/application-templates/{templateId}/download-url",
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
        status.HTTP_409_CONFLICT: {"description": "Application template not uploaded!"},
    },
)
async def get_admin_application_template_download_url(
    get_download_url: Annotated[GetApplicationTemplateDownloadUrl, Depends(get_application_template_download_url)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> str:
    try:
        return await get_download_url.execute(template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application template not uploaded!")


@application_templates_router.put(
    "/admin/application-templates/{templateId}",
    response_model=ApplicationTemplateRepresentation,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
        status.HTTP_409_CONFLICT: {"description": "Only draft application template can be updated!"},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "Invalid fields configuration!"},
    },
)
async def update_application_template(
    update_template: Annotated[UpdateApplicationTemplate, Depends(get_update_application_template)],
    template_id: Annotated[UUID, Path(alias="templateId")],
    details_data: ApplicationTemplateDetailsData,
) -> ApplicationTemplateRepresentation:
    try:
        return await update_template.execute(template_id, details_data)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only draft application template can be updated!"
        )
    except InvalidApplicationFieldsConfig as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e))


@application_templates_router.post(
    "/admin/application-templates/{templateId}/publish",
    response_model=ApplicationTemplateRepresentation,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
        status.HTTP_409_CONFLICT: {
            "description": "Only draft application template with instructions can be published!"
        },
    },
)
async def publish_application_template(
    publish_template: Annotated[PublishApplicationTemplate, Depends(get_publish_application_template)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> ApplicationTemplateRepresentation:
    try:
        return await publish_template.execute(template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft application template with instructions can be published!",
        )


@application_templates_router.post(
    "/admin/application-templates/{templateId}/unpublish",
    response_model=ApplicationTemplateRepresentation,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
        status.HTTP_409_CONFLICT: {"description": "Application template not published!"},
    },
)
async def unpublish_application_template(
    unpublish_template: Annotated[UnpublishApplicationTemplate, Depends(get_unpublish_application_template)],
    template_id: Annotated[UUID, Path(alias="templateId")],
) -> ApplicationTemplateRepresentation:
    try:
        return await unpublish_template.execute(template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
    except ApplicationTemplateInInvalidState:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Application template not published!")


@application_templates_router.delete(
    "/admin/application-templates/{templateId}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=(Depends(require_admin),),
    responses={
        status.HTTP_404_NOT_FOUND: {"description": "Application template not found!"},
    },
)
async def delete_application_template(
    delete_template: Annotated[DeleteApplicationTemplate, Depends(get_delete_application_template)],
    template_id: Annotated[UUID, Path(alias="templateId")],
):
    try:
        await delete_template.execute(template_id)
    except ApplicationTemplateNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application template not found!")
