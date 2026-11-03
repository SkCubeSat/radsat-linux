#!/bin/bash
set -euo pipefail
echo "=== processes ==="
pgrep -af sync-and-build-image || echo "(no sync script)"
pgrep -af 'make O=/home/logan/radsat-output' | head -8 || true
echo "=== recent interesting log lines ==="
grep -E '0006|0007|malformed|BUILD_|Patching|uboot 1.1.0|error:|FAILED|VERIFY' \
  /home/logan/radsat-output/build-image.nohup.out 2>/dev/null | tail -50 || true
echo "=== log tail ==="
tail -20 /home/logan/radsat-output/build-image.nohup.out 2>/dev/null || true
