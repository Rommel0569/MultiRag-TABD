"""Grouped 3-fold development comparison; paraphrases never cross fold boundaries."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.metrics import classification_report, accuracy_score


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    data=json.loads(Path(__file__).with_name('queries.json').read_text(encoding='utf-8'))['consultas']
    labels=np.asarray([r['categoria_correcta'] for r in data])
    result={'protocol':'3-fold stratified CV over original question IDs. Original and paraphrase stay together. No hyperparameter selection. Development estimate, not independent held-out validation.', 'seed':42,'models':{}}
    for name, classifier in [('linear_svm',LinearSVC(random_state=42)),('naive_bayes',MultinomialNB())]:
        predictions=[None]*len(data); latencies=[]; folds=[]
        for train,test in StratifiedKFold(3,shuffle=True,random_state=42).split(data,labels):
            model=make_pipeline(TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5)),classifier)
            texts=[data[i][key] for i in train for key in ['query','parafrasis']]
            ys=[labels[i] for i in train for _ in range(2)]
            model.fit(texts,ys)
            for i in test:
                start=time.perf_counter(); predictions[i]=model.predict([data[i]['query']])[0]
                latencies.append(time.perf_counter()-start)
            folds.append({'train_ids':[data[i]['id'] for i in train],'test_ids':[data[i]['id'] for i in test]})
        result['models'][name]={'accuracy':accuracy_score(labels,predictions),
            'report':classification_report(labels,predictions,output_dict=True,zero_division=0),
            'mean_inference_s':float(np.mean(latencies)),'predictions':predictions,'folds':folds}
    args.output.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print({k:{m:v[m] for m in ['accuracy','mean_inference_s']} for k,v in result['models'].items()})


if __name__=='__main__': main()
