"""Compare the UCI ARFF with the CSV mirror; retain traceable duplicate IDs."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import urllib.request
import zipfile
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
URL = 'https://archive.ics.uci.edu/static/public/266/seismic+bumps.zip'

def audit(source):
    payload = Path(source).read_bytes()
    lines = payload.decode('utf-8').splitlines()
    names, records, started = [], [], False
    for line in lines:
        line = line.strip()
        if line.lower().startswith('@attribute'):
            names.append(line.split()[1].strip("'\""))
        elif line.lower() == '@data': started = True
        elif started and line and not line.startswith('%'): records.append(line)
    original = pd.read_csv(io.StringIO('\n'.join(records)), names=names, skipinitialspace=True)
    mirror = pd.read_csv(ROOT / 'data/seismic-bumps.csv')
    for c in ('seismic','seismoacoustic','shift','ghazard'):
        original[c] = original[c].str.strip()
    duplicate = original.duplicated(keep='first')
    dedup = original.loc[~duplicate].reset_index(drop=True)
    if list(original.columns) != list(mirror.columns): raise ValueError('column mismatch')
    matched = bool((dedup == mirror).to_numpy().all()) if dedup.shape == mirror.shape else False
    if not matched: raise ValueError('mirror is not the order-preserving first-occurrence deduplication')
    mapping = pd.DataFrame({'mirror_row_0based':range(len(dedup)),
                            'uci_row_1based':original.index[~duplicate]+1})
    mapping.to_csv(ROOT/'results/source_row_mapping.csv',index=False)
    removed=[]
    for i,row in original.loc[duplicate].iterrows():
        first=original.index[(original==row).all(axis=1)][0]
        removed.append(dict(removed_uci_row_1based=int(i+1),kept_uci_row_1based=int(first+1),
                            **{k:(str(v) if k in ('seismic','seismoacoustic','shift','ghazard') else int(v)) for k,v in row.items()}))
    pd.DataFrame(removed).to_csv(ROOT/'results/source_duplicates.csv',index=False)
    result=dict(source_url=URL,mirror_url='https://raw.githubusercontent.com/datasets/seismic-bumps/main/data/seismic-bumps.csv',
                original_rows=len(original),mirror_rows=len(mirror),removed_rows=int(duplicate.sum()),
                original_positives=int(original['class'].sum()),removed_positives=int(original.loc[duplicate,'class'].sum()),
                order_preserving_dedup_matches=matched,arff_sha256=hashlib.sha256(payload).hexdigest(),
                mirror_sha256=hashlib.sha256((ROOT/'data/seismic-bumps.csv').read_bytes()).hexdigest())
    (ROOT/'results/source_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--source'); ap.add_argument('--proxy')
    args=ap.parse_args()
    if args.source: path=Path(args.source)
    else:
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({'https':args.proxy})) if args.proxy else urllib.request.build_opener()
        with opener.open(URL,timeout=40) as r: archive=zipfile.ZipFile(io.BytesIO(r.read()))
        path=ROOT/'data/original-seismic-bumps.arff'; path.write_bytes(archive.read('seismic-bumps.arff'))
    audit(path)
