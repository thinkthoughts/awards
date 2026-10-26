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

    def test_bridge_sources_are_sorry_free_and_all_audited(self):
        import re
        bridges = sorted((SURVEY / "lean-bridges" / "SurveyBridges").glob("*.lean"))
        script = (SURVEY / "scripts" / "check_bridges.sh").read_text(encoding="utf-8")
        audit = (SURVEY / "lean-bridges" / "Audit.lean").read_text(encoding="utf-8")
        listed = re.search(r"^MODULES=\((.*)\)$", script, re.M).group(1).split()
        self.assertEqual(sorted(listed), [f.stem for f in bridges])
        for f in bridges + sorted((SURVEY / "lean").rglob("*.lean")):
            if ".lake" in f.parts:
                continue
            self.assertIsNone(re.search(r"\b(sorry|admit|native_decide)\b", f.read_text(encoding="utf-8")), f)
        for f in bridges:
            self.assertIn(f"import SurveyBridges.{f.stem}", audit)

    def test_comparator_pairs_are_independent_and_exact(self):
        import re

        def statement(text, short):
            m = re.search(rf"theorem {re.escape(short)}\b(.*?):=", text, re.S)
            return " ".join(m.group(1).split()) if m else None

        bridges = SURVEY / "lean-bridges"
        lakefile = (bridges / "lakefile.toml").read_text(encoding="utf-8")
        self.assertIn('name = "SurveyChallenge"', lakefile)
        self.assertIn('name = "SurveySolution"', lakefile)
        self.assertIn('defaultTargets = ["SurveyBridges"]', lakefile)
        edges = {e["id"]: e for e in self.reg["edges"]["edges"]}
        configs = sorted((bridges / "Comparator").glob("*.json"))
        self.assertTrue(configs)
        for cfg_path in configs:
            cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
            self.assertEqual(sorted(cfg["permitted_axioms"]), sorted(["propext", "Quot.sound", "Classical.choice"]))
            self.assertFalse(cfg.get("definition_names"), "definition holes would weaken the comparison")
            chal = bridges / (cfg["challenge_module"].replace(".", "/") + ".lean")
            sol = bridges / (cfg["solution_module"].replace(".", "/") + ".lean")
            chal_text, sol_text = chal.read_text(encoding="utf-8"), sol.read_text(encoding="utf-8")
            chal_imports = re.findall(r"^import\s+(\S+)", chal_text, re.M)
            self.assertTrue(chal_imports and all(i.startswith("BGP212.") for i in chal_imports), chal)
            sol_imports = re.findall(r"^import\s+(\S+)", sol_text, re.M)
            self.assertIsNone(re.search(r"\b(sorry|admit|native_decide)\b", sol_text), sol)
            for name in cfg["theorem_names"]:
                short = name.rsplit(".", 1)[-1]
                chal_stmt = statement(chal_text, short)
                self.assertIsNotNone(chal_stmt, f"{name} missing from {chal}")
                proof_files = [bridges / (i.replace(".", "/") + ".lean") for i in sol_imports
                               if i.startswith("SurveyBridges.")]
                proof_stmts = [statement(f.read_text(encoding="utf-8"), short) for f in proof_files]
                self.assertIn(chal_stmt, proof_stmts, f"{name}: Challenge and Solution statements differ")
                edge = next(e for e in edges.values() if e["statement"].get("lean_name") == name)
                self.assertIn(short, edge["statement"]["lean"])
                for ev_id in edge.get("evidence", []):
                    ev = next(e for e in self.reg["evidence"]["evidence"] if e["id"] == ev_id)
                    for f in ev.get("files", []):
                        if any(str(pf).endswith(f["path"].split("survey/", 1)[1]) for pf in proof_files):
                            self.assertEqual(sha256(ROOT / f["path"]), f["sha256"])

    def test_only_isolated_comparator_acceptance_verifies(self):
        cmp_ev = {"id": "EV-TEST-CMP", "layer": "L4", "subjects": ["LIFT-041-2"], "kind": "comparator",
                  "isolation": "non-isolating", "declarations": ["Survey.PrimeBridges.h1Le_mono"],
                  "result": "Your solution is okay!", "axioms": {"Survey.PrimeBridges.h1Le_mono":
                  ["propext", "Classical.choice", "Quot.sound"]},
                  "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"], "sorry_free": True}

        def with_run(isolation, verification, obligation):
            def mutate(r):
                ev = dict(cmp_ev, isolation=isolation)
                r["evidence"]["evidence"].append(ev)
                e = self.edge(r, "LIFT-041-2")
                e["state"]["verification"] = verification
                e["evidence"] = e["evidence"] + ["EV-TEST-CMP"]
                e["obligation"] = obligation
            return mutate

        # non-isolated acceptance is recorded, stays Compiled, keeps the obligation open
        self.assertEqual(self.errors_after(with_run("non-isolating", "comparator-nonisolated", "open")), [])
        self.assertRejected(with_run("non-isolating", "comparator-nonisolated", "discharged"),
                            "discharged exactly when it is Verified")
        # a non-isolated run cannot be recorded as Verified
        self.assertRejected(with_run("non-isolating", "comparator-accepted", "discharged"),
                            "needs Comparator evidence run under Linux landrun isolation")
        # isolated acceptance verifies and discharges
        self.assertEqual(self.errors_after(with_run("landrun-linux", "comparator-accepted", "discharged")), [])
        # Comparator evidence must state its isolation
        def no_isolation(r):
            ev = dict(cmp_ev); ev.pop("isolation")
            r["evidence"]["evidence"].append(ev)
        self.assertRejected(no_isolation, "states its isolation")

    def test_nonisolating_runner_is_marked_and_detected(self):
        runner = (SURVEY / "scripts" / "landrun-noisolate.sh").read_text(encoding="utf-8")
        script = (SURVEY / "scripts" / "compare_bridges.sh").read_text(encoding="utf-8")
        self.assertEqual(runner.splitlines()[1], "# SURVEY-NONISOLATING-RUNNER")
        self.assertIn("grep -q 'SURVEY-NONISOLATING-RUNNER'", script)
        self.assertIn('echo "isolation: $ISOLATION"', script)
        out = subprocess.run([str(SURVEY / "scripts" / "landrun-noisolate.sh"), "--ro", "/", "--rwx", ".",
                              "--", sys.executable, "-c", "print('ran')"], capture_output=True, text=True, check=True)
        self.assertEqual(out.stdout.strip(), "ran")

    def test_subset_closure_is_typed(self):
        e = self.edge(self.reg, "LIFT-ADM-2")
        self.assertEqual(e["relation"], "closure")
        self.assertEqual((e["from"], e["to"]), ("OBJ-admissible-z", "OBJ-admissible-z"))
        self.assertEqual(e["closure"]["direction"], "downward")
        self.assertIn("K ⊆ H", e["closure"]["lean"])
        self.assertIn("hKH : K ⊆ H", [h.get("lean") for h in e["hypotheses"]])
        self.assertRejected(lambda r: self.edge(r, "LIFT-ADM-2").pop("closure"), "closure record go together")
        self.assertRejected(lambda r: self.edge(r, "LIFT-ADM-2").update(to="SPEC-admissible-pair"),
                            "relates a property to itself")
        self.assertRejected(lambda r: self.edge(r, "LIFT-ADM-3").update(closure=e["closure"]),
                            "closure record go together")

    def test_zmod_statements_match_lean_source(self):
        import re
        src = (SURVEY / "lean-bridges" / "SurveyBridges" / "AdmissibleZMod.lean").read_text(encoding="utf-8")
        norm = lambda s: " ".join(s.replace("BGP212.Gap.", "").split())
        specs = {s["id"]: s for s in self.reg["specs"]["specs"]}
        for sid in ("SPEC-admissible-omits-residue", "SPEC-admissible-card-lt"):
            stmt = specs[sid]["statement"]["lean"]
            name = specs[sid]["statement"]["lean_name"].rsplit(".", 1)[-1]
            decl = re.search(rf"theorem {name}\b.*?:=", src, re.S).group(0)[:-2]
            self.assertEqual(norm(decl), norm(stmt), sid)
        ri = (SURVEY / "lean-bridges" / "SurveyBridges" / "ResidueImage.lean").read_text(encoding="utf-8")
        self.assertIn("H.image (fun (h : ℤ) => (h : ZMod p))", ri)
        for e in ("LIFT-ADM-4", "LIFT-ADM-5"):
            edge = self.edge(self.reg, e)
            self.assertEqual(validate_registry.lift_state(edge), "Compiled", e)
            self.assertEqual(edge["obligation"], "open", e)

    def test_audit_hash_history_is_pinned_by_commit(self):
        ev = {v["id"]: v for v in self.reg["evidence"]["evidence"]}
        self.assertIn("at commit 58d810f (sha256 6dcef42dad00b7024424deff62d5fdcf61337f3e41c7c3f196064e33ebe66ed6)",
                      ev["EV-0007"]["notes"])
        self.assertIn("f34452cacba252276ed683231780ad34c4f15cfb24eaa8b00b254bc1ef0ffb78", ev["EV-0008"]["notes"])
        log = (ROOT / "survey/evidence/kernel/bridges-zmod-2.log").read_text(encoding="utf-8")
        self.assertIn("== Audit sha256 f34452cacba252276ed683231780ad34c4f15cfb24eaa8b00b254bc1ef0ffb78", log)

    def test_residue_nu_statements_match_lean_source(self):
        import re
        src = (SURVEY / "lean-bridges" / "SurveyBridges" / "ResidueNu.lean").read_text(encoding="utf-8")
        norm = lambda s: " ".join(s.replace("BGP212.Gap.", "").split())
        for eid in ("LIFT-ADM-6", "LIFT-ADM-7"):
            e = self.edge(self.reg, eid)
            name = e["statement"]["lean_name"].rsplit(".", 1)[-1]
            decl = re.search(rf"theorem {name}\b.*?:=", src, re.S).group(0)[:-2]
            self.assertEqual(norm(decl), norm(e["statement"]["lean"]), eid)
            self.assertEqual(validate_registry.lift_state(e), "Compiled", eid)
            self.assertEqual(e["obligation"], "open", eid)
        # the prime form keeps the requested signature
        self.assertIn("theorem residueImage_card_eq_nu\n    (p : ℕ) (hp : p.Prime) (H : Finset ℤ) :", src)
        # LIFT-ADM-1 keeps its upstream route and open bridge
        adm1 = self.edge(self.reg, "LIFT-ADM-1")
        self.assertEqual(adm1["state"]["formalization"], "specified")
        self.assertEqual([h["status"] for h in adm1["hypotheses"]], ["open"])

    def test_residue_nu_relations_are_typed(self):
        e6, e7 = self.edge(self.reg, "LIFT-ADM-6"), self.edge(self.reg, "LIFT-ADM-7")
        self.assertEqual(e6["relation"], "cardinality-equality")
        self.assertEqual(e6["count"]["lean"], "(residueImage p H).card = BGP212.MultiShift.nu p H")
        self.assertIn("p = 0 included", e6["count"]["moduli"])
        self.assertEqual(e7["relation"], "equivalent")
        self.assertEqual(e7["characterizes"]["object"], "OBJ-admissible-z")
        self.assertEqual(e7["characterizes"]["via"], ["LIFT-ADM-4", "LIFT-ADM-5", "LIFT-ADM-6"])
        self.assertRejected(lambda r: self.edge(r, "LIFT-ADM-6").pop("count"), "count record go together")
        self.assertRejected(lambda r: self.edge(r, "LIFT-ADM-7").update(relation="implies"),
                            "a characterization is a logical equivalence")
        self.assertRejected(lambda r: self.edge(r, "LIFT-ADM-7")["characterizes"].update(object="OBJ-prime-z"),
                            "neither endpoint")
        ev = {v["id"]: v for v in self.reg["evidence"]["evidence"]}
        self.assertIn("9cc05336370922aac8d862633b8d3f826879d0e140e3894619b4f34e8a807acd", ev["EV-0009"]["notes"])
        log = (ROOT / "survey/evidence/kernel/bridges-nu.log").read_text(encoding="utf-8")
        self.assertIn("== Audit sha256 9cc05336370922aac8d862633b8d3f826879d0e140e3894619b4f34e8a807acd", log)
        self.assertIn("f34452cacba252276ed683231780ad34c4f15cfb24eaa8b00b254bc1ef0ffb78", ev["EV-0008"]["notes"])

    def test_local_factor_statements_match_lean_source(self):
        import re
        src = (SURVEY / "lean-bridges" / "SurveyBridges" / "LocalFactor.lean").read_text(encoding="utf-8")
        norm = lambda s: " ".join(s.replace("BGP212.Gap.", "").split())
        for eid in ("LIFT-ADM-8", "LIFT-GDT-2", "LIFT-GDT-3", "LIFT-GDT-4"):
            e = self.edge(self.reg, eid)
            name = e["statement"]["lean_name"].rsplit(".", 1)[-1]
            decl = re.search(rf"theorem {name}\b.*?:=", src, re.S).group(0)[:-2]
            self.assertEqual(norm(decl), norm(e["statement"]["lean"]), eid)
            self.assertEqual(validate_registry.lift_state(e), "Compiled", eid)
            self.assertEqual(e["obligation"], "open", eid)
        # AdmissibleH (fixed class a) stays out of the AdmissibleZ / localCount statements
        for name in ("localCount_pos_iff", "localCount_pos_of_admissibleZ"):
            decl = re.search(rf"theorem {name}\b.*?:=", src, re.S).group(0)
            self.assertNotIn("AdmissibleH", decl)
        ev = {v["id"]: v for v in self.reg["evidence"]["evidence"]}
        self.assertIn("25a3d75acae92227f5f98128becfcb02ab4f221c888c3bb09bea2734308f02d8", ev["EV-0010"]["notes"])
        log = (ROOT / "survey/evidence/kernel/bridges-localfactor.log").read_text(encoding="utf-8")
        self.assertIn("== Audit sha256 25a3d75acae92227f5f98128becfcb02ab4f221c888c3bb09bea2734308f02d8", log)

    def test_single_shift_totient_matches_lean_source(self):
        import re
        src = (SURVEY / "lean-bridges" / "SurveyBridges" / "SingleShiftTotient.lean").read_text(encoding="utf-8")
        e = self.edge(self.reg, "LIFT-GDT-5")
        decl = re.search(r"theorem localCount_singleton_eq_totient\b.*?:=", src, re.S).group(0)[:-2]
        self.assertEqual(" ".join(decl.split()), " ".join(e["statement"]["lean"].split()))
        self.assertIn("hN : 0 < N", [h.get("lean") for h in e["hypotheses"]])
        self.assertIn("theorem localCount_singleton_at_zero", src)
        self.assertEqual(validate_registry.lift_state(e), "Compiled")
        self.assertEqual(e["obligation"], "open")
        # LIFT-GDT-4's totient side condition is discharged by LIFT-GDT-5 (EV-0011)
        g4 = self.edge(self.reg, "LIFT-GDT-4")
        tot = [h for h in g4["hypotheses"] if h["id"] == "totient"]
        self.assertEqual([h["status"] for h in tot], ["discharged"])
        self.assertIn("EV-0011", g4["evidence"])
        ev = {v["id"]: v for v in self.reg["evidence"]["evidence"]}
        self.assertIn("074c3fbaaea5587a852c73ebb7470f2d18beab47c08a94a2b01742e4cf0ad3de", ev["EV-0011"]["notes"])
        log = (ROOT / "survey/evidence/kernel/bridges-totient.log").read_text(encoding="utf-8")
        self.assertIn("== Audit sha256 074c3fbaaea5587a852c73ebb7470f2d18beab47c08a94a2b01742e4cf0ad3de", log)

    def test_foundation_package_stays_core_only(self):
        lakefile = (SURVEY / "lean" / "lakefile.toml").read_text(encoding="utf-8")
        manifest = json.loads((SURVEY / "lean" / "lake-manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("[[require]]", lakefile)
        self.assertEqual(manifest["packages"], [])


if __name__ == "__main__":
    unittest.main()
