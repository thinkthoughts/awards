"""RPI-1 regression suite. No Lean build required."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
SCRIPTS=ROOT/'survey/scripts'
import sys
sys.path.insert(0,str(SCRIPTS))
import onboard_reading
import validate_registry

class RPITests(unittest.TestCase):
    def test_dam_typed_edges_and_preserved_graph(self):
        reg=validate_registry.load_registry()
        ed={e['id']:e for e in reg['edges']['edges']}
        self.assertEqual(len(ed),36)
        self.assertEqual(ed['EDGE-DAM-001']['relation'],'proof-dependency')
        self.assertIn('LeanDAM.sum_cond_crossTalk_eq_zero',[u['name'] for u in ed['EDGE-DAM-001']['uses']])
        self.assertEqual(ed['EDGE-DAM-002']['relation'],'research-target')
        self.assertEqual(validate_registry.validate(reg,validate_registry.load_records()),[])

    def test_research_target_cannot_claim_proof(self):
        reg=copy.deepcopy(validate_registry.load_registry())
        target=next(e for e in reg['edges']['edges'] if e['id']=='EDGE-DAM-002')
        target['state']['verification']='comparator-accepted'
        target['obligation']='discharged'
        errors=validate_registry.validate(reg,validate_registry.load_records())
        self.assertTrue(any('research-target must remain' in e for e in errors),errors)

    def test_research_target_must_not_cite_theorems(self):
        reg=copy.deepcopy(validate_registry.load_registry())
        target=next(e for e in reg['edges']['edges'] if e['id']=='EDGE-DAM-002')
        target['uses']=[{'source':'lean-dense-associative-memory','name':'LeanDAM.not_a_proof','kind':'theorem','file':'LeanDAM/ExpectedGap.lean'}]
        errors=validate_registry.validate(reg,validate_registry.load_records())
        self.assertTrue(any('research-target cannot cite' in e for e in errors),errors)

    def test_proof_dependency_must_cite_theorem(self):
        reg=copy.deepcopy(validate_registry.load_registry())
        dep=next(e for e in reg['edges']['edges'] if e['id']=='EDGE-DAM-001')
        dep['uses']=[]
        errors=validate_registry.validate(reg,validate_registry.load_records())
        self.assertTrue(any('proof-dependency must cite' in e for e in errors),errors)

    def test_multiple_claims_same_repository_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            regdir = Path(tmp) / 'registry'
            regdir.mkdir()
            for layer in validate_registry.LAYERS:
                (regdir / f"{layer}.json").write_bytes((validate_registry.REGISTRY / f"{layer}.json").read_bytes())
            url = 'https://github.com/example/shared-research'
            a = onboard_reading.create('repository', url, 'example/shared-research#claim-a', 'First claim',
                       'SPEC-nat-add-one', 'First reading', registry_dir=regdir)
            b = onboard_reading.create('repository', url, 'example/shared-research#claim-b', 'Second claim',
                       'SPEC-nat-add-one', 'Second reading', registry_dir=regdir)
            self.assertNotEqual(a['rpi'], b['rpi'])
            with self.assertRaisesRegex(ValueError, 'duplicate source reading'):
                onboard_reading.create('repository', url, 'example/shared-research#claim-a', 'Duplicate',
                       'SPEC-nat-add-one', 'Duplicate reading', registry_dir=regdir)

    def test_baseline_registry_unchanged_and_valid(self):
        self.assertEqual(validate_registry.validate(validate_registry.load_registry(),validate_registry.load_records()),[])
    def test_unique_crosswalk(self):
        reg=validate_registry.load_registry()
        assignments=json.loads(onboard_reading.CROSSWALK.read_text())['assignments']
        self.assertEqual(set(x['reading_id'] for x in assignments),{r['id'] for r in reg['readings']['readings'] if not r.get('rpi')})
        self.assertEqual(len({x['rpi'] for x in assignments}),len(assignments))
    def make(self,directory,dry_run=False):
        return onboard_reading.create('repository','https://github.com/test/example','test/example','Sample','SPEC-nat-add-one','A candidate reading, not a proof',dry_run=dry_run,registry_dir=directory)
    def test_intake_and_duplicate(self):
        with tempfile.TemporaryDirectory() as d:
            dst=Path(d)
            for layer in validate_registry.LAYERS:
                (dst/f'{layer}.json').write_bytes((validate_registry.REGISTRY/f'{layer}.json').read_bytes())
            created=self.make(dst)
            self.assertRegex(created['rpi'],r'^RPI-\d{6}$')
            self.assertEqual(created['state']['verification'],'unverified')
            with self.assertRaisesRegex(ValueError,'duplicate source reading'):
                self.make(dst)
            reg=validate_registry.load_registry(dst)
            self.assertEqual(validate_registry.validate(reg,validate_registry.load_records()),[])
    def test_dry_run_does_not_modify(self):
        with tempfile.TemporaryDirectory() as d:
            dst=Path(d)
            for layer in validate_registry.LAYERS:
                (dst/f'{layer}.json').write_bytes((validate_registry.REGISTRY/f'{layer}.json').read_bytes())
            before=(dst/'readings.json').read_bytes()
            self.make(dst,dry_run=True)
            self.assertEqual(before,(dst/'readings.json').read_bytes())
    def test_unknown_spec_and_bad_url(self):
        with self.assertRaisesRegex(ValueError,'unknown specification'):
            onboard_reading.create('news','https://example.org/a','a','Title','SPEC-missing','Statement',True)
        with self.assertRaisesRegex(ValueError,'HTTPS'):
            onboard_reading.create('news','http://example.org/a','a','Title','SPEC-nat-add-one','Statement',True)
    def test_duplicate_rpi_rejected(self):
        reg=copy.deepcopy(validate_registry.load_registry())
        r=copy.deepcopy(reg['readings']['readings'][0]);r.update(id='RP-NEW',rpi='RPI-000001',origin={'kind':'foundational','url':'https://example.org','external_id':'new','title':'New'},source_review='discovered')
        reg['readings']['readings'].append(r)
        errors=validate_registry.validate(reg,validate_registry.load_records())
        self.assertTrue(any('duplicate rpi' in e for e in errors),errors)
if __name__=='__main__':unittest.main()
