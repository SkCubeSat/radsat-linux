#!/bin/bash
set -e
LOG=/home/logan/radsat-output/build-image.log
NOHUP=/home/logan/radsat-output/build-image.nohup.out
for i in $(seq 1 90); do
  if grep -qE 'BUILD_OK|BUILD_FAILED' "$LOG" 2>/dev/null; then
    grep -E 'BUILD_OK|BUILD_FAILED|sha256' "$LOG" | tail -5
    tail -15 "$LOG"
    exit 0
  fi
  if ! pgrep -f 'sync-and-build-image.sh|make O=/home/logan/radsat-output' >/dev/null; then
    echo BUILD_PROCESS_GONE
    tail -40 "$NOHUP" 2>/dev/null || tail -40 "$LOG"
    exit 1
  fi
  echo "still_building minute=$i"
  tail -2 "$LOG" 2>/dev/null | sed 's/^/  /'
  sleep 60
done
echo TIMEOUT
tail -40 "$LOG"
exit 2
