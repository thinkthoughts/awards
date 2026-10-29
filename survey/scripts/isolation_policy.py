"""Isolation policy for Linux Comparator runs: one source for compare_bridges_linux.sh and
validate_registry.py.

Configurations, by the Landlock ABI of the kernel that ran Comparator:

  ABI 1     rejected. landrun adds the `refer` right to every read-write directory, and Comparator
            always passes `--rw /dev`; ABI 1 cannot express `refer`, so go-landlock's best-effort
            mode (v0.9.0 and v0.10.1: FSRule.downgrade -> "Use ABI V0 (do nothing)") applies no
            Landlock ruleset at all.
  ABI 2-3   landrun-fs-systemd: landrun's filesystem rules apply (including `refer`); its network
            rules need ABI 4 and are dropped, so the systemd unit's socket filter and read-only
            mounts are required and audited (truncate(2) is a Landlock right only from ABI 3).
  ABI >= 4  landrun-linux: landrun's filesystem and TCP rules apply; the same systemd layers are
            required and audited.

Every Linux run needs its isolation_audit record, with the landrun build pinned by the VCS
revision Go embeds in the binary.

Usage from the shell:  python3 isolation_policy.py ABI   -> prints the configuration, or exits 1.
"""

import sys

LANDRUN_PIN = "ec104f6edc1e14d7fec6d31146f1ec6f9c192c5a"   # landrun main, 2026-10-16 (reports 0.1.18)
GO_LANDLOCK_PIN = "v0.10.1"                                # go.mod of LANDRUN_PIN
REQUIRED_SOCKETS = {"AF_UNIX", "AF_INET", "AF_INET6"}
DENIED_PROBES = ("read_outside_grants", "write_outside_work_lake", "write_through_shared_build_symlinks")
LINUX_ISOLATIONS = {"landrun-linux", "landrun-fs-systemd"}

ABI1_REJECTION = ("Landlock ABI 1: landrun requests the `refer` right for every read-write directory "
                  "(Comparator always passes --rw /dev), which ABI 1 cannot express, so go-landlock's "
                  "best-effort mode applies no Landlock ruleset; a kernel with Landlock ABI >= 2 "
                  "(Linux >= 5.19) is required")


def isolation_for_abi(abi: int) -> str:
    """The isolation configuration for a Landlock ABI, or ValueError for an unusable ABI."""
    if not isinstance(abi, int) or isinstance(abi, bool) or abi < 1:
        raise ValueError(f"Landlock unavailable (ABI {abi!r})")
    if abi == 1:
        raise ValueError(ABI1_REJECTION)
    return "landrun-linux" if abi >= 4 else "landrun-fs-systemd"


def audit_errors(isolation: str, audit) -> list[str]:
    """Reasons an isolation_audit record cannot support Verified for this configuration."""
    if not isinstance(audit, dict):
        return [f"{isolation} needs its isolation_audit record"]
    errs = []
    abi = audit.get("landlock_abi")
    try:
        expected = isolation_for_abi(abi)
        if expected != isolation:
            errs.append(f"Landlock ABI {abi} is the {expected} configuration, not {isolation}")
    except ValueError as e:
        errs.append(str(e))
    probes = audit.get("landlock_probes") or {}
    for probe in DENIED_PROBES:
        if probes.get(probe) != "denied":
            errs.append(f"{isolation} audit lacks a denied {probe} probe")
    if probes.get("write_work_lake") != "allowed":
        errs.append(f"{isolation} audit lacks the allowed write_work_lake probe")
    if not audit.get("readonly_mounts"):
        errs.append(f"{isolation} audit lists no read-only mounts")
    if not REQUIRED_SOCKETS <= set(audit.get("sockets_denied") or []):
        errs.append(f"{isolation} audit must deny AF_UNIX, AF_INET and AF_INET6 sockets")
    if not audit.get("systemd_unit"):
        errs.append(f"{isolation} audit names no systemd unit")
    if audit.get("landrun_revision") != LANDRUN_PIN or audit.get("landrun_modified") is not False:
        errs.append(f"{isolation} audit must record landrun built unmodified from {LANDRUN_PIN} "
                    f"(got {audit.get('landrun_revision')!r}, modified {audit.get('landrun_modified')!r})")
    if audit.get("go_landlock") != GO_LANDLOCK_PIN:
        errs.append(f"{isolation} audit must record go-landlock {GO_LANDLOCK_PIN} (got {audit.get('go_landlock')!r})")
    return errs


if __name__ == "__main__":
    try:
        print(isolation_for_abi(int(sys.argv[1])))
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
