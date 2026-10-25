#!/usr/bin/env bash
# SURVEY-NONISOLATING-RUNNER
#
# A stand-in for landrun that provides NO sandbox. It accepts landrun's command line, ignores every
# option before `--`, and runs the command after `--` directly, with the caller's full file-system
# and network access.
#
# Purpose: lets Lean Comparator run on macOS, where landrun (Linux Landlock) is unavailable.
# compare_bridges.sh recognises this file by the marker on line 2 and reports
# `isolation: non-isolating`; an acceptance obtained through it is recorded as
# comparator-nonisolated and leaves the lift at Compiled. Only a run under real landrun on Linux
# (`isolation: landrun-linux`) is recorded as comparator-accepted (Verified).
set -euo pipefail
while [ "$#" -gt 0 ] && [ "$1" != "--" ]; do shift; done
[ "$#" -gt 0 ] || { echo "landrun-noisolate: no -- separator in arguments" >&2; exit 2; }
shift
exec "$@"
