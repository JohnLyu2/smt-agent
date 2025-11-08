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


def generate_readable_log(log_path: Path, show_tokens: bool = False, show_stats: bool = True) -> str:
    """Generate a readable log from a log.json file."""
    if not log_path.exists():
        return f"Error: File not found: {log_path}"

    data = json.loads(log_path.read_text())
    output_lines = []

    if show_stats:
        info = data.get("info", {})
        model_stats = info.get("model_stats", {})
        output_lines.append("\n" + "=" * 80)
        output_lines.append("CONVERSATION SUMMARY")
        output_lines.append("=" * 80)
        output_lines.append(f"Model: {info.get('config', {}).get('model', {}).get('model_name', 'N/A')}")
        output_lines.append(f"Total API calls: {model_stats.get('api_calls', 0)}")
        output_lines.append(f"Total cost: ${model_stats.get('instance_cost', 0):.6f}")
        output_lines.append(f"Exit status: {info.get('exit_status', 'N/A')}")
        output_lines.append("=" * 80)

    messages = data.get("messages", [])
    output_lines.append(f"\nReplaying {len(messages)} messages...\n")

    for _, msg in enumerate(messages, 1):
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        extra = msg.get("extra") if show_tokens else None

        formatted = format_message(role, content, extra)
        output_lines.append(formatted)

    output_lines.append(f"\n{'=' * 80}")
    output_lines.append("End of conversation")
    output_lines.append("=" * 80)

    return "\n".join(output_lines)


@app.command()
def replay(
    log_path: Path = typer.Argument(..., help="Path to log.json file"),
    show_tokens: bool = typer.Option(False, "--show-tokens", "-t", help="Show token usage for each message"),
    show_stats: bool = typer.Option(True, "--stats/--no-stats", help="Show summary statistics"),
    output: Path | None = typer.Option(
        None, "-o", "--output", help="Output file path (if not specified, prints to stdout)"
    ),
):
    """Replay the LLM conversation from a log.json file."""
    output_text = generate_readable_log(log_path, show_tokens=show_tokens, show_stats=show_stats)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(output_text)
        typer.echo(f"Replay saved to: {output}")
    else:
        typer.echo(output_text)


if __name__ == "__main__":
    app()
