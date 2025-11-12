from z3 import *

# Load the problem
g = Goal()
g.add(*parse_smt2_file("generic_1458_update_rate_data_v1_sanity-QF_UFLIA.smt2"))

# Run various probes
print("=== Problem Meta Information ===")
print(f"Memory usage: {Probe('memory')(g)}")
print(f"Number of assertions (size): {Probe('size')(g)}")
print(f"Number of expressions: {Probe('num-exprs')(g)}")
print(f"Number of non-Boolean constants: {Probe('num-consts')(g)}")
print(f"Number of Boolean constants: {Probe('num-bool-consts')(g)}")
print(f"Number of arithmetic constants: {Probe('num-arith-consts')(g)}")
print(f"Number of bit-vector constants: {Probe('num-bv-consts')(g)}")
print(f"Depth of the problem: {Probe('depth')(g)}")
print(f"Has quantifiers: {Probe('is-qfbv')(g)}")
print(f"Is QF_BV: {Probe('is-qfbv')(g)}")
print(f"Is unbounded: {Probe('is-unbounded')(g)}")
print(f"Is propositional: {Probe('is-propositional')(g)}")
print(f"Is QF: {Probe('is-qf')(g)}")

