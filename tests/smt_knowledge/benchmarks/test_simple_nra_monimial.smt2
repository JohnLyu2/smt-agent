(set-logic QF_NRA)
(declare-fun x () Real)
(declare-fun y () Real)
(declare-fun z () Real)

; Some non-linear constraints with monomials:
; - x * y (1 monomial)
; - x^2 (1 monomial) 
; - 2 * x * y * z (1 monomial)
; - x * y + z^2 (2 monomials: x*y and z^2)
(assert (>= (* x y) 0))
(assert (<= (pow x 2.0) 10))
(assert (>= (* 2.0 x y z) 5))
(assert (= (+ (* x y) (pow z 2.0)) 7))

(check-sat)
(get-model)

