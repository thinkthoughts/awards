#!/usr/bin/env python3
"""EDGE-GDT-1 prerequisite check for the Linux Comparator run (read-only).

Usage: python3 -I gdt-vps-prereq.py PROVIDER
  PROVIDER  the lean-bgp212 checkout the runner shares builds from (any commit containing 89b43fa)

Recomputes the import closure of Solution.MultiShift from lean-bgp212 89b43fa (read with git show)
and the provider's package sources, then checks that every non-BGP212 module in it has its compiled
files (.olean, .olean.server, .olean.private, .ir) in PROVIDER/.lake/packages/<pkg>/.lake/build.
Exits 1 and lists what is missing. Writes nothing.
"""
import re, subprocess, sys
from pathlib import Path
PIN = "89b43fa019337645b4c2c66ae917bcb1fe76450f"
prov = Path(sys.argv[1]).resolve(); P = prov / ".lake/packages"
pkg = {"Mathlib": "mathlib", "Batteries": "batteries", "Aesop": "aesop", "Qq": "Qq", "ProofWidgets": "proofwidgets",
       "Plausible": "plausible", "LeanSearchClient": "LeanSearchClient", "ImportGraph": "importGraph"}
manifest = {p["name"]: p["rev"] for p in __import__("json").loads(subprocess.check_output(
    ["git", "-C", str(prov), "show", f"{PIN}:lake-manifest.json"]))["packages"]}
bad = []
for top, name in pkg.items():
    rev = subprocess.run(["git", "-C", str(P / name), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    if rev != manifest[name]:
        bad.append(f"package {name} at {rev or 'missing'}, manifest {manifest[name]}")
def text(m):
    top = m.split(".")[0]
    if top in ("BGP212", "Solution"):
        return subprocess.check_output(["git", "-C", str(prov), "show", f"{PIN}:{m.replace('.', '/')}.lean"], text=True)
    if top in pkg:
        f = P / pkg[top] / (m.replace(".", "/") + ".lean")
        return f.read_text(encoding="utf-8") if f.exists() else None
    return ""   # Lean core (Init, Std, Lean) ships with the toolchain
seen, stack, missing_src = set(), ["Solution.MultiShift"], []
while stack:
    m = stack.pop()
    if m in seen: continue
    seen.add(m); t = text(m)
    if t is None: missing_src.append(m); continue
    t = re.sub(r"/-.*?-/", "", t, flags=re.S)
    stack += re.findall(r"^(?:public |meta )*import\s+(?:all\s+)?([A-Z]\S*)", t, re.M)
deps = sorted(m for m in seen if m.split(".")[0] in pkg)
for m in deps:
    base = P / pkg[m.split(".")[0]] / ".lake/build/lib/lean" / m.replace(".", "/")
    for ext in (".olean", ".olean.server", ".olean.private", ".ir"):
        if not Path(str(base) + ext).exists():
            bad.append(f"{m}: no {base.name}{ext}")
for m in ("Mathlib.Data.Nat.GCD.BigOperators", "Mathlib.Tactic.FieldSimp", "Mathlib.Tactic.Positivity", "Mathlib.Tactic.Linarith"):
    ok = Path(str(P / "mathlib/.lake/build/lib/lean" / m.replace(".", "/")) + ".olean").exists()
    print(f"{m}: {'built' if ok else 'MISSING'}")
from collections import Counter
print(f"closure of Solution.MultiShift at {PIN[:7]}: {len(deps)} package modules {dict(Counter(m.split('.')[0] for m in deps))}")
for m in missing_src: bad.append(f"{m}: source not found")
if bad:
    print("MISSING PREREQUISITES:"); print("\n".join("  " + b for b in bad)); sys.exit(1)
print("all prerequisites present: every module in the closure has its compiled files in the shared builds")
