# Held-out evaluation (n=63), deterministic gold-key scoring
bank: unt/unt_bank.json

## ALL  (n=63)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| G_v2 | 54/63 = 85.7% | 76.2-93.7 | 5 | 4 |
| D | 55/63 = 87.3% | 79.4-95.2 | 2 | 6 |
| H | 57/63 = 90.5% | 82.5-96.8 | 3 | 3 |
| F | 56/63 = 88.9% | 81.0-95.2 | 3 | 4 |

## answerable in-domain  (n=49)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| G_v2 | 40/49 = 81.6% | 69.4-91.8 | 5 | 4 |
| D | 41/49 = 83.7% | 73.5-93.9 | 2 | 6 |
| H | 43/49 = 87.8% | 77.6-95.9 | 3 | 3 |
| F | 42/49 = 85.7% | 75.5-93.9 | 3 | 4 |

## must abstain (unanswerable + OOD)  (n=14)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| G_v2 | 14/14 = 100.0% | 100.0-100.0 | 0 | 0 |
| D | 14/14 = 100.0% | 100.0-100.0 | 0 | 0 |
| H | 14/14 = 100.0% | 100.0-100.0 | 0 | 0 |
| F | 14/14 = 100.0% | 100.0-100.0 | 0 | 0 |

## novel phrasing (sim<0.75 to any dev question)  (n=60)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| G_v2 | 51/60 = 85.0% | 75.0-93.3 | 5 | 4 |
| D | 52/60 = 86.7% | 78.3-95.0 | 2 | 6 |
| H | 54/60 = 90.0% | 81.7-96.7 | 3 | 3 |
| F | 53/60 = 88.3% | 80.0-95.0 | 3 | 4 |

## type lookup  (n=16)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| G_v2 | 15/16 = 93.8% | 81.2-100.0 | 1 | 0 |
| D | 15/16 = 93.8% | 81.2-100.0 | 0 | 1 |
| H | 16/16 = 100.0% | 100.0-100.0 | 0 | 0 |
| F | 16/16 = 100.0% | 100.0-100.0 | 0 | 0 |

## type list  (n=5)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| G_v2 | 4/5 = 80.0% | 40.0-100.0 | 0 | 1 |
| D | 4/5 = 80.0% | 40.0-100.0 | 0 | 1 |
| H | 4/5 = 80.0% | 40.0-100.0 | 0 | 1 |
| F | 4/5 = 80.0% | 40.0-100.0 | 0 | 1 |

## type open  (n=22)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| G_v2 | 16/22 = 72.7% | 54.5-90.9 | 3 | 3 |
| D | 18/22 = 81.8% | 63.6-95.5 | 2 | 2 |
| H | 18/22 = 81.8% | 63.6-95.5 | 2 | 2 |
| F | 18/22 = 81.8% | 63.6-95.5 | 2 | 2 |

## type locate  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| G_v2 | 5/6 = 83.3% | 50.0-100.0 | 1 | 0 |
| D | 4/6 = 66.7% | 33.3-100.0 | 0 | 2 |
| H | 5/6 = 83.3% | 50.0-100.0 | 1 | 0 |
| F | 4/6 = 66.7% | 33.3-100.0 | 1 | 1 |

## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)
- H - D: +3.2 pp (95% CI -4.8 to +12.7); only-H=5, only-D=3, McNemar p=0.727
- F - D: +1.6 pp (95% CI -4.8 to +7.9); only-F=3, only-D=2, McNemar p=1
- H - F: +1.6 pp (95% CI -6.3 to +9.5); only-H=4, only-F=3, McNemar p=1
- H - G_v2: +4.8 pp (95% CI -6.3 to +15.9); only-H=7, only-G_v2=4, McNemar p=0.549
- F - G_v2: +3.2 pp (95% CI -4.8 to +11.1); only-F=4, only-G_v2=2, McNemar p=0.688

## Latency per query (s): mean / median
- G_v2: 63.81 / 71.21
- D: 7.51 / 7.81
- H: 9.67 / 7.66
- F: 19.15 / 19.03

## phase usage G_v2 {'FASE 3 — RECUPERACIÓN HÍBRIDA + RERANKING + GENERACIÓN': 52, 'FASE 2 — CLASIFICADOR DEL CONTEXTO': 11}
## phase usage D {'D': 63}
## phase usage H {'H': 63}
## phase usage F {'F': 63}