#!/usr/bin/env python3
"""
Script to count all monomials in a formula if the theory is non-linear arithmetic.

A monomial is a product of variables (possibly with a coefficient), such as:
- x * y
- x^2
- 2 * x * y * z
- x * y^2

Usage:
    python count_monomials.py <formula_file.smt2>
    or
    python count_monomials.py  # to use from Python API
"""

import sys
from pysmt.walkers import DagWalker
from pysmt import walkers
from pysmt import operators as op
from pysmt.oracles import TheoryOracle
from pysmt.shortcuts import read_smtlib, get_env


class MonomialCounter(DagWalker):
    """Walker that counts monomials in a formula.

    A monomial is identified as:
    - A TIMES node that contains at least one variable (non-constant)
    - A POW node where the base contains a variable

    Note: Each TIMES node is counted separately. A flat TIMES like (* x y z)
    counts as 1 monomial, while nested TIMES like (* x (* y z)) counts as 2 monomials.
    """

    def __init__(self, env=None):
        DagWalker.__init__(self, env=env)
        self.monomial_count = 0

    def count_monomials(self, formula):
        """Count and return the number of monomials in the formula."""
        self.monomial_count = 0
        # Clear memoization to ensure fresh count
        self.memoization.clear()
        self.walk(formula)
        return self.monomial_count

    def _has_variable(self, formula):
        """Check if a formula contains at least one variable (non-constant)."""
        if formula.is_constant():
            return False
        if formula.is_symbol():
            return True
        # Recursively check children
        for arg in formula.args():
            if self._has_variable(arg):
                return True
        return False

    @walkers.handles([op.TIMES])
    def walk_times(self, formula, args, **kwargs):
        """Handle TIMES nodes - count as monomial if it contains variables."""
        # DAG walker memoizes, so we only process each node once
        # Check if at least one argument contains a variable
        has_var = False
        for arg in formula.args():
            if self._has_variable(arg):
                has_var = True
                break

        # Count this TIMES as a monomial if it has variables
        if has_var:
            self.monomial_count += 1

        return None

    @walkers.handles([op.POW])
    def walk_pow(self, formula, args, **kwargs):
        """Handle POW nodes - count as monomial if base contains a variable."""
        base = formula.arg(0)
        if self._has_variable(base):
            self.monomial_count += 1
        return None

    # Handle all other node types - just traverse, don't count
    @walkers.handles(set(op.ALL_TYPES) - {op.TIMES, op.POW})
    def walk_other(self, formula, args, **kwargs):
        """Default handler for all other node types - just traverse."""
        return None


def count_monomials_in_formula(formula, env=None):
    """Count monomials in a formula if it's non-linear arithmetic.

    Args:
        formula: The formula to analyze
        env: Optional environment (defaults to current environment)

    Returns:
        int: Number of monomials found

    Raises:
        AssertionError: If the theory is not non-linear arithmetic
    """
    if env is None:
        env = get_env()

    # Check if the theory is non-linear arithmetic
    theory_oracle = TheoryOracle(env=env)
    theory = theory_oracle.get_theory(formula)

    is_nonlinear = (theory.real_arithmetic or theory.integer_arithmetic) and not theory.linear
    assert is_nonlinear, "Formula must be non-linear arithmetic"

    # Count monomials
    counter = MonomialCounter(env=env)
    return counter.count_monomials(formula)


def main():
    """Main function to run the script from command line."""
    if len(sys.argv) < 2:
        print("Usage: python count_monomials.py <formula_file.smt2>")
        print("\nExample:")
        print("  python count_monomials.py formula.smt2")
        sys.exit(1)

    filename = sys.argv[1]

    try:
        # Read the formula from file
        formula = read_smtlib(filename)

        # Count monomials
        count = count_monomials_in_formula(formula)

        print(f"Number of monomials: {count}")

    except AssertionError as e:
        print(f"Theory is not non-linear arithmetic: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file {filename}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
