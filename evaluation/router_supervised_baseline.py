"""Router supervisado (SVM / Naive Bayes / LogReg+e5) vs router zero-shot Llama 3.
Entrena con el banco de 500; prueba (a) en las 30 consultas coloquiales originales (otra distribucion)
y (b) con CV agrupada por plantilla dentro del banco. Mide latencia por consulta. Costo: 0."""
import json, sys, time, re, collections
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import make_pipeline, make_union
from sklearn.svm import LinearSVC
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import accuracy_score, f1_score, recall_score, confusion_matrix
sys.stdout.reconfigure(encoding="utf-8")
bank=json.load(open("evaluation/evidence/ragas_500/inputs/queries_500_pdf_verified_ai_adjudicated.json",encoding="utf-8"))["consultas"]
orig=json.load(open("evaluation/queries.json",encoding="utf-8"))["consultas"]
print(list(orig[0].keys()))
catkey="categoria_correcta" if "categoria_correcta" in orig[0] else "category"
Xb=[c["query"] for c in bank]; yb=[c["category"] for c in bank]
Xo=[c["query"] for c in orig]; yo=[c[catkey] for c in orig]
print("solapamiento exacto banco/originales:", len(set(Xb)&set(Xo)))
LAB=["CRONOGRAMA","VACANTES","TEMARIO","REGLAMENTO","FUERA_DE_DOMINIO"]
def tfidf(): return make_union(TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,strip_accents="unicode",lowercase=True),
                               TfidfVectorizer(analyzer="char_wb",ngram_range=(2,5),sublinear_tf=True,strip_accents="unicode"))
models={"Linear SVM (TF-IDF)":lambda: make_pipeline(tfidf(),LinearSVC(C=1.0)),
        "Naive Bayes (TF-IDF)":lambda: make_pipeline(TfidfVectorizer(ngram_range=(1,2),sublinear_tf=True,strip_accents="unicode"),MultinomialNB(alpha=0.1))}
# plantilla = consulta con nombres propios/numeros removidos -> primeras 4 palabras
def tmpl(q): return " ".join(re.sub(r"[^\w\s]","",q.lower()).split()[:4])
groups=[tmpl(q) for q in Xb]; print("plantillas:",len(set(groups)))
res={}
for name,mk in models.items():
    m=mk().fit(Xb,yb); t=time.perf_counter(); p=m.predict(Xo); dt=(time.perf_counter()-t)/len(Xo)*1000
    # latencia individual
    ts=[]
    for q in Xo*5:
        t0=time.perf_counter(); m.predict([q]); ts.append(time.perf_counter()-t0)
    gk=GroupKFold(n_splits=5); cvp=np.empty(len(Xb),dtype=object)
    for tr,te in gk.split(Xb,yb,groups):
        cvp[te]=mk().fit([Xb[i] for i in tr],[yb[i] for i in tr]).predict([Xb[i] for i in te])
    res[name]=dict(acc30=accuracy_score(yo,p),recall_regl=recall_score(yo,p,labels=["REGLAMENTO"],average=None)[0],
        macroF1_30=f1_score(yo,p,labels=LAB,average="macro"),ms=float(np.mean(ts)*1000),
        cv_acc=accuracy_score(yb,cvp),cv_macroF1=f1_score(yb,cvp,labels=LAB,average="macro"),
        regl_cv=recall_score(yb,cvp,labels=["REGLAMENTO"],average=None)[0])
    print(name,json.dumps(res[name],indent=1)); print(confusion_matrix(yo,p,labels=LAB))
# e5 embeddings + LogReg
from sentence_transformers import SentenceTransformer
enc=SentenceTransformer("intfloat/multilingual-e5-base",local_files_only=True)
f=lambda L: enc.encode(["query: "+q for q in L],normalize_embeddings=True,batch_size=64)
Eb,Eo=f(Xb),f(Xo)
clf=LogisticRegression(max_iter=2000,C=10).fit(Eb,yb); p=clf.predict(Eo)
ts=[]
for q in Xo[:15]:
    t0=time.perf_counter(); clf.predict(f([q])); ts.append(time.perf_counter()-t0)
cvp=np.empty(len(Xb),dtype=object)
for tr,te in GroupKFold(5).split(Eb,yb,groups): cvp[te]=LogisticRegression(max_iter=2000,C=10).fit(Eb[tr],np.array(yb)[tr]).predict(Eb[te])
res["e5 + LogReg"]=dict(acc30=accuracy_score(yo,p),recall_regl=recall_score(yo,p,labels=["REGLAMENTO"],average=None)[0],
    macroF1_30=f1_score(yo,p,labels=LAB,average="macro"),ms=float(np.mean(ts)*1000),cv_acc=accuracy_score(yb,cvp),
    cv_macroF1=f1_score(yb,cvp,labels=LAB,average="macro"),regl_cv=recall_score(yb,cvp,labels=["REGLAMENTO"],average=None)[0])
print("e5",json.dumps(res["e5 + LogReg"],indent=1)); print(confusion_matrix(yo,p,labels=LAB))
json.dump(res,open("evaluation/router_supervised_results.json","w"),indent=1)
