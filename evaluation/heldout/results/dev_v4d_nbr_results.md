# Held-out evaluation (n=89), deterministic gold-key scoring
bank: heldout_bank.json

## ALL  (n=89)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 75/89 = 84.3% | 76.4-91.0 | 6 | 8 |
| Qwen_nbr | 77/89 = 86.5% | 78.7-93.3 | 3 | 9 |
| Llama_top5 | 75/89 = 84.3% | 76.4-91.0 | 5 | 9 |

## answerable in-domain  (n=74)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 60/74 = 81.1% | 71.6-89.2 | 6 | 8 |
| Qwen_nbr | 62/74 = 83.8% | 75.7-91.9 | 3 | 9 |
| Llama_top5 | 60/74 = 81.1% | 71.6-89.2 | 5 | 9 |

## must abstain (unanswerable + OOD)  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |
| Qwen_nbr | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |
| Llama_top5 | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |

## novel phrasing (sim<0.75 to any dev question)  (n=75)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 61/75 = 81.3% | 72.0-89.3 | 6 | 8 |
| Qwen_nbr | 63/75 = 84.0% | 76.0-92.0 | 3 | 9 |
| Llama_top5 | 61/75 = 81.3% | 72.0-89.3 | 5 | 9 |

## category CRONOGRAMA  (n=14)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 13/14 = 92.9% | 78.6-100.0 | 0 | 1 |
| Qwen_nbr | 13/14 = 92.9% | 78.6-100.0 | 0 | 1 |
| Llama_top5 | 13/14 = 92.9% | 78.6-100.0 | 0 | 1 |

## category VACANTES  (n=25)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 24/25 = 96.0% | 88.0-100.0 | 0 | 1 |
| Qwen_nbr | 24/25 = 96.0% | 88.0-100.0 | 0 | 1 |
| Llama_top5 | 25/25 = 100.0% | 100.0-100.0 | 0 | 0 |

## category TEMARIO  (n=20)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 11/20 = 55.0% | 35.0-75.0 | 5 | 4 |
| Qwen_nbr | 10/20 = 50.0% | 30.0-70.0 | 3 | 7 |
| Llama_top5 | 10/20 = 50.0% | 30.0-70.0 | 4 | 6 |

## category REGLAMENTO  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 12/15 = 80.0% | 60.0-100.0 | 1 | 2 |
| Qwen_nbr | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |
| Llama_top5 | 12/15 = 80.0% | 60.0-100.0 | 1 | 2 |

## category SIN_RESPUESTA  (n=6)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| Qwen_nbr | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |
| Llama_top5 | 6/6 = 100.0% | 100.0-100.0 | 0 | 0 |

## category FUERA_DE_DOMINIO  (n=9)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 9/9 = 100.0% | 100.0-100.0 | 0 | 0 |
| Qwen_nbr | 9/9 = 100.0% | 100.0-100.0 | 0 | 0 |
| Llama_top5 | 9/9 = 100.0% | 100.0-100.0 | 0 | 0 |

## type lookup  (n=36)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 32/36 = 88.9% | 77.8-97.2 | 3 | 1 |
| Qwen_nbr | 31/36 = 86.1% | 75.0-97.2 | 2 | 3 |
| Llama_top5 | 31/36 = 86.1% | 75.0-97.2 | 3 | 2 |

## type list  (n=11)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 9/11 = 81.8% | 54.5-100.0 | 0 | 2 |
| Qwen_nbr | 9/11 = 81.8% | 54.5-100.0 | 0 | 2 |
| Llama_top5 | 9/11 = 81.8% | 54.5-100.0 | 0 | 2 |

## type open  (n=15)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 12/15 = 80.0% | 60.0-100.0 | 1 | 2 |
| Qwen_nbr | 15/15 = 100.0% | 100.0-100.0 | 0 | 0 |
| Llama_top5 | 12/15 = 80.0% | 60.0-100.0 | 1 | 2 |

## type aggregate  (n=4)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 1/4 = 25.0% | 0.0-75.0 | 0 | 3 |
| Qwen_nbr | 1/4 = 25.0% | 0.0-75.0 | 0 | 3 |
| Llama_top5 | 1/4 = 25.0% | 0.0-75.0 | 1 | 2 |

## type multistep  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| Qwen_nbr | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| Llama_top5 | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |

## type superlative  (n=2)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| Qwen_nbr | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |
| Llama_top5 | 2/2 = 100.0% | 100.0-100.0 | 0 | 0 |

## type comparison  (n=1)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| Qwen_nbr | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |
| Llama_top5 | 1/1 = 100.0% | 100.0-100.0 | 0 | 0 |

## type locate  (n=3)
| system | correct | 95% CI | abstained (safe, incorrect) | wrong |
|---|---|---|---|---|
| Qwen_top5 | 1/3 = 33.3% | 0.0-100.0 | 2 | 0 |
| Qwen_nbr | 1/3 = 33.3% | 0.0-100.0 | 1 | 1 |
| Llama_top5 | 2/3 = 66.7% | 0.0-100.0 | 0 | 1 |

## Paired comparisons on ALL items (bootstrap 95% CI of accuracy difference; exact McNemar)
- Qwen_nbr - Qwen_top5: +2.2 pp (95% CI -2.2 to +6.7); only-Qwen_nbr=3, only-Qwen_top5=1, McNemar p=0.625

## Latency per query (s): mean / median
- Qwen_top5: 20.32 / 18.59
- Qwen_nbr: 31.45 / 31.89
- Llama_top5: 21.60 / 18.53

## phase usage Qwen_top5 {'hybrid_fallback_generation': 52, 'structured_table_date_cell': 4, 'structured_schedule_days': 1, 'structured_column_cell': 15, 'structured_column_superlative': 2, 'structured_aggregate_summary_row': 2, 'structured_column_list': 2, 'structured_column_comparison': 1, 'structured_column_sum': 1, 'router_ood': 9}
## phase usage Qwen_nbr {'hybrid_fallback_generation': 52, 'structured_table_date_cell': 4, 'structured_schedule_days': 1, 'structured_column_cell': 15, 'structured_column_superlative': 2, 'structured_aggregate_summary_row': 2, 'structured_column_list': 2, 'structured_column_comparison': 1, 'structured_column_sum': 1, 'router_ood': 9}
## phase usage Llama_top5 {'hybrid_fallback_generation': 54, 'structured_table_date_cell': 4, 'structured_schedule_days': 1, 'structured_column_cell': 15, 'structured_column_superlative': 2, 'structured_aggregate_summary_row': 2, 'structured_column_list': 2, 'structured_column_comparison': 1, 'structured_column_sum': 1, 'router_ood': 7}