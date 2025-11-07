#!/usr/bin/env python3
"""Replay LLM conversation from a log.json file."""

import json
from pathlib import Path
from typing import Any

import typer

app = typer.Typer()


def format_message(role: str, content: str, extra: dict[str, Any] | None = None) -> str:
    """Format a message for display."""
    lines = []
    lines.append(f"\n{'=' * 80}")
    lines.append(f"[{role.upper()}]")
    lines.append(f"{'=' * 80}")
    lines.append(content)

    if extra and "response" in extra:
        response = extra["response"]
        if "usage" in response:
            usage = response["usage"]
            lines.append("\n[Token Usage]")
            lines.append(f"  Prompt tokens: {usage.get('prompt_tokens', 'N/A')}")
            lines.append(f"  Completion tokens: {usage.get('completion_tokens', 'N/A')}")
            lines.append(f"  Total tokens: {usage.get('total_tokens', 'N/A')}")
            if "cache_read_input_tokens" in usage:
                lines.append(f"  Cache read tokens: {usage.get('cache_read_input_tokens', 0)}")
            if "cache_creation_input_tokens" in usage:
                lines.append(f"  Cache creation tokens: {usage.get('cache_creation_input_tokens', 0)}")

    return "\n".join(lines)


@app.command()
def replay(
    log_path: Path = typer.Argument(..., help="Path to log.json file"),
    show_tokens: bool = typer.Option(False, "--show-tokens", "-t", help="Show token usage for each message"),
    show_stats: bool = typer.Option(True, "--stats/--no-stats", help="Show summary statistics"),
):
    """Replay the LLM conversation from a log.json file."""
    if not log_path.exists():
        typer.echo(f"Error: File not found: {log_path}", err=True)
        raise typer.Exit(1)

    data = json.loads(log_path.read_text())

    if show_stats:
        info = data.get("info", {})
        model_stats = info.get("model_stats", {})
        typer.echo("\n" + "=" * 80)
        typer.echo("CONVERSATION SUMMARY")
        typer.echo("=" * 80)
        typer.echo(f"Model: {info.get('config', {}).get('model', {}).get('model_name', 'N/A')}")
        typer.echo(f"Total API calls: {model_stats.get('api_calls', 0)}")
        typer.echo(f"Total cost: ${model_stats.get('instance_cost', 0):.6f}")
        typer.echo(f"Exit status: {info.get('exit_status', 'N/A')}")
        typer.echo("=" * 80)

    messages = data.get("messages", [])
    typer.echo(f"\nReplaying {len(messages)} messages...\n")

    for _, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        extra = msg.get("extra") if show_tokens else None

        formatted = format_message(role, content, extra)
        typer.echo(formatted)

    typer.echo(f"\n{'=' * 80}")
    typer.echo("End of conversation")
    typer.echo("=" * 80)


if __name__ == "__main__":
    app()
