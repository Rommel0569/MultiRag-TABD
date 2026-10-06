# Held-out evaluation (n=138), deterministic gold-key scoring
bank: test2/test2_bank.json

## ALL  (n=138)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 105/138 = 76.1% | 68.8-83.3 | 10 | 23 |
| V6 | 106/138 = 76.8% | 69.6-83.3 | 13 | 19 |
| V4_old | 103/138 = 74.6% | 67.4-81.9 | 19 | 16 |
| V4b | 113/138 = 81.9% | 75.4-87.7 | 11 | 14 |

## answerable in-domain  (n=123)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 91/123 = 74.0% | 65.9-81.3 | 10 | 22 |
| V6 | 91/123 = 74.0% | 65.9-81.3 | 13 | 19 |
| V4_old | 88/123 = 71.5% | 63.4-79.7 | 19 | 16 |
| V4b | 98/123 = 79.7% | 72.4-86.2 | 11 | 14 |

## must abstain (unanswerable + OOD)  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 14/15 = 93.3% | 80.0-100.0 | 0 | 1 |
| V6 | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4_old | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4b | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |

## novel phrasing (sim<0.75 to any dev question)  (n=124)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 92/124 = 74.2% | 66.1-81.5 | 10 | 22 |
| V6 | 92/124 = 74.2% | 66.1-81.5 | 13 | 19 |
| V4_old | 90/124 = 72.6% | 64.5-79.8 | 18 | 16 |
| V4b | 99/124 = 79.8% | 72.6-86.3 | 11 | 14 |

## category CRONOGRAMA  (n=17)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 17/17 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 | 15/17 = 88.2% | 70.6-100.0 | 1 | 1 |
| V4_old | 15/17 = 88.2% | 70.6-100.0 | 1 | 1 |
| V4b | 17/17 = 100.0% | 100.0-100.0 | 0 | 0 |

## category VACANTES  (n=47)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 29/47 = 61.7% | 46.8-74.5 | 3 | 15 |
| V6 | 32/47 = 68.1% | 55.3-80.9 | 6 | 9 |
| V4_old | 35/47 = 74.5% | 61.7-87.2 | 4 | 8 |
| V4b | 39/47 = 83.0% | 72.3-93.6 | 1 | 7 |

## category TEMARIO  (n=30)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 25/30 = 83.3% | 70.0-96.7 | 1 | 4 |
| V6 | 23/30 = 76.7% | 60.0-90.0 | 0 | 7 |
| V4_old | 23/30 = 76.7% | 60.0-90.0 | 3 | 4 |
| V4b | 24/30 = 80.0% | 63.3-93.3 | 3 | 3 |

## category REGLAMENTO  (n=29)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 20/29 = 69.0% | 51.7-86.2 | 6 | 3 |
| V6 | 21/29 = 72.4% | 55.2-86.2 | 6 | 2 |
| V4_old | 15/29 = 51.7% | 34.5-69.0 | 11 | 3 |
| V4b | 18/29 = 62.1% | 44.8-79.3 | 7 | 4 |

## category SIN_RESPUESTA  (n=5)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 5/5 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 | 5/5 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4_old | 5/5 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4b | 5/5 = 100.0% | 100.0-100.0 | 0 | 0 |

## category FUERA_DE_DOMINIO  (n=10)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 9/10 = 90.0% | 70.0-100.0 | 0 | 1 |
| V6 | 10/10 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4_old | 10/10 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4b | 10/10 = 100.0% | 100.0-100.0 | 0 | 0 |

## type lookup  (n=57)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 45/57 = 78.9% | 68.4-89.5 | 3 | 9 |
| V6 | 45/57 = 78.9% | 68.4-89.5 | 7 | 5 |
| V4_old | 47/57 = 82.5% | 71.9-91.2 | 6 | 4 |
| V4b | 53/57 = 93.0% | 86.0-98.2 | 1 | 3 |

## type list  (n=34)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 27/34 = 79.4% | 64.7-91.2 | 1 | 6 |
| V6 | 25/34 = 73.5% | 58.8-88.2 | 2 | 7 |
| V4_old | 24/34 = 70.6% | 55.9-85.3 | 6 | 4 |
| V4b | 26/34 = 76.5% | 61.8-91.2 | 3 | 5 |

## type open  (n=19)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 14/19 = 73.7% | 52.6-94.7 | 4 | 1 |
| V6 | 15/19 = 78.9% | 57.9-94.7 | 3 | 1 |
| V4_old | 11/19 = 57.9% | 36.8-78.9 | 7 | 1 |
| V4b | 12/19 = 63.2% | 42.1-84.2 | 6 | 1 |

## type aggregate  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 1/6 = 16.7% | 0.0-50.0 | 1 | 4 |
| V6 | 4/6 = 66.7% | 33.3-100.0 | 0 | 2 |
| V4_old | 4/6 = 66.7% | 33.3-100.0 | 0 | 2 |
| V4b | 4/6 = 66.7% | 33.3-100.0 | 1 | 1 |

## type multistep  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| V4_old | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V4b | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |

## type superlative  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V6 | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V4_old | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |
| V4b | 0/2 = 0.0% | 0.0-0.0 | 0 | 2 |

## type comparison  (n=1)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V6 | 0/1 = 0.0% | 0.0-0.0 | 1 | 0 |
| V4_old | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4b | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |

## type locate  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 1/2 = 50.0% | 0.0-100.0 | 1 | 0 |
| V6 | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| V4_old | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| V4b | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |

## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)
- V4b - V4_old: +7.2 pp (95% CI +3.6 to +11.6); only-V4b=10, only-V4_old=0, McNemar p=0.00195
- V4b - V1: +5.8 pp (95% CI -0.7 to +12.3); only-V4b=15, only-V1=7, McNemar p=0.134
- V4b - V6: +5.1 pp (95% CI -0.7 to +10.9); only-V4b=13, only-V6=6, McNemar p=0.167
- V4_old - V1: -1.4 pp (95% CI -8.7 to +5.8); only-V4_old=13, only-V1=15, McNemar p=0.851
- V6 - V1: +0.7 pp (95% CI -6.5 to +8.0); only-V6=13, only-V1=12, McNemar p=1

## Latency per query (s): mean / median
- V1: 17.50 / 15.82
- V6: 36.56 / 21.48
- V4_old: 20.66 / 20.95
- V4b: 27.26 / 24.42

## phase usage V1 {'baseline_V1': 138}
## phase usage V6 {'baseline_V6': 138}
## phase usage V4_old {'structured_table_cell': 21, 'hybrid_fallback_generation': 98, 'structured_table_date_cell': 3, 'router_ood': 15, 'structured_article_extract': 1}
## phase usage V4b {'structured_table_cell': 22, 'structured_column_cell': 14, 'hybrid_fallback_generation': 82, 'structured_column_superlative': 1, 'structured_column_sum': 3, 'structured_table_date_cell': 5, 'router_ood': 10, 'structured_article_extract': 1}