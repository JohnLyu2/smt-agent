from z3 import *

print("Loading SMT2 file...")
g = Goal()
g.add(*parse_smt2_file("z3_issue7991_asg.smt2"))

print("\n=== Problem Metadata ===")
print(f"Memory usage: {Probe('memory')(g):.2f} MB")
print(f"Number of assertions (size): {Probe('size')(g)}")
print(f"Number of expressions: {Probe('num-exprs')(g)}")
print(f"Number of constants: {Probe('num-consts')(g)}")
print(f"Number of Boolean constants: {Probe('num-bool-consts')(g)}")
print(f"Number of arithmetic constants: {Probe('num-arith-consts')(g)}")
print(f"Number of bit-vector constants: {Probe('num-bv-consts')(g)}")
print(f"Depth: {Probe('depth')(g)}")
print(f"Has quantifiers: {Probe('is-qfbv')(g) == 0}")
print(f"Is QF_BV: {Probe('is-qfbv')(g) > 0}")
print(f"Is QF_AUFBV: {Probe('is-qfaufbv')(g) > 0}")
print(f"Is propositional: {Probe('is-propositional')(g) > 0}")
print(f"Is unbounded: {Probe('is-unbounded')(g) > 0}")

