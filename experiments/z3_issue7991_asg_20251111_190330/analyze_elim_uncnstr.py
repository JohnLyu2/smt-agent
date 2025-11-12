from z3 import *

print("Loading SMT2 file...")
g = Goal()
g.add(*parse_smt2_file("z3_issue7991_asg.smt2"))

print("\n=== After simplify + solve-eqs + elim-uncnstr ===")
t = Then(Tactic('simplify'), Tactic('solve-eqs'), Tactic('elim-uncnstr'))
g_new = t(g)[0]
print(f"Size: {Probe('size')(g_new)}")
print(f"Num exprs: {Probe('num-exprs')(g_new)}")
print(f"Num consts: {Probe('num-consts')(g_new)}")

