"""Reanalyze saved per-query scores with validated one-to-one pairing."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import wilcoxon

METRICS = ['faithfulness', 'answer_relevancy', 'context_precision', 'context_recall']

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--csv',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    df=pd.read_csv(args.csv)
    if df['query'].duplicated().any(): raise ValueError('duplicate query rows')
    result={'input':str(args.csv),'rows':len(df),'metrics':{}}
    raw_p=[]
    for metric in METRICS:
        a=df[f'{metric}_multirag'].to_numpy(float); b=df[f'{metric}_baseline'].to_numpy(float)
        valid=np.isfinite(a)&np.isfinite(b); diff=a[valid]-b[valid]
        if not len(diff): raise ValueError(f'no valid pairs for {metric}')
        test=wilcoxon(a[valid],b[valid],zero_method='wilcox',alternative='two-sided',method='auto')
        ranks=pd.Series(np.abs(diff)).rank(method='average').to_numpy()
        wplus=float(ranks[diff>0].sum()); wminus=float(ranks[diff<0].sum())
        result['metrics'][metric]={'n_pairs':len(diff),'excluded':int(len(a)-len(diff)),
          'mean_baseline':float(np.mean(b[valid])),'mean_multirag':float(np.mean(a[valid])),
          'mean_paired_delta':float(np.mean(diff)),'median_paired_delta':float(np.median(diff)),
          'wilcoxon_W':float(test.statistic),'p_raw':float(test.pvalue),
          'rank_biserial_effect':(wplus-wminus)/(wplus+wminus) if wplus+wminus else 0.0,
          'note':'Wilcoxon paired signed-rank; two-sided; exact if SciPy auto permits, otherwise normal approximation.'}
        raw_p.append((metric,float(test.pvalue)))
    # Holm family-wise adjustment over the four predeclared quality metrics.
    ordered=sorted(raw_p,key=lambda item:item[1]); running=0.0; m=len(ordered)
    for rank,(metric,p) in enumerate(ordered):
        adjusted=min(1.0,(m-rank)*p); running=max(running,adjusted)
        result['metrics'][metric]['p_holm_4metrics']=running
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result['metrics'],indent=2))

if __name__=='__main__': main()
