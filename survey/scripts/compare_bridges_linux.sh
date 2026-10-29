#!/usr/bin/env bash
# Linux, landrun-isolated Lean Comparator run on the survey's Challenge/Solution pairs, with the
# compiled dependency builds shared read-only instead of copied.
#
# Why a second runner: compare_bridges.sh assembles its workspace by copying every package's
# .lake/build (copy-on-write on APFS/Btrfs/XFS, a full copy on ext4: about 16 GB for Mathlib).
# This runner copies nothing that is compiled:
#
#   WORK/                                 survey/lean-bridges sources (lakefile, manifest, modules)
#   WORK/.lake/packages/bgp212            fresh checkout of the pinned commit (git alternates into
#                                         the provider repository, no hardlinks); its modules are
#                                         compiled here, inside the sandbox, from pinned sources
#   WORK/.lake/packages/<dep>             fresh checkout of the manifest revision (git alternates)
#   WORK/.lake/packages/<dep>/.lake/build -> PROVIDER/.lake/packages/<dep>/.lake/build  (symlink)
#
# Three layers keep the shared builds and the rest of the system unchanged during the run:
#   1. Landlock, through Comparator's own landrun call (`--best-effort --ro / --rw /dev
#      --rwx WORK/.lake`): every write outside WORK/.lake is denied;
#   2. the systemd unit's mount namespace (`-p PrivateUsers=yes -p ReadOnlyPaths=PROVIDER ...`):
#      the provider tree is a read-only mount, so writes and truncate(2) fail with EROFS even on
#      Landlock ABI 2 kernels, where Landlock does not cover truncate;
#   3. the unit's seccomp filter (`-p 'RestrictAddressFamilies=~AF_UNIX AF_INET AF_INET6'`): no
#      UNIX or IP sockets, the network confinement that landrun's Landlock rules only provide on
#      ABI 4+ (Linux 6.7+), where --best-effort otherwise drops it silently.
# The script checks all three before Comparator runs and records the Landlock ABI. It rejects
# ABI 1 outright (survey/scripts/isolation_policy.py: landrun's read-write directories request
# `refer`, which ABI 1 cannot express, so go-landlock best-effort applies no ruleset), reports
# `isolation: landrun-linux` on ABI >= 4 and `isolation: landrun-fs-systemd` on ABI 2-3, with an
# `isolation-audit:` JSON line listing every check, for the evidence record.
#
# Comparator runs `lake build` under landrun with `--ro /`, `--rw /dev` and `--rwx WORK/.lake`
# only. Landlock checks the inode a path resolves to, so every file reached through a build
# symlink is outside WORK/.lake and read-only: Lake can replay the shared Mathlib traces, and
# any attempt to write a shared artifact fails with EACCES instead of altering it. Lake's own
# per-workspace files (lakefile.olean of each Lean-configured package, BGP212 and survey
# outputs) are written under WORK/.lake. Before Comparator runs, this script proves the write
# denial on a shared build directory with the same landrun flags, builds BGP212.Gap and
# BGP212.MultiShift under that sandbox (the minimal test), and afterwards checks that no
# shared file changed and that WORK holds no hardlinked file.
#
# Usage:
#   compare_bridges_linux.sh [--plan|--preflight] PROVIDER COMPARATOR [config.json ...]
#     PROVIDER    an existing lean-bgp212 checkout (any commit that contains the pinned one)
#                 whose .lake/packages hold built dependencies at the survey manifest revisions
#     COMPARATOR  a Comparator checkout at exactly 19e111e2141cf333c7daff0f64c5f24acc91dd2e
#                 with lean4export cacf989bd75f608700820f6afc595f32e7a99a4d, both built
#     --plan      check pins, provider packages and disk; assemble WORK; stop (no lake, no landrun)
#     --preflight additionally run the isolation probes and the sandboxed dependency build; stop
#   Environment: COMPARATOR_LANDRUN (default: landrun on PATH), COMPARE_WORKDIR_BASE (default
#   ${TMPDIR:-/tmp}), KEEP_WORK=1 keeps the workspace for inspection.
#   Run inside: systemd-run --user --pipe --same-dir --wait --collect -p PrivateUsers=yes \
#                 -p ReadOnlyPaths=PROVIDER -p ReadOnlyPaths=COMPARATOR -p ReadOnlyPaths=AWARDS \
#                 -p 'RestrictAddressFamilies=~AF_UNIX AF_INET AF_INET6' \
#                 -E PATH="$PATH" -E HOME="$HOME" -E COMPARATOR_LANDRUN=... -- ...
#   Full procedure: survey/docs/COMPARATOR_RUNS.md
set -euo pipefail

