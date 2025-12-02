(set-logic QF_NRA)
(declare-fun x () Real)
(declare-fun y () Real)
(declare-fun z () Real)
(declare-fun w () Real)

; Nested TIMES examples:
; - x * (y * z) should count as 2 monomials (outer TIMES and inner TIMES)
; - (x * y) * (z * w) should count as 3 monomials (outer TIMES, first inner TIMES, second inner TIMES)
(assert (>= (* x (* y z)) 0))
(assert (>= (* (* x y) (* z w)) 5))

(check-sat)

