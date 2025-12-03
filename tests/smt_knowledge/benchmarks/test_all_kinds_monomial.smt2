(set-logic QF_NRA)
(declare-fun x () Real)
(declare-fun y () Real)
(declare-fun z () Real)
(declare-fun u () Real)
(declare-fun v () Real)

(assert (>= (pow v 2.0) 0))           ; Yes; v^2
(assert (>= (* 3.0 x y) 0))           ; Yes: 3x * y
(assert (>= (* u (pow v 2.0)) 0))     ; Yes: u * v^2
(assert (>= (* z (* (pow x 2.0) y)) 0)) ; Yes: z * (x^2 * y) - nested
(assert (>= x 0))                      ; No: x
(assert (>= (+ 2.0 (pow y 3.0)) 0))   ; No: 2 + y^3
(assert (>= (* x (- y 1)) 0))         ; No; x * (y - 1)

(assert (>= (* x (* y z)) 0))         
(assert (>= (* y z) 0))               ; test whether y * z will be counted separately

(check-sat)

