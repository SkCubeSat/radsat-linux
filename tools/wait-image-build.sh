#!/bin/bash
set -e
LOG=/home/logan/radsat-output/build-image.log
NOHUP=/home/logan/radsat-output/build-image.nohup.out
for i in $(seq 1 90); do
  if grep -qE 'BUILD_OK|BUILD_FAILED' "$LOG" 2>/dev/null; then
    grep -E 'BUILD_OK|BUILD_FAILED' "$LOG" | tail -1
    exit 0
  fi
  if grep -qE 'BUILD_OK|BUILD_FAILED' "$NOHUP" 2>/dev/null; then
    grep -E 'BUILD_OK|BUILD_FAILED' "$NOHUP" | tail -1
    exit 0
  fi
  if ! pgrep -f 'sync-and-build-image.sh|make O=/home/logan/radsat-output' >/dev/null; then
    echo BUILD_PROCESS_GONE
    tail -50 "$NOHUP"
    exit 1
  fi
  lines=$(wc -l < "$NOHUP" || echo 0)
  echo "still_building minute=$i lines=$lines"
  tail -3 "$NOHUP" | sed 's/^/  /'
  sleep 60
done
echo TIMEOUT
tail -40 "$NOHUP"
exit 2
