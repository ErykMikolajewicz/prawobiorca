from dataclasses import asdict

import sqlalchemy as sqla
from sqlalchemy.dialects import postgresql

from src.app.dtos.application_templates import ApplicationTemplateRepresentation
from src.domain.value_objects.application_templates import (
    ApplicationFieldType,
    ApplicationTemplateField,
    ApplicationTemplateStatus,
)
from src.infrastructure.relational_db.connection import mapper_registry, metadata
from src.shared.consts import MAX_FILENAME_LENGTH


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
            ApplicationTemplateField(**{**field, "field_type": ApplicationFieldType(field["field_type"])})
            for field in value
        ]


application_templates_table = sqla.Table(
    "application_templates",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime, server_default=sqla.text("now()"), nullable=False),
    sqla.Column("name", sqla.String(MAX_FILENAME_LENGTH), nullable=False),
    sqla.Column("instructions", sqla.Text, nullable=True),
    sqla.Column(
        "status",
        sqla.Enum(ApplicationTemplateStatus, name="applicationtemplatestatus"),
        nullable=False,
        default=ApplicationTemplateStatus.NOT_UPLOADED,
    ),
    sqla.Column("fields", ApplicationTemplateFieldsType, nullable=False, server_default=sqla.text("'[]'::jsonb")),
)


mapper_registry.map_imperatively(ApplicationTemplateRepresentation, application_templates_table)
