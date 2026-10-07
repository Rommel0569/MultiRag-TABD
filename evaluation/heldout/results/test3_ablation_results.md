# Held-out evaluation (n=60), deterministic gold-key scoring
bank: test3/test3_bank.json

## ALL  (n=60)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |
| no_structured | 42/60 = 70.0% | 58.3-81.7 | 5 | 13 |
| no_evidence | 44/60 = 73.3% | 61.7-83.3 | 7 | 9 |
| no_verbalizer | 44/60 = 73.3% | 61.7-83.3 | 3 | 13 |
| terse_style | 46/60 = 76.7% | 65.0-86.7 | 6 | 8 |
| top5 | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |
| V1 | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |

## answerable in-domain  (n=60)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |
| no_structured | 42/60 = 70.0% | 58.3-81.7 | 5 | 13 |
| no_evidence | 44/60 = 73.3% | 61.7-83.3 | 7 | 9 |
| no_verbalizer | 44/60 = 73.3% | 61.7-83.3 | 3 | 13 |
| terse_style | 46/60 = 76.7% | 65.0-86.7 | 6 | 8 |
| top5 | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |
| V1 | 47/60 = 78.3% | 66.7-88.3 | 4 | 9 |

## novel phrasing (sim<0.75 to any dev question)  (n=50)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 39/50 = 78.0% | 66.0-88.0 | 4 | 7 |
| no_structured | 34/50 = 68.0% | 54.0-80.0 | 5 | 11 |
| no_evidence | 36/50 = 72.0% | 60.0-84.0 | 7 | 7 |
| no_verbalizer | 36/50 = 72.0% | 58.0-84.0 | 3 | 11 |
| terse_style | 37/50 = 74.0% | 62.0-86.0 | 6 | 7 |
| top5 | 38/50 = 76.0% | 64.0-88.0 | 4 | 8 |
| V1 | 38/50 = 76.0% | 64.0-88.0 | 3 | 9 |

## category CRONOGRAMA  (n=8)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| no_structured | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| no_evidence | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| no_verbalizer | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| terse_style | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| top5 | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |
| V1 | 8/8 = 100.0% | 100.0-100.0 | 0 | 0 |

## category VACANTES  (n=16)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 14/16 = 87.5% | 68.8-100.0 | 0 | 2 |
| no_structured | 12/16 = 75.0% | 56.2-93.8 | 1 | 3 |
| no_evidence | 14/16 = 87.5% | 68.8-100.0 | 0 | 2 |
| no_verbalizer | 14/16 = 87.5% | 68.8-100.0 | 0 | 2 |
| terse_style | 14/16 = 87.5% | 68.8-100.0 | 0 | 2 |
| top5 | 13/16 = 81.2% | 62.5-100.0 | 0 | 3 |
| V1 | 12/16 = 75.0% | 50.0-93.8 | 1 | 3 |

## category TEMARIO  (n=16)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 10/16 = 62.5% | 37.5-87.5 | 1 | 5 |
| no_structured | 9/16 = 56.2% | 31.2-81.2 | 1 | 6 |
| no_evidence | 9/16 = 56.2% | 31.2-81.2 | 3 | 4 |
| no_verbalizer | 9/16 = 56.2% | 31.2-81.2 | 1 | 6 |
| terse_style | 11/16 = 68.8% | 43.8-87.5 | 2 | 3 |
| top5 | 12/16 = 75.0% | 50.0-93.8 | 1 | 3 |
| V1 | 12/16 = 75.0% | 50.0-93.8 | 1 | 3 |

## category REGLAMENTO  (n=20)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 15/20 = 75.0% | 55.0-95.0 | 3 | 2 |
| no_structured | 13/20 = 65.0% | 45.0-85.0 | 3 | 4 |
| no_evidence | 13/20 = 65.0% | 45.0-85.0 | 4 | 3 |
| no_verbalizer | 13/20 = 65.0% | 45.0-85.0 | 2 | 5 |
| terse_style | 13/20 = 65.0% | 45.0-85.0 | 4 | 3 |
| top5 | 14/20 = 70.0% | 50.0-90.0 | 3 | 3 |
| V1 | 15/20 = 75.0% | 55.0-95.0 | 2 | 3 |

## type lookup  (n=19)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 19/19 = 100.0% | 100.0-100.0 | 0 | 0 |
| no_structured | 18/19 = 94.7% | 84.2-100.0 | 1 | 0 |
| no_evidence | 18/19 = 94.7% | 84.2-100.0 | 1 | 0 |
| no_verbalizer | 19/19 = 100.0% | 100.0-100.0 | 0 | 0 |
| terse_style | 19/19 = 100.0% | 100.0-100.0 | 0 | 0 |
| top5 | 18/19 = 94.7% | 84.2-100.0 | 0 | 1 |
| V1 | 16/19 = 84.2% | 68.4-100.0 | 0 | 3 |

## type list  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 11/15 = 73.3% | 53.3-93.3 | 1 | 3 |
| no_structured | 10/15 = 66.7% | 40.0-86.7 | 1 | 4 |
| no_evidence | 10/15 = 66.7% | 40.0-86.7 | 2 | 3 |
| no_verbalizer | 10/15 = 66.7% | 40.0-86.7 | 1 | 4 |
| terse_style | 12/15 = 80.0% | 60.0-100.0 | 2 | 1 |
| top5 | 12/15 = 80.0% | 60.0-100.0 | 1 | 2 |
| V1 | 13/15 = 86.7% | 66.7-100.0 | 1 | 1 |

