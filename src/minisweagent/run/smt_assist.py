#!/usr/bin/env python3

"""Run SMT assist agent in your local environment. This is the default executable `smt_assist`."""

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

DEFAULT_ANALYZER_CONFIG = Path(os.getenv("MSWEA_ANALYZER_CONFIG_PATH", builtin_config_dir / "smt_analysis.yaml"))
DEFAULT_SOLVER_CONFIG = Path(os.getenv("MSWEA_SOLVER_CONFIG_PATH", builtin_config_dir / "smt_solver.yaml"))
console = Console(highlight=False)
app = typer.Typer(rich_markup_mode="rich")
prompt_session = PromptSession(history=FileHistory(global_config_dir / "mini_task_history.txt"))
_HELP_TEXT = """Run SMT assist agent in your local environment.

[not dim]
There are two different user interfaces:

[bold green]smt_assist[/bold green] Simple REPL-style interface
[bold green]smt_assist -v[/bold green] Pager-style interface (Textual)

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
    analyzer_config_spec: Path = typer.Option(DEFAULT_ANALYZER_CONFIG, "--analyzer-config", help="Path to analyzer agent config file"),
    solver_config_spec: Path = typer.Option(DEFAULT_SOLVER_CONFIG, "--solver-config", help="Path to solver agent config file"),
    exit_immediately: bool = typer.Option( False, "--exit-immediately", help="Exit immediately when the agent wants to finish instead of prompting.", rich_help_panel="Advanced"),
) -> Any:
    # fmt: on
    configure_if_first_time()
    
    # Load analyzer config
    analyzer_config_path = get_config_path(analyzer_config_spec)
    console.print(f"Loading analyzer agent config from [bold green]'{analyzer_config_path}'[/bold green]")
    analyzer_config = yaml.safe_load(analyzer_config_path.read_text())
    
    # Load solver config
    solver_config_path = get_config_path(solver_config_spec)
    console.print(f"Loading solver agent config from [bold green]'{solver_config_path}'[/bold green]")
    solver_config = yaml.safe_load(solver_config_path.read_text())

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
    smt_knowledge_dir = project_root / "smt_knowledge"
    z3_source_dir = smt_knowledge_dir / "z3"
    experiments_dir.mkdir(exist_ok=True)
    # Create a working directory for this task under the experiment folder
    instance_name = task_path.stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exp_folder = experiments_dir / f"{timestamp}_{instance_name}"
    exp_folder.mkdir(exist_ok=True)
    # Copy SMT file to experiment folder
    dest_file = exp_folder / task_path.name
    shutil.copy2(task_path, dest_file)
    # Update task to new path
    task = str(dest_file)
    # Set solver log path
    solver_log = exp_folder / "solver_log.json"
    console.print(f"[bold green]Created experiment folder: {exp_folder}[/bold green]")
    console.print(f"[bold green]Copied SMT file to: {dest_file}[/bold green]")

    # Use solver config for model and env (shared resources)
    model = get_model(model_name, solver_config.get("model", {}))
    env = LocalEnvironment(**solver_config.get("env", {}))

    # Both visual flag and the MSWEA_VISUAL_MODE_DEFAULT flip the mode, so it's essentially a XOR
    agent_class = InteractiveAgent
    if visual == (os.getenv("MSWEA_VISUAL_MODE_DEFAULT", "false") == "false"):
        agent_class = TextualAgent

    # Step 1: Problem Analysis Agent
    console.print("[bold cyan]Step 1: Running problem analysis agent...[/bold cyan]")
    analysis_summary_path = exp_folder / "problem_analysis_summary.md"
    
    # Use analyzer config as-is
    analyzer_agent = agent_class(model, env, **analyzer_config.get("agent", {}))
    analyzer_agent.extra_template_vars["knowledge_dir"] = smt_knowledge_dir
    analyzer_agent.extra_template_vars["z3_dir"] = z3_source_dir
    analyzer_agent.extra_template_vars["analysis_summary_path"] = str(analysis_summary_path)
    
    analyzer_exit_status, analyzer_result, analyzer_extra_info = None, None, None
    analyzer_log = exp_folder / "analysis_log.json"
    try:
        analyzer_exit_status, analyzer_result = analyzer_agent.run(task)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f"Error running analyzer agent: {e}", exc_info=True)
        analyzer_exit_status, analyzer_result = type(e).__name__, str(e)
        analyzer_extra_info = {"traceback": traceback.format_exc()}
    finally:
        save_traj(analyzer_agent, analyzer_log, exit_status=analyzer_exit_status, result=analyzer_result, extra_info=analyzer_extra_info)  # type: ignore[arg-type]
        analyzer_readable_log_path = exp_folder / "analysis_readable_log.md"
        analyzer_readable_log_content = generate_readable_log(analyzer_log, show_tokens=False, show_stats=True)
        analyzer_readable_log_path.write_text(analyzer_readable_log_content)
        console.print(f"[bold green]Analysis agent finished. Log saved to: {analyzer_log}[/bold green]")
        console.print(f"[bold green]Created analyzer agent readable log: {analyzer_readable_log_path}[/bold green]")
    
    # Read the analysis summary if it exists
    if analysis_summary_path.exists():
        analysis_summary = analysis_summary_path.read_text()
        console.print(f"[bold green]Analysis summary saved to: {analysis_summary_path}[/bold green]")
    else:
        console.print(f"[bold yellow]Warning: Analysis summary file not found at {analysis_summary_path}[/bold yellow]")
        analysis_summary = "No analysis summary available."
    
    # Step 2: Problem Solving Agent
    console.print("[bold cyan]Step 2: Running problem solving agent...[/bold cyan]")
    
    # Use solver config as-is
    solver_agent = agent_class(model, env, **solver_config.get("agent", {}))
    solver_agent.extra_template_vars["knowledge_dir"] = smt_knowledge_dir
    solver_agent.extra_template_vars["z3_dir"] = z3_source_dir
    solver_agent.extra_template_vars["analysis_summary"] = analysis_summary
    
    solver_exit_status, solver_result, solver_extra_info = None, None, None
    try:
        solver_exit_status, solver_result = solver_agent.run(task)  # type: ignore[arg-type]
    except Exception as e:
        logger.error(f"Error running solver agent: {e}", exc_info=True)
        solver_exit_status, solver_result = type(e).__name__, str(e)
        solver_extra_info = {"traceback": traceback.format_exc()}
    finally:
        save_traj(solver_agent, solver_log, exit_status=solver_exit_status, result=solver_result, extra_info=solver_extra_info)  # type: ignore[arg-type]
        solver_readable_log_path = exp_folder / "solver_readable_log.md"
        solver_readable_log_content = generate_readable_log(solver_log, show_tokens=False, show_stats=True)
        solver_readable_log_path.write_text(solver_readable_log_content)
        console.print(f"[bold green]Solver agent finished. Log saved to: {solver_log}[/bold green]")
        console.print(f"[bold green]Created solver agent readable log: {solver_readable_log_path}[/bold green]")
    return solver_agent


if __name__ == "__main__":
    app()
