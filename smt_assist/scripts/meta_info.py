import warnings
from pathlib import Path

import typer

import pysmt.smtlib.commands as smtcmd
from pysmt.oracles import SizeOracle, get_logic
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

    # script level info
    num_asserts = script.count_command_occurrences(smtcmd.ASSERT)
    # num_declares = sum(1 for cmd in commands if getattr(cmd, "name", None) == "declare-fun")
    # num_defines = sum(1 for cmd in commands if getattr(cmd, "name", None) == "define-fun")
    # num_checks = sum(1 for cmd in commands if getattr(cmd, "name", None) == "check-sat")

    print(f"Number of assertions: {num_asserts}")
    # print(f"Number of function declarations: {num_declares}")
    # print(f"Number of function definitions: {num_defines}")
    # print(f"Number of check-sat commands: {num_checks}")

    # formula level info
    # Followings are 6 size metrics from PySMT SizeOracle
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="pysmt")
        tree_node_size = f.size(SizeOracle.MEASURE_TREE_NODES)
        dag_node_size = f.size(SizeOracle.MEASURE_DAG_NODES)
        tree_leaf_size = f.size(SizeOracle.MEASURE_LEAVES)
        depth = f.size(SizeOracle.MEASURE_DEPTH)
        symbol_size = f.size(SizeOracle.MEASURE_SYMBOLS)
        bool_dag_size = f.size(SizeOracle.MEASURE_BOOL_DAG)

    print(f"Number of nodes in the formula seen as a tree: {tree_node_size}")
    print(f"Number of nodes in the formula seen as a DAG: {dag_node_size}")
    print(f"Number of leaves in the formula seen as a tree: {tree_leaf_size}")
    print(f"Depth of the formula: {depth}")
    print(f"Number of different symbols in the formula: {symbol_size}")
    print(f"Number of nodes in the formula seen as a boolean DAG: {bool_dag_size}")


if __name__ == "__main__":
    app()