## type open  (n=16)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 11/16 = 68.8% | 43.8-87.5 | 3 | 2 |
| no_structured | 9/16 = 56.2% | 31.2-81.2 | 3 | 4 |
| no_evidence | 10/16 = 62.5% | 37.5-87.5 | 3 | 3 |
| no_verbalizer | 9/16 = 56.2% | 31.2-81.2 | 2 | 5 |
| terse_style | 9/16 = 56.2% | 31.2-81.2 | 4 | 3 |
| top5 | 10/16 = 62.5% | 37.5-87.5 | 3 | 3 |
| V1 | 12/16 = 75.0% | 50.0-93.8 | 2 | 2 |

## type aggregate  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 5/6 = 83.3% | 50.0-100.0 | 0 | 1 |
| no_structured | 3/6 = 50.0% | 16.7-83.3 | 0 | 3 |
| no_evidence | 5/6 = 83.3% | 50.0-100.0 | 0 | 1 |
| no_verbalizer | 5/6 = 83.3% | 50.0-100.0 | 0 | 1 |
| terse_style | 4/6 = 66.7% | 33.3-100.0 | 0 | 2 |
| top5 | 5/6 = 83.3% | 50.0-100.0 | 0 | 1 |
| V1 | 2/6 = 33.3% | 0.0-66.7 | 1 | 3 |

## type multistep  (n=1)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| no_structured | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| no_evidence | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| no_verbalizer | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| terse_style | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| top5 | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| V1 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |

## type comparison  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| no_structured | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| no_evidence | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| no_verbalizer | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| terse_style | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| top5 | 1/2 = 50.0% | 0.0-100.0 | 0 | 1 |
| V1 | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |

## type locate  (n=1)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| V4d | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| no_structured | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| no_evidence | 0/1 = 0.0% | 0.0-0.0 | 1 | 0 |
| no_verbalizer | 0/1 = 0.0% | 0.0-0.0 | 0 | 1 |
| terse_style | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| top5 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| V1 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |

## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)
- no_structured - V4d: -8.3 pp (95% CI -16.7 to +0.0); only-no_structured=1, only-V4d=6, McNemar p=0.125
- no_evidence - V4d: -5.0 pp (95% CI -11.7 to +1.7); only-no_evidence=1, only-V4d=4, McNemar p=0.375
- no_verbalizer - V4d: -5.0 pp (95% CI -11.7 to +0.0); only-no_verbalizer=0, only-V4d=3, McNemar p=0.25
- terse_style - V4d: -1.7 pp (95% CI -8.3 to +5.0); only-terse_style=2, only-V4d=3, McNemar p=1
- top5 - V4d: +0.0 pp (95% CI -10.0 to +10.0); only-top5=4, only-V4d=4, McNemar p=1

## Latency per query (s): mean / median
- V4d: 46.93 / 48.48
- no_structured: 59.81 / 61.16
- no_evidence: 31.44 / 28.03
- no_verbalizer: 22.32 / 22.93
- terse_style: 41.01 / 40.22
- top5: 22.09 / 20.36
- V1: 21.91 / 20.51

## phase usage V4d {'hybrid_fallback_generation': 43, 'router_ood': 2, 'structured_column_cell': 7, 'structured_aggregate_sum_rows': 2, 'structured_aggregate_comparison': 1, 'structured_aggregate_sum_columns': 1, 'structured_aggregate_group_superlative': 1, 'structured_aggregate_group_sum': 1, 'structured_table_date_cell': 2}
## phase usage no_structured {'hybrid_fallback_generation': 58, 'router_ood': 2}
## phase usage no_evidence {'hybrid_fallback_generation': 39, 'router_ood': 6, 'structured_column_cell': 7, 'structured_aggregate_sum_rows': 2, 'structured_aggregate_comparison': 1, 'structured_aggregate_sum_columns': 1, 'structured_aggregate_group_superlative': 1, 'structured_aggregate_group_sum': 1, 'structured_table_date_cell': 2}
## phase usage no_verbalizer {'hybrid_fallback_generation': 43, 'router_ood': 2, 'structured_column_cell': 7, 'structured_aggregate_sum_rows': 2, 'structured_aggregate_comparison': 1, 'structured_aggregate_sum_columns': 1, 'structured_aggregate_group_superlative': 1, 'structured_aggregate_group_sum': 1, 'structured_table_date_cell': 2}
## phase usage terse_style {'hybrid_fallback_generation': 43, 'router_ood': 2, 'structured_column_cell': 7, 'structured_aggregate_sum_rows': 2, 'structured_aggregate_comparison': 1, 'structured_aggregate_sum_columns': 1, 'structured_aggregate_group_superlative': 1, 'structured_aggregate_group_sum': 1, 'structured_table_date_cell': 2}
## phase usage top5 {'hybrid_fallback_generation': 43, 'router_ood': 2, 'structured_column_cell': 7, 'structured_aggregate_sum_rows': 2, 'structured_aggregate_comparison': 1, 'structured_aggregate_sum_columns': 1, 'structured_aggregate_group_superlative': 1, 'structured_aggregate_group_sum': 1, 'structured_table_date_cell': 2}
## phase usage V1 {'dense_global_top5': 60}