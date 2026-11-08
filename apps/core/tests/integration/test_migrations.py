import alembic.command
import alembic.config
from testcontainers.community.postgres import PostgresContainer


def test_migrations_match_schemas(postgres_container: PostgresContainer):
    alembic_cfg = alembic.config.Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", postgres_container.get_connection_url())

    alembic.command.check(alembic_cfg)
