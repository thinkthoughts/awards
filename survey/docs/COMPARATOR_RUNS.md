# Comparator runs

How the survey runs Lean Comparator on its Challenge/Solution pairs, and how each run is recorded.

## Verification policy

| Check | Verification value | Lift state | Obligation |
| --- | --- | --- | --- |
| Kernel acceptance and axiom audit (`check_bridges.sh`) | `kernel-checked` | Compiled | open |
| Comparator acceptance without sandbox isolation | `comparator-nonisolated` | Compiled | open |
| Comparator acceptance under landrun on Linux | `comparator-accepted` | Verified | discharged |

Linux runs record one of two isolation configurations:

| `isolation` | Kernel | Filesystem confinement | Network confinement | Shared-tree protection |
| --- | --- | --- | --- | --- |
| `landrun-linux` | Landlock ABI ≥ 4 (Linux ≥ 6.7) | landrun (Landlock) | landrun TCP rules, plus the systemd socket filter | Landlock, plus systemd read-only mounts |
| `landrun-fs-systemd` | Landlock ABI 2–3 (Linux 5.19–6.6) | landrun (Landlock filesystem rules; `--best-effort` drops the network rules) | systemd `RestrictAddressFamilies=~AF_UNIX AF_INET AF_INET6` | systemd `ReadOnlyPaths=` (also covers `truncate(2)` on ABI 2) |
| rejected | Landlock ABI 1 (Linux 5.13–5.18, e.g. 5.15) | none: see below | — | — |

Both Linux configurations count for `comparator-accepted` only with their `isolation_audit` record:
the `isolation-audit:` line that `compare_bridges_linux.sh` prints, copied verbatim. The policy
(`survey/scripts/isolation_policy.py`, shared by the runner and the validator) requires:
- a Landlock ABI matching the label (2–3 for `landrun-fs-systemd`, ≥ 4 for `landrun-linux`);
- the three Landlock probes denied (read outside grants, write outside `WORK/.lake`, write through
  the shared build symlinks) and the write into `WORK/.lake` allowed;
- at least one read-only mount, AF_UNIX, AF_INET and AF_INET6 sockets denied, a systemd unit id;
- landrun built unmodified from `ec104f6` with go-landlock `v0.10.1`.

**Why ABI 1 is rejected.** landrun adds Landlock's `refer` right (moving or linking files between
directories) to every read-write directory rule, and Comparator always passes `--rw /dev`, plus
`--rwx <project>/.lake` for builds. ABI 1 cannot express `refer`. In best-effort mode go-landlock
(v0.9.0 and v0.10.1 alike) then gives up on the whole ruleset: `FSRule.downgrade` returns
`ok = false` and `downgrade()` returns ABI "V0 (do nothing)", so the command runs with no Landlock
restriction although landrun reports success. A read-only-only probe is still enforced, which is
why only a write probe with Comparator's flags reveals it. The runner therefore rejects ABI 1 in
its first step, before creating a workspace or starting Comparator.

Disposable diagnostic (writes only under a fresh temporary directory):

```bash
T="$(mktemp -d)"; mkdir -p "$T/allowed" "$T/outside"; LR="$HOME/landrun/landrun"
python3 -c 'import ctypes; print("landlock abi", ctypes.CDLL(None).syscall(444, None, 0, 1))'
"$LR" --best-effort --ro / --rw /dev -ldd -add-exec --rwx "$T/allowed" -- /usr/bin/touch "$T/outside/A"; echo "A exit $?"
"$LR" --best-effort --ro / -ldd -add-exec -- /usr/bin/touch "$T/outside/B"; echo "B exit $?"
"$LR" --best-effort --ro / --rw /dev -ldd -add-exec -- /usr/bin/touch "$T/outside/C"; echo "C exit $?"
"$LR" --ro / --rw /dev -ldd -add-exec --rwx "$T/allowed" -- /bin/true; echo "D exit $?"
ls "$T/outside"; rm -rf "$T"
```

