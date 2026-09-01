#!/usr/bin/env bash
# Point git at the tracked hooks in scripts/hooks/.
#
# Uses core.hooksPath rather than copying into .git/hooks, so a hook edit takes
# effect for everyone on their next pull instead of silently going stale in
# each clone.

set -euo pipefail

root=$(git rev-parse --show-toplevel)
chmod +x "$root/scripts/hooks/"* 2>/dev/null || true
git -C "$root" config core.hooksPath scripts/hooks
echo "core.hooksPath -> scripts/hooks"
printf '  %s\n' "$root"/scripts/hooks/*
