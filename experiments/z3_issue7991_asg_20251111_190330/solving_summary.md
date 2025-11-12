# Z3 Solving Attempts Summary

## Problem Characteristics
- **Source**: CBMC 6.7.1 (C Bounded Model Checker)
- **Logic**: QF_AUFBV (Quantifier-Free Arrays, Uninterpreted Functions, Bit-Vectors)
- **Size**: 6.5 MB, 42,927 lines, 13,219 assertions
- **Expressions**: 95,026
- **Constants**: 1,856 (51 Boolean, 1,780 bit-vector)
- **Memory**: 34.18 MB
- **Final assertion**: Large disjunction of 223 Boolean variables (error reachability check)

## Simplification Analysis
- `simplify`: No size reduction (13,219 → 13,219)
- `solve-eqs`: 10% reduction (13,219 → 11,825)
- `elim-uncnstr`: 72% constant reduction (1,856 → 510)

## Solving Attempts (all with 30s timeout)

| Strategy | Result | Conflicts | Decisions | Memory (MB) | Notes |
|----------|--------|-----------|-----------|-------------|-------|
| Default | Timeout | 1,425 | 322,127 | 4,463 | Baseline |
| simplify + solve-eqs + propagate-values + smt | Timeout | 1,370 | 460,222 | 4,374 | Similar to default |
| qfaufbv | Timeout | 1,373 | 310,075 | 4,151 | Slightly better memory |
| ctx-solver-simplify + qfaufbv | Timeout | - | - | 4,757 | Slow preprocessing |
| bvarray2uf + simplify + solve-eqs + smt | Unknown | - | - | 37 | Fast but inconclusive |
| simplify + solve-eqs + elim-uncnstr + smt | Timeout | 985 | 319,659 | 3,691 | Best memory usage |
| simplify + solve-eqs + elim-uncnstr + sat | Unknown | - | - | 37 | Theory not supported |
| simplify + solve-eqs + elim-uncnstr + qfaufbv | Timeout | 945 | 309,115 | 5,027 | Good preprocessing |
| Phase selection + restart tuning | Timeout | 926 | 906,968 | 7,272 | More decisions |
| qfufbv_ackr | Timeout | 976 | 532,297 | 4,273 | Ackermannization |
| Parallel (4 threads) | Timeout | - | - | 5,701 | 68.97s total time |
| qfbv | Timeout | 3,138 | 6,230,952 | 5,395 | **Most progress** |

## Best Performing Strategy
The `qfbv` tactic made the most progress with:
- 3,138 conflicts (2x more than others)
- 10 restarts (vs 4-5 for others)
- 6.2M decisions
- But still timed out

## Conclusion
This is a genuinely hard problem that requires more than 30 seconds to solve with Z3.
