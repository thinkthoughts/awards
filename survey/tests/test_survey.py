"""Regression checks for the survey: catalog parsing, reproducible data, registry rules.

Run from the repository root:  python3 -m unittest discover -s survey/tests -v
Standard library only. The prize catalog is read, never written.
"""

import copy
import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "survey"


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, SURVEY / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


parse_catalog = load("parse_catalog")
validate_registry = load("validate_registry")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class CatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        vols = sorted((ROOT / "problems").glob("catalog-*.md"))
        cls.records = [r for v in vols for r in parse_catalog.parse_volume(v)]
        cls.index = parse_catalog.read_index(ROOT / "problems" / "README.md")

    def test_catalog_validates(self):
        self.assertEqual(parse_catalog.validate(self.records, self.index), [])

    def test_ids_contiguous_and_match_index(self):
        ids = [r["id"] for r in self.records]
        self.assertEqual(ids, [f"JSP-{i:06d}" for i in range(1, len(self.index) + 1)])

    def test_validator_reports_a_missing_record(self):
        errors = parse_catalog.validate(self.records[:-1], self.index)
        self.assertTrue(any("missing" in e for e in errors))

    def test_provenance_matches_catalog_and_records(self):
        prov = json.loads((SURVEY / "data" / "provenance.json").read_text(encoding="utf-8"))
        for f in prov["catalog"]["files"]:
            self.assertEqual(sha256(ROOT / f["path"]), f["sha256"], f"catalog file changed: {f['path']}")
        self.assertEqual(sha256(SURVEY / "data" / "records.json"), prov["records"]["sha256"])
        self.assertEqual(prov["records"]["count"], len(self.records))

    def test_generated_data_is_reproducible(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            shutil.copytree(ROOT / "problems", tmp / "problems")
            shutil.copytree(SURVEY / "scripts", tmp / "survey" / "scripts")
            for script in ("parse_catalog.py", "classify_reach.py"):
                subprocess.run([sys.executable, "-I", f"survey/scripts/{script}"], cwd=tmp, check=True,
                               capture_output=True)
            for name in ("records.json", "reach.json", "reach.csv"):
                self.assertEqual((tmp / "survey/data" / name).read_bytes(),
                                 (SURVEY / "data" / name).read_bytes(), f"{name} differs on regeneration")

    def test_renumbering_crosswalk_accounts_for_every_record(self):
        for path in (SURVEY / "data").glob("renumbering-*.json"):
            d = json.loads(path.read_text(encoding="utf-8"))
            total = d["unchanged_ids"] + len(d["renumbered"]) + len(d["without_match_in_target"])
            self.assertEqual(total, d["from_count"], path.name)
            moved = {row["from"] for row in d["renumbered"]} | {row["from"] for row in d["without_match_in_target"]}
            for jsp in ("JSP-000009", "JSP-000029", "JSP-000041"):
                self.assertNotIn(jsp, moved)


class RegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reg = validate_registry.load_registry()
        cls.records = validate_registry.load_records()

    def errors_after(self, mutate):
        reg = copy.deepcopy(self.reg)
        mutate(reg)
        return validate_registry.validate(reg, self.records)

    def edge(self, reg, eid):
        return next(e for e in reg["edges"]["edges"] if e["id"] == eid)

    def assertRejected(self, mutate, fragment):
        errors = self.errors_after(mutate)
        self.assertTrue(any(fragment in e for e in errors), f"expected '{fragment}' in {errors}")

    def test_registry_is_valid(self):
        self.assertEqual(validate_registry.validate(self.reg, self.records), [])

    def test_every_lift_is_an_obligation_until_verified(self):
        for e in self.reg["edges"]["edges"]:
            if e["obligation"] == "recorded":
                continue
            verified = validate_registry.lift_state(e) == "Verified"
            self.assertEqual(e["obligation"] == "discharged", verified, e["id"])

    def test_discharging_an_unverified_lift_is_rejected(self):
        self.assertRejected(lambda r: self.edge(r, "LIFT-009-2").update(obligation="discharged"),
                            "discharged exactly when it is Verified")

    def test_conditional_implication_names_an_assumption(self):
        def drop(r):
            e = self.edge(r, "LIFT-009-4")
            e["hypotheses"] = [h for h in e["hypotheses"] if h["role"] != "assumption"]
        self.assertRejected(drop, "names at least one assumption")

    def test_direct_application_carries_no_assumption(self):
        def add(r):
            self.edge(r, "LIFT-041-3")["hypotheses"].append(
                {"id": "x", "statement": "an open conjecture", "role": "assumption", "status": "open-conjecture"})
        self.assertRejected(add, "side conditions only")

    def test_structural_analogy_transfers_no_conclusion(self):
        self.assertRejected(lambda r: self.edge(r, "EDGE-ANA-1").update(relation="implies"),
                            "transfers structure only")

    def test_candidate_cannot_be_verified(self):
        def promote(r):
            e = self.edge(r, "EDGE-CAND-1")
            e["state"] = {"mathematical": "candidate", "formalization": "compiled", "verification": "comparator-accepted"}
            e["obligation"] = "discharged"
        self.assertRejected(promote, "candidate relationship cannot be Verified")

    def test_catalog_block_must_match_records(self):
        def retitle(r):
            r["readings"]["readings"][1]["catalog"]["title"] = "Twin primes"
        self.assertRejected(retitle, "differs from records.json")

    def test_verification_needs_evidence(self):
        def strip(r):
            r["readings"]["readings"][0]["evidence"] = []
        self.assertRejected(strip, "needs evidence")

    def test_local_evidence_rejects_sorry(self):
        def taint(r):
            ev = r["evidence"]["evidence"][0]
            ev["axioms"]["Survey.Foundation.one_add_one"] = ["sorryAx"]
        self.assertRejected(taint, "outside the whitelist")

    def test_unknown_spec_and_unknown_field_are_rejected(self):
        self.assertRejected(lambda r: r["readings"]["readings"][2].update(spec="SPEC-missing"), "unknown spec")
        self.assertRejected(lambda r: r["objects"]["objects"][0].update(colour="blue"), "unexpected field")

    def test_states_stay_independent(self):
        self.assertRejected(lambda r: r["specs"]["specs"][0]["state"].update(verification="proved"), "is not one of")

    def test_kernel_evidence_hash_matches_lean_file(self):
        for ev in self.reg["evidence"]["evidence"]:
            if ev["kind"] == "upstream-record":
                continue
            for f in ev["files"]:
                self.assertEqual(sha256(ROOT / f["path"]), f["sha256"],
                                 f"{f['path']} changed since {ev['id']}; re-run its check")

    def test_kernel_check_alone_leaves_a_lift_open(self):
        for e in self.reg["edges"]["edges"]:
            if e["state"]["verification"] == "kernel-checked":
                self.assertEqual(validate_registry.lift_state(e), "Compiled", e["id"])
                self.assertEqual(e["obligation"], "open", e["id"])
        self.assertRejected(lambda r: self.edge(r, "LIFT-041-2").update(obligation="discharged"),
                            "discharged exactly when it is Verified")

    def test_bridge_package_pins_the_registered_commit(self):
        sources = {s["id"]: s for s in self.reg["sources"]["sources"]}
        lakefile = (SURVEY / "lean-bridges" / "lakefile.toml").read_text(encoding="utf-8")
        manifest = json.loads((SURVEY / "lean-bridges" / "lake-manifest.json").read_text(encoding="utf-8"))
        pin = sources["lean-bgp212-89b43fa"]["commit"]
        self.assertIn(f'rev = "{pin}"', lakefile)
        bgp = next(p for p in manifest["packages"] if p["name"] == "bgp212")
        self.assertEqual(bgp["rev"], pin)
        self.assertEqual(sources["lean-bgp212"]["commit"], "14ec5e0c77f9867d97fe394f135d61c349ddd0b1")
        toolchains = {(SURVEY / d / "lean-toolchain").read_text(encoding="utf-8").strip() for d in ("lean", "lean-bridges")}
        self.assertEqual(toolchains, {sources["lean-bgp212-89b43fa"]["toolchain"]})

    def test_foundation_package_stays_core_only(self):
        lakefile = (SURVEY / "lean" / "lakefile.toml").read_text(encoding="utf-8")
        manifest = json.loads((SURVEY / "lean" / "lake-manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("[[require]]", lakefile)
        self.assertEqual(manifest["packages"], [])


if __name__ == "__main__":
    unittest.main()
