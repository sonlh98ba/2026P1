from pathlib import Path

from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.database import Base
from app.models import ErrorKnowledgeBase, ErrorTraceMap, Incident, ProcessedLogEvent


def export_schema(output_path: Path) -> None:
    # Ensure model metadata is fully registered before rendering SQL.
    _ = (ErrorKnowledgeBase, ErrorTraceMap, Incident, ProcessedLogEvent)

    lines: list[str] = []
    lines.append("-- Auto-generated from SQLAlchemy models (PostgreSQL dialect).")
    lines.append("-- Re-generate with: python backend/scripts/export_schema.py")
    lines.append("")

    for table in Base.metadata.sorted_tables:
        lines.append(str(CreateTable(table).compile(dialect=postgresql.dialect())).strip() + ";")
        lines.append("")

    for table in Base.metadata.sorted_tables:
        for index in table.indexes:
            lines.append(str(CreateIndex(index).compile(dialect=postgresql.dialect())).strip() + ";")
        if table.indexes:
            lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[1]
    target = project_root / "schema.sql"
    export_schema(target)
    print(f"Schema exported to: {target}")