On ABI 1, A and C succeed (no ruleset), B is denied, D reports missing kernel support. On ABI ≥ 2,
A, B and C are denied.

**The Lake launcher.** On `PATH`, `lake` is normally elan's proxy (`~/.elan/bin/lake`), a static
(musl) binary that execs the toolchain's dynamically linked `bin/lake`. landrun's `-ldd` grants
execute only on the dependencies of the binary it starts, so through the proxy the toolchain lake's
ELF interpreter (`ld-linux`) is not executable and the exec fails with `Permission denied`. The
runner therefore starts the toolchain lake itself, for its own sandboxed `lake env`/`lake build` and
for Comparator's: it puts `$(lean --print-prefix)/bin` first on `PATH`, after checking that the
prefix is the elan directory for the survey toolchain, that `bin/lake` is a dynamically linked ELF
(not the proxy), that `lake` resolves to it and that it reports the toolchain version. The grants
stay as they were: `--rox` on the Lean prefix and `git`, `-ldd -add-exec` for the started binary,
`--rwx WORK/.lake`. Lake's own children (`lean`, `git`) share that interpreter.

**The landrun build.** `landrun --version` prints `0.1.18` for both `811cfff` (go-landlock v0.9.0)
and the pin `ec104f6` (go-landlock v0.10.1), so the runner identifies the build from the module
information Go embeds in the binary (`vcs.revision`, `vcs.modified`, and the go-landlock
dependency line) and requires the pin. Build it in a clean checkout so that information is
present: `git checkout --detach ec104f6edc1e14d7fec6d31146f1ec6f9c192c5a && go build -buildvcs=true
-o landrun ./cmd/landrun`, then check with `go version -m landrun`. Both versions share the ABI 1
behaviour above.

`compare_bridges.sh` prints one `isolation:` line, `landrun-linux` or `non-isolating`, and the
evidence record copies it into its `isolation` field. The validator admits `comparator-accepted`
only with `landrun-linux` evidence.

Each Comparator evidence record keeps: the exact Comparator output (the full `tee` log, and its
sha256), the toolchain, the Comparator and lean4export commits and binary sha256s, the runner path,
sha256 and description, the host line, the lean-bgp212 pin, and the sha256 of every Challenge,
Solution, bridge and config file.

## Pinned versions

