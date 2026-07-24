"""MCP server exposing the Legal Judgments KG as tools.

Run: python -m mcp_server.server
"""
from fastmcp import FastMCP

mcp = FastMCP("legal-judgments-kg")


@mcp.tool()
def most_cited_precedents(limit: int = 5) -> list[dict]:
    """Return the judgments cited by the most other judgments."""
    # TODO: run the CITES aggregation against the Samyama graph engine
    return []


@mcp.tool()
def statutes_most_invoked(limit: int = 5) -> list[dict]:
    """Return the statutes invoked across the most judgments."""
    # TODO: run the INVOKES_STATUTE aggregation
    return []


if __name__ == "__main__":
    mcp.run()
