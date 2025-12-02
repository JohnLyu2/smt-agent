import warnings
from collections import Counter
from pathlib import Path

import typer
import pysmt.smtlib.commands as smtcmd
from pysmt.environment import get_env
from pysmt.operators import op_to_str, QUANTIFIERS, BOOL_CONNECTIVES, CONSTANTS
from pysmt.oracles import SizeOracle, get_logic
from pysmt.smtlib.parser import SmtLibParser
from pysmt.logics import Logic, get_closer_smtlib_logic

from pysmt_walker_counter import extract_features

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

    env = get_env()
    is_qf = env.qfo.is_qf(f)
    theory = env.theoryo.get_theory(f)
    types = env.typeso.get_types(f)

    logic = Logic(name="Detected Logic", description="", quantifier_free=is_qf, theory=theory)
    # Return a logic supported by PySMT that is close to the one computed
    smtlib_logic = get_closer_smtlib_logic(logic)
    print(f"logic (identified by PySMT): {smtlib_logic}")

    # the below is commented out because PySMT does not support QF_UFNIA
    # pysmt_logic = get_logic(f)
    # print(f"logic (identified by PySMT): {pysmt_logic}")

    # script level info
    cmd_counter = Counter(cmd.name for cmd in script)

    for cmd_name, count in cmd_counter.items():
        print(f"Num of {cmd_name} commands: {count}")

    # Followings are 6 size metrics from PySMT SizeOracle
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=UserWarning, module="pysmt")
        tree_node_size = f.size(SizeOracle.MEASURE_TREE_NODES)
        dag_node_size = f.size(SizeOracle.MEASURE_DAG_NODES)
        tree_leaf_size = f.size(SizeOracle.MEASURE_LEAVES)
        depth = f.size(SizeOracle.MEASURE_DEPTH)
        symbol_size = f.size(SizeOracle.MEASURE_SYMBOLS)
        free_vars = f.get_free_variables()
        free_vars_size = len(free_vars)
        bool_dag_size = f.size(SizeOracle.MEASURE_BOOL_DAG)
        bool_atoms = f.get_atoms()
        bool_atoms_size = len(bool_atoms)

    # Extract all element counts
    element_counts = extract_features(smt_lib_path)

    print("\n=== Formula Level Info ===")
    print(f"Num of nodes in the formula seen as a tree: {tree_node_size}")
    print(f"Num of nodes in the formula seen as a DAG: {dag_node_size}")
    print(f"Num of leaves in the formula seen as a tree: {tree_leaf_size}")
    print(f"Depth of the formula: {depth}")
    # `MEASURE_SYMBOLS` measures the number of declared fun's and declared const's,
    # same as the length of SmtLibScript.get_declared_symbols()
    # still some questions about these... SYMBOL, FUNCTION types...
    print(f"Num of different symbols in the formula: {symbol_size}")
    print(f"Num of free variables in the formula: {free_vars_size}")
    # figure out the difference between `bool_dag_size` and `bool_atoms_size`
    print(f"Num of nodes in the formula seen as a boolean DAG: {bool_dag_size}")
    print(f"Num of Boolean atoms (a Boolean variable or a theory atom) in the formula: {bool_atoms_size}")

    print(f"All appearing types: {types}")

    print(f"Is Quantifier-Free: {is_qf}")
    # if not is_qf:
    #     for quantifier in QUANTIFIERS:
    #         count = element_counts.get(quantifier, 0)
    #         quantifier_str = op_to_str(quantifier)
    #         print(f"Num of {quantifier_str}: {count}")

    # for bool_connective in BOOL_CONNECTIVES:
    #     if count := element_counts.get(bool_connective, 0):
    #         bool_connective_str = op_to_str(bool_connective)
    #         print(f"Num of {bool_connective_str}: {count}")

    # later may move counters of symbol, constant, and operator for different theories together
    # for constant in CONSTANTS:
    #     if count := element_counts.get(constant, 0):
    #         constant_str = op_to_str(constant)
    #         print(f"Num of {constant_str}: {count}")

    # involved_theories = [theory for theory, present in theories.items() if present]
    # print(f"Involved theories: {involved_theories}")

    print("\n=== Formula DAG Node Type Counts ===")
    for node_type, count in sorted(element_counts.items()):
        print(f"{op_to_str(node_type)}: {count}")


if __name__ == "__main__":
    app()
