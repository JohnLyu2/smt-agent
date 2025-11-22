from collections import Counter
from pysmt.walkers import DagWalker
from pysmt.shortcuts import read_smtlib
from pysmt.operators import ALL_TYPES
import sys


class FeatureExtractor(DagWalker):
    """Feature extractor that counts all node types in ALL_TYPES."""

    def __init__(self):
        super().__init__()
        self.counts = Counter()

    def _walk_and_count(self, formula):
        """Recursively walk and count node types."""
        # Count this node's type
        node_type = formula.node_type()

        # Check that node type is in ALL_TYPES
        if node_type not in ALL_TYPES:
            raise ValueError(f"Unknown node type {node_type} not in ALL_TYPES")

        self.counts[node_type] += 1

        # Recursively process children
        for child in formula.args():
            self._walk_and_count(child)

    def walk(self, formula, **kwargs):
        """Walk the formula and count all node types."""
        self._walk_and_count(formula)
        return dict(self.counts)


def extract_features(filepath):
    """Extract features from an SMT-LIB2 file by counting all node types.

    Args:
        filepath: Path to an SMT-LIB2 file

    Returns:
        Dictionary mapping node type names to their counts
    """
    formula = read_smtlib(filepath)
    extractor = FeatureExtractor()
    return extractor.walk(formula)


def main():
    """Main function that reads SMT-LIB2 file path from command line."""
    if len(sys.argv) != 2:
        print("Usage: python feature_extractor.py <smt2_file_path>")
        sys.exit(1)

    filepath = sys.argv[1]
    try:
        features = extract_features(filepath)
        print(features)
    except Exception as e:
        print(f"Error processing file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
