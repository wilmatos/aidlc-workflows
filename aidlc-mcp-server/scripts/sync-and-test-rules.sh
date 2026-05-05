#!/usr/bin/env bash
# sync-and-test-rules.sh — Sync rules from monorepo root and run tests.
#
# Since the aidlc-mcp-server now lives inside the aidlc-workflows monorepo,
# rules are always sourced locally. There is no remote fallback mechanism —
# if tests fail, the rules in the monorepo need to be fixed.
#
# Usage:
#   ./scripts/sync-and-test-rules.sh
#
# Exit codes:
#   0 — sync succeeded and tests pass
#   1 — sync failed or tests fail

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SYNC_SCRIPT="$SCRIPT_DIR/sync-aidlc-rules.sh"

echo "=== Step 1: Sync rules from monorepo root ==="
"$SYNC_SCRIPT"

echo ""
echo "=== Step 2: Run tests ==="
if pytest --tb=short -q 2>&1; then
    echo ""
    echo "=== Tests passed ==="
    exit 0
fi

echo ""
echo "=== Tests FAILED ===" >&2
echo "The rules from the monorepo root caused test failures." >&2
echo "Fix the rules in the monorepo's aidlc-rules/ directory." >&2
exit 1
