# Held-out evaluation (n=89), deterministic gold-key scoring
bank sha256-based id: 2026-10-02T20:17:31.334331+00:00  | max sim to any dev question: 0.895

## ALL (89)  (n=89)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 57/89 = 64.0% | 53.9-74.2 | 14 | 18 |
| V2 dense+rerank | 59/89 = 66.3% | 56.2-76.4 | 11 | 19 |
| V3 router+hybrid | 51/89 = 57.3% | 47.2-67.4 | 12 | 26 |
| V5 router+hybrid+rerank (no extraction) | 54/89 = 60.7% | 50.6-70.8 | 7 | 28 |
| V6 hybrid+rerank, no router | 59/89 = 66.3% | 56.2-76.4 | 5 | 25 |
| V4 complete | 58/89 = 65.2% | 55.1-75.3 | 9 | 22 |

## answerable in-domain  (n=74)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 43/74 = 58.1% | 47.3-68.9 | 14 | 17 |
| V2 dense+rerank | 45/74 = 60.8% | 50.0-71.6 | 11 | 18 |
| V3 router+hybrid | 43/74 = 58.1% | 45.9-68.9 | 12 | 19 |
| V5 router+hybrid+rerank (no extraction) | 46/74 = 62.2% | 51.4-73.0 | 7 | 21 |
| V6 hybrid+rerank, no router | 45/74 = 60.8% | 50.0-71.6 | 5 | 24 |
| V4 complete | 43/74 = 58.1% | 47.3-68.9 | 9 | 22 |

## must abstain (unanswerable + OOD)  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 14/15 = 93.3% | 80.0-100.0 | 0 | 1 |
| V2 dense+rerank | 14/15 = 93.3% | 80.0-100.0 | 0 | 1 |
| V3 router+hybrid | 8/15 = 53.3% | 26.7-80.0 | 0 | 7 |
| V5 router+hybrid+rerank (no extraction) | 8/15 = 53.3% | 26.7-80.0 | 0 | 7 |
| V6 hybrid+rerank, no router | 14/15 = 93.3% | 80.0-100.0 | 0 | 1 |
| V4 complete | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |

## novel phrasing (sim<0.75 to any dev question)  (n=75)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 44/75 = 58.7% | 48.0-69.3 | 14 | 17 |
| V2 dense+rerank | 47/75 = 62.7% | 52.0-73.3 | 10 | 18 |
| V3 router+hybrid | 41/75 = 54.7% | 42.7-65.3 | 10 | 24 |
| V5 router+hybrid+rerank (no extraction) | 42/75 = 56.0% | 44.0-66.7 | 6 | 27 |
| V6 hybrid+rerank, no router | 47/75 = 62.7% | 52.0-73.3 | 5 | 23 |
| V4 complete | 46/75 = 61.3% | 50.7-72.0 | 8 | 21 |

## category CRONOGRAMA  (n=14)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 13/14 = 92.9% | 78.6-100.0 | 0 | 1 |
| V2 dense+rerank | 12/14 = 85.7% | 64.3-100.0 | 1 | 1 |
| V3 router+hybrid | 12/14 = 85.7% | 64.3-100.0 | 1 | 1 |
| V5 router+hybrid+rerank (no extraction) | 12/14 = 85.7% | 64.3-100.0 | 1 | 1 |
| V6 hybrid+rerank, no router | 12/14 = 85.7% | 64.3-100.0 | 1 | 1 |
| V4 complete | 11/14 = 78.6% | 57.1-100.0 | 1 | 2 |

## category VACANTES  (n=25)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 12/25 = 48.0% | 28.0-68.0 | 4 | 9 |
| V2 dense+rerank | 11/25 = 44.0% | 24.0-64.0 | 5 | 9 |
| V3 router+hybrid | 12/25 = 48.0% | 28.0-68.0 | 4 | 9 |
| V5 router+hybrid+rerank (no extraction) | 15/25 = 60.0% | 40.0-80.0 | 3 | 7 |
| V6 hybrid+rerank, no router | 10/25 = 40.0% | 20.0-60.0 | 3 | 12 |
| V4 complete | 14/25 = 56.0% | 36.0-76.0 | 3 | 8 |

