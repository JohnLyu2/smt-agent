from z3 import *

print("Loading SMT2 file...")
g = Goal()
g.add(*parse_smt2_file("z3_issue7991_asg.smt2"))

print("\n=== Original Problem ===")
print(f"Size: {Probe('size')(g)}")
print(f"Num exprs: {Probe('num-exprs')(g)}")
print(f"Depth: {Probe('depth')(g)}")

print("\n=== After simplify ===")
t = Tactic('simplify')
g2 = t(g)[0]
print(f"Size: {Probe('size')(g2)}")
print(f"Num exprs: {Probe('num-exprs')(g2)}")
print(f"Depth: {Probe('depth')(g2)}")

print("\n=== After simplify + solve-eqs ===")
t = Then(Tactic('simplify'), Tactic('solve-eqs'))
g3 = t(g)[0]
print(f"Size: {Probe('size')(g3)}")
print(f"Num exprs: {Probe('num-exprs')(g3)}")
print(f"Depth: {Probe('depth')(g3)}")

print("\n=== After simplify + solve-eqs + propagate-values ===")
t = Then(Tactic('simplify'), Tactic('solve-eqs'), Tactic('propagate-values'))
g4 = t(g)[0]
print(f"Size: {Probe('size')(g4)}")
print(f"Num exprs: {Probe('num-exprs')(g4)}")
print(f"Depth: {Probe('depth')(g4)}")