MODE=run
case "${1:-}" in --plan) MODE=plan; shift ;; --preflight) MODE=preflight; shift ;; esac
PROVIDER="$(cd "${1:?usage: compare_bridges_linux.sh [--plan|--preflight] PROVIDER COMPARATOR [config ...]}" && pwd)"
CMP="$(cd "${2:?usage: compare_bridges_linux.sh [--plan|--preflight] PROVIDER COMPARATOR [config ...]}" && pwd)"
shift 2
SCRIPT="$(cd "$(dirname "$0")" && pwd)/$(basename "$0")"
HERE="$(cd "$(dirname "$0")/../lean-bridges" && pwd)"
TOOLCHAIN="$(tr -d '[:space:]' < "$HERE/lean-toolchain")"
PIN="$(sed -n 's/^rev = "\([0-9a-f]\{40\}\)".*/\1/p' "$HERE/lakefile.toml")"
COMPARATOR_PIN=19e111e2141cf333c7daff0f64c5f24acc91dd2e
LEAN4EXPORT_PIN=cacf989bd75f608700820f6afc595f32e7a99a4d
if [ "$#" -gt 0 ]; then CONFIGS=("$@"); else CONFIGS=("$HERE"/Comparator/*.json); fi
export GIT_OPTIONAL_LOCKS=0      # read-only git queries on provider repositories: no index refresh

fail() { echo "compare_bridges_linux: $*" >&2; exit 1; }
sha() { sha256sum "$1" | cut -d' ' -f1; }
norm() { printf '%s' "$1" | sed -e 's#^git@github.com:#https://github.com/#' -e 's#\.git$##' -e 's#/$##'; }
clean() { [ -z "$(git -C "$1" status --porcelain --untracked-files=no)" ]; }

# 0. Linux with landrun only. The marked non-isolating runner belongs to compare_bridges.sh.
[ "$(uname -s)" = "Linux" ] || fail "Linux only; on macOS use compare_bridges.sh (non-isolating)"
LANDRUN="${COMPARATOR_LANDRUN:-$(command -v landrun || true)}"
POLICY="$(cd "$(dirname "$0")" && pwd)/isolation_policy.py"
if [ "$MODE" != plan ]; then
  [ -n "$LANDRUN" ] && [ -x "$LANDRUN" ] || fail "no landrun: build it (survey/docs/COMPARATOR_RUNS.md) or set COMPARATOR_LANDRUN"
  ! grep -q 'SURVEY-NONISOLATING-RUNNER' "$LANDRUN" 2>/dev/null || fail "$LANDRUN is the non-isolating runner; this script records landrun-linux runs only"
  # The kernel's Landlock ABI decides the configuration; ABI 1 is rejected here, before any
  # workspace, probe or Comparator run.
  grep -qw landlock /sys/kernel/security/lsm 2>/dev/null || fail "Landlock is not an active LSM"
  ABI="$(python3 -c 'import ctypes; print(ctypes.CDLL(None, use_errno=True).syscall(444, None, 0, 1))')"
  ISOLATION="$(python3 -I "$POLICY" "$ABI")" || fail "Landlock ABI $ABI rejected (see above)"
  # The landrun build, from the module information Go embeds in the binary: `landrun --version`
  # reads 0.1.18 for both 811cfff (go-landlock v0.9.0) and ec104f6 (go-landlock v0.10.1).
  LANDRUN_INFO="$(python3 -I - "$LANDRUN" "$POLICY" <<'PY'
import importlib.util, re, sys
spec = importlib.util.spec_from_file_location("isolation_policy", sys.argv[2])
pol = importlib.util.module_from_spec(spec); spec.loader.exec_module(pol)
data = open(sys.argv[1], "rb").read()
rev = re.search(rb"vcs\.revision=([0-9a-f]{40})", data)
mod = re.search(rb"vcs\.modified=(true|false)", data)
gll = re.search(rb"\tgithub\.com/landlock-lsm/go-landlock\t(v[0-9][^\t\n]*)", data)
rev, mod, gll = (m.group(1).decode() if m else None for m in (rev, mod, gll))
print(rev, mod, gll)
if rev != pol.LANDRUN_PIN or mod != "false" or gll != pol.GO_LANDLOCK_PIN:
    print(f"landrun build: vcs.revision {rev}, vcs.modified {mod}, go-landlock {gll}; formal runs need "
          f"an unmodified build of {pol.LANDRUN_PIN} with go-landlock {pol.GO_LANDLOCK_PIN} "
          f"(go build in a clean checkout embeds this; see survey/docs/COMPARATOR_RUNS.md)", file=sys.stderr)
    sys.exit(1)
PY
)" || fail "landrun is not the pinned build"
  read -r LANDRUN_REV LANDRUN_MODIFIED GO_LANDLOCK <<< "$LANDRUN_INFO"
fi

# 1. The pinned lean-bgp212 commit, read from the provider's object store.
git -C "$PROVIDER" cat-file -e "$PIN^{commit}" 2>/dev/null || fail "provider $PROVIDER lacks pinned commit $PIN"
PROVIDER_HEAD="$(git -C "$PROVIDER" rev-parse HEAD)"
if git -C "$PROVIDER" merge-base --is-ancestor "$PIN" "$PROVIDER_HEAD"; then REL="descends from the pin"; else REL="does not descend from the pin"; fi
[ "$(git -C "$PROVIDER" show "$PIN:lean-toolchain" | tr -d '[:space:]')" = "$TOOLCHAIN" ] || fail "lean-bgp212 $PIN targets another toolchain"
[ "$(tr -d '[:space:]' < "$PROVIDER/lean-toolchain")" = "$TOOLCHAIN" ] || fail "provider builds target $(cat "$PROVIDER/lean-toolchain"); the survey needs $TOOLCHAIN"

# 2. Every dependency: survey manifest = pinned lean-bgp212 manifest = provider checkout, with a
#    clean provider tree and an existing build directory to share.
PKGS="$(mktemp)"
trap 'rm -f "$PKGS" "$PKGS.pin"' EXIT
git -C "$PROVIDER" show "$PIN:lake-manifest.json" > "$PKGS.pin"
python3 - "$HERE/lake-manifest.json" "$PKGS.pin" "$PIN" > "$PKGS" <<'PY' || fail "manifest mismatch (see above)"
import json, sys
survey = {p["name"]: p for p in json.load(open(sys.argv[1]))["packages"]}
pinned = {p["name"]: p for p in json.load(open(sys.argv[2]))["packages"]}
ok = survey["bgp212"]["rev"] == sys.argv[3]
if not ok:
    print(f"survey manifest pins bgp212 at {survey['bgp212']['rev']}, lakefile at {sys.argv[3]}", file=sys.stderr)
for name, p in survey.items():
    if name == "bgp212":
        continue
    q = pinned.get(name)
    if q is None or q["rev"] != p["rev"] or q["url"].rstrip("/") != p["url"].rstrip("/"):
        print(f"{name}: survey manifest {p['rev']} differs from lean-bgp212 pin {q and q['rev']}", file=sys.stderr)
        ok = False
for name, p in survey.items():
    print(name, p["rev"], p["url"], p.get("configFile") or "lakefile.lean")
sys.exit(0 if ok else 1)
PY
rm -f "$PKGS.pin"
NEED=0
SOURCE_ONLY=()
while read -r name rev url _cfg; do
  if [ "$name" = bgp212 ]; then src="$PROVIDER"; at="$PIN"; else
    src="$PROVIDER/.lake/packages/$name"; at="$rev"
    [ -d "$src/.git" ] || [ -f "$src/.git" ] || fail "provider package $name missing at $src"
    [ "$(git -C "$src" rev-parse HEAD)" = "$rev" ] || fail "provider $name is at $(git -C "$src" rev-parse HEAD); the manifest pins $rev"
    [ "$(norm "$(git -C "$src" remote get-url origin)")" = "$(norm "$url")" ] || fail "provider $name origin differs from $url"
    clean "$src" || fail "provider $name has modified tracked files; its build cannot be trusted to match $rev"
    # A dependency without a provider build (e.g. Cli, needed only by Lake executables) is
    # checked out source-only; Lake builds whatever it needs from it inside WORK/.lake.
    [ -d "$src/.lake/build" ] || SOURCE_ONLY+=("$name")
  fi
  bytes="$(git -C "$src" ls-tree -r -l "$at" | awk '$4 ~ /^[0-9]+$/ {s += $4} END {print s + 0}')"
  NEED=$((NEED + bytes))
done < "$PKGS"
for name in "${SOURCE_ONLY[@]}"; do
  [ "$name" != mathlib ] || fail "provider mathlib has no build; this runner shares Mathlib and never rebuilds it"
done

# 3. Comparator and lean4export at their exact pins, built for the survey toolchain.
L4E="$CMP/.lake/packages/lean4export"
# (--plan with COMPARE_PLAN_SKIP_COMPARATOR=1 skips this step: layout tests only; no evidence.)
if [ "$MODE" = plan ] && [ "${COMPARE_PLAN_SKIP_COMPARATOR:-0}" = 1 ]; then :; else
[ "$(git -C "$CMP" rev-parse HEAD)" = "$COMPARATOR_PIN" ] || fail "Comparator at $CMP is $(git -C "$CMP" rev-parse HEAD); formal runs need exactly $COMPARATOR_PIN"
[ "$(git -C "$L4E" rev-parse HEAD)" = "$LEAN4EXPORT_PIN" ] || fail "lean4export at $L4E is $(git -C "$L4E" rev-parse HEAD); formal runs need exactly $LEAN4EXPORT_PIN"
clean "$CMP" && clean "$L4E" || fail "Comparator or lean4export has modified tracked files"
[ "$(tr -d '[:space:]' < "$CMP/lean-toolchain")" = "$TOOLCHAIN" ] || fail "Comparator targets $(cat "$CMP/lean-toolchain")"
COMPARATOR_BIN="$CMP/.lake/build/bin/comparator"
export COMPARATOR_LEAN4EXPORT="${COMPARATOR_LEAN4EXPORT:-$L4E/.lake/build/bin/lean4export}"
[ "$MODE" = plan ] || { [ -x "$COMPARATOR_BIN" ] && [ -x "$COMPARATOR_LEAN4EXPORT" ]; } || fail "Comparator or lean4export binary missing (lake build in $CMP and $L4E)"
fi

# 4. Disk: checked-out sources (exact blob bytes) + 512 MiB for BGP212, survey and Lake config
#    outputs, with a 1 GiB safety margin.
BASE="${COMPARE_WORKDIR_BASE:-${TMPDIR:-/tmp}}"
NEED_KB=$(( NEED / 1024 + 512 * 1024 ))
AVAIL_KB="$(df -Pk "$BASE" | awk 'NR == 2 {print $4}')"
[ "$AVAIL_KB" -ge $(( NEED_KB + 1024 * 1024 )) ] || fail "need about $((NEED_KB / 1024)) MiB plus a 1 GiB margin in $BASE; $((AVAIL_KB / 1024)) MiB available"

# 5. Solutions free of sorry/admit/native_decide; each pair independent (as in compare_bridges.sh).
for f in "$HERE"/SurveySolution/*.lean "$HERE"/SurveyBridges/*.lean; do
  if grep -nwE 'sorry|admit|native_decide' "$f"; then fail "$f uses sorry, admit or native_decide"; fi
done
python3 - "$HERE" "${CONFIGS[@]}" <<'PY' || fail "a Comparator config or its pair breaks the independence rules"
import json, re, sys
from pathlib import Path
here, ok = Path(sys.argv[1]), True
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
            print(f"compare_bridges_linux: {cfg_path}: {what} fails", file=sys.stderr); ok = False
    print(f"pair {Path(cfg_path).name}: {cfg['challenge_module']} imports {chal}; "
          f"{cfg['solution_module']} imports {sol}; theorems {cfg['theorem_names']}")
sys.exit(0 if ok else 1)
PY

# 6. The workspace. Sources come from git objects at the pinned revisions (alternates point at
#    the provider object stores, read-only); only .lake/build of each dependency is shared.
WORK="$(mktemp -d "$BASE/survey-compare.XXXXXX")"
if [ "${KEEP_WORK:-0}" = 1 ]; then trap 'rm -f "$PKGS"; echo "workspace kept: $WORK"' EXIT; else trap 'rm -rf "$WORK"; rm -f "$PKGS"' EXIT; fi
for item in lakefile.toml lake-manifest.json lean-toolchain SurveyBridges.lean SurveyBridges SurveyChallenge SurveySolution Comparator; do
  cp -R "$HERE/$item" "$WORK/"
done
mkdir -p "$WORK/.lake/packages"
SHARED=()
checkout() {  # checkout DEST SRC_REPO REV URL: a fresh repository borrowing SRC_REPO's objects
  local dest="$1" src="$2" rev="$3" url="$4" objs
  objs="$(cd "$src" && cd "$(git rev-parse --git-common-dir)" && pwd)/objects"
  git init -q "$dest"
  printf '%s\n' "$objs" > "$dest/.git/objects/info/alternates"
  git -C "$dest" -c advice.detachedHead=false checkout -q --detach "$rev"
  git -C "$dest" remote add origin "$url"
  [ "$(git -C "$dest" rev-parse HEAD)" = "$rev" ] && clean "$dest" || fail "checkout of $rev into $dest failed"
}
while read -r name rev url _cfg; do
  dest="$WORK/.lake/packages/$name"
  if [ "$name" = bgp212 ]; then
    checkout "$dest" "$PROVIDER" "$PIN" "$url"
  else
    src="$PROVIDER/.lake/packages/$name"
    checkout "$dest" "$src" "$rev" "$url"
    mkdir -p "$dest/.lake"
    if [ -d "$src/.lake/build" ]; then
      ln -s "$src/.lake/build" "$dest/.lake/build"
      SHARED+=("$src/.lake/build")
    fi
  fi
done < "$PKGS"
# Every Mathlib module the survey imports must already be built in the shared tree; the sandbox
# could not create a missing one.
for m in $(cat "$HERE"/SurveyBridges/*.lean "$HERE"/SurveyChallenge/*.lean | sed -n 's/^import \(Mathlib\.[A-Za-z0-9_.]*\).*/\1/p' | sort -u); do
  o="$WORK/.lake/packages/mathlib/.lake/build/lib/lean/$(printf '%s' "$m" | tr . /).olean"
  [ -f "$o" ] || fail "shared Mathlib build lacks $m ($o)"
done
touch "$WORK/.lake/run-start"
LINKED="$(find "$WORK" -type f -links +1 -print -quit)"
[ -z "$LINKED" ] || fail "hardlinked file in the workspace: $LINKED"

echo "provider lean-bgp212 $PROVIDER_HEAD ($REL $PIN); workspace bgp212 checkout $PIN"
while read -r name rev url cfgf; do
  [ "$name" = bgp212 ] && continue
  if [ -d "$PROVIDER/.lake/packages/$name/.lake/build" ]; then
    echo "dependency $name $rev ($url, $cfgf): shared read-only build $PROVIDER/.lake/packages/$name/.lake/build"
  else
    echo "dependency $name $rev ($url, $cfgf): source-only checkout; any build happens in WORK/.lake"
  fi
done < "$PKGS"
echo "workspace $WORK on $(df -P "$BASE" | awk 'NR == 2 {print $1}'): sources $((NEED / 1048576)) MiB, estimate $((NEED_KB / 1024)) MiB, available $((AVAIL_KB / 1024)) MiB"
if [ "$MODE" = plan ]; then echo "plan: workspace assembled; no lake or landrun run"; exit 0; fi

# 7. Isolation, established before Comparator runs, with Comparator's own landrun flags
#    (including --best-effort, which on older kernels keeps only the filesystem rules).
# (Landlock active and ABI >= 2 were established in step 0.)
SANDBOX=(--best-effort --ro / --rw /dev -ldd -add-exec --rwx "$WORK/.lake")
PROBE="$(mktemp -d "$WORK/.probe.XXXXXX")"; echo secret > "$PROBE/f"
if "$LANDRUN" --best-effort -ldd -add-exec --rox /usr --rox /bin --rox /lib -- /bin/cat "$PROBE/f" >/dev/null 2>&1; then
  fail "$LANDRUN let a sandboxed process read a path it was not granted (Landlock not enforced)"
fi
"$LANDRUN" "${SANDBOX[@]}" -- /usr/bin/touch "$WORK/.lake/landlock-write-probe" \
  || fail "the sandbox cannot write WORK/.lake"
if "$LANDRUN" "${SANDBOX[@]}" -- /usr/bin/touch "$PROBE/outside" 2>/dev/null; then
  fail "the sandbox wrote outside WORK/.lake (Landlock not enforced)"
fi
rm -rf "$PROBE"
for b in "${SHARED[@]}"; do
  pkg="$(basename "$(dirname "$(dirname "$b")")")"
  if "$LANDRUN" "${SANDBOX[@]}" -- /usr/bin/touch "$WORK/.lake/packages/$pkg/.lake/build/landlock-write-probe" 2>/dev/null; then
    fail "the sandbox wrote into shared build $b"
  fi
done
python3 - "$PROVIDER" "$CMP" "$HERE" "${SHARED[@]}" <<'PY' || fail "provider, Comparator and survey trees must be read-only mounts (systemd -p ReadOnlyPaths=...)"
import os, sys
bad = [p for p in sys.argv[1:] if not os.statvfs(os.path.realpath(p)).f_flag & os.ST_RDONLY]
for p in bad:
    print(f"compare_bridges_linux: {p} is writable", file=sys.stderr)
sys.exit(1 if bad else 0)
PY
python3 - <<'PY' || fail "UNIX or IP sockets are allowed: run under systemd-run -p 'RestrictAddressFamilies=~AF_UNIX AF_INET AF_INET6'"
import socket, sys
open_ = []
for fam in ("AF_UNIX", "AF_INET", "AF_INET6"):
    try:
        socket.socket(getattr(socket, fam)).close(); open_.append(fam)
    except OSError:
        pass
for fam in open_:
    print(f"compare_bridges_linux: {fam} sockets allowed", file=sys.stderr)
sys.exit(1 if open_ else 0)
PY
LANDRUN_VERSION="$({ "$LANDRUN" --version 2>&1 || true; } | head -n1)"
echo "host $(uname -srm)"
echo "lsm $(cat /sys/kernel/security/lsm)"
echo "runner $LANDRUN sha256 $(sha "$LANDRUN"): landrun ${LANDRUN_VERSION}, vcs.revision $LANDRUN_REV, vcs.modified $LANDRUN_MODIFIED, go-landlock $GO_LANDLOCK"
echo "landlock abi $ABI: reads outside grants denied, writes outside WORK/.lake denied, shared builds write-denied"
echo "mounts: provider, Comparator and survey trees read-only; sockets: AF_UNIX, AF_INET, AF_INET6 denied"
echo "systemd unit: ${INVOCATION_ID:-none}"
# Isolation configurations (survey/docs/COMPARATOR_RUNS.md):
#   landrun-linux       Landlock ABI >= 4: landrun's own filesystem and TCP rules apply, plus the
#                       systemd read-only mounts and socket filter checked above;
#   landrun-fs-systemd  Landlock ABI 2-3: --best-effort keeps landrun's filesystem rules only;
#                       network confinement is the systemd socket filter and write/truncate
#                       protection of shared trees is the systemd read-only mounts.
#   (ABI 1 was rejected in step 0; ISOLATION comes from isolation_policy.py.)
NET_RULES="$([ "$ABI" -ge 4 ] && echo "landrun TCP rules (Landlock ABI >= 4)" || echo "dropped by --best-effort (Landlock ABI < 4)")"
AUDIT="$(python3 - "$ABI" "$NET_RULES" "$PROVIDER" "$CMP" "$HERE" "${INVOCATION_ID:-}" "$(uname -r)" "$LANDRUN_REV" "$LANDRUN_MODIFIED" "$GO_LANDLOCK" <<'PY'
import json, sys
abi, net, prov, cmp_, here, unit, kernel, lrev, lmod, gll = sys.argv[1:11]
print(json.dumps({
    "landrun_revision": lrev, "landrun_modified": lmod == "true", "go_landlock": gll,
    "kernel": kernel, "landlock_abi": int(abi), "landrun_flags": "--best-effort --ro / --rw /dev -ldd -add-exec --rwx WORK/.lake",
    "landlock_probes": {"read_outside_grants": "denied", "write_outside_work_lake": "denied",
                        "write_through_shared_build_symlinks": "denied", "write_work_lake": "allowed"},
    "landrun_network_rules": net,
    "readonly_mounts": [prov, cmp_, here],
    "sockets_denied": ["AF_UNIX", "AF_INET", "AF_INET6"],
    "systemd_unit": unit or None,
}, sort_keys=True))
PY
)"
[ -n "${INVOCATION_ID:-}" ] || fail "not running inside a systemd unit (INVOCATION_ID unset)"
python3 -I - "$POLICY" "$ISOLATION" "$AUDIT" <<'PY' || fail "the isolation audit does not meet the policy"
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("isolation_policy", sys.argv[1])
pol = importlib.util.module_from_spec(spec); spec.loader.exec_module(pol)
errs = pol.audit_errors(sys.argv[2], json.loads(sys.argv[3]))
for e in errs:
    print(f"compare_bridges_linux: {e}", file=sys.stderr)
