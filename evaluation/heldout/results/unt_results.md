# Held-out evaluation (n=63), deterministic gold-key scoring
bank sha256-based id: 2026-10-02T21:48:02.741782+00:00

## ALL (89)  (n=63)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 55/63 = 87.3% | 79.4-95.2 | 2 | 6 |
| H hybrid (RRF) top-8 | 57/63 = 90.5% | 82.5-96.8 | 3 | 3 |
| F hybrid + rerank top-8 | 56/63 = 88.9% | 81.0-95.2 | 3 | 4 |
| G shipped workspace pipeline (scope check + F) | 52/63 = 82.5% | 73.0-92.1 | 5 | 6 |

## answerable in-domain  (n=49)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 41/49 = 83.7% | 73.5-93.9 | 2 | 6 |
| H hybrid (RRF) top-8 | 43/49 = 87.8% | 77.6-95.9 | 3 | 3 |
| F hybrid + rerank top-8 | 42/49 = 85.7% | 75.5-93.9 | 3 | 4 |
| G shipped workspace pipeline (scope check + F) | 38/49 = 77.6% | 65.3-87.8 | 5 | 6 |

## must abstain (unanswerable + OOD)  (n=14)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 14/14 = 100.0% | 100.0-100.0 | 0 | 0 |
| H hybrid (RRF) top-8 | 14/14 = 100.0% | 100.0-100.0 | 0 | 0 |
| F hybrid + rerank top-8 | 14/14 = 100.0% | 100.0-100.0 | 0 | 0 |
| G shipped workspace pipeline (scope check + F) | 14/14 = 100.0% | 100.0-100.0 | 0 | 0 |

## type lookup  (n=16)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 15/16 = 93.8% | 81.2-100.0 | 0 | 1 |
| H hybrid (RRF) top-8 | 16/16 = 100.0% | 100.0-100.0 | 0 | 0 |
| F hybrid + rerank top-8 | 16/16 = 100.0% | 100.0-100.0 | 0 | 0 |
| G shipped workspace pipeline (scope check + F) | 14/16 = 87.5% | 68.8-100.0 | 2 | 0 |

## type list  (n=5)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 4/5 = 80.0% | 40.0-100.0 | 0 | 1 |
| H hybrid (RRF) top-8 | 4/5 = 80.0% | 40.0-100.0 | 0 | 1 |
| F hybrid + rerank top-8 | 4/5 = 80.0% | 40.0-100.0 | 0 | 1 |
| G shipped workspace pipeline (scope check + F) | 4/5 = 80.0% | 40.0-100.0 | 0 | 1 |

## type open  (n=22)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 18/22 = 81.8% | 63.6-95.5 | 2 | 2 |
| H hybrid (RRF) top-8 | 18/22 = 81.8% | 63.6-95.5 | 2 | 2 |
| F hybrid + rerank top-8 | 18/22 = 81.8% | 63.6-95.5 | 2 | 2 |
| G shipped workspace pipeline (scope check + F) | 17/22 = 77.3% | 59.1-95.5 | 2 | 3 |

## type locate  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 4/6 = 66.7% | 33.3-100.0 | 0 | 2 |
| H hybrid (RRF) top-8 | 5/6 = 83.3% | 50.0-100.0 | 1 | 0 |
| F hybrid + rerank top-8 | 4/6 = 66.7% | 33.3-100.0 | 1 | 1 |
| G shipped workspace pipeline (scope check + F) | 3/6 = 50.0% | 16.7-83.3 | 1 | 2 |

## type unanswerable  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| H hybrid (RRF) top-8 | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| F hybrid + rerank top-8 | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| G shipped workspace pipeline (scope check + F) | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |

## type ood  (n=8)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| D dense top-8 | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| H hybrid (RRF) top-8 | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| F hybrid + rerank top-8 | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| G shipped workspace pipeline (scope check + F) | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |

## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)
- F - D: +1.6 pp (95% CI -4.8 to +7.9); only-F=3, only-D=2, McNemar p=1
- F - H: -1.6 pp (95% CI -9.5 to +6.3); only-F=3, only-H=4, McNemar p=1
- H - D: +3.2 pp (95% CI -4.8 to +12.7); only-H=5, only-D=3, McNemar p=0.727
- G - D: -4.8 pp (95% CI -12.7 to +3.2); only-G=2, only-D=5, McNemar p=0.453
- G - F: -6.3 pp (95% CI -12.7 to -1.6); only-G=0, only-F=4, McNemar p=0.125

## Latency per query (s): mean / median
- D dense top-8: 7.51 / 7.81
- H hybrid (RRF) top-8: 9.67 / 7.66
- F hybrid + rerank top-8: 19.15 / 19.03
- G shipped workspace pipeline (scope check + F): 16.86 / 19.23
