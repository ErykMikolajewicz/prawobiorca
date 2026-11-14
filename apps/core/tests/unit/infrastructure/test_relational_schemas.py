import subprocess
import sys

RESOLVE_FOREIGN_KEYS_AFTER_SINGLE_SCHEMA_IMPORT = """
from core_service.infrastructure.relational_db.connection import metadata
from core_service.infrastructure.relational_db.schemas import regulations

for table in metadata.tables.values():
    for foreign_key in table.foreign_keys:
        foreign_key.column
"""


def test_importing_single_schema_registers_all_referenced_tables():
    result = subprocess.run(
        [sys.executable, "-c", RESOLVE_FOREIGN_KEYS_AFTER_SINGLE_SCHEMA_IMPORT],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
