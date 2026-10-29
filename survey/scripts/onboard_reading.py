#!/usr/bin/env python3
"""Onboard a source-backed L2 reading, without changing old RP identifiers.

Example (run from repository root):
 python3 survey/scripts/onboard_reading.py --kind repository --url https://github.com/example/repo \
   --external-id example/repo --title 'Example reading' --spec SPEC-nat-add-one \
   --statement 'An explicitly described mathematical reading' --dry-run

An existing L1 specification is required. Distinct claim-specific external IDs can share one URL. Onboarding does not imply a Lean proof.
"""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

from validate_registry import REGISTRY, SURVEY, load_registry, load_records, validate

CROSSWALK = SURVEY / 'data' / 'rpi-crosswalk.json'

def create(kind, url, external_id, title, spec, statement, dry_run=False, registry_dir=REGISTRY):
    parsed = urlparse(url)
    if parsed.scheme != 'https' or not parsed.netloc or parsed.username or parsed.password:
        raise ValueError('origin URL must be absolute HTTPS, without credentials')
    for name, val in [('external_id',external_id),('title',title),('statement',statement)]:
        if not val.strip():
            raise ValueError(f'{name} must not be blank')
    reg=load_registry(registry_dir)
    if spec not in {s['id'] for s in reg['specs']['specs']}:
        raise ValueError(f'unknown specification: {spec}; define the L1 specification before onboarding')
    readings=reg['readings']['readings']
    for r in readings:
        origin=r.get('origin',{})
        if origin.get('kind')==kind and origin.get('external_id')==external_id:
            raise ValueError(f'duplicate source reading: {r["id"]}')
    crosswalk=json.loads(CROSSWALK.read_text(encoding='utf-8'))['assignments']
    occupied={x['rpi'] for x in crosswalk}|{r.get('rpi') for r in readings}
    indices=[int(x[4:]) for x in occupied if isinstance(x,str) and re.fullmatch(r'RPI-[0-9]{6}',x)]
    index=max(indices,default=0)+1
    if index > 999999:
        raise ValueError('RPI namespace exhausted')
    rpi=f'RPI-{index:06d}'
    # Human-readable legacy-compatible identifier for existing edge tooling.
    rid='RP-'+rpi
    row={'id':rid,'rpi':rpi,'layer':'L2','kind':kind,'origin':{'kind':kind,'url':url,'external_id':external_id,'title':title},'source_review':'discovered','spec':spec,'parameters':{},'statement':{'math':statement},'leading_constraints':[],'excluded_generalizations':[],'state':{'mathematical':'open','formalization':'prose','verification':'unverified'},'notes':'Intake only: no Lean proof or validity claim. Update the reading and attach evidence separately.'}
    readings.append(row)
    errors=validate(reg,load_records())
    if errors:
        raise ValueError('registry validation failed: '+'; '.join(errors))
    if not dry_run:
        (registry_dir/'readings.json').write_text(json.dumps(reg['readings'],indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    return row

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--kind',required=True,choices=['arxiv','news','repository','other'])
    for field in ['url','external-id','title','spec','statement']:
        ap.add_argument('--'+field,required=True)
    ap.add_argument('--dry-run',action='store_true')
    a=ap.parse_args()
    try:
        print(json.dumps(create(a.kind,a.url,a.external_id,a.title,a.spec,a.statement,a.dry_run),indent=2,ensure_ascii=False))
    except ValueError as e:
        ap.error(str(e))
if __name__=='__main__':
    main()
