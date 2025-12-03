import sys
from pathlib import Path

import pytest
from pysmt.shortcuts import read_smtlib

# Add smt_knowledge/scripts to path for imports
scripts_dir = Path(__file__).parent.parent.parent / "smt_knowledge" / "scripts"
sys.path.insert(0, str(scripts_dir))

from monomials_counter import MonomialCounter, count_monomials_in_formula


@pytest.fixture
def benchmarks_dir():
    """Return the path to tests/smt_knowledge/benchmarks directory."""
    return Path(__file__).parent / "benchmarks"


@pytest.mark.parametrize(
    ("smt2_file", "expected_count"),
    [
        ("test_simple_nra_monimial.smt2", 4),
        ("test_nested_nra_monomial.smt2", 5),
        ("test_all_kinds_monomial.smt2", 9),
    ],
)
def test_count_monomials_in_formula(benchmarks_dir, smt2_file, expected_count):
    """Test monomial counting on non-linear arithmetic formulas."""
    formula_path = benchmarks_dir / smt2_file
    formula = read_smtlib(str(formula_path))
    count, _ = count_monomials_in_formula(formula)
    assert count == expected_count


def test_count_monomials_asserts_non_linear():
    """Test that count_monomials_in_formula asserts for non-non-linear formulas."""
    from pysmt.shortcuts import And, GE, Real, Symbol
    from pysmt.typing import REAL

    x = Symbol("x", REAL)
    y = Symbol("y", REAL)
    # Linear formula: x + y >= 0
    linear_formula = And(GE(x + y, Real(0)))

    with pytest.raises(AssertionError, match="Formula must be non-linear arithmetic"):
        count_monomials_in_formula(linear_formula)


def test_monomial_counter_directly(benchmarks_dir):
    """Test MonomialCounter class directly."""
    formula_path = benchmarks_dir / "test_simple_nra_monimial.smt2"
    formula = read_smtlib(str(formula_path))

    counter = MonomialCounter()
    count, _ = counter.count_monomials(formula)
    assert count == 4

    # Test that counter resets properly
    count2, _ = counter.count_monomials(formula)
    assert count2 == 4
