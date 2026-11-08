import sqlalchemy as sqla
from pgvector.sqlalchemy import Vector

from src.app.dtos.regulations import RegulationRepresentation
from src.domain.value_objects.regulations import (
    RegulationDescriptionStatus,
    RegulationPreparationStatus,
    RegulationType,
)
from src.infrastructure.relational_db.connection import mapper_registry, metadata
from src.shared.consts import MAX_FILENAME_LENGTH, MAX_REGULATION_DESCRIPTION_LENGTH, VECTOR_LENGTH

regulations_table = sqla.Table(
    "regulations",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime(timezone=True), server_default=sqla.text("now()"), nullable=False),
    sqla.Column("user_id", sqla.UUID, sqla.ForeignKey("users.id", ondelete="CASCADE"), nullable=True),
    sqla.Column("presentation_name", sqla.String(MAX_FILENAME_LENGTH), nullable=False),
    sqla.Column("description", sqla.String(MAX_REGULATION_DESCRIPTION_LENGTH), nullable=True),
    sqla.Column("description_vector", Vector(VECTOR_LENGTH), nullable=True),
    sqla.Column(
        "description_status",
        sqla.Enum(RegulationDescriptionStatus, name="regulationdescriptionstatus"),
        nullable=False,
        default=RegulationDescriptionStatus.NOT_REQUESTED,
    ),
    sqla.Column("regulation_type", sqla.Enum(RegulationType, name="regulationtype"), nullable=True, default=None),
    sqla.Column(
        "preparation_status",
        sqla.Enum(RegulationPreparationStatus, name="regulationpreparationstatus"),
        nullable=False,
        default=RegulationPreparationStatus.NOT_STARTED,
    ),
    sqla.Column("organization_id", sqla.UUID, sqla.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True),
    sqla.Column("suborganization_id", sqla.UUID, nullable=True),
    sqla.UniqueConstraint("id", "user_id", name="uq_regulations_id_user_id"),
    sqla.ForeignKeyConstraint(
        ["suborganization_id", "organization_id"],
        ["suborganizations.id", "suborganizations.organization_id"],
        ondelete="CASCADE",
        name="fk_regulations_suborganization_id_organization_id",
    ),
    sqla.CheckConstraint(
        "user_id IS NULL OR organization_id IS NULL", name="ck_regulations_private_without_organization"
    ),
    sqla.CheckConstraint(
        "suborganization_id IS NULL OR organization_id IS NOT NULL",
        name="ck_regulations_suborganization_with_organization",
    ),
    sqla.Index("ix_regulations_organization_id_suborganization_id", "organization_id", "suborganization_id"),
)


mapper_registry.map_imperatively(RegulationRepresentation, regulations_table, exclude_properties=["description_vector"])
