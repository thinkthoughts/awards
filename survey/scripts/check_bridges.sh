#!/usr/bin/env bash
# Kernel-check the survey/lean-bridges modules and print their axiom audit.
#
# Uses an existing lean-bgp212 checkout as the build environment, so nothing is downloaded or
# rebuilt: the checkout must sit at the commit pinned in survey/lean-bridges/lakefile.toml, have
# a clean tree, and already hold built .olean files for BGP212.Gap and its imports. Only `lean`
# is run, through `lake env`; the checkout's sources and build outputs are left as they are.
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
for f in "$HERE"/SurveyBridges/*.lean; do
  m="$(basename "$f" .lean)"
  echo "== SurveyBridges.$m sha256 $(sha "$f")"
  lake env lean -o "$OUT/SurveyBridges/$m.olean" "$f"
done
lake env bash -c 'LEAN_PATH="$0:$LEAN_PATH" lean "$1"' "$OUT" "$HERE/Audit.lean"
