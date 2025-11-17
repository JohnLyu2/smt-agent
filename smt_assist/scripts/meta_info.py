from pathlib import Path

import typer

import pysmt.smtlib.commands as smtcmd
from pysmt.oracles import get_logic
from pysmt.smtlib.parser import SmtLibParser

app = typer.Typer()


@app.command()
def main(smt_lib_path: str = typer.Argument(help="Path to SMT-LIB file")):
    """Extract metadata from an SMT-LIB file using pysmt."""
    path = Path(smt_lib_path)
    if not path.exists():
        typer.echo(f"Error: File not found: {smt_lib_path}", err=True)
        raise typer.Exit(1)

    print("=== SMT-LIB File Metadata ===")
    print(f"File: {smt_lib_path}")
    print(f"File size: {path.stat().st_size} bytes")

    # To-DO: may print annotations

    parser = SmtLibParser()
    with path.open() as f:
        script = parser.get_script(f)

    set_logic_commands = list(script.filter_by_command_name(smtcmd.SET_LOGIC))
    assert len(set_logic_commands) <= 1, "Multiple set-logic commands found"
    if set_logic_commands:
        print(f"Logic (set in the file): {set_logic_commands[0].args[0]}")

    f = script.get_last_formula()

    pysmt_logic = get_logic(f)
    print(f"logic (identified by PySMT): {pysmt_logic}")

    # commands = list(script) if hasattr(script, "__iter__") else getattr(script, "commands", [])
    # print(f"\nNumber of commands: {len(commands)}")

    # num_asserts = sum(1 for cmd in commands if getattr(cmd, "name", None) == "assert")
    # num_declares = sum(1 for cmd in commands if getattr(cmd, "name", None) == "declare-fun")
    # num_defines = sum(1 for cmd in commands if getattr(cmd, "name", None) == "define-fun")
    # num_checks = sum(1 for cmd in commands if getattr(cmd, "name", None) == "check-sat")

    # print(f"Number of assertions: {num_asserts}")
    # print(f"Number of function declarations: {num_declares}")
    # print(f"Number of function definitions: {num_defines}")
    # print(f"Number of check-sat commands: {num_checks}")


if __name__ == "__main__":
    app()
