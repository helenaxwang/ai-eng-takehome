"""Tool for exploring the database schema structure."""

from framework.agent import Tool
from framework.database import describe_table, list_schemas, list_tables


def explore_schema(schema: str | None = None) -> str:
    """Explore available schemas, tables, and columns in the database.

    Args:
        schema: Optional schema name to inspect in detail. If omitted, lists all
                schemas and their table names.

    Returns:
        A formatted string listing schemas/tables, or tables/columns for a schema.
    """
    if schema is None:
        schemas = list_schemas()
        if not schemas:
            return "No schemas found in the database."
        lines = ["Available schemas and tables:", ""]
        for schema_name in schemas:
            tables = list_tables(schema_name) or []
            lines.append(f"[{schema_name}]")
            for table in tables:
                lines.append(f"  {schema_name}.{table}")
            lines.append("")
        return "\n".join(lines).rstrip()
    else:
        tables = list_tables(schema) or []
        if not tables:
            return f"Schema '{schema}' not found or has no tables."
        lines = [f"Schema: {schema}", ""]
        for table in tables:
            lines.append(f"{schema}.{table}")
            for col in describe_table(schema, table):
                lines.append(f"  - {col}")
            lines.append("")
        return "\n".join(lines).rstrip()


EXPLORE_SCHEMA: Tool = Tool(
    name="explore_schema",
    description=(
        "Explore the database schema to discover available schemas, tables, and columns. "
        "Call with no arguments to list all schemas and their table names. "
        "Call with a schema name to get all tables in that schema with full column details "
        "(names and types). "
        "Always call this tool before writing a query to confirm the exact schema and table "
        "names — do NOT guess names like 'public.beers' or 'baseball.batting'."
    ),
    parameters={
        "type": "object",
        "properties": {
            "schema": {
                "type": "string",
                "description": (
                    "Optional. The exact schema name to inspect (e.g., 'CraftBeer', "
                    "'lahman_2014'). If omitted, returns all schemas and their table names."
                ),
            },
        },
        "required": [],
    },
    function=explore_schema,
)