sys.exit(1 if errs else 0)
PY
echo "isolation-audit: $AUDIT"
echo "isolation: $ISOLATION"

# 8. Lean prefix, LEAN_PATH and the BGP212 dependency modules, all inside the sandbox. This is the
#    minimal test: Lake must replay every shared Mathlib trace without writing to it.
#
#    The Lake launcher. On PATH, `lake` is usually elan's proxy (~/.elan/bin/lake), a static (musl)
#    binary that execs the toolchain's dynamically linked bin/lake. landrun -ldd grants execute
#    only on the dependencies of the binary it starts, so with the proxy the ELF interpreter
#    (ld-linux) of the toolchain lake stays non-executable and the exec fails with EACCES. Both
#    this script's sandbox and Comparator's own `lake build` therefore start the toolchain's lake
#    directly: TOOLCHAIN_PATH puts $LEAN_PREFIX/bin first, landrun resolves `lake` there, and -ldd
#    grants its interpreter and libraries, which `lean` and `git` (spawned by Lake, inside the
#    --rox grants) share. No grant is widened.
cd "$WORK"
LEAN_PREFIX="$(lean --print-prefix)"
GIT_BIN="$(command -v git)"
# >>> toolchain-lake (checked before any sandboxed Lake run; fails closed)
TOOLCHAIN_LAKE="$LEAN_PREFIX/bin/lake"
[ "$(basename "$LEAN_PREFIX")" = "$(printf '%s' "$TOOLCHAIN" | sed 's#/#--#; s#:#---#')" ] \
  || fail "lean --print-prefix gives $LEAN_PREFIX, not the elan toolchain directory for $TOOLCHAIN"
