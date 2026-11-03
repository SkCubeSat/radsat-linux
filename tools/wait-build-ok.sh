#!/bin/bash
set -eu
LOG=/home/logan/radsat-output/build-image.nohup.out
for i in $(seq 1 180); do
  if grep -q 'BUILD_OK' "$LOG" 2>/dev/null; then
    echo BUILD_OK
    grep BUILD_OK "$LOG" | tail -1
    sha256sum /home/logan/radsat-output/images/kubos-linux.img.gz 2>/dev/null || true
    exit 0
  fi
  if grep -q 'BUILD_FAILED' "$LOG" 2>/dev/null; then
    echo BUILD_FAILED
    grep -E 'BUILD_FAILED|Error|error:|malformed|adhoc' "$LOG" | tail -40
    exit 1
  fi
  if (( i % 6 == 0 )); then
    echo "still building... $(date -Is)"
    tail -3 "$LOG" || true
  fi
  sleep 30
done
echo TIMEOUT
tail -40 "$LOG"
exit 2
