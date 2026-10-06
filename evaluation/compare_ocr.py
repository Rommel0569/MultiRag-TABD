"""Compare a visual reference sample to prior audited OCR and a new run."""
import argparse
import json
from pathlib import Path
import sys
import re
import unicodedata
import numpy as np
from PIL import Image
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'app'))
from ocr_engine import _lines


def normalize(text):
    return re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', text).casefold()).strip()


def distance(a, b):
    previous = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(current[-1]+1, previous[j]+1, previous[j-1]+(ca != cb)))
        previous = current
    return previous[-1]


def region_text(data, bbox, width, height):
    chosen = []
    for d in data.get('detections', []):
        pts = np.asarray(d['bbox'])
        cx, cy = pts.mean(axis=0) / [width, height]
        if bbox[0] <= cx <= bbox[2] and bbox[1] <= cy <= bbox[3]:
            chosen.append((d['bbox'], d['text'], d['confidence']))
    return ' '.join(line['text'] for line in _lines(chosen))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--gold', type=Path, required=True)
    parser.add_argument('--previous', type=Path, required=True)
    args = parser.parse_args()
    gold = json.loads(args.gold.read_text(encoding='utf-8'))
    new, old, sizes = {}, {}, {}
    for page in range(1, 5):
        name = f'page_{page:03}'
        new[page] = json.loads((args.run/f'{name}.json').read_text(encoding='utf-8'))
        old[page] = json.loads((args.previous/f'{name}.json').read_text(encoding='utf-8'))
        sizes[page] = Image.open(args.run/f'{name}.png').size
    report = {'reference_note': gold['provenance'], 'cells': [], 'text_regions': []}
    for row in gold['numeric_rows']:
        page = row['page']; width, height = sizes[page]
        for i, (x, target) in enumerate(zip(row['xs'], row['values'])):
            point = np.asarray(new[page]['affine_matrix']) @ np.asarray([x*width, row['y']*height, 1])
            cells = [c for t in new[page]['tables'] for c in t['cells']
                     if c['bbox'][0] <= point[0] <= c['bbox'][2] and c['bbox'][1] <= point[1] <= c['bbox'][3]]
            value = re.sub(r'^[^\w]+|[^\w]+$', '', cells[0]['text']) if len(cells) == 1 else '<unmapped>'
            left = (row['xs'][i-1]+x)/2 if i else x-0.012
            right = (row['xs'][i+1]+x)/2 if i+1 < len(row['xs']) else x+0.012
            previous = region_text(old[page], [left,row['y']-0.005,right,row['y']+0.005],width,height)
            report['cells'].append({'page':page,'row':row['label'],'column_sample':i,
                'expected':target,'previous':previous,'new':value,'previous_exact':normalize(previous)==target,
                'new_exact':normalize(value)==target})
    for region in gold['text_regions']:
        page=region['page']; width,height=sizes[page]
        target=normalize(region['text'])
        item=dict(region)
        for label, collection in [('previous',old),('new',new)]:
            value=normalize(region_text(collection[page],region['bbox'],width,height))
            item[label]=value
            item[label+'_edit_distance']=distance(target,value)
        item['reference_characters']=len(target)
        report['text_regions'].append(item)
    report['numeric_cell_count']=len(report['cells'])
    report['numeric_exact']={label:sum(c[label+'_exact'] for c in report['cells'])/len(report['cells'])
                             for label in ['previous','new']}
    total=sum(r['reference_characters'] for r in report['text_regions'])
    report['sample_CER']={label:sum(r[label+'_edit_distance'] for r in report['text_regions'])/total
                         for label in ['previous','new']}
    (args.run/'comparison.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:report[k] for k in ['numeric_cell_count','numeric_exact','sample_CER']},indent=2))


if __name__=='__main__':
    main()
