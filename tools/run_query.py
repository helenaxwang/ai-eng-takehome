"""Tool for executing exploratory SQL queries before committing to a final answer."""

from framework.agent import Tool
from framework.database import execute_query


def run_query(query: str) -> str:
    """Execute a SQL query and return a preview of the results.

    Args:
        query: SQL query to execute, with schema-qualified table names.

    Returns:
        A formatted string with up to 10 rows of results, or an error message.
    """
    result = execute_query(query)
    if not result.is_success:
        return f"Query failed: {result.error_message}"
    if result.is_empty:
        return "Query executed successfully but returned no rows."
    df = result.dataframe
    total_rows = len(df)
    output = str(df.head(10))
    if total_rows > 10:
        output += f"\n\n... ({total_rows} total rows, showing first 10)"
    else:
        output += f"\n\n({total_rows} row{'s' if total_rows != 1 else ''})"
    return output


RUN_QUERY: Tool = Tool(
    name="run_query",
    description=(
        "Execute a SQL query and return the results as a preview. "
        "Use this to test and validate your query before submitting a final answer. "
        "Returns up to 10 rows of results, or an error message if the query fails. "
        "Do NOT use this for final submission — use 'submit_answer' for that."
    ),
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The SQL query to execute. Use schema-qualified table names "
                    "(e.g., 'SELECT * FROM CraftBeer.beers LIMIT 5')."
                ),
            },
        },
        "required": ["query"],
    },
    function=run_query,
)
