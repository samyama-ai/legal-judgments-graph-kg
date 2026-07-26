"""Legal Judgments KG MCP Server — auto-generated via samyama-mcp-serve.

Usage:
    # Embedded mode (loads the graph from ./data on startup):
    python -m mcp_server.server --data-dir data

    # Connect to a running Samyama server with pre-loaded data:
    python -m mcp_server.server --url http://localhost:8080

    # List all auto-generated + custom tools:
    python -m mcp_server.server --data-dir data --list-tools

    # Claude Desktop config (embedded):
    # {"mcpServers": {"legal-judgments-kg": {
    #     "command": "python", "args": ["-m", "mcp_server.server", "--data-dir", "data"]}}}
"""
from __future__ import annotations

import argparse
import os
import sys


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="legal-judgments-kg-mcp",
        description="Legal Judgments Knowledge Graph MCP Server (powered by samyama-mcp-serve)",
    )
    parser.add_argument(
        "--url", default=None,
        help="Connect to a running Samyama server (skip embedded loading).",
    )
    parser.add_argument(
        "--data-dir", default="data",
        help="Path to the 9 legal-judgments CSV files (default: data).",
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Cap the number of cases loaded in embedded mode (default: all).",
    )
    parser.add_argument(
        "--embed", action="store_true",
        help="Also embed case summaries for semantic search (embedded mode).",
    )
    parser.add_argument(
        "--list-tools", action="store_true",
        help="Print discovered tools and exit.",
    )
    parser.add_argument("--name", default="Legal Judgments KG", help="MCP server name.")

    args = parser.parse_args(argv)

    from samyama import SamyamaClient

    if args.url:
        client = SamyamaClient.connect(args.url)
    else:
        client = SamyamaClient.embedded()
        _load_data(client, args.data_dir, args.limit, args.embed)

    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")

    from samyama_mcp.config import ToolConfig
    from samyama_mcp.server import SamyamaMCPServer

    config = ToolConfig.from_yaml(config_path)
    server = SamyamaMCPServer(client, server_name=args.name, config=config)

    if args.list_tools:
        tools = server.list_tools()
        print(f"Legal Judgments KG: {len(tools)} tools\n")
        for name in sorted(tools):
            print(f"  - {name}")
        sys.exit(0)

    server.run()


def _load_data(client, data_dir: str, limit, embed: bool) -> None:
    """Load the legal-judgments CSVs into the embedded client."""
    if not os.path.isdir(data_dir):
        print(
            f"Warning: data directory '{data_dir}' not found. "
            f"Run `python -m etl.download_data` first. Starting with an empty graph.",
            file=sys.stderr,
        )
        return

    from etl.loader import load_legal_judgments

    stats = load_legal_judgments(client, data_dir=data_dir, limit=limit, embed=embed)
    print(
        f"Loaded {stats.get('cases', 0)} cases "
        f"({stats.get('nodes', 0)} nodes / {stats.get('edges', 0)} edges)",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