| Component | Version |
| --- | --- |
| Lean toolchain | `leanprover/lean4:v4.34.0-rc2` (`survey/lean-bridges/lean-toolchain`) |
| lean-bgp212 | `89b43fa` (`survey/lean-bridges/lakefile.toml`), with `BGP212.Gap` built |
| Comparator | `19e111e2141cf333c7daff0f64c5f24acc91dd2e` (last commit targeting 4.34.0-rc2) |
| lean4export | `cacf989bd75f608700820f6afc595f32e7a99a4d` (Comparator's manifest pin) |
| landrun (Linux only) | `ec104f6edc1e14d7fec6d31146f1ec6f9c192c5a` (main, 2026-10-16; reports 0.1.18), Go ≥ 1.24 |

Comparator's `main` now targets v4.35 and core Lean ships it as `lake comparator` from v4.35.0, so
the 4.34.0-rc2 run uses a separate checkout at `19e111e`. An existing v4.35 checkout stays as it is.

## macOS: non-isolated run (records `comparator-nonisolated`)

landrun needs Linux Landlock. On macOS the explicitly non-isolating runner
`survey/scripts/landrun-noisolate.sh` stands in for it: it drops every sandbox option and runs the
command after `--` with full access. Its second line carries the marker
`SURVEY-NONISOLATING-RUNNER`, which `compare_bridges.sh` detects.

```bash
# One-time: a Comparator checkout for 4.34.0-rc2, next to (not inside) the existing ~/comparator.
git clone https://github.com/leanprover/comparator ~/comparator-v4.34.0-rc2
cd ~/comparator-v4.34.0-rc2
git checkout 19e111e2141cf333c7daff0f64c5f24acc91dd2e
cat lean-toolchain                                    # leanprover/lean4:v4.34.0-rc2
lake build                                            # comparator binary
(cd .lake/packages/lean4export && git rev-parse HEAD && lake build)   # cacf989..., lean4export binary

# The run. Writes nothing in ~/lean-bgp212 or survey/lean-bridges; the workspace is temporary.
cd ~/awards
mkdir -p ~/comparator-runs
COMPARATOR_LANDRUN="$HOME/awards/survey/scripts/landrun-noisolate.sh" \
  survey/scripts/compare_bridges.sh ~/lean-bgp212 ~/comparator-v4.34.0-rc2 \
  survey/lean-bridges/Comparator/h1le_mono.json \
  2>&1 | tee ~/comparator-runs/h1le_mono-macos-nonisolated.log
echo "exit ${PIPESTATUS[0]}"
shasum -a 256 ~/comparator-runs/h1le_mono-macos-nonisolated.log
```

Acceptance shows `Your solution is okay!` from Comparator, then
`comparator: all configs accepted (isolation: non-isolating)` and exit 0. This records
LIFT-041-2 as `comparator-nonisolated`; the lift stays Compiled with its obligation open.

## Linux VPS: isolated run (records `comparator-accepted`)

> Superseded for formal evidence by `compare_bridges_linux.sh` (next section): Linux Comparator
> evidence now needs the `isolation_audit` record that only that runner prints.

The smallest reproduction with the same pins. Needs Linux ≥ 5.19 with Landlock active (ABI ≥ 2)
(`/sys/kernel/security/lsm` lists `landlock`), systemd with a user session, git, curl, python3,
Go ≥ 1.24, and a non-root user. Disk: about 8 GB for lean-bgp212 with the Mathlib cache, plus as
much again for the temporary workspace on filesystems without reflink (ext4); XFS or Btrfs clone
instead.

```bash
# 1. Toolchain
curl -sSf https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh \
  | sh -s -- -y --default-toolchain none
source ~/.elan/env

# 2. lean-bgp212 at the pin, BGP212.Gap built from the Mathlib cache
git clone https://github.com/thinkthoughts/lean-bgp212 ~/lean-bgp212
cd ~/lean-bgp212 && git checkout 89b43fa
lake exe cache get
lake build BGP212.Gap

# 3. Comparator and lean4export at their pins
git clone https://github.com/leanprover/comparator ~/comparator-v4.34.0-rc2
cd ~/comparator-v4.34.0-rc2 && git checkout 19e111e2141cf333c7daff0f64c5f24acc91dd2e
lake build && (cd .lake/packages/lean4export && lake build)

# 4. landrun from main at the pinned commit
git clone https://github.com/Zouuup/landrun ~/landrun
cd ~/landrun && git checkout ec104f6edc1e14d7fec6d31146f1ec6f9c192c5a
go build -o landrun ./cmd/landrun && ./landrun --version

# 5. The survey branch
git clone -b survey/prime-bridges https://github.com/thinkthoughts/awards ~/awards

# 6. The run, with AF_UNIX blocked as Comparator's README requires
cd ~/awards && mkdir -p ~/comparator-runs
systemd-run --user --pipe --same-dir --wait --collect \
  -p RestrictAddressFamilies=~AF_UNIX -E PATH="$PATH" -E HOME="$HOME" \
  -E COMPARATOR_LANDRUN="$HOME/landrun/landrun" -- \
  survey/scripts/compare_bridges.sh ~/lean-bgp212 ~/comparator-v4.34.0-rc2 \
  survey/lean-bridges/Comparator/h1le_mono.json \
  2>&1 | tee ~/comparator-runs/h1le_mono-linux-landrun.log
sha256sum ~/comparator-runs/h1le_mono-linux-landrun.log
```

Before Comparator runs, `compare_bridges.sh` establishes isolation, because Comparator passes
landrun `--best-effort`, which would otherwise fall back silently on a kernel without Landlock:

- Landlock is an active LSM;
- landrun runs with `-ldd -add-exec` and no `--best-effort`, and denies a read outside its grants;
- AF_UNIX sockets cannot be created.

If any of these fails, the script stops. On success it prints `isolation: landrun-linux`, and the
log ends `comparator: all configs accepted (isolation: landrun-linux)`. That log is the evidence
for `comparator-accepted`: LIFT-041-2 becomes Verified and its obligation discharged.

## Linux VPS with an existing build: shared read-only dependencies (`compare_bridges_linux.sh`)

`compare_bridges.sh` copies every dependency build into its workspace, about 16 GB for Mathlib on
ext4. `compare_bridges_linux.sh` shares those builds read-only instead and copies nothing
compiled, so an existing VPS build serves the formal run unchanged.

**Workspace layout** (`$COMPARE_WORKDIR_BASE/survey-compare.XXXXXX`, removed afterwards):

| Path | Content | Writable in the sandbox |
| --- | --- | --- |
| `./` | survey/lean-bridges sources | no |
| `.lake/packages/bgp212` | checkout of `89b43fa` from the provider's git objects (alternates) | yes; BGP212 modules compiled here from pinned sources |
| `.lake/packages/<dep>` | checkout of the manifest revision (alternates) | yes (Lake's `lakefile.olean`) |
| `.lake/packages/<dep>/.lake/build` | symlink to the provider's build | no: resolves outside `WORK/.lake`, and the provider is a read-only mount |

Sources come from git objects at the pinned revisions, never from the provider's working trees;
alternates borrow objects read-only and no file is hardlinked (the script checks `-links +1`).
Lake verifies every shared module against its trace by content hash, so a build that does not
match the pinned sources makes Lake attempt a rebuild, which the sandbox denies: the run fails
instead of using or altering it.

**Isolation, three layers, all checked before Comparator runs:**
1. Landlock through Comparator's own landrun flags (`--best-effort --ro / --rw /dev --rwx WORK/.lake`):
   reads outside the grants and writes outside `WORK/.lake` are probed and must fail.
2. systemd mount namespace (`PrivateUsers=yes`, `ReadOnlyPaths=`): provider, Comparator and
   awards trees are read-only mounts (checked with `statvfs`). This also covers `truncate(2)`,
   which Landlock controls only from ABI 3 (Linux 6.2).
3. systemd seccomp (`RestrictAddressFamilies=~AF_UNIX AF_INET AF_INET6`): socket creation for
   all three families is probed and must fail. Landlock's own network rules need ABI 4
   (Linux 6.7); on ABI 2–3 `--best-effort` drops them, and this layer replaces them.

The log records the Landlock ABI and the resulting configuration: on ABI ≥ 4 `isolation:
landrun-linux`; on ABI 2–3 `isolation: landrun-fs-systemd`, followed by the `isolation-audit:` JSON
line for the evidence record. ABI 1 (Linux 5.15) is rejected in the first step. The script refuses
to run outside a systemd unit.

**Disk** (ext4, no reflink): the script sums the exact blob sizes of every checkout and requires
that plus 512 MiB plus a 1 GiB margin. Expected:

| Item | Size |
| --- | --- |
| Dependency source checkouts (Mathlib about 150 MB, others about 40 MB) | about 190 MB |
| lean-bgp212 checkout at `89b43fa` | about 40 MB |
| BGP212 closure of `Gap`, `MultiShift` and survey builds | under 150 MB |
| Lake configuration oleans of Lean-configured packages | under 20 MB |
| Workspace total | about 0.4 GB (script requires ≈ 1.9 GB free) |
| Comparator `19e111e` checkout and build, lean4export `cacf989` | about 0.3 GB |
| landrun build (plus Go toolchain if absent, about 0.6 GB) | 0.01–0.7 GB |
| **Total additional** | **about 0.7–1.4 GB of 6.5 GB** |

**Prerequisites:** Linux ≥ 5.19 with Landlock ABI ≥ 2, systemd user manager with unprivileged user
namespaces (`PrivateUsers=yes`), git, python3, elan with `v4.34.0-rc2`, a provider lean-bgp212
checkout that contains `89b43fa` and whose `.lake/packages` sit at the survey manifest revisions
with clean trees and complete builds, Comparator at exactly `19e111e` with lean4export
`cacf989`, landrun `ec104f6`.

```bash
# Pinned Comparator, separate from the existing checkout (alternates, no hardlinks)
git clone --shared ~/comparator ~/comparator-19e111e
cd ~/comparator-19e111e && git checkout --detach 19e111e2141cf333c7daff0f64c5f24acc91dd2e
lake build && (cd .lake/packages/lean4export && git rev-parse HEAD && lake build)

# landrun at the pinned commit; the runner checks the embedded vcs.revision and go-landlock version
git clone https://github.com/Zouuup/landrun ~/landrun   # or reuse the existing checkout
cd ~/landrun && git checkout --detach ec104f6edc1e14d7fec6d31146f1ec6f9c192c5a && git status --short
go build -buildvcs=true -o landrun ./cmd/landrun && go version -m landrun | grep -E 'vcs\.|go-landlock'

# Unit options shared by the preflight and the run
mkdir -p ~/survey-compare ~/comparator-runs
UNIT=(systemd-run --user --pipe --same-dir --wait --collect -p PrivateUsers=yes
      -p ReadOnlyPaths="$HOME/lean-bgp212" -p ReadOnlyPaths="$HOME/comparator-19e111e"
      -p ReadOnlyPaths="$HOME/awards" -p 'RestrictAddressFamilies=~AF_UNIX AF_INET AF_INET6'
      -E PATH="$PATH" -E HOME="$HOME" -E COMPARATOR_LANDRUN="$HOME/landrun/landrun"
      -E COMPARE_WORKDIR_BASE="$HOME/survey-compare" --)
cd ~/awards

# Minimal test: pins, layout, isolation probes, sandboxed BGP212 build on shared Mathlib
"${UNIT[@]}" survey/scripts/compare_bridges_linux.sh --preflight ~/lean-bgp212 ~/comparator-19e111e \
  2>&1 | tee ~/comparator-runs/linux-preflight.log

# Formal run, first target
"${UNIT[@]}" survey/scripts/compare_bridges_linux.sh ~/lean-bgp212 ~/comparator-19e111e \
  survey/lean-bridges/Comparator/h1le_mono.json 2>&1 | tee ~/comparator-runs/h1le_mono-linux-landrun.log
```

The admissibility configs follow the same way (`admissibleZ_subset.json`,
`admissibleZ_pair_iff_even.json`, `admissibleZ_iff_nu_lt.json`). A successful log ends
`comparator: all configs accepted (isolation: landrun-fs-systemd)` on ABI 2–3 (`landrun-linux`
on ABI ≥ 4) after `shared builds unchanged;
… no hardlinks`.

The twin-prime configs run in three groups, ordered by mathematical dependency so that each
failure points at one layer:

1. **Admissibility of `{0, 2}`** (`admissible_twin.json`, LIFT-009-5; `admissible_twin_of_pair.json`,
   LIFT-009-6): statements over lean-bgp212's `AdmissibleZ` only; no survey definition restated.
2. **Twin primes and `H1Le 2`** (`twin_primes_iff_h1Le_two.json`, LIFT-009-3): the equivalence, its
   two directions and its two side conditions; `InfinitelyManyTwinPrimes` restated verbatim under
   `open BGP212.Gap Filter`.
3. **Twin primes ⇒ `H1Le 186`** (`twin_primes_implies_h1Le_186.json`, LIFT-041-3): the composition,
   whose steps are group 2 and `h1le_mono.json` (LIFT-041-2, EV-0013). A failure here with group 2
   accepted isolates the composition.
