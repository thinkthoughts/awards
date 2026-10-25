# Comparator runs

How the survey runs Lean Comparator on its Challenge/Solution pairs, and how each run is recorded.

## Verification policy

| Check | Verification value | Lift state | Obligation |
| --- | --- | --- | --- |
| Kernel acceptance and axiom audit (`check_bridges.sh`) | `kernel-checked` | Compiled | open |
| Comparator acceptance without sandbox isolation | `comparator-nonisolated` | Compiled | open |
| Comparator acceptance under landrun on Linux | `comparator-accepted` | Verified | discharged |

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

The smallest reproduction with the same pins. Needs Linux ≥ 5.13 with Landlock active
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
