from dataclasses import asdict, replace

import sqlalchemy as sqla
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

from core_service.application.dtos.application_templates import ApplicationTemplateRepresentation
from core_service.domain.consts import MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH, MAX_FILENAME_LENGTH
from core_service.domain.entities.application_template import ApplicationTemplate
from core_service.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from core_service.domain.value_objects.descriptions import DescriptionStatus
from core_service.infrastructure.consts import VECTOR_LENGTH
from core_service.infrastructure.relational_db.connection import mapper_registry, metadata

APPLICATION_TEMPLATES_ORGANIZATION_FOREIGN_KEY = "application_templates_organization_id_fkey"

APPLICATION_TEMPLATES_SUBORGANIZATION_FOREIGN_KEY = "application_templates_suborganization_id_fkey"

APPLICATION_TEMPLATES_ORGANIZATION_SUBORGANIZATION_FOREIGN_KEY = (
    "fk_application_templates_suborganization_id_organization_id"
)


class ApplicationTemplateFieldsType(sqla.types.TypeDecorator):
    impl = postgresql.JSONB
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return [asdict(field) for field in value]

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return [
            replace(ApplicationTemplateField(**field), field_type=ApplicationFieldType(field["field_type"]))
            for field in value
        ]


application_templates_table = sqla.Table(
    "application_templates",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime(timezone=True), server_default=sqla.text("now()"), nullable=False),
    sqla.Column("name", sqla.String(MAX_FILENAME_LENGTH), nullable=False),
    sqla.Column("instructions", sqla.Text, nullable=True),
    sqla.Column("description", sqla.String(MAX_APPLICATION_TEMPLATE_DESCRIPTION_LENGTH), nullable=True),
    sqla.Column("description_vector", Vector(VECTOR_LENGTH), nullable=True),
    sqla.Column(
        "description_status",
        sqla.Enum(DescriptionStatus, name="applicationtemplatedescriptionstatus"),
        nullable=False,
        default=DescriptionStatus.NOT_REQUESTED,
    ),
    sqla.Column(
        "status",
        sqla.Enum(ApplicationTemplateStatus, name="applicationtemplatestatus"),
        nullable=False,
        default=ApplicationTemplateStatus.NOT_UPLOADED,
    ),
    sqla.Column("fields", ApplicationTemplateFieldsType, nullable=False, server_default=sqla.text("'[]'::jsonb")),
    sqla.Column(
        "organization_id",
        sqla.UUID,
        sqla.ForeignKey("organizations.id", ondelete="SET NULL", name=APPLICATION_TEMPLATES_ORGANIZATION_FOREIGN_KEY),
        nullable=True,
    ),
    sqla.Column(
        "suborganization_id",
        sqla.UUID,
        sqla.ForeignKey(
            "suborganizations.id", ondelete="SET NULL", name=APPLICATION_TEMPLATES_SUBORGANIZATION_FOREIGN_KEY
        ),
        nullable=True,
    ),
    sqla.ForeignKeyConstraint(
        ["suborganization_id", "organization_id"],
        ["suborganizations.id", "suborganizations.organization_id"],
        ondelete="SET NULL (suborganization_id)",
        name=APPLICATION_TEMPLATES_ORGANIZATION_SUBORGANIZATION_FOREIGN_KEY,
    ),
    sqla.Index("ix_application_templates_organization_id_suborganization_id", "organization_id", "suborganization_id"),
)


mapper_registry.map_imperatively(
    ApplicationTemplateRepresentation, application_templates_table, exclude_properties=["description_vector"]
)
mapper_registry.map_imperatively(
    ApplicationTemplate, application_templates_table, exclude_properties=["create_date", "description_vector"]
)
