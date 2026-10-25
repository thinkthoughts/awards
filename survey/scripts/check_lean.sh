#!/usr/bin/env bash
# Kernel-check the survey's core-only Lean files and print the axiom audit.
# Needs only the pinned Lean toolchain (survey/lean/lean-toolchain); no Mathlib, no lake build.
# Usage: survey/scripts/check_lean.sh [path/to/lean]
set -euo pipefail
LEAN="${1:-lean}"
HERE="$(cd "$(dirname "$0")/../lean" && pwd)"
OUT="$(mktemp -d)"
trap 'rm -rf "$OUT"' EXIT
mkdir -p "$OUT/SurveyFoundation"
"$LEAN" --version
"$LEAN" -o "$OUT/SurveyFoundation/OnePlusOne.olean" "$HERE/SurveyFoundation/OnePlusOne.lean"
LEAN_PATH="$OUT" "$LEAN" "$HERE/Audit.lean"
