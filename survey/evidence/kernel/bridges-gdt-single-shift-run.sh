#!/usr/bin/env bash
# Kernel check of SurveyBridges.GDTSingleShift on pinned sources, with the user's compiled Mathlib closure.
set -euo pipefail
K=/home/claude/kcheck; L=/home/claude/lean-tc/lean-4.34.0-rc2-linux/bin/lean; O=$K/out
rm -rf $O; mkdir -p $O
LP=$O; for p in mathlib batteries aesop Qq proofwidgets plausible LeanSearchClient importGraph; do LP="$LP:$K/pkgs/$p/.lake/build/lib/lean"; done
export LEAN_PATH=$LP
$L --version
comp() { local root=$1 mod=$2; local f=$root/${mod//.//}.lean o=$O/${mod//.//}.olean; mkdir -p "$(dirname $o)"
  echo "== $mod sha256 $(sha256sum $f | cut -c1-64)"; $L -R $root -o $o $f; }
for m in BGP212.GDTv1Basic BGP212.MultiShift BGP212.GDTv1 Solution.MultiShift; do comp $K/bgp $m; done
comp $K/survey SurveyBridges.GDTSingleShift
echo "== audit"; $L -R $K $K/AuditGDT.lean
comp $K/survey SurveyChallenge.GDTSingleShift
echo "== challenge types"; $L -R $K $K/ChalTypes.lean
