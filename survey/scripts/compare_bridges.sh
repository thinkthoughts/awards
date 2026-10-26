#!/usr/bin/env bash
# Run Lean Comparator on the survey's Challenge/Solution pairs (survey/lean-bridges/Comparator/*.json).
#
# Comparator builds the Challenge and Solution modules with `lake build` inside the Lake project it
# runs in, exports both with lean4export, checks that every listed theorem exists in the Solution
# with the Challenge's exact statement (definitions it uses are compared in full), rejects axioms
# outside permitted_axioms (sorryAx and native_decide's axioms included), and replays the Solution
# in the Lean kernel. A compile or axiom audit alone is not this check.
#
# This script changes nothing in the lean-bgp212 checkout or in survey/lean-bridges. It assembles a
# fresh Lake workspace in a temporary directory from survey/lean-bridges sources, with the pinned
# packages copied from the existing lean-bgp212 build (copy-on-write where the filesystem allows,
# e.g. APFS), so nothing is downloaded and only survey modules are built. The workspace is removed
# afterwards.
#
# Usage: survey/scripts/compare_bridges.sh PATH/TO/lean-bgp212 PATH/TO/comparator [config.json ...]
#   PATH/TO/comparator: a Comparator checkout built for the survey's toolchain. For Lean
#     4.34.0-rc2 that is Comparator 19e111e2141cf333c7daff0f64c5f24acc91dd2e with its pinned
#     lean4export cacf989bd75f608700820f6afc595f32e7a99a4d (`lake build` in the checkout and in
#     .lake/packages/lean4export). COMPARATOR_LEAN4EXPORT overrides the lean4export binary.
#   COMPARATOR_LANDRUN: the sandbox binary (default: landrun on PATH). landrun is Linux-only
#     (Landlock). On macOS, set it to survey/scripts/landrun-noisolate.sh, which runs commands with
#     no sandbox. The output line `isolation:` states which case applies:
#       landrun-linux   real landrun on Linux -> may be recorded as comparator-accepted (Verified)
#       non-isolating   the marked runner, or any runner off Linux -> comparator-nonisolated (Compiled)
#   Recommended on Linux, per Comparator's README:
#     systemd-run --user --pipe --same-dir --wait --collect -p RestrictAddressFamilies=~AF_UNIX ...
#   Full procedures: survey/docs/COMPARATOR_RUNS.md
set -euo pipefail
BGP="$(cd "${1:?usage: compare_bridges.sh PATH/TO/lean-bgp212 PATH/TO/comparator [config ...]}" && pwd)"
CMP="$(cd "${2:?usage: compare_bridges.sh PATH/TO/lean-bgp212 PATH/TO/comparator [config ...]}" && pwd)"
shift 2
HERE="$(cd "$(dirname "$0")/../lean-bridges" && pwd)"
TOOLCHAIN="$(tr -d '[:space:]' < "$HERE/lean-toolchain")"
PIN="$(sed -n 's/^rev = "\([0-9a-f]\{40\}\)".*/\1/p' "$HERE/lakefile.toml")"
if [ "$#" -gt 0 ]; then CONFIGS=("$@"); else CONFIGS=("$HERE"/Comparator/*.json); fi

fail() { echo "compare_bridges: $*" >&2; exit 1; }
sha() { if command -v sha256sum >/dev/null; then sha256sum "$1"; else shasum -a 256 "$1"; fi | cut -d' ' -f1; }
clonetree() { cp -cR "$1" "$2" 2>/dev/null || cp -R --reflink=auto "$1" "$2" 2>/dev/null || cp -R "$1" "$2"; }

# 1. The pinned, clean lean-bgp212 checkout provides every package.
[ "$(git -C "$BGP" rev-parse HEAD)" = "$PIN" ] || fail "lean-bgp212 is at $(git -C "$BGP" rev-parse HEAD); the survey pins $PIN"
[ -z "$(git -C "$BGP" status --porcelain --untracked-files=no)" ] || fail "lean-bgp212 has uncommitted changes to tracked files"

# 2. Comparator and lean4export must target the survey's toolchain.
L4E="$CMP/.lake/packages/lean4export"
[ "$(tr -d '[:space:]' < "$CMP/lean-toolchain")" = "$TOOLCHAIN" ] || fail "Comparator at $CMP targets $(cat "$CMP/lean-toolchain"); the survey needs $TOOLCHAIN"
[ "$(tr -d '[:space:]' < "$L4E/lean-toolchain")" = "$TOOLCHAIN" ] || fail "lean4export at $L4E targets $(cat "$L4E/lean-toolchain"); the survey needs $TOOLCHAIN"
COMPARATOR_BIN="$CMP/.lake/build/bin/comparator"
[ -x "$COMPARATOR_BIN" ] || fail "no Comparator binary at $COMPARATOR_BIN (run lake build in $CMP)"
export COMPARATOR_LEAN4EXPORT="${COMPARATOR_LEAN4EXPORT:-$L4E/.lake/build/bin/lean4export}"
[ -x "$COMPARATOR_LEAN4EXPORT" ] || fail "no lean4export binary at $COMPARATOR_LEAN4EXPORT (run lake build in $L4E)"
export COMPARATOR_LANDRUN="${COMPARATOR_LANDRUN:-$(command -v landrun || true)}"
[ -n "$COMPARATOR_LANDRUN" ] && [ -x "$COMPARATOR_LANDRUN" ] || fail "no landrun: install it or set COMPARATOR_LANDRUN"
if grep -q 'SURVEY-NONISOLATING-RUNNER' "$COMPARATOR_LANDRUN" 2>/dev/null; then
  ISOLATION="non-isolating"; RUNNER="survey non-isolating runner (no sandbox)"
elif [ "$(uname -s)" != "Linux" ]; then
  ISOLATION="non-isolating"; RUNNER="$(uname -s) has no Landlock; treated as unsandboxed"
else
  # Comparator calls landrun with --best-effort, which falls back to weaker or no sandboxing when
  # the kernel lacks Landlock. So isolation is established here before Comparator runs:
  #   a. Landlock is an active LSM;
  #   b. this landrun enforces a sandbox without --best-effort and understands -ldd/-add-exec
  #      (main-branch landrun, as Comparator's README requires): reading outside --ro fails;
  #   c. AF_UNIX sockets are blocked (systemd-run -p RestrictAddressFamilies=~AF_UNIX), the guard
  #      Comparator's README gives for the landrun weakness fixed in Linux 7.1.
  command -v python3 >/dev/null || fail "python3 is needed for the AF_UNIX check"
  grep -qw landlock /sys/kernel/security/lsm 2>/dev/null || fail "Landlock is not an active LSM (/sys/kernel/security/lsm)"
  PROBE="$(mktemp -d)"; echo secret > "$PROBE/f"
  "$COMPARATOR_LANDRUN" -ldd -add-exec --rox /usr --rox /bin --rox /lib --ro /etc -- /bin/true \
    || fail "$COMPARATOR_LANDRUN does not run -ldd -add-exec without --best-effort (needs main-branch landrun)"
  if "$COMPARATOR_LANDRUN" -ldd -add-exec --rox /usr --rox /bin --rox /lib -- /bin/cat "$PROBE/f" >/dev/null 2>&1; then
    rm -rf "$PROBE"; fail "$COMPARATOR_LANDRUN let a sandboxed process read a path it was not granted"
  fi
  rm -rf "$PROBE"
  if python3 -c 'import socket; socket.socket(socket.AF_UNIX)' 2>/dev/null; then
    fail "AF_UNIX sockets are allowed: run under systemd-run --user -p RestrictAddressFamilies=~AF_UNIX"
  fi
  RUNNER="landrun (Landlock enforced; AF_UNIX blocked) $({ "$COMPARATOR_LANDRUN" --version 2>&1 || true; } | head -n1)"
  ISOLATION="landrun-linux"
fi

# 3. Solutions must be free of sorry, admit and native_decide before Comparator runs.
for f in "$HERE"/SurveySolution/*.lean "$HERE"/SurveyBridges/*.lean; do
  if grep -nwE 'sorry|admit|native_decide' "$f"; then fail "$f uses sorry, admit or native_decide"; fi
done

# 3b. Each config names one Challenge and one Solution. The Challenge imports only lean-bgp212
#     (BGP212.*), so its statement is written against the foundational definitions alone; the
#     Solution imports only kernel-checked SurveyBridges modules. Every config permits exactly
#     the three standard axioms and leaves no definition holes.
python3 - "$HERE" "${CONFIGS[@]}" <<'PY' || fail "a Comparator config or its pair breaks the independence rules"
import json, re, sys
from pathlib import Path
here = Path(sys.argv[1])
ok = True
for cfg_path in sys.argv[2:]:
    cfg = json.loads(Path(cfg_path).read_text(encoding="utf-8"))
    def imports(mod):
        text = (here / (mod.replace(".", "/") + ".lean")).read_text(encoding="utf-8")
        return re.findall(r"^import\s+(\S+)", text, re.M)
    chal, sol = imports(cfg["challenge_module"]), imports(cfg["solution_module"])
    checks = {
        "challenge imports only BGP212.*": bool(chal) and all(i.startswith("BGP212.") for i in chal),
        "solution imports only SurveyBridges.*": bool(sol) and all(i.startswith("SurveyBridges.") for i in sol),
        "three standard axioms": sorted(cfg["permitted_axioms"]) == ["Classical.choice", "Quot.sound", "propext"],
        "no definition holes": not cfg.get("definition_names"),
        "theorem names given": bool(cfg.get("theorem_names")),
    }
    for what, good in checks.items():
        if not good:
            print(f"compare_bridges: {cfg_path}: {what} fails", file=sys.stderr); ok = False
    print(f"pair {Path(cfg_path).name}: {cfg['challenge_module']} imports {chal}; "
          f"{cfg['solution_module']} imports {sol}; theorems {cfg['theorem_names']}")
sys.exit(0 if ok else 1)
PY

# 4. A fresh workspace: survey/lean-bridges sources plus copies of the pinned packages.
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT
for item in lakefile.toml lake-manifest.json lean-toolchain SurveyBridges.lean SurveyBridges SurveyChallenge SurveySolution Comparator; do
  cp -R "$HERE/$item" "$WORK/"
done
mkdir -p "$WORK/.lake/packages"
python3 - "$HERE/lake-manifest.json" > "$WORK/packages.txt" <<'PY'
import json, sys
for p in json.load(open(sys.argv[1]))["packages"]:
    print(p["name"], p["rev"], p["url"])
PY
norm() { printf '%s' "$1" | sed -e 's#^git@github.com:#https://github.com/#' -e 's#\.git$##' -e 's#/$##'; }
while read -r name rev url; do
  if [ "$name" = "bgp212" ]; then
    src="$BGP"
    [ "$rev" = "$PIN" ] || fail "manifest pins bgp212 at $rev, lakefile at $PIN"
    [ "$(norm "$(git -C "$src" remote get-url origin)")" = "$(norm "$url")" ] || fail "lean-bgp212 origin differs from $url"
    git clone -q --no-checkout "$src" "$WORK/.lake/packages/bgp212"
    git -C "$WORK/.lake/packages/bgp212" checkout -q "$rev"
    git -C "$WORK/.lake/packages/bgp212" remote set-url origin "$url"
    mkdir -p "$WORK/.lake/packages/bgp212/.lake"
    clonetree "$src/.lake/build" "$WORK/.lake/packages/bgp212/.lake/build"
  else
    src="$BGP/.lake/packages/$name"
    [ -d "$src" ] || fail "lean-bgp212 has no built package $name"
    [ "$(git -C "$src" rev-parse HEAD)" = "$rev" ] || fail "$name is at $(git -C "$src" rev-parse HEAD), manifest pins $rev"
    [ "$(git -C "$src" remote get-url origin)" = "$url" ] || fail "$name origin differs from $url"
    clonetree "$src" "$WORK/.lake/packages/$name"
  fi
done < "$WORK/packages.txt"
rm "$WORK/packages.txt"

# 5. Record what is being checked, then run Comparator on each config.
echo "lean-bgp212 $PIN (clean)"
tree() { if [ -z "$(git -C "$1" status --porcelain --untracked-files=no)" ]; then echo clean; else echo MODIFIED; fi; }
echo "Comparator $(git -C "$CMP" rev-parse HEAD) ($(tree "$CMP")); lean4export $(git -C "$L4E" rev-parse HEAD) ($(tree "$L4E")); toolchain $TOOLCHAIN"
echo "comparator binary sha256 $(sha "$COMPARATOR_BIN"); lean4export binary sha256 $(sha "$COMPARATOR_LEAN4EXPORT")"
echo "host $(uname -srm)"
[ -r /sys/kernel/security/lsm ] && echo "lsm $(cat /sys/kernel/security/lsm)"
echo "runner $COMPARATOR_LANDRUN sha256 $(sha "$COMPARATOR_LANDRUN"): $RUNNER"
echo "systemd unit: ${INVOCATION_ID:-none}"
echo "isolation: $ISOLATION"
cd "$WORK"
lake env lean --version
for f in SurveyChallenge/*.lean SurveySolution/*.lean SurveyBridges/*.lean; do echo "sha256 $(sha "$f")  $f"; done
for cfg in "${CONFIGS[@]}"; do
  rel="Comparator/$(basename "$cfg")"
  echo "== $rel sha256 $(sha "$rel")"
  lake env "$COMPARATOR_BIN" "$rel"
done
echo "comparator: all configs accepted (isolation: $ISOLATION)"
