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
        self.assertRejected(lambda r: self.edge(r, "LIFT-009-5").update(obligation="discharged"),
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

    def test_comparator_pairs_cover_the_admissibility_lifts(self):
        import re
        bridges = SURVEY / "lean-bridges"
        expected = {
            "h1le_mono.json": ("H1LeMono", "h1Le_mono", "LIFT-041-2", "H1LeMono"),
            "admissibleZ_subset.json": ("AdmissibleSubset", "admissibleZ_subset", "LIFT-ADM-2", "AdmissibleSubset"),
            "admissibleZ_pair_iff_even.json": ("AdmissiblePair", "admissibleZ_pair_iff_even", "LIFT-ADM-3", "AdmissiblePair"),
            "admissibleZ_iff_nu_lt.json": ("AdmissibleNu", "admissibleZ_iff_nu_lt", "LIFT-ADM-7", "ResidueNu"),
        }
        self.assertEqual(sorted(p.name for p in (bridges / "Comparator").glob("*.json")), sorted(expected))
        for cfg_name, (mod, thm, eid, proof_mod) in expected.items():
            cfg = json.loads((bridges / "Comparator" / cfg_name).read_text(encoding="utf-8"))
            self.assertEqual(cfg["challenge_module"], f"SurveyChallenge.{mod}")
            self.assertEqual(cfg["solution_module"], f"SurveySolution.{mod}")
            self.assertEqual(cfg["theorem_names"], [f"Survey.PrimeBridges.{thm}"])
            self.assertEqual(self.edge(self.reg, eid)["statement"]["lean_name"], f"Survey.PrimeBridges.{thm}")
            sol = (bridges / "SurveySolution" / f"{mod}.lean").read_text(encoding="utf-8")
            self.assertEqual(re.findall(r"^import\s+(\S+)", sol, re.M), [f"SurveyBridges.{proof_mod}"])
            # the Solution header pins the kernel-checked source by its current sha256
            proof_hash = sha256(bridges / "SurveyBridges" / f"{proof_mod}.lean")
            self.assertTrue(proof_hash in sol or proof_hash[:8] in sol, cfg_name)
            chal = (bridges / "SurveyChallenge" / f"{mod}.lean").read_text(encoding="utf-8")
            self.assertNotIn("SurveyBridges", re.sub(r"/-.*?-/", "", chal, flags=re.S))
        # non-isolated acceptance (EV-0012): Compiled, obligation open until isolated landrun acceptance
        ev12 = next(v for v in self.reg["evidence"]["evidence"] if v["id"] == "EV-0012")
        self.assertEqual(ev12["isolation"], "non-isolating")
        for path, h in ev12["comparator"]["configs"].items():
            self.assertEqual(sha256(ROOT / path), h, path)
        log = (ROOT / ev12["comparator"]["log"]).read_text(encoding="utf-8")
        self.assertEqual(log.count("Your solution is okay!"), 3)
        self.assertIn("comparator: all configs accepted (isolation: non-isolating)", log)
        # isolated acceptance (EV-0014, landrun-linux) verifies; the macOS record EV-0012 stays as history
        ev14 = next(v for v in self.reg["evidence"]["evidence"] if v["id"] == "EV-0014")
        self.assertEqual(ev14["isolation"], "landrun-linux")
        self.assertEqual(validate_registry.isolation_policy.audit_errors("landrun-linux", ev14["isolation_audit"]), [])
        log14 = (ROOT / ev14["comparator"]["log"]).read_text(encoding="utf-8")
        self.assertEqual(sha256(ROOT / ev14["comparator"]["log"]), "88be84d8c2b62ada42d9558b090295e39647eb337ccf08b46515d3663cf77096")
        for cfg in ("admissibleZ_subset.json", "admissibleZ_pair_iff_even.json", "admissibleZ_iff_nu_lt.json"):
            section = log14.split(f"== Comparator/{cfg} ")[1].split("\n== Comparator/")[0]
            self.assertEqual(section.count("Your solution is okay!"), 1, cfg)
        self.assertIn("isolation-audit: " + json.dumps(ev14["isolation_audit"], sort_keys=True), log14)
        for eid in ("LIFT-ADM-2", "LIFT-ADM-3", "LIFT-ADM-7"):
            e = self.edge(self.reg, eid)
            self.assertEqual(e["state"]["verification"], "comparator-accepted", eid)
            self.assertEqual(validate_registry.lift_state(e), "Verified", eid)
            self.assertEqual(e["obligation"], "discharged", eid)
            self.assertIn("EV-0012", e["evidence"])
            self.assertIn("EV-0014", e["evidence"])
        e = self.edge(self.reg, "LIFT-041-2")
        self.assertEqual((validate_registry.lift_state(e), e["obligation"]), ("Verified", "discharged"))
        ev13 = next(v for v in self.reg["evidence"]["evidence"] if v["id"] == "EV-0013")
        self.assertEqual(sha256(ROOT / ev13["comparator"]["log"]), "9bef502360610f10f85d995ac358415946ac98fbd96688e3a8e76327ac73b5e6")
        self.assertIn("isolation-audit: " + json.dumps(ev13["isolation_audit"], sort_keys=True),
                      (ROOT / ev13["comparator"]["log"]).read_text(encoding="utf-8"))

    def test_linux_runner_shares_builds_read_only(self):
        import os, re
        path = SURVEY / "scripts" / "compare_bridges_linux.sh"
        script = path.read_text(encoding="utf-8")
        self.assertTrue(os.access(path, os.X_OK))
        # exact pins for formal evidence
        self.assertIn("COMPARATOR_PIN=19e111e2141cf333c7daff0f64c5f24acc91dd2e", script)
        self.assertIn("LEAN4EXPORT_PIN=cacf989bd75f608700820f6afc595f32e7a99a4d", script)
        # no copies or hardlinks of builds: sources via git alternates, builds via symlink
        code = "\n".join(l for l in script.splitlines() if not l.lstrip().startswith("#"))
        self.assertNotRegex(code, r"--reflink|cp -c|cp -l|\bln (?!-s)|git clone|cp -R \"\$src")
        self.assertIn("objects/info/alternates", code)
        self.assertIn('ln -s "$src/.lake/build" "$dest/.lake/build"', code)
        self.assertIn("-links +1", code)
        self.assertIn("-newer", code)
        # Comparator's own landrun flags, probed before it runs
        cmp_main = "--best-effort --ro / --rw /dev -ldd -add-exec --rwx"
        self.assertIn('SANDBOX=(' + cmp_main + ' "$WORK/.lake")', code)
        for probe in ("ST_RDONLY", "AF_INET6", "syscall(444", "SURVEY-NONISOLATING-RUNNER"):
            self.assertIn(probe, code)
        self.assertIn('echo "isolation: $ISOLATION"', code)
        self.assertIn('echo "isolation-audit: $AUDIT"', code)
        self.assertIn('sha256 $(sha "$SCRIPT")', code)
        # it refuses the non-isolating runner (or non-Linux hosts) before touching anything
        out = subprocess.run(["bash", str(path), "--preflight", str(ROOT), str(ROOT)],
                             env=dict(os.environ, COMPARATOR_LANDRUN=str(SURVEY / "scripts" / "landrun-noisolate.sh")),
                             capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertRegex(out.stderr, r"Linux only|non-isolating runner")
        # the macOS script and its recorded hashes stay as they were
        self.assertEqual(sha256(SURVEY / "scripts" / "compare_bridges.sh"),
                         "4bde79bb936750c7ddb3d23b274d7ddfa80bb6cd7e1b4d59043e8d1e03f12553")

    def test_only_isolated_comparator_acceptance_verifies(self):
        cmp_ev = {"id": "EV-TEST-CMP", "layer": "L4", "subjects": ["LIFT-041-2"], "kind": "comparator",
                  "isolation": "non-isolating", "declarations": ["Survey.PrimeBridges.h1Le_mono"],
                  "result": "Your solution is okay!", "axioms": {"Survey.PrimeBridges.h1Le_mono":
                  ["propext", "Classical.choice", "Quot.sound"]},
                  "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"], "sorry_free": True}

        pol = validate_registry.isolation_policy
        linux_audit = {"kernel": "6.8.0", "landlock_abi": 4, "landrun_flags": "--best-effort --ro / --rw /dev -ldd -add-exec --rwx WORK/.lake",
                       "landlock_probes": {p: "denied" for p in pol.DENIED_PROBES} | {"write_work_lake": "allowed"},
                       "landrun_network_rules": "landrun TCP rules (Landlock ABI >= 4)", "readonly_mounts": ["/p"],
                       "sockets_denied": ["AF_UNIX", "AF_INET", "AF_INET6"], "systemd_unit": "u",
                       "landrun_revision": pol.LANDRUN_PIN, "landrun_modified": False, "go_landlock": pol.GO_LANDLOCK_PIN}

        def with_run(isolation, verification, obligation):
            def mutate(r):
                ev = dict(cmp_ev, isolation=isolation)
                if isolation == "landrun-linux":
                    ev["isolation_audit"] = linux_audit
                r["evidence"]["evidence"].append(ev)
                e = self.edge(r, "LIFT-041-2")
                e["state"]["verification"] = verification
                # only the test record: the recorded Linux run (EV-0013) is set aside
                e["evidence"] = [x for x in e["evidence"] if x != "EV-0013"] + ["EV-TEST-CMP"]
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
        # LIFT-ADM-6 is kernel-checked (Compiled); LIFT-ADM-7 is Verified by EV-0014
        self.assertEqual(validate_registry.lift_state(self.edge(self.reg, "LIFT-ADM-6")), "Compiled")
        self.assertEqual(self.edge(self.reg, "LIFT-ADM-6")["obligation"], "open")
        self.assertEqual(validate_registry.lift_state(self.edge(self.reg, "LIFT-ADM-7")), "Verified")
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

    @unittest.skipUnless(sys.platform.startswith("linux"), "the Linux runner checks out workspaces on Linux only")
    def test_linux_runner_checks_out_source_only_dependencies(self):
        import os
        g = ["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false",
             "-c", "init.defaultBranch=main"]
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)

            def repo(d, files, url):
                d.mkdir(parents=True, exist_ok=True)
                for name, text in files.items():
                    (d / name).parent.mkdir(parents=True, exist_ok=True)
                    (d / name).write_text(text)
                subprocess.run(g + ["init", "-q", str(d)], check=True)
                subprocess.run(g + ["-C", str(d), "add", "-A"], check=True)
                subprocess.run(g + ["-C", str(d), "commit", "-qm", "c"], check=True)
                subprocess.run(g + ["-C", str(d), "remote", "add", "origin", url], check=True)
                return subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], check=True,
                                      capture_output=True, text=True).stdout.strip()

            prov = tmp / "prov"
            urls = {"mathlib": "https://github.com/leanprover-community/mathlib4", "Cli": "https://github.com/leanprover/lean4-cli"}
            revs = {n: repo(prov / ".lake/packages" / n, {"README": n, ".gitignore": "/.lake\n"}, u) for n, u in urls.items()}
            olean = prov / ".lake/packages/mathlib/.lake/build/lib/lean/Mathlib/Foo.olean"
            olean.parent.mkdir(parents=True); olean.write_text("olean")
            entry = lambda n, rev, url: {"url": url, "type": "git", "rev": rev, "name": n, "configFile": "lakefile.toml",
                                         "manifestFile": "lake-manifest.json", "inputRev": rev, "inherited": True,
                                         "scope": "", "subDir": None}
            deps = [entry(n, revs[n], urls[n]) for n in urls]
            tc = "leanprover/lean4:v4.34.0-rc2\n"
            pin = repo(prov, {"lean-toolchain": tc, ".gitignore": "/.lake\n", "BGP212/Gap.lean": "-- gap\n",
                              "lake-manifest.json": json.dumps({"version": "1.2.0", "packages": deps})},
                       "https://github.com/thinkthoughts/lean-bgp212")
            lb = tmp / "survey/lean-bridges"
            for sub in ("SurveyBridges", "SurveyChallenge", "SurveySolution", "Comparator"):
                (lb / sub).mkdir(parents=True)
            (tmp / "survey/scripts").mkdir(parents=True)
            shutil.copy2(SURVEY / "scripts/compare_bridges_linux.sh", tmp / "survey/scripts/")
            (lb / "lakefile.toml").write_text(f'[[require]]\nname = "bgp212"\nrev = "{pin}"\n')
            (lb / "lake-manifest.json").write_text(json.dumps({"version": "1.2.0", "packages":
                [entry("bgp212", pin, "https://github.com/thinkthoughts/lean-bgp212")] + deps}))
            (lb / "lean-toolchain").write_text(tc)
            (lb / "SurveyBridges.lean").write_text("import SurveyBridges.A\n")
            (lb / "SurveyBridges/A.lean").write_text("import BGP212.Gap\nimport Mathlib.Foo\ntheorem a : True := trivial\n")
            (lb / "SurveyChallenge/A.lean").write_text("import BGP212.Gap\ntheorem a : True := sorry\n")
            (lb / "SurveySolution/A.lean").write_text("import SurveyBridges.A\n")
            (lb / "Comparator/a.json").write_text(json.dumps({"challenge_module": "SurveyChallenge.A",
                "solution_module": "SurveySolution.A", "theorem_names": ["a"],
                "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"]}))
            (tmp / "wb").mkdir()
            env = dict(os.environ, COMPARE_WORKDIR_BASE=str(tmp / "wb"), KEEP_WORK="1", COMPARE_PLAN_SKIP_COMPARATOR="1")
            run = lambda: subprocess.run(["bash", str(tmp / "survey/scripts/compare_bridges_linux.sh"), "--plan",
                                          str(prov), str(tmp)], env=env, capture_output=True, text=True)
            out = run()
            self.assertEqual(out.returncode, 0, out.stderr)
            self.assertIn("dependency Cli " + revs["Cli"], out.stdout)
            self.assertIn("source-only checkout; any build happens in WORK/.lake", out.stdout)
            self.assertIn("shared read-only build " + str(prov / ".lake/packages/mathlib/.lake/build"), out.stdout)
            work = next((tmp / "wb").iterdir())
            cli, ml = work / ".lake/packages/Cli", work / ".lake/packages/mathlib"
            self.assertFalse((cli / ".lake/build").exists())                    # nothing shared for Cli
            self.assertTrue((ml / ".lake/build").is_symlink())                  # Mathlib shared read-only
            self.assertEqual(os.readlink(ml / ".lake/build"), str(prov / ".lake/packages/mathlib/.lake/build"))
            for n in urls:                                                      # exact revisions, clean trees
                d = work / ".lake/packages" / n
                head = subprocess.run(["git", "-C", str(d), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
                self.assertEqual(head, revs[n])
                self.assertEqual(subprocess.run(["git", "-C", str(d), "status", "--porcelain", "--untracked-files=no"],
                                                capture_output=True, text=True).stdout, "")
            shutil.rmtree(work)
            # revision and clean-tree checks still apply to source-only packages
            subprocess.run(g + ["-C", str(prov / ".lake/packages/Cli"), "commit", "-q", "--allow-empty", "-m", "drift"], check=True)
            out = run()
            self.assertNotEqual(out.returncode, 0)
            self.assertIn("provider Cli is at", out.stderr)
            subprocess.run(["git", "-C", str(prov / ".lake/packages/Cli"), "reset", "-q", "--hard", "HEAD~1"], check=True)
            (prov / ".lake/packages/Cli/README").write_text("changed")
            out = run()
            self.assertIn("provider Cli has modified tracked files", out.stderr)
            # Mathlib itself is never source-only
            subprocess.run(["git", "-C", str(prov / ".lake/packages/Cli"), "checkout", "-q", "README"], check=True)
            shutil.rmtree(prov / ".lake/packages/mathlib/.lake")
            out = run()
            self.assertIn("provider mathlib has no build", out.stderr)

    @unittest.skipUnless(sys.platform.startswith("linux"), "ELF launcher check runs on Linux")
    def test_linux_runner_sandboxes_the_toolchain_lake_not_the_elan_proxy(self):
        import os, re, stat
        script = (SURVEY / "scripts/compare_bridges_linux.sh").read_text(encoding="utf-8")
        # both sandboxed Lake entry points start the toolchain lake through TOOLCHAIN_PATH
        self.assertIn('BOX=(env PATH="$TOOLCHAIN_PATH" "$LANDRUN" "${SANDBOX[@]}" --rox "$LEAN_PREFIX" --rox "$GIT_BIN" --env PATH --env HOME --)', script)
        self.assertRegex(script, r'env PATH="\$TOOLCHAIN_PATH" LEAN_PATH="\$LEAN_PATH_WS" COMPARATOR_LANDRUN="\$LANDRUN" \\\n\s+COMPARATOR_LEAN4EXPORT="\$COMPARATOR_LEAN4EXPORT" "\$COMPARATOR_BIN" "\$rel"')
        self.assertLess(script.index("# <<< toolchain-lake"), script.index('ENV_OUT="$("${BOX[@]}" lake env)"'))
        self.assertIn('SANDBOX=(--best-effort --ro / --rw /dev -ldd -add-exec --rwx "$WORK/.lake")', script)   # grants unchanged
        block = script[script.index("# >>> toolchain-lake"):script.index("# <<< toolchain-lake")]
        real = Path(os.path.realpath(sys.executable))          # a dynamically linked ELF that prints a version
        version = subprocess.run([str(real), "--version"], capture_output=True, text=True).stdout.split()[-1]

        def check(make_lake, prefix_name=None):
            with tempfile.TemporaryDirectory() as tmp:
                tc = f"leanprover/lean4:v{version}"
                prefix = Path(tmp) / (prefix_name or f"leanprover--lean4---v{version}")
                (prefix / "bin").mkdir(parents=True)
                make_lake(prefix / "bin" / "lake")
                harness = ('fail() { echo "FAIL: $*" >&2; exit 1; }\n'
                           f'LEAN_PREFIX="{prefix}"; TOOLCHAIN="{tc}"\n' + block + 'echo OK "$TOOLCHAIN_PATH"\n')
                return subprocess.run(["bash", "-c", harness], capture_output=True, text=True)

        def script_lake(p):
            p.write_text("#!/bin/sh\necho Lake\n"); p.chmod(0o755)

        def static_lake(p):      # ELF without PT_INTERP, as elan's static (musl) proxy
            p.write_bytes(b"\x7fELF\x02\x01\x01" + bytes(57)); p.chmod(0o755)

        ok = check(lambda p: p.symlink_to(real))
        self.assertEqual(ok.returncode, 0, ok.stderr)
        self.assertTrue(ok.stdout.startswith("OK "))
        self.assertIn("not a dynamically linked ELF", check(script_lake).stderr)
        self.assertIn("not a dynamically linked ELF", check(static_lake).stderr)
        self.assertIn("no toolchain lake", check(lambda p: None).stderr)
        self.assertIn("not the elan toolchain directory", check(lambda p: p.symlink_to(real), "other").stderr)

    def test_fs_systemd_isolation_is_audited(self):
        pol = validate_registry.isolation_policy
        audit = {"kernel": "6.1.0", "landlock_abi": 2, "landrun_flags": "--best-effort --ro / --rw /dev -ldd -add-exec --rwx WORK/.lake",
                 "landlock_probes": {"read_outside_grants": "denied", "write_outside_work_lake": "denied",
                                     "write_through_shared_build_symlinks": "denied", "write_work_lake": "allowed"},
                 "landrun_network_rules": "dropped by --best-effort (Landlock ABI < 4)",
                 "readonly_mounts": ["/home/u/lean-bgp212"], "sockets_denied": ["AF_UNIX", "AF_INET", "AF_INET6"],
                 "systemd_unit": "0123abcd", "landrun_revision": pol.LANDRUN_PIN, "landrun_modified": False,
                 "go_landlock": pol.GO_LANDLOCK_PIN}
        base = {"id": "EV-TEST-FS", "layer": "L4", "subjects": ["LIFT-041-2"], "kind": "comparator",
                "isolation": "landrun-fs-systemd", "declarations": ["Survey.PrimeBridges.h1Le_mono"],
                "result": "Your solution is okay!", "axioms": {"Survey.PrimeBridges.h1Le_mono":
                ["propext", "Classical.choice", "Quot.sound"]},
                "permitted_axioms": ["propext", "Quot.sound", "Classical.choice"], "sorry_free": True}

        def verify(ev):
            def mutate(r):
                r["evidence"]["evidence"].append(ev)
                e = self.edge(r, "LIFT-041-2")
                e["state"]["verification"] = "comparator-accepted"
                e["evidence"] = e["evidence"] + [ev["id"]]
                e["obligation"] = "discharged"
            return mutate

        def with_audit(**changes):
            return dict(base, isolation_audit=dict(audit, **changes))

        # complete audits verify: ABI 2-3 as landrun-fs-systemd, ABI >= 4 as landrun-linux
        self.assertEqual(self.errors_after(verify(with_audit())), [])
        self.assertEqual(self.errors_after(verify(with_audit(landlock_abi=3))), [])
        self.assertEqual(self.errors_after(verify(dict(with_audit(landlock_abi=4), isolation="landrun-linux"))), [])
        # incomplete or mismatched audits cannot establish Verified
        self.assertRejected(verify(dict(base)), "needs its isolation_audit record")
        self.assertRejected(verify(dict(base, isolation="landrun-linux")), "needs its isolation_audit record")
        self.assertRejected(verify(with_audit(sockets_denied=["AF_UNIX"])), "must deny AF_UNIX, AF_INET and AF_INET6")
        self.assertRejected(verify(with_audit(readonly_mounts=[])), "readonly_mounts: fewer than 1 items")
        self.assertRejected(verify(with_audit(systemd_unit=None)), "names no systemd unit")
        for probe in pol.DENIED_PROBES:
            probes = dict(audit["landlock_probes"]); probes[probe] = "allowed"
            self.assertRejected(verify(with_audit(landlock_probes=probes)), f"lacks a denied {probe} probe")
        probes = dict(audit["landlock_probes"]); probes.pop("write_work_lake")
        self.assertRejected(verify(with_audit(landlock_probes=probes)), "allowed write_work_lake probe")
        self.assertRejected(verify(with_audit(landlock_abi=4)), "is the landrun-linux configuration, not landrun-fs-systemd")
        self.assertRejected(verify(dict(with_audit(landlock_abi=3), isolation="landrun-linux")),
                            "is the landrun-fs-systemd configuration, not landrun-linux")
        # the landrun build is pinned: 811cfff (go-landlock v0.9.0) and modified builds are rejected
        self.assertRejected(verify(with_audit(landrun_revision="811cfff" + "0" * 33)), "built unmodified from")
        self.assertRejected(verify(with_audit(landrun_modified=True)), "built unmodified from")
        self.assertRejected(verify(with_audit(go_landlock="v0.9.0")), "must record go-landlock v0.10.1")
        self.assertRejected(verify(dict(base, isolation="non-isolating", isolation_audit=audit)),
                            "belongs to a Linux landrun run")

    def test_landlock_abi_1_is_rejected(self):
        pol = validate_registry.isolation_policy
        with self.assertRaises(ValueError) as ctx:
            pol.isolation_for_abi(1)
        self.assertIn("refer", str(ctx.exception))
        for bad in (0, -1, None, True):
            with self.assertRaises(ValueError):
                pol.isolation_for_abi(bad)
        self.assertEqual([pol.isolation_for_abi(a) for a in (2, 3, 4, 6)],
                         ["landrun-fs-systemd", "landrun-fs-systemd", "landrun-linux", "landrun-linux"])
        # the command-line form used by the runner exits non-zero with the diagnosis
        out = subprocess.run([sys.executable, "-I", str(SURVEY / "scripts/isolation_policy.py"), "1"],
                             capture_output=True, text=True)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("Landlock ABI 1", out.stderr)
        self.assertEqual(subprocess.run([sys.executable, "-I", str(SURVEY / "scripts/isolation_policy.py"), "2"],
                                        capture_output=True, text=True).stdout.strip(), "landrun-fs-systemd")
        # an ABI 1 audit cannot verify under either Linux label
        audit = {"landlock_abi": 1}
        for iso in ("landrun-fs-systemd", "landrun-linux"):
            self.assertTrue(any("Landlock ABI 1" in e for e in pol.audit_errors(iso, audit)), iso)
        # the runner settles the ABI in step 0: before the workspace, the probes and Comparator
        script = (SURVEY / "scripts/compare_bridges_linux.sh").read_text(encoding="utf-8")
        reject = script.index('ISOLATION="$(python3 -I "$POLICY" "$ABI")" || fail')
        for later in ('WORK="$(mktemp -d', 'SANDBOX=(--best-effort', '"$COMPARATOR_BIN" "$rel"'):
            self.assertLess(reject, script.index(later), later)
        self.assertNotIn("ISOLATION=landrun-fs-systemd", script)   # the label comes only from the policy

    def test_foundation_package_stays_core_only(self):
        lakefile = (SURVEY / "lean" / "lakefile.toml").read_text(encoding="utf-8")
        manifest = json.loads((SURVEY / "lean" / "lake-manifest.json").read_text(encoding="utf-8"))
        self.assertNotIn("[[require]]", lakefile)
        self.assertEqual(manifest["packages"], [])


if __name__ == "__main__":
    unittest.main()
