import sqlalchemy as sqla

from src.app.dtos.applications import ApplicationRepresentation
from src.domain.value_objects.applications import ApplicationGenerationStatus, ApplicationType
from src.infrastructure.relational_db.connection import mapper_registry, metadata

applications_table = sqla.Table(
    "applications",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime, server_default=sqla.text("now()"), nullable=False),
    sqla.Column("case_id", sqla.UUID, sqla.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("user_id", sqla.UUID, sqla.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("application_type", sqla.Enum(ApplicationType, name="applicationtype"), nullable=False),
    sqla.Column(
        "generation_status",
        sqla.Enum(ApplicationGenerationStatus, name="applicationgenerationstatus"),
        nullable=False,
        default=ApplicationGenerationStatus.IN_PROGRESS,
    ),
)


mapper_registry.map_imperatively(ApplicationRepresentation, applications_table)
