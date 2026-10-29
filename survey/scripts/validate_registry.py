#!/usr/bin/env python3
"""Validate the survey registry: schemas, cross-references, independent states, PiπΠ lift rules.

Usage (from the repository root):
    python3 survey/scripts/validate_registry.py
    python3 survey/scripts/validate_registry.py --sources-dir DIR   # also check cited declarations

Standard library only. The JSON Schemas in survey/schemas use a small subset of draft 2020-12
(type, enum, pattern, required, properties, additionalProperties, items, minLength, $ref),
which this script implements; any full JSON Schema validator gives the same structural result.

--sources-dir DIR expects local clones named after source ids (DIR/lean-bgp212, ...). Each cited
declaration is then looked up in its file at the pinned commit with `git show`. Two source ids
may share one clone (DIR/lean-bgp212-89b43fa can link to the same repository as DIR/lean-bgp212).
Survey-local references give their file relative to survey/.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SURVEY = ROOT / "survey"
SCHEMAS = SURVEY / "schemas"
REGISTRY = SURVEY / "registry"
LAYERS = ["sources", "objects", "specs", "readings", "edges", "evidence"]
# Verification policy:
#   kernel-checked          kernel acceptance and axiom audit                    -> Compiled
#   comparator-nonisolated  Comparator acceptance without sandbox isolation      -> Compiled
#   comparator-accepted     Comparator acceptance under Linux landrun isolation  -> Verified
#                           (landrun-linux: Landlock ABI >= 4; landrun-fs-systemd: ABI 2-3; both
#                           with systemd read-only mounts and UNIX/IP socket denial, audited;
#                           ABI 1 is rejected: survey/scripts/isolation_policy.py)
LOCAL_VERIFIED = {"kernel-checked", "comparator-nonisolated", "comparator-accepted"}   # checks run for the survey
VERIFIED = {"comparator-accepted"}
_policy_spec = importlib.util.spec_from_file_location("isolation_policy", Path(__file__).with_name("isolation_policy.py"))
isolation_policy = importlib.util.module_from_spec(_policy_spec)
_policy_spec.loader.exec_module(isolation_policy)
ISOLATED = isolation_policy.LINUX_ISOLATIONS   # Comparator isolation configurations that verify



LIFT_RELATIONS = {"reading-of", "equivalent", "implies", "special-case", "closure", "cardinality-equality", "supplies-hypothesis"}


# ---------------------------------------------------------------- schema subset

def _resolve(ref: str, here: dict) -> dict:
    file, _, pointer = ref.partition("#")
    doc = json.loads((SCHEMAS / file).read_text(encoding="utf-8")) if file else here
    for part in [p for p in pointer.split("/") if p]:
        doc = doc[part]
    return doc


def check_schema(value, schema: dict, path: str, root: dict, errors: list[str]) -> None:
    if "$ref" in schema:
        check_schema(value, _resolve(schema["$ref"], root), path, root, errors)
        return
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"{path}: {value!r} is not one of {schema['enum']}")
        return
    types = schema.get("type")
    if types is not None:
        allowed = types if isinstance(types, list) else [types]
        pytypes = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None), "integer": int}
        if not any(isinstance(value, pytypes[t]) and not (t == "integer" and isinstance(value, bool))
                   for t in allowed):
            errors.append(f"{path}: expected {types}")
            return
    if isinstance(value, int) and not isinstance(value, bool) and value < schema.get("minimum", value):
        errors.append(f"{path}: {value} is below {schema['minimum']}")
    if isinstance(value, list) and len(value) < schema.get("minItems", 0):
        errors.append(f"{path}: fewer than {schema['minItems']} items")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: empty string")
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append(f"{path}: {value!r} does not match {schema['pattern']}")
    if isinstance(value, dict):
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}: missing required field '{key}'")
        props = schema.get("properties", {})
        for key, sub in value.items():
            if key in props:
                check_schema(sub, props[key], f"{path}.{key}", root, errors)
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}: unexpected field '{key}'")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            check_schema(item, schema["items"], f"{path}[{i}]", root, errors)


# ---------------------------------------------------------------- loading

def load_registry(directory: Path = REGISTRY) -> dict:
    return {name: json.loads((directory / f"{name}.json").read_text(encoding="utf-8")) for name in LAYERS}


def load_records(path: Path = SURVEY / "data" / "records.json") -> dict:
    return {r["id"]: r for r in json.loads(path.read_text(encoding="utf-8"))}


def lift_state(edge: dict) -> str:
    """The four-state summary of an edge: Proposed, Specified, Compiled, Verified.

    Verified means Comparator accepted the proof against an independently written Challenge with
    its commands sandboxed by landrun on Linux. A kernel check, or Comparator acceptance without
    sandbox isolation, leaves the edge at Compiled."""
    s = edge["state"]
    if s["verification"] in VERIFIED:
        return "Verified"
    return {"prose": "Proposed", "specified": "Specified", "compiled": "Compiled"}[s["formalization"]]


# ---------------------------------------------------------------- semantic rules

def validate(reg: dict, records: dict) -> list[str]:
    errors: list[str] = []
    for name in LAYERS:
        schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text(encoding="utf-8"))
        check_schema(reg[name], schema, name, schema, errors)
    if errors:
        return errors  # structural errors first; semantic checks assume the shapes

    sources = {s["id"]: s for s in reg["sources"]["sources"]}
    objects = {o["id"]: o for o in reg["objects"]["objects"]}
    specs = {s["id"]: s for s in reg["specs"]["specs"]}
    readings = {r["id"]: r for r in reg["readings"]["readings"]}
    edges = {e["id"]: e for e in reg["edges"]["edges"]}
    evidence = {e["id"]: e for e in reg["evidence"]["evidence"]}

    all_ids: dict[str, str] = {}
    for layer, table in [("objects", objects), ("specs", specs), ("readings", readings),
                         ("edges", edges), ("evidence", evidence)]:
        listed = [x["id"] for x in reg[layer][layer]]
        for i in sorted({i for i in listed if listed.count(i) > 1}):
            errors.append(f"{layer}: duplicate id {i}")
        for i in table:
            if i in all_ids:
                errors.append(f"{i}: id used in both {all_ids[i]} and {layer}")
            all_ids[i] = layer

    def node_exists(ref: str) -> bool:
        if ref.startswith("lean:"):
            parts = ref.split(":", 2)
            return len(parts) == 3 and (parts[1] in sources or parts[1] == "survey-local") and bool(parts[2])
        return ref in all_ids or ref in records

    def check_lean_refs(owner: str, refs: list[dict]) -> None:
        for ref in refs:
            if ref["source"] != "survey-local" and ref["source"] not in sources:
                errors.append(f"{owner}: Lean reference {ref['name']} cites unknown source {ref['source']}")

    def check_state(owner: str, rec: dict, has_lean_text: bool) -> None:
        st = rec["state"]
        if st["formalization"] in {"specified", "compiled"} and not has_lean_text:
            errors.append(f"{owner}: formalization {st['formalization']} needs Lean text or a Lean reference")
        if st["verification"] in LOCAL_VERIFIED and st["formalization"] != "compiled":
            errors.append(f"{owner}: verification {st['verification']} needs formalization 'compiled'")
        ev_ids = rec.get("evidence", [])
        if st["verification"] != "unverified" and not ev_ids:
            errors.append(f"{owner}: verification {st['verification']} needs evidence")
        kinds, isolations = set(), set()
        for ev_id in ev_ids:
            ev = evidence.get(ev_id)
            if ev is None:
                errors.append(f"{owner}: unknown evidence {ev_id}")
                continue
            if owner not in ev["subjects"]:
                errors.append(f"{owner}: evidence {ev_id} does not list it as a subject")
            kinds.add(ev["kind"])
            if ev["kind"] == "comparator":
                isolations.add(ev.get("isolation"))
        wanted = {"kernel-checked": {"kernel-check", "comparator"}, "comparator-nonisolated": {"comparator"},
                  "comparator-accepted": {"comparator"}, "upstream-reported": {"upstream-record"}}.get(st["verification"])
        if wanted and not kinds & wanted:
            errors.append(f"{owner}: verification {st['verification']} needs evidence of kind {sorted(wanted)}")
        if st["verification"] == "comparator-accepted" and not isolations & ISOLATED:
            errors.append(f"{owner}: comparator-accepted (Verified) needs Comparator evidence run under "
                          f"Linux landrun isolation; a non-isolated run is comparator-nonisolated")

    for oid, o in objects.items():
        check_lean_refs(oid, o["lean"])
        check_state(oid, o, bool(o["lean"]))

    for sid, s in specs.items():
        check_lean_refs(sid, s.get("lean", []))
        for obj in s["objects"]:
            if obj not in objects:
                errors.append(f"{sid}: unknown object {obj}")
        check_state(sid, s, bool(s["statement"].get("lean") or s.get("lean")))

    # Stable RPI identity: legacy readings use the frozen crosswalk; new ones embed rpi.
    crosswalk_path = SURVEY / "data" / "rpi-crosswalk.json"
    crosswalk = json.loads(crosswalk_path.read_text(encoding="utf-8"))["assignments"]
    allocated = {}
    seen_legacy = set()
    for entry in crosswalk:
        rid, rpi = entry["reading_id"], entry["rpi"]
        if rid in seen_legacy:
            errors.append(f"RPI crosswalk: duplicate reading {rid}")
        seen_legacy.add(rid)
        if rid not in readings:
            errors.append(f"RPI crosswalk: unknown reading {rid}")
        if rpi in allocated:
            errors.append(f"RPI crosswalk: duplicate {rpi}")
        allocated[rpi] = rid
        if rid in readings and readings[rid].get("rpi", rpi) != rpi:
            errors.append(f"{rid}: embedded rpi conflicts with crosswalk")
    for rid, reading in readings.items():
        if rid not in seen_legacy:
            rpi = reading.get("rpi")
            if not rpi:
                errors.append(f"{rid}: new reading requires rpi")
            elif rpi in allocated:
                errors.append(f"{rid}: duplicate rpi {rpi}")
            else:
                allocated[rpi] = rid
            if "origin" not in reading or "source_review" not in reading:
                errors.append(f"{rid}: new reading needs origin and source_review")
        origin = reading.get("origin")
        if origin and origin.get("kind") != reading["kind"]:
            errors.append(f"{rid}: origin kind differs from reading kind")
        if origin and origin.get("source_id") and origin["source_id"] not in sources:
            errors.append(f"{rid}: origin source_id unknown")
        if reading["kind"] in {"arxiv", "news", "repository", "other"} and not origin:
            errors.append(f"{rid}: external reading needs origin")

    for rid, r in readings.items():
        check_lean_refs(rid, r.get("lean", []))
        if r["spec"] not in specs:
            errors.append(f"{rid}: unknown spec {r['spec']}")
        if r["kind"] == "jsp":
            jsp = r.get("jsp")
            rec = records.get(jsp)
            if rec is None:
                errors.append(f"{rid}: {jsp} is absent from records.json")
            elif "catalog" not in r:
                errors.append(f"{rid}: JSP reading needs a catalog block")
            else:
                cat = r["catalog"]
                for key, rec_key in [("title", "title"), ("volume", "volume"), ("status", "status"),
                                     ("lean_proof", "lean_proof")]:
                    if cat[key] != rec[rec_key]:
                        errors.append(f"{rid}: catalog {key} {cat[key]!r} differs from records.json {rec[rec_key]!r}")
                if "text" in cat and cat["text"] != rec["description"]:
                    errors.append(f"{rid}: catalog text differs from records.json description")
        elif "jsp" in r or "catalog" in r:
            errors.append(f"{rid}: non-JSP readings carry no jsp or catalog block")
        check_state(rid, r, bool(r["statement"].get("lean")))

    for eid, e in edges.items():
        for end in ("from", "to"):
            if not node_exists(e[end]):
                errors.append(f"{eid}: {end} {e[end]} is neither a registry id nor a catalog id")
        check_lean_refs(eid, e.get("uses", []))
        roles = [h["role"] for h in e["hypotheses"]]
        strength, relation = e["strength"], e["relation"]
        if relation == "proof-dependency":
            if strength != "direct-application":
                errors.append(f"{eid}: proof-dependency requires direct-application strength")
            if not e.get("uses") or not any(u["kind"] == "theorem" for u in e["uses"]):
                errors.append(f"{eid}: proof-dependency must cite an explicit Lean theorem in uses")
            if e["state"]["mathematical"] != "established":
                errors.append(f"{eid}: proof-dependency must be an established source-level relationship")
        if relation == "research-target":
            if strength != "research-progression":
                errors.append(f"{eid}: research-target requires research-progression strength")
            if (e["state"]["mathematical"] != "candidate"
                    or e["state"]["formalization"] != "prose"
                    or e["state"]["verification"] != "unverified"
                    or e["obligation"] != "open"):
                errors.append(f"{eid}: research-target must remain candidate/prose/unverified/open")
            if e.get("uses") or e.get("evidence"):
                errors.append(f"{eid}: research-target cannot cite Lean proof use or verification evidence")
        if strength == "research-progression" and relation != "research-target":
            errors.append(f"{eid}: research-progression strength is reserved for research-target")
        if strength == "conditional-implication" and "assumption" not in roles:
            errors.append(f"{eid}: a conditional implication names at least one assumption")
        if strength == "direct-application" and "assumption" in roles:
            errors.append(f"{eid}: a direct application carries side conditions only; assumptions make it conditional")
        if strength in {"structural-analogy", "shared-reading"} and relation != "analogy":
            errors.append(f"{eid}: {strength} transfers structure only, so its relation is 'analogy'")
        if strength == "general-distinction" and relation != "membership":
            errors.append(f"{eid}: a general distinction records membership")
        if (relation == "closure") != ("closure" in e):
            errors.append(f"{eid}: relation 'closure' and the closure record go together")
        if relation == "closure" and e["from"] != e["to"]:
            errors.append(f"{eid}: a closure relates a property to itself (from equals to)")
        if (relation == "cardinality-equality") != ("count" in e):
            errors.append(f"{eid}: relation 'cardinality-equality' and the count record go together")
        if "characterizes" in e:
            ch = e["characterizes"]
            if relation != "equivalent":
                errors.append(f"{eid}: a characterization is a logical equivalence (relation 'equivalent')")
            if ch["object"] not in (e["from"], e["to"]):
                errors.append(f"{eid}: characterizes {ch['object']}, which is neither endpoint")
            for via in ch.get("via", []):
                if via not in edges:
                    errors.append(f"{eid}: characterization via unknown edge {via}")
            if "↔" not in ch["lean"]:
                errors.append(f"{eid}: a characterization states an equivalence (↔)")
        if (strength == "boundary") != (relation == "scope-boundary"):
            errors.append(f"{eid}: strength 'boundary' and relation 'scope-boundary' go together")
        if relation in LIFT_RELATIONS and strength not in {"direct-application", "conditional-implication"}:
            errors.append(f"{eid}: relation {relation} carries a conclusion, so its strength is a "
                          f"direct application or a conditional implication")
        for h in e["hypotheses"]:
            if h["role"] == "assumption" and h["status"] == "discharged":
                errors.append(f"{eid}: assumption {h['id']} is recorded as discharged; make it a side condition")
        verified = e["state"]["verification"] in VERIFIED
        recorded_kind = relation in {"analogy", "scope-boundary"}
        if recorded_kind != (e["obligation"] == "recorded"):
            errors.append(f"{eid}: analogy and scope-boundary edges carry obligation 'recorded'; "
                          f"every other edge is a proof obligation ('open' or 'discharged')")
        elif not recorded_kind and (e["obligation"] == "discharged") != verified:
            errors.append(f"{eid}: obligation is {e['obligation']} but lift state is {lift_state(e)}; "
                          f"a lift is discharged exactly when it is Verified")
        if e["state"]["mathematical"] == "candidate" and verified:
            errors.append(f"{eid}: a candidate relationship cannot be Verified")
        if verified and any(h["status"] != "discharged" for h in e["hypotheses"] if h["role"] == "side-condition"):
            errors.append(f"{eid}: Verified with an undischarged side condition")
        check_state(eid, e, bool(e["statement"].get("lean") or e.get("uses")))

    for vid, ev in evidence.items():
        for subj in ev["subjects"]:
            if subj not in all_ids:
                errors.append(f"{vid}: unknown subject {subj}")
        for dep in ev.get("dependencies", []):
            if dep not in sources:
                errors.append(f"{vid}: dependency {dep} is absent from sources.json")
        if ev["kind"] == "comparator" and ev.get("isolation") not in ISOLATED | {"non-isolating"}:
            errors.append(f"{vid}: Comparator evidence states its isolation "
                          f"(landrun-linux, landrun-fs-systemd or non-isolating)")
        if ev.get("isolation") in ISOLATED:
            errors += [f"{vid}: {m}" for m in isolation_policy.audit_errors(ev["isolation"], ev.get("isolation_audit"))]
        if "isolation_audit" in ev and ev.get("isolation") not in ISOLATED:
            errors.append(f"{vid}: isolation_audit belongs to a Linux landrun run")
        if ev["kind"] != "comparator" and "isolation" in ev:
            errors.append(f"{vid}: isolation applies to Comparator evidence only")
        if ev["kind"] == "upstream-record":
            if ev.get("source") not in sources:
                errors.append(f"{vid}: upstream evidence names a source from sources.json")
        else:
            if ev.get("sorry_free") is not True:
                errors.append(f"{vid}: local evidence records sorry_free = true")
            axioms = ev.get("axioms")
            if not isinstance(axioms, dict) or set(axioms) != set(ev["declarations"]):
                errors.append(f"{vid}: local evidence lists the axioms of every declaration it covers")
            else:
                for decl, used in axioms.items():
                    extra = set(used) - set(ev["permitted_axioms"])
                    if extra or "sorryAx" in used:
                        errors.append(f"{vid}: {decl} uses axioms outside the whitelist: {sorted(extra)}")
    return errors


# ---------------------------------------------------------------- cited declarations

DECL_KW = r"(?:theorem|lemma|def|abbrev|structure|inductive|instance|class)"


def check_declarations(reg: dict, sources_dir: Path) -> list[str]:
    """Look up every cited external declaration in its file at the pinned commit."""
    errors, cache = [], {}
    sources = {s["id"]: s for s in reg["sources"]["sources"]}
    refs = []
    for layer in ("objects", "specs", "readings"):
        for rec in reg[layer][layer]:
            refs += [(rec["id"], r) for r in rec.get("lean", [])]
    for e in reg["edges"]["edges"]:
        refs += [(e["id"], r) for r in e.get("uses", [])]
    for owner, ref in refs:
        if ref["source"] == "survey-local":
            path = SURVEY / ref["file"]
            short = ref["name"].rsplit(".", 1)[-1]
            if not path.exists() or not re.search(rf"\b{DECL_KW}\s+{re.escape(short)}\b", path.read_text(encoding="utf-8")):
                errors.append(f"{owner}: survey-local {ref['name']} absent from {ref['file']}")
            continue
        if "file" not in ref:
            continue  # e.g. Lean core declarations, cited by name and toolchain only
        src = sources[ref["source"]]
        key = (ref["source"], ref.get("file"))
        if key not in cache:
            repo = sources_dir / ref["source"]
            try:
                cache[key] = subprocess.run(["git", "-C", str(repo), "show", f"{src['commit']}:{ref['file']}"],
                                            check=True, capture_output=True, text=True).stdout
            except (subprocess.CalledProcessError, FileNotFoundError) as exc:
                cache[key] = None
                errors.append(f"{owner}: cannot read {ref['file']} at {src['commit'][:12]} in {repo}: {exc}")
        text = cache[key]
        if text is None:
            continue
        namespace, _, short = ref["name"].rpartition(".")
        if not re.search(rf"\b{DECL_KW}\s+{re.escape(short)}\b", text):
            errors.append(f"{owner}: {ref['name']} not declared in {ref['source']}:{ref['file']}")
        elif namespace and f"namespace {namespace}" not in text:
            errors.append(f"{owner}: namespace {namespace} not opened in {ref['source']}:{ref['file']}")
    return errors


def summary(reg: dict) -> str:
    lines = ["edge                     relation              strength                 lift state  obligation"]
    for e in reg["edges"]["edges"]:
        lines.append(f"{e['id']:24s} {e['relation']:21s} {e['strength']:24s} {lift_state(e):11s} {e['obligation']}")
    counts = {}
    for e in reg["edges"]["edges"]:
        counts[lift_state(e)] = counts.get(lift_state(e), 0) + 1
    lines.append("lift states: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sources-dir", type=Path, help="directory of local clones named by source id")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    reg = load_registry()
    errors = validate(reg, load_records())
    if not errors and args.sources_dir:
        errors += check_declarations(reg, args.sources_dir)
    if errors:
        for e in errors:
            print("ERROR", e, file=sys.stderr)
        print(f"{len(errors)} error(s)", file=sys.stderr)
        return 1
    if not args.quiet:
        print(summary(reg))
    counts = {k: len(reg[k][k]) for k in LAYERS}
    print("registry valid: " + ", ".join(f"{v} {k}" for k, v in counts.items()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
