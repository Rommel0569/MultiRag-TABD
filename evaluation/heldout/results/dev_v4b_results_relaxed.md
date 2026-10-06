# Held-out evaluation (n=89), deterministic gold-key scoring
bank: heldout_bank.json

## ALL  (n=89)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 57/89 = 64.0% | 53.9-74.2 | 14 | 18 |
| V6 | 60/89 = 67.4% | 57.3-77.5 | 5 | 24 |
| V4_old | 59/89 = 66.3% | 56.2-75.3 | 9 | 21 |
| V4b | 70/89 = 78.7% | 69.7-86.5 | 3 | 16 |

## answerable in-domain  (n=74)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 43/74 = 58.1% | 47.3-68.9 | 14 | 17 |
| V6 | 46/74 = 62.2% | 51.4-73.0 | 5 | 23 |
| V4_old | 44/74 = 59.5% | 48.6-70.3 | 9 | 21 |
| V4b | 55/74 = 74.3% | 63.5-83.8 | 3 | 16 |

## must abstain (unanswerable + OOD)  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 14/15 = 93.3% | 80.0-100.0 | 0 | 1 |
| V6 | 14/15 = 93.3% | 80.0-100.0 | 0 | 1 |
| V4_old | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4b | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |

## novel phrasing (sim<0.75 to any dev question)  (n=75)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 44/75 = 58.7% | 48.0-69.3 | 14 | 17 |
| V6 | 48/75 = 64.0% | 53.3-74.7 | 5 | 22 |
| V4_old | 47/75 = 62.7% | 52.0-73.3 | 8 | 20 |
| V4b | 56/75 = 74.7% | 65.3-84.0 | 3 | 16 |

## category CRONOGRAMA  (n=14)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 13/14 = 92.9% | 78.6-100.0 | 0 | 1 |
| V6 | 12/14 = 85.7% | 64.3-100.0 | 1 | 1 |
| V4_old | 11/14 = 78.6% | 57.1-100.0 | 1 | 2 |
| V4b | 12/14 = 85.7% | 64.3-100.0 | 0 | 2 |

## category VACANTES  (n=25)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 12/25 = 48.0% | 28.0-68.0 | 4 | 9 |
| V6 | 10/25 = 40.0% | 20.0-60.0 | 3 | 12 |
| V4_old | 14/25 = 56.0% | 36.0-76.0 | 3 | 8 |
| V4b | 23/25 = 92.0% | 80.0-100.0 | 0 | 2 |

## category TEMARIO  (n=20)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 8/20 = 40.0% | 20.0-60.0 | 7 | 5 |
| V6 | 12/20 = 60.0% | 40.0-80.0 | 1 | 7 |
| V4_old | 9/20 = 45.0% | 25.0-65.0 | 4 | 7 |
| V4b | 10/20 = 50.0% | 30.0-70.0 | 2 | 8 |

## category REGLAMENTO  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 10/15 = 66.7% | 40.0-86.7 | 3 | 2 |
| V6 | 12/15 = 80.0% | 60.0-100.0 | 0 | 3 |
| V4_old | 10/15 = 66.7% | 40.0-86.7 | 1 | 4 |
| V4b | 10/15 = 66.7% | 40.0-86.7 | 1 | 4 |

## category SIN_RESPUESTA  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4_old | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4b | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |

## category FUERA_DE_DOMINIO  (n=9)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 8/9 = 88.9% | 66.7-100.0 | 0 | 1 |
| V6 | 8/9 = 88.9% | 66.7-100.0 | 0 | 1 |
| V4_old | 9/9 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4b | 9/9 = 100.0% | 100.0-100.0 | 0 | 0 |

## type lookup  (n=36)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 24/36 = 66.7% | 50.0-80.6 | 6 | 6 |
| V6 | 23/36 = 63.9% | 47.2-77.8 | 3 | 10 |
| V4_old | 24/36 = 66.7% | 50.0-80.6 | 5 | 7 |
| V4b | 30/36 = 83.3% | 69.4-94.4 | 2 | 4 |

## type list  (n=11)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 5/11 = 45.5% | 18.2-72.7 | 3 | 3 |
| V6 | 7/11 = 63.6% | 36.4-90.9 | 1 | 3 |
| V4_old | 6/11 = 54.5% | 27.3-81.8 | 3 | 2 |
| V4b | 9/11 = 81.8% | 54.5-100.0 | 0 | 2 |

## type open  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 10/15 = 66.7% | 40.0-86.7 | 3 | 2 |
| V6 | 12/15 = 80.0% | 60.0-100.0 | 0 | 3 |
| V4_old | 10/15 = 66.7% | 40.0-86.7 | 1 | 4 |
| V4b | 10/15 = 66.7% | 40.0-86.7 | 1 | 4 |

## type aggregate  (n=4)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 0/4 = 0.0% | 0.0-0.0 | 1 | 3 |
| V6 | 0/4 = 0.0% | 0.0-0.0 | 0 | 4 |
| V4_old | 0/4 = 0.0% | 0.0-0.0 | 0 | 4 |
| V4b | 0/4 = 0.0% | 0.0-0.0 | 0 | 4 |

## type multistep  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| V6 | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4_old | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| V4b | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |

## type superlative  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V6 | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V4_old | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V4b | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |

## type comparison  (n=1)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 | 0/1 = 0.0% | 0.0-0.0 | 1 | 0 |
| V4_old | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4b | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |

## type locate  (n=3)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 2/3 = 66.7% | 0.0-100.0 | 1 | 0 |
| V6 | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |
| V4_old | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |
| V4b | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |

## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)
- V4b - V4_old: +12.4 pp (95% CI +5.6 to +19.1); only-V4b=11, only-V4_old=0, McNemar p=0.000977
- V4b - V1: +14.6 pp (95% CI +6.7 to +23.6); only-V4b=15, only-V1=2, McNemar p=0.00235
- V4b - V6: +11.2 pp (95% CI +2.2 to +21.3); only-V4b=15, only-V6=5, McNemar p=0.0414

## Latency per query (s): mean / median
- V1: 2.74 / 2.37
- V6: 17.40 / 16.64
- V4_old: 7.76 / 5.69
- V4b: 23.40 / 23.17

## phase usage V1 {'dense_global_top5': 89}
## phase usage V6 {'global_hybrid_rerank': 89}
## phase usage V4_old {'hybrid_fallback_generation': 70, 'structured_table_date_cell': 4, 'structured_table_cell': 6, 'router_ood': 8, 'structured_document_requirements': 1}
## phase usage V4b {'hybrid_fallback_generation': 54, 'structured_table_date_cell': 5, 'structured_column_cell': 10, 'structured_column_superlative': 2, 'structured_column_list': 2, 'structured_column_comparison': 1, 'structured_table_cell': 6, 'structured_column_sum': 1, 'structured_document_requirements': 1, 'router_ood': 7}