[ -f "$TOOLCHAIN_LAKE" ] && [ -x "$TOOLCHAIN_LAKE" ] || fail "no toolchain lake at $TOOLCHAIN_LAKE"
python3 -I - "$TOOLCHAIN_LAKE" <<'PY' || fail "$TOOLCHAIN_LAKE is not a dynamically linked ELF executable (expected the toolchain lake, not a proxy or script)"
import sys
data = open(sys.argv[1], "rb").read(1 << 16)
# ELF magic, then a PT_INTERP program header (type 3) in the 64-bit header table
if data[:4] != b"\x7fELF" or data[4] != 2:
    sys.exit(1)
phoff = int.from_bytes(data[32:40], "little"); phentsize = int.from_bytes(data[54:56], "little")
phnum = int.from_bytes(data[56:58], "little")
types = [int.from_bytes(data[phoff + i * phentsize:phoff + i * phentsize + 4], "little") for i in range(phnum)]
sys.exit(0 if 3 in types else 1)
PY
TOOLCHAIN_PATH="$LEAN_PREFIX/bin:$PATH"
[ "$(PATH="$TOOLCHAIN_PATH" command -v lake)" = "$TOOLCHAIN_LAKE" ] || fail "lake does not resolve to $TOOLCHAIN_LAKE"
"$TOOLCHAIN_LAKE" --version | grep -qF "$(printf '%s' "$TOOLCHAIN" | sed 's#.*:v##')" \
  || fail "$TOOLCHAIN_LAKE is not the $TOOLCHAIN lake"
