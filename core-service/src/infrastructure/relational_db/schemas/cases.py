import sqlalchemy as sqla

from src.app.dtos.cases import CaseData, CaseDocument
from src.infrastructure.relational_db.connection import mapper_registry, metadata
from src.shared.consts import MAX_FILENAME_LENGTH

cases_table = sqla.Table(
    "cases",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime, server_default=sqla.text("now()"), nullable=False),
    sqla.Column("user_id", sqla.UUID, sqla.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("name", sqla.String(MAX_FILENAME_LENGTH), nullable=False),
)

case_documents_table = sqla.Table(
    "case_documents",
    metadata,
    sqla.Column("id", sqla.UUID, primary_key=True, server_default=sqla.text("gen_random_uuid()")),
    sqla.Column("create_date", sqla.DateTime, server_default=sqla.text("now()"), nullable=False),
    sqla.Column("case_id", sqla.UUID, sqla.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("user_id", sqla.UUID, sqla.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    sqla.Column("presentation_name", sqla.String(MAX_FILENAME_LENGTH), nullable=False),
    sqla.Column("content", sqla.Text, nullable=False),
    sqla.Column("header", sqla.Text, nullable=True),
)


mapper_registry.map_imperatively(CaseData, cases_table)


mapper_registry.map_imperatively(CaseDocument, case_documents_table)
