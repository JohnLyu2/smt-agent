#!/usr/bin/env python3
"""
Script to count all monomials in a formula if the theory is non-linear arithmetic.

A variable term is either:
- A variable (e.g., x)
- A variable with a non-negative integer exponent (e.g., x^3)

A monomial is either:
- A variable with a non-negative integer exponent, OR
- The product of at least two variable terms

Examples:
- Yes: 3x * y, u * v^2, z * (x^2 * y), y^3 [nested counts as multiple monomials, including exponents]
- No: x (single variable without exponent), -3, 2 + y^3, x * (y - 1), u^(-1)

Usage:
    python count_monomials.py <formula_file.smt2>
"""

import sys
from pysmt.walkers import DagWalker
from pysmt import walkers
from pysmt import operators as op
from pysmt.oracles import TheoryOracle
from pysmt.shortcuts import read_smtlib, get_env


class MonomialCounter(DagWalker):
    """Walker that counts monomials in a formula.

    A monomial is the product of at least two variable terms.
    Nested TIMES nodes are counted as multiple monomials (each TIMES with >= 2 variable terms is counted separately).
    """

    def __init__(self, env=None):
        DagWalker.__init__(self, env=env)
        self.monomial_count = 0
        # Track all TIMES nodes and their variable term counts
        self.times_nodes = {}  # formula -> variable_term_count
        # Track POW nodes that are variable terms
        self.pow_nodes = []  # list of POW formulas that are variable terms
        # Store the monomial formulas that are counted
        self.monomials = []  # list of monomial formulas

    def count_monomials(self, formula):
        """Count and return the number of monomials and the list of monomial formulas.

        Returns:
            tuple: (count, list_of_monomials) where count is int and list_of_monomials is list of FNode
        """
        self.monomial_count = 0
        self.monomials = []
        self.times_nodes = {}
        self.pow_nodes = []
        # Clear memoization to ensure fresh count
        self.memoization.clear()
        self.walk(formula)

        # Now count monomials:
        # 1. Count all TIMES nodes with >= 2 variable terms
        # 2. Count POW nodes that are variable terms (single variable with exponent)
        # Nested TIMES and POW nodes are counted separately (multiple monomials)
        for times_node, var_count in self.times_nodes.items():
            if var_count >= 2:
                # Count this TIMES as a monomial
                self.monomial_count += 1
                self.monomials.append(times_node)

        # Count all POW nodes that are variable terms (single variable with non-negative integer exponent)
        # Count them even if they're nested inside TIMES nodes
        for pow_node in self.pow_nodes:
            self.monomial_count += 1
            self.monomials.append(pow_node)

        return self.monomial_count, self.monomials

    def _is_variable_term(self, formula):
        """Check if a formula is a variable term.

        A variable term is either:
        - A variable (symbol)
        - A POW with a variable base and non-negative integer exponent
        """
        if formula.is_symbol():
            return True

        if formula.node_type() == op.POW:
            base = formula.arg(0)
            exponent = formula.arg(1)
            # Base must be a variable
            if not base.is_symbol():
                return False
            # Exponent must be a non-negative integer constant
            if not exponent.is_constant():
                return False
            try:
                exp_value = exponent.constant_value()
                # Check if it's a non-negative integer
                # Handle int, float, and Fraction types
                from fractions import Fraction

                if isinstance(exp_value, int):
                    return exp_value >= 0
                elif isinstance(exp_value, float):
                    # Check if it's a non-negative integer (2.0, 3.0, etc.)
                    return exp_value >= 0 and (exp_value == int(exp_value))
                elif isinstance(exp_value, Fraction):
                    # Check if it's a non-negative integer fraction (2/1, 3/1, etc.)
                    return exp_value >= 0 and exp_value.denominator == 1
            except (ValueError, TypeError):
                return False
        return False

    def _count_variable_terms_in_times(self, formula):
        """Count the number of variable terms in a TIMES node.

        Recursively handles nested TIMES nodes by flattening them.
        Returns the count of variable terms.
        """
        count = 0
        for arg in formula.args():
            if arg.is_times():
                # Recursively count variable terms in nested TIMES
                count += self._count_variable_terms_in_times(arg)
            elif self._is_variable_term(arg):
                count += 1
        return count

    @walkers.handles([op.TIMES])
    def walk_times(self, formula, args, **kwargs):
        """Handle TIMES nodes - collect information about variable terms."""
        # Count variable terms in this TIMES (including nested TIMES)
        var_term_count = self._count_variable_terms_in_times(formula)
        self.times_nodes[formula] = var_term_count
        return None

    @walkers.handles([op.POW])
    def walk_pow(self, formula, args, **kwargs):
        """Handle POW nodes - collect those that are variable terms (single variable with exponent)."""
        # Check if this POW is a variable term (base is variable, exponent is non-negative integer)
        if self._is_variable_term(formula):
            self.pow_nodes.append(formula)
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
        tuple: (count, monomials) where count is int and monomials is list of FNode

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
        count, monomials = count_monomials_in_formula(formula)

        print(f"Number of monomials: {count}")
        if count > 0:
            print("\nMonomials found:")
            for i, monomial in enumerate(monomials, 1):
                print(f"  {i}. {monomial}")

    except AssertionError as e:
        print(f"Theory is not non-linear arithmetic: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing file {filename}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
