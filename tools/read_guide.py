"""Tool for reading domain-specific business rules guides by schema name."""

from pathlib import Path

from framework.agent import Tool
from framework.schema_guide_map import SCHEMA_TO_GUIDE

GUIDES_DIR = Path(__file__).parent.parent / "evaluation" / "data" / "guides"


def read_guide(schema: str | None = None, guide: str | None = None) -> str:
    """Read the business-rules guide for a schema or by guide name.

    Args:
        schema: The exact schema name (e.g., 'financial', 'CraftBeer').
        guide: The guide file name (without .md), for unmapped schemas.

    Returns:
        The full guide content, a list of available guides, or an error message.
    """
    # Direct guide name lookup (for unmapped schemas)
    if guide is not None:
        path = GUIDES_DIR / f"{guide}.md"
        if not path.exists():
            available = sorted(p.stem for p in GUIDES_DIR.glob("*.md"))
            return (
                f"Guide '{guide}' not found. Available guides:\n"
                + "\n".join(f"  {name}" for name in available)
            )
        return path.read_text()

    # Schema-based lookup
    if schema is None:
        return "Provide either a 'schema' or 'guide' parameter."

    guide_stem = SCHEMA_TO_GUIDE.get(schema)
    if guide_stem is None:
        available = sorted(p.stem for p in GUIDES_DIR.glob("*.md"))
        return (
            f"No guide is mapped for schema '{schema}'. "
            "You may pick a relevant guide from the list below and call "
            "this tool again with the 'guide' parameter.\n\n"
            "Available guides:\n" + "\n".join(f"  {g}" for g in available)
        )

    path = GUIDES_DIR / f"{guide_stem}.md"
    if not path.exists():
        return f"Guide file '{guide_stem}.md' not found on disk."

    return path.read_text()


READ_GUIDE: Tool = Tool(
    name="read_guide",
    description=(
        "Read the business-rules guide for a given schema. "
        "Pass 'schema' (e.g., 'financial', 'CraftBeer') to look up the mapped "
        "guide automatically. If no guide is mapped, the tool returns a list of "
        "available guides — pick one and call again with 'guide' (e.g., "
        "'financial_operations') to read it directly."
    ),
    parameters={
        "type": "object",
        "properties": {
            "schema": {
                "type": "string",
                "description": "The exact schema name to look up a guide for.",
            },
            "guide": {
                "type": "string",
                "description": (
                    "The guide name to read directly (without .md extension). "
                    "Use this when no guide is mapped for your schema."
                ),
            },
        },
        "required": [],
    },
    function=read_guide,
)
