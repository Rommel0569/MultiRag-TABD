"""Versioned response cache; semantic reuse remains an explicit experimental mode."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unicodedata
from datetime import datetime, timezone
import numpy as np
from filelock import FileLock
from embeddings import embed_query, EMBED_MODEL_NAME, RERANKER_MODEL_NAME

ROOT = Path(__file__).resolve().parents[1]
_INDEX_DIR = Path(os.environ.get('CEPRUNSA_INDEX_DIR', str(ROOT/'data/index'))).expanduser()
INDEX_DIR = (_INDEX_DIR if _INDEX_DIR.is_absolute() else ROOT/_INDEX_DIR).resolve()
_CACHE_DIR = Path(os.environ.get('CEPRUNSA_CACHE_DIR', str(ROOT/'data/cache'))).expanduser()
CACHE_DIR = str((_CACHE_DIR if _CACHE_DIR.is_absolute() else ROOT/_CACHE_DIR).resolve())
CACHE_MODE = os.environ.get('CEPRUNSA_CACHE_MODE', 'semantic').strip().lower()
if CACHE_MODE not in {'exact', 'semantic', 'disabled'}:
    raise ValueError('CEPRUNSA_CACHE_MODE must be exact, semantic or disabled')
SHORTLIST_THRESHOLD, SHORTLIST_TOP_K, VERIFY_THRESHOLD = 0.80, 3, 0.50
signature = hashlib.sha256()
for path in sorted(INDEX_DIR.glob('*.json')):
    signature.update(path.name.encode())
    signature.update(path.read_bytes())
signature.update(json.dumps([EMBED_MODEL_NAME, RERANKER_MODEL_NAME, CACHE_MODE,
    os.environ.get('CEPRUNSA_GENERATOR_MODEL', 'llama3'),
    os.environ.get('CEPRUNSA_LLM_URL', 'http://localhost:11434/v1'),
    os.environ.get('CEPRUNSA_ROUTER_MODEL', 'llama3'),
    os.environ.get('CEPRUNSA_ROUTER_URL', 'http://localhost:11434/v1')]).encode())
for source_name in ('llm.py', 'router.py', 'retriever.py', 'pipeline.py', 'structured_answers.py'):
    source_path = Path(__file__).with_name(source_name)
    if source_path.exists():
        signature.update(source_name.encode())
        signature.update(source_path.read_bytes())
NAMESPACE = signature.hexdigest()
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = str(Path(CACHE_DIR)/f'semantic_cache_{NAMESPACE[:16]}.json')

def _load_cache():
    if Path(CACHE_FILE).exists():
        data = json.loads(Path(CACHE_FILE).read_text(encoding='utf-8'))
        if data.get('namespace') == NAMESPACE:
            return data
    return {'namespace': NAMESPACE, 'entries': [], 'lookups': 0, 'hits': 0}

def _save_cache(data):
    fd, temporary = tempfile.mkstemp(dir=CACHE_DIR, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(temporary, CACHE_FILE)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

def _normalize(query):
    return ' '.join(unicodedata.normalize('NFKC', query).casefold().split())

def search_cache(query):
    if CACHE_MODE == 'disabled':
        return None
    with FileLock(CACHE_FILE+'.lock'):
        data = _load_cache()
        data['lookups'] += 1
        matches = [(1.0, entry) for entry in data['entries']
                   if _normalize(entry['query']) == _normalize(query)]
        verification = 1.0
        if not matches and CACHE_MODE == 'semantic' and data['entries']:
            from embeddings import relevance_probs
            vector = embed_query(query)
            candidates = []
            for entry in data['entries']:
                cached = np.asarray(entry['vector'], dtype=np.float32)
                if cached.shape == vector.shape:
                    score = float(np.dot(vector, cached))
                    if score >= SHORTLIST_THRESHOLD:
                        candidates.append((score, entry))
            candidates.sort(key=lambda pair: pair[0], reverse=True)
            candidates = candidates[:SHORTLIST_TOP_K]
            if candidates:
                scores = relevance_probs([(query, entry['query']) for _, entry in candidates])
                i = int(np.argmax(scores))
                verification = float(scores[i])
                if verification >= VERIFY_THRESHOLD:
                    matches = [candidates[i]]
        if not matches:
            _save_cache(data)
            return None
        similarity, entry = matches[0]
        entry['hits'] += 1
        data['hits'] += 1
        _save_cache(data)
        return {**entry['response'], 'tokens_used': 0, 'cache_hit': True,
                'similarity': similarity, 'verification': verification,
                'original_query': entry['query'], 'category': entry['category']}

def add_to_cache(query, response, category):
    if CACHE_MODE == 'disabled' or not response.get('sources') or not response.get('answer'):
        return
    vector = embed_query(query).tolist() if CACHE_MODE == 'semantic' else []
    with FileLock(CACHE_FILE+'.lock'):
        data = _load_cache()
        data['entries'] = [entry for entry in data['entries']
                           if _normalize(entry['query']) != _normalize(query)]
        data['entries'].append({'query': query, 'vector': vector, 'response': response,
            'category': category, 'hits': 0, 'created_at': datetime.now(timezone.utc).isoformat()})
        _save_cache(data)

def get_cache_stats():
    with FileLock(CACHE_FILE+'.lock'):
        data = _load_cache()
    top = sorted(data['entries'], key=lambda e: e['hits'], reverse=True)[:5]
    return {'total_entries': len(data['entries']), 'total_hits': data['hits'],
            'total_queries': data['lookups'], 'hit_rate': data['hits']/max(data['lookups'], 1),
            'mode': CACHE_MODE, 'top_queries': [{k: e[k] for k in ['query', 'hits', 'category']} for e in top]}
