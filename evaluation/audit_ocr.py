"""Reproducible OCR-only run; writes a new directory, never overwrites evidence."""
import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'app'))
from ocr_engine import extract_page


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    poppler_fallback = r'C:\Users\USER\Downloads\Release-26.02.0-0\poppler-26.02.0\Library\bin'
    parser.add_argument('--poppler', default=os.environ.get('CEPRUNSA_POPPLER_PATH') or
                        (poppler_fallback if Path(poppler_fallback).is_dir() else None))
    parser.add_argument('--threads', type=int, default=4)
    parser.add_argument('--engine', choices=['easyocr', 'textract'], default='easyocr')
    parser.add_argument('--region', default=os.environ.get('CEPRUNSA_TEXTRACT_REGION'))
    parser.add_argument('--profile', default=os.environ.get('CEPRUNSA_AWS_PROFILE'))
    parser.add_argument('--allow-paid-textract', action='store_true',
                        help='Required: authorizes sending page images to billable AWS Textract.')
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    from pdf2image import convert_from_path
    if args.engine == 'easyocr':
        import torch
        import easyocr
        from ocr_engine import extract_page
        torch.set_num_threads(args.threads)
        reader = easyocr.Reader(['es', 'en'], gpu=False, download_enabled=False)
    else:
        if not args.allow_paid_textract:
            raise SystemExit('Textract calls are paid and transmit page images externally. '
                             'Pass --allow-paid-textract only after approving that use.')
        from textract_engine import create_textract_client, extract_page
        reader = create_textract_client(args.region, args.profile)
    manifest = {'source': str(args.pdf.resolve()), 'sha256': hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
                'dpi': 300, 'threads': args.threads, 'python': sys.version,
                'engine': args.engine, 'region': args.region if args.engine == 'textract' else None,
                'aws_profile': args.profile if args.engine == 'textract' else None,
                'versions': {p: importlib.metadata.version(p) for p in
                             (['easyocr', 'torch', 'opencv-python'] if args.engine == 'easyocr'
                              else ['boto3', 'botocore'])},
                'engine_sha256': hashlib.sha256((ROOT/'app'/
                    ('ocr_engine.py' if args.engine == 'easyocr' else 'textract_engine.py')).read_bytes()).hexdigest(),
                'pages': []}
    pages = convert_from_path(args.pdf, dpi=300, poppler_path=args.poppler)
    for i, page in enumerate(pages, 1):
        page.save(args.output/f'page_{i:03}.png')
        start = time.perf_counter()
        result = extract_page(page, reader)
        result.update(source=args.pdf.name, page=i, elapsed_s=time.perf_counter()-start)
        (args.output/f'page_{i:03}.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        (args.output/f'page_{i:03}.txt').write_text(result['page_text'], encoding='utf-8')
        manifest['pages'].append({'page': i, 'elapsed_s': result['elapsed_s'], 'tables': len(result['tables']),
                                  'cells': sum(len(t['cells']) for t in result['tables'])})
        (args.output/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print(manifest['pages'][-1], flush=True)


if __name__ == '__main__':
    main()