# <<< toolchain-lake
echo "lake launcher $TOOLCHAIN_LAKE sha256 $(sha "$TOOLCHAIN_LAKE"): $("$TOOLCHAIN_LAKE" --version)"
BOX=(env PATH="$TOOLCHAIN_PATH" "$LANDRUN" "${SANDBOX[@]}" --rox "$LEAN_PREFIX" --rox "$GIT_BIN" --env PATH --env HOME --)
ENV_OUT="$("${BOX[@]}" lake env)" || fail "lake env failed inside the sandbox"
LEAN_PATH_WS="$(printf '%s\n' "$ENV_OUT" | sed -n 's/^LEAN_PATH=//p')"
[ -n "$LEAN_PATH_WS" ] || fail "lake env printed no LEAN_PATH"
echo "== sandboxed dependency build: lake build BGP212.Gap BGP212.MultiShift"
"${BOX[@]}" lake build BGP212.Gap BGP212.MultiShift || fail "sandboxed dependency build failed (a shared artifact may be stale or missing)"
if [ "$MODE" = preflight ]; then
  CHANGED="$(for b in "${SHARED[@]}"; do find "$b/" -newer "$WORK/.lake/run-start" -print -quit; done)"
  [ -z "$CHANGED" ] || fail "a shared build file changed during preflight: $CHANGED"
  echo "preflight: isolation established, dependency build replayed shared artifacts, shared builds unchanged; workspace $(du -sh "$WORK" | cut -f1)"
  exit 0
