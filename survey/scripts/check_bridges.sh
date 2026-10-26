#!/usr/bin/env bash
# Kernel-check the survey/lean-bridges modules (AdmissibleTwin, H1LeMono, TwinPrimeEquiv,
# TwinPrimeTo186) and audit their axioms.
#
# Uses an existing lean-bgp212 checkout as the build environment, so nothing is downloaded or
# rebuilt: the checkout must sit at the commit pinned in survey/lean-bridges/lakefile.toml, have
# a clean tree, and already hold built .olean files for BGP212.Gap and its imports. Only `lean`
# is run, through `lake env`; the checkout's sources and build outputs are left as they are.
# `-R "$HERE"` sets the source root to survey/lean-bridges, so module names (SurveyBridges.*)
# resolve there rather than inside the lean-bgp212 checkout that provides the environment.
#
# Usage: survey/scripts/check_bridges.sh PATH/TO/lean-bgp212
#
# The reproducible route from scratch is `lake build` inside survey/lean-bridges, which fetches
# lean-bgp212 and Mathlib at their pinned commits (several GB with the Mathlib cache).
set -euo pipefail
BGP="$(cd "${1:?usage: check_bridges.sh PATH/TO/lean-bgp212}" && pwd)"
HERE="$(cd "$(dirname "$0")/../lean-bridges" && pwd)"
PIN="$(sed -n 's/^rev = "\([0-9a-f]\{40\}\)".*/\1/p' "$HERE/lakefile.toml")"

head="$(git -C "$BGP" rev-parse HEAD)"
if [ "$head" != "$PIN" ]; then
  echo "lean-bgp212 is at $head; the survey pins $PIN" >&2
  exit 1
fi
if [ -n "$(git -C "$BGP" status --porcelain --untracked-files=no)" ]; then
  echo "lean-bgp212 has uncommitted changes to tracked files" >&2
  exit 1
fi

sha() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }

OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT
mkdir -p "$OUT/SurveyBridges"
cd "$BGP"
echo "lean-bgp212 $head (clean)"
lake env lean --version
# Bridge modules, in dependency order. Each imports lean-bgp212 (BGP212.Gap) and may import
# bridge modules listed before it, whose .olean files are found through $OUT on LEAN_PATH.
MODULES=(AdmissibleTwin H1LeMono TwinPrimeEquiv TwinPrimeTo186 AdmissibleSubset AdmissiblePair ResidueImage AdmissibleZMod)
for m in "${MODULES[@]}"; do
  f="$HERE/SurveyBridges/$m.lean"
  if grep -nwE 'sorry|admit|native_decide' "$f"; then
    echo "SurveyBridges.$m uses sorry, admit or native_decide" >&2
    exit 1
  fi
  echo "== SurveyBridges.$m sha256 $(sha "$f")"
  lake env bash -c 'LEAN_PATH="$0:$LEAN_PATH" lean -R "$1" -o "$2" "$3"' \
    "$OUT" "$HERE" "$OUT/SurveyBridges/$m.olean" "$f"
done
for f in "$HERE"/SurveyBridges/*.lean; do
  case " ${MODULES[*]} " in *" $(basename "$f" .lean) "*) ;; *)
    echo "unlisted bridge module $f: add it to MODULES" >&2; exit 1;; esac
done

echo "== Audit sha256 $(sha "$HERE/Audit.lean")"
AUDIT="$(lake env bash -c 'LEAN_PATH="$0:$LEAN_PATH" lean -R "$1" "$2"' "$OUT" "$HERE" "$HERE/Audit.lean")"
printf '%s\n' "$AUDIT"
# Every audited declaration may use only the three standard axioms.
bad="$(printf '%s\n' "$AUDIT" | sed -n "s/.*depends on axioms: \[\(.*\)\]/\1/p" | tr ',' '\n' \
  | sed 's/^ *//; s/ *$//' | grep -vxE 'propext|Classical\.choice|Quot\.sound' || true)"
if [ -n "$bad" ]; then
  echo "axioms outside propext, Classical.choice, Quot.sound: $bad" >&2
  exit 1
fi
echo "axiom audit: only propext, Classical.choice, Quot.sound"
