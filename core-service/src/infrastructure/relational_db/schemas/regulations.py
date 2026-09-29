import sqlalchemy as sqla

from src.app.dtos.regulations import RegulationRepresentation
from src.domain.value_objects.regulations import RegulationPreparationStatus, RegulationType
from src.infrastructure.relational_db.connection import mapper_registry, metadata
from src.shared.consts import MAX_FILENAME_LENGTH, MAX_REGULATION_DESCRIPTION_LENGTH

regulations_table = sqla.Table(
    "regulations",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime, server_default=sqla.text("now()"), nullable=False),
    sqla.Column("user_id", sqla.UUID, sqla.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    sqla.Column("presentation_name", sqla.String(MAX_FILENAME_LENGTH), nullable=False),
    sqla.Column("description", sqla.String(MAX_REGULATION_DESCRIPTION_LENGTH), nullable=True),
    sqla.Column("regulation_type", sqla.Enum(RegulationType, name="regulationtype"), nullable=True, default=None),
    sqla.Column(
        "preparation_status",
        sqla.Enum(RegulationPreparationStatus, name="regulationpreparationstatus"),
        nullable=False,
        default=RegulationPreparationStatus.NOT_STARTED,
    ),
    sqla.UniqueConstraint("id", "user_id", name="uq_regulations_id_user_id"),
)


mapper_registry.map_imperatively(RegulationRepresentation, regulations_table)
