# Held-out evaluation (n=60), deterministic gold-key scoring
bank: test3/test3_bank.json

## ALL  (n=60)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |
| V1c | 45/60 = 75.0% | 63.3-85.0 | 3 | 12 |
| V4d | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |

## answerable in-domain  (n=60)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |
| V1c | 45/60 = 75.0% | 63.3-85.0 | 3 | 12 |
| V4d | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |

## novel phrasing (sim<0.75 to any dev question)  (n=50)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 38/50 = 76.0% | 64.0-88.0 | 3 | 9 |
| V1c | 36/50 = 72.0% | 58.0-84.0 | 2 | 12 |
| V4d | 39/50 = 78.0% | 66.0-88.0 | 4 | 7 |

## category CRONOGRAMA  (n=8)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| V1c | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4d | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |

## category VACANTES  (n=16)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 12/16 = 75.0% | 50.0-93.8 | 1 | 3 |
| V1c | 10/16 = 62.5% | 37.5-87.5 | 1 | 5 |
| V4d | 14/16 = 87.5% | 68.8-100.0 | 0 | 2 |

## category TEMARIO  (n=16)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 12/16 = 75.0% | 50.0-93.8 | 1 | 3 |
| V1c | 13/16 = 81.2% | 62.5-100.0 | 0 | 3 |
| V4d | 10/16 = 62.5% | 37.5-87.5 | 1 | 5 |

## category REGLAMENTO  (n=20)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 15/20 = 75.0% | 55.0-95.0 | 2 | 3 |
| V1c | 14/20 = 70.0% | 50.0-90.0 | 2 | 4 |
| V4d | 15/20 = 75.0% | 55.0-95.0 | 3 | 2 |

## type lookup  (n=19)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 16/19 = 84.2% | 68.4-100.0 | 0 | 3 |
| V1c | 15/19 = 78.9% | 57.9-94.7 | 0 | 4 |
| V4d | 19/19 = 100.0% | 100.0-100.0 | 0 | 0 |

## type list  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 13/15 = 86.7% | 66.7-100.0 | 1 | 1 |
| V1c | 14/15 = 93.3% | 80.0-100.0 | 0 | 1 |
| V4d | 11/15 = 73.3% | 53.3-93.3 | 1 | 3 |

## type open  (n=16)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 12/16 = 75.0% | 50.0-93.8 | 2 | 2 |
| V1c | 11/16 = 68.8% | 43.8-87.5 | 2 | 3 |
| V4d | 11/16 = 68.8% | 43.8-87.5 | 3 | 2 |

## type aggregate  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 2/6 = 33.3% | 0.0-66.7 | 1 | 3 |
| V1c | 1/6 = 16.7% | 0.0-50.0 | 1 | 4 |
| V4d | 5/6 = 83.3% | 50.0-100.0 | 0 | 1 |

## type multistep  (n=1)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V1c | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4d | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |

## type comparison  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| V1c | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4d | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |

## type locate  (n=1)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V1 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V1c | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V4d | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |

## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)
- V4d - V1: +0.0 pp (95% CI -13.3 to +13.3); only-V4d=8, only-V1=8, McNemar p=1
- V4d - V1c: +3.3 pp (95% CI -10.0 to +16.7); only-V4d=10, only-V1c=8, McNemar p=0.815

## Latency per query (s): mean / median
- V1: 21.91 / 20.51
- V1c: 23.64 / 22.54
- V4d: 46.93 / 48.48

## phase usage V1 {'dense_global_top5': 60}
## phase usage V1c {'dense_global_top5': 60}
## phase usage V4d {'hybrid_fallback_generation': 43, 'router_ood': 2, 'structured_column_cell': 7, 'structured_aggregate_sum_rows': 2, 'structured_aggregate_comparison': 1, 'structured_aggregate_sum_columns': 1, 'structured_aggregate_group_superlative': 1, 'structured_aggregate_group_sum': 1, 'structured_table_date_cell': 2}