## category TEMARIO  (n=20)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 8/20 = 40.0% | 20.0-60.0 | 7 | 5 |
| V2 dense+rerank | 11/20 = 55.0% | 35.0-75.0 | 3 | 6 |
| V3 router+hybrid | 9/20 = 45.0% | 25.0-65.0 | 5 | 6 |
| V5 router+hybrid+rerank (no extraction) | 9/20 = 45.0% | 25.0-65.0 | 2 | 9 |
| V6 hybrid+rerank, no router | 12/20 = 60.0% | 40.0-80.0 | 1 | 7 |
| V4 complete | 9/20 = 45.0% | 25.0-65.0 | 4 | 7 |

## category REGLAMENTO  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 10/15 = 66.7% | 40.0-86.7 | 3 | 2 |
| V2 dense+rerank | 11/15 = 73.3% | 53.3-93.3 | 2 | 2 |
| V3 router+hybrid | 10/15 = 66.7% | 40.0-86.7 | 2 | 3 |
| V5 router+hybrid+rerank (no extraction) | 10/15 = 66.7% | 40.0-86.7 | 1 | 4 |
| V6 hybrid+rerank, no router | 11/15 = 73.3% | 46.7-93.3 | 0 | 4 |
| V4 complete | 9/15 = 60.0% | 33.3-86.7 | 1 | 5 |

## category SIN_RESPUESTA  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| V2 dense+rerank | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| V3 router+hybrid | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| V5 router+hybrid+rerank (no extraction) | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 hybrid+rerank, no router | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4 complete | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |

## category FUERA_DE_DOMINIO  (n=9)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 8/9 = 88.9% | 66.7-100.0 | 0 | 1 |
| V2 dense+rerank | 8/9 = 88.9% | 66.7-100.0 | 0 | 1 |
| V3 router+hybrid | 2/9 = 22.2% | 0.0-55.6 | 0 | 7 |
| V5 router+hybrid+rerank (no extraction) | 2/9 = 22.2% | 0.0-55.6 | 0 | 7 |
| V6 hybrid+rerank, no router | 8/9 = 88.9% | 66.7-100.0 | 0 | 1 |
| V4 complete | 9/9 = 100.0% | 100.0-100.0 | 0 | 0 |

## type lookup  (n=36)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 24/36 = 66.7% | 50.0-80.6 | 6 | 6 |
| V2 dense+rerank | 24/36 = 66.7% | 50.0-80.6 | 4 | 8 |
| V3 router+hybrid | 23/36 = 63.9% | 47.2-77.8 | 8 | 5 |
| V5 router+hybrid+rerank (no extraction) | 25/36 = 69.4% | 52.8-83.3 | 4 | 7 |
| V6 hybrid+rerank, no router | 23/36 = 63.9% | 47.2-77.8 | 3 | 10 |
| V4 complete | 24/36 = 66.7% | 50.0-80.6 | 5 | 7 |

## type list  (n=11)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 5/11 = 45.5% | 18.2-72.7 | 3 | 3 |
| V2 dense+rerank | 6/11 = 54.5% | 27.3-81.8 | 3 | 2 |
| V3 router+hybrid | 6/11 = 54.5% | 27.3-81.8 | 2 | 3 |
| V5 router+hybrid+rerank (no extraction) | 6/11 = 54.5% | 27.3-81.8 | 2 | 3 |
| V6 hybrid+rerank, no router | 7/11 = 63.6% | 36.4-90.9 | 1 | 3 |
| V4 complete | 6/11 = 54.5% | 27.3-81.8 | 3 | 2 |