fi

# 9. Record, then Comparator on each config.
echo "survey compare script $SCRIPT sha256 $(sha "$SCRIPT")"
echo "Comparator $COMPARATOR_PIN (clean); lean4export $LEAN4EXPORT_PIN (clean); toolchain $TOOLCHAIN"
echo "comparator binary sha256 $(sha "$COMPARATOR_BIN"); lean4export binary sha256 $(sha "$COMPARATOR_LEAN4EXPORT")"
lean --version
for f in SurveyChallenge/*.lean SurveySolution/*.lean SurveyBridges/*.lean; do echo "sha256 $(sha "$f")  $f"; done
for cfg in "${CONFIGS[@]}"; do
  rel="Comparator/$(basename "$cfg")"
  echo "== $rel sha256 $(sha "$rel")"
  env PATH="$TOOLCHAIN_PATH" LEAN_PATH="$LEAN_PATH_WS" COMPARATOR_LANDRUN="$LANDRUN" \
    COMPARATOR_LEAN4EXPORT="$COMPARATOR_LEAN4EXPORT" "$COMPARATOR_BIN" "$rel"
done

# 10. Post-checks: shared builds untouched, no hardlinks, workspace size.
CHANGED="$(for b in "${SHARED[@]}"; do find "$b/" -newer "$WORK/.lake/run-start" -print -quit; done)"
[ -z "$CHANGED" ] || fail "a shared build file changed during the run: $CHANGED"
LINKED="$(find "$WORK" -type f -links +1 -print -quit)"
[ -z "$LINKED" ] || fail "hardlinked file in the workspace: $LINKED"
echo "shared builds unchanged; workspace $(du -sh "$WORK" | cut -f1), no hardlinks"
echo "comparator: all configs accepted (isolation: $ISOLATION)"
