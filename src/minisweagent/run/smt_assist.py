#!/usr/bin/env python3

"""Run mini-SWE-agent in your local environment. This is the default executable `mini`."""
# Read this first: https://mini-swe-agent.com/latest/usage/mini/  (usage)

import os
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import typer
import yaml
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.shortcuts import PromptSession
from rich.console import Console

from minisweagent import global_config_dir
from minisweagent.agents.interactive import InteractiveAgent
from minisweagent.agents.interactive_textual import TextualAgent
from minisweagent.config import builtin_config_dir, get_config_path
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models import get_model
from minisweagent.run.extra.config import configure_if_first_time
from minisweagent.run.utils.save import save_traj
from minisweagent.utils.log import logger
from minisweagent.utils.replay_log import generate_readable_log

DEFAULT_CONFIG = Path(os.getenv("MSWEA_MINI_CONFIG_PATH", builtin_config_dir / "smt.yaml"))
console = Console(highlight=False)
app = typer.Typer(rich_markup_mode="rich")
prompt_session = PromptSession(history=FileHistory(global_config_dir / "mini_task_history.txt"))
_HELP_TEXT = """Run mini-SWE-agent in your local environment.

[not dim]
There are two different user interfaces:

[bold green]mini[/bold green] Simple REPL-style interface
[bold green]mini -v[/bold green] Pager-style interface (Textual)

More information about the usage: [bold green]https://mini-swe-agent.com/latest/usage/mini/[/bold green]
[/not dim]
"""


# fmt: off
@app.command(help=_HELP_TEXT)
def main(
    visual: bool = typer.Option(False, "-v", "--visual", help="Toggle (pager-style) UI (Textual) depending on the MSWEA_VISUAL_MODE_DEFAULT environment setting",),
    model_name: str | None = typer.Option( None, "-m", "--model", help="Model to use",),
    model_class: str | None = typer.Option(None, "--model-class", help="Model class to use (e.g., 'anthropic' or 'minisweagent.models.anthropic.AnthropicModel')", rich_help_panel="Advanced"),
    task: str | None = typer.Option(None, "-t", "--task", help="SMT file path", show_default=False),
    yolo: bool = typer.Option(False, "-y", "--yolo", help="Run without confirmation"),
    cost_limit: float | None = typer.Option(None, "-l", "--cost-limit", help="Cost limit. Set to 0 to disable."),
    config_spec: Path = typer.Option(DEFAULT_CONFIG, "-c", "--config", help="Path to config file"),
    exit_immediately: bool = typer.Option( False, "--exit-immediately", help="Exit immediately when the agent wants to finish instead of prompting.", rich_help_panel="Advanced"),
) -> Any:
    # fmt: on
    configure_if_first_time()
    config_path = get_config_path(config_spec)
    console.print(f"Loading agent config from [bold green]'{config_path}'[/bold green]")
    config = yaml.safe_load(config_path.read_text())

    while True:
        if not task or not task.strip():
            console.print("[bold yellow]Specify the SMT file path")
            task = prompt_session.prompt(
                "",
                multiline=True,
                bottom_toolbar=HTML(
                    "Submit task: <b fg='yellow' bg='black'>Esc+Enter</b> | "
                    "Navigate history: <b fg='yellow' bg='black'>Arrow Up/Down</b> | "
                    "Search history: <b fg='yellow' bg='black'>Ctrl+R</b>"
                ),
            )
            if not task or not task.strip():
                console.print("[bold red]SMT file path cannot be empty[/bold red]")
                task = None
                continue
        
        task_path = Path(task).resolve()
        if not task_path.exists():
            console.print(f"[bold red]File not found: {task_path}[/bold red]")
            task = None
            continue
        
        if not task_path.is_file():
            console.print(f"[bold red]Path is not a file: {task_path}[/bold red]")
            task = None
            continue
        
        break
    
    # Create experiment folder under project root if not exist
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    experiments_dir = project_root / "experiments"
    experiments_dir.mkdir(exist_ok=True)
    # Create a working directory for this task under the experiment folder
    instance_name = task_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_folder = experiments_dir / f"{instance_name}_{timestamp}"
    exp_folder.mkdir(exist_ok=True)
    # Copy SMT file to experiment folder
    dest_file = exp_folder / task_path.name
    shutil.copy2(task_path, dest_file)
    # Update task to new path
    task = str(dest_file)
    # Set output to log.json in the working directory
    output_log = exp_folder / "log.json"
    console.print(f"[bold green]Created experiment folder: {exp_folder}[/bold green]")
    console.print(f"[bold green]Copied SMT file to: {dest_file}[/bold green]")

    if yolo:
        config.setdefault("agent", {})["mode"] = "yolo"
    if cost_limit is not None:
        config.setdefault("agent", {})["cost_limit"] = cost_limit
    if exit_immediately:
        config.setdefault("agent", {})["confirm_exit"] = False
    if model_class is not None:
        config.setdefault("model", {})["model_class"] = model_class
    model = get_model(model_name, config.get("model", {}))
    env = LocalEnvironment(**config.get("env", {}))

    # Both visual flag and the MSWEA_VISUAL_MODE_DEFAULT flip the mode, so it's essentially a XOR
    agent_class = InteractiveAgent
    if visual == (os.getenv("MSWEA_VISUAL_MODE_DEFAULT", "false") == "false"):
        agent_class = TextualAgent

    agent = agent_class(model, env, **config.get("agent", {}))
    exit_status, result, extra_info = None, None, None
    try:
        exit_status, result = agent.run(task)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
        exit_status, result = type(e).__name__, str(e)
        extra_info = {"traceback": traceback.format_exc()}
    finally:
        save_traj(agent, output_log, exit_status=exit_status, result=result, extra_info=extra_info)  # type: ignore[arg-type]
        readable_log_path = exp_folder / "readable_log.md"
        readable_log_content = generate_readable_log(output_log, show_tokens=False, show_stats=True)
        readable_log_path.write_text(readable_log_content)
        console.print(f"[bold green]Created readable log: {readable_log_path}[/bold green]")
    return agent


if __name__ == "__main__":
    app()