## type open  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 10/15 = 66.7% | 40.0-86.7 | 3 | 2 |
| V2 dense+rerank | 11/15 = 73.3% | 53.3-93.3 | 2 | 2 |
| V3 router+hybrid | 10/15 = 66.7% | 40.0-86.7 | 2 | 3 |
| V5 router+hybrid+rerank (no extraction) | 10/15 = 66.7% | 40.0-86.7 | 1 | 4 |
| V6 hybrid+rerank, no router | 11/15 = 73.3% | 46.7-93.3 | 0 | 4 |
| V4 complete | 9/15 = 60.0% | 33.3-86.7 | 1 | 5 |

## type aggregate  (n=4)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 0/4 = 0.0% | 0.0-0.0 | 1 | 3 |
| V2 dense+rerank | 0/4 = 0.0% | 0.0-0.0 | 0 | 4 |
| V3 router+hybrid | 0/4 = 0.0% | 0.0-0.0 | 0 | 4 |
| V5 router+hybrid+rerank (no extraction) | 0/4 = 0.0% | 0.0-0.0 | 0 | 4 |
| V6 hybrid+rerank, no router | 0/4 = 0.0% | 0.0-0.0 | 0 | 4 |
| V4 complete | 0/4 = 0.0% | 0.0-0.0 | 0 | 4 |

## type multistep  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| V2 dense+rerank | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| V3 router+hybrid | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| V5 router+hybrid+rerank (no extraction) | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 hybrid+rerank, no router | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4 complete | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |

## type superlative  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V2 dense+rerank | 0/2 = 0.0% | 0.0-0.0 | 1 | 1 |
| V3 router+hybrid | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V5 router+hybrid+rerank (no extraction) | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V6 hybrid+rerank, no router | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V4 complete | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |

## type comparison  (n=1)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V2 dense+rerank | 0/1 = 0.0% | 0.0-0.0 | 1 | 0 |
| V3 router+hybrid | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V5 router+hybrid+rerank (no extraction) | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 hybrid+rerank, no router | 0/1 = 0.0% | 0.0-0.0 | 1 | 0 |
| V4 complete | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |

## type locate  (n=3)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 dense baseline | 2/3 = 66.7% | 0.0-100.0 | 1 | 0 |
| V2 dense+rerank | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |
| V3 router+hybrid | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |
| V5 router+hybrid+rerank (no extraction) | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |
| V6 hybrid+rerank, no router | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |
| V4 complete | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |

## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)
- V4 - V1: +1.1 pp (95% CI -7.9 to +10.1); only-V4=8, only-V1=7, McNemar p=1
- V4 - V6: -1.1 pp (95% CI -9.0 to +6.7); only-V4=6, only-V6=7, McNemar p=1
- V4 - V5: +4.5 pp (95% CI -2.2 to +11.2); only-V4=7, only-V5=3, McNemar p=0.344
- V5 - V1: -3.4 pp (95% CI -13.5 to +5.6); only-V5=8, only-V1=11, McNemar p=0.648
- V5 - V6: -5.6 pp (95% CI -14.6 to +3.4); only-V5=6, only-V6=11, McNemar p=0.332
- V6 - V1: +2.2 pp (95% CI -6.7 to +11.2); only-V6=9, only-V1=7, McNemar p=0.804

## Latency per query (s): mean / median
- V1 dense baseline: 2.74 / 2.37
- V2 dense+rerank: 8.84 / 7.37
- V3 router+hybrid: 4.28 / 4.00
- V5 router+hybrid+rerank (no extraction): 15.08 / 11.85
- V6 hybrid+rerank, no router: 17.40 / 16.64
- V4 complete: 7.76 / 5.69

## V4 phase usage: {'hybrid_fallback_generation': 70, 'structured_table_date_cell': 4, 'structured_table_cell': 6, 'router_ood': 8, 'structured_document_requirements': 1}