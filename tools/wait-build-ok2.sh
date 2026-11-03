#!/bin/bash
set -eu
LOG=/home/logan/radsat-output/build-image.nohup.out
# Ignore failures that occurred before this waiter started.
start_lines=$(wc -l < "$LOG")
echo "watching from line $start_lines"
for i in $(seq 1 240); do
  tail -n +"$((start_lines + 1))" "$LOG" > /tmp/build-watch.tail || true
  if grep -q 'BUILD_OK' /tmp/build-watch.tail 2>/dev/null; then
    echo BUILD_OK
    grep BUILD_OK /tmp/build-watch.tail | tail -1
    ls -lh /home/logan/radsat-output/images/kubos-linux.img.gz /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz 2>/dev/null || true
    sha256sum /home/logan/radsat-output/images/kubos-linux.img.gz 2>/dev/null || true
    # Quick artifact checks for this plan
    test -f /home/logan/radsat-output/target/etc/init.d/S79mram-env-sync && echo S79_OK
    test -x /home/logan/radsat-output/target/usr/sbin/mram-env-sync && echo MRAM_ENV_SYNC_OK || echo MRAM_ENV_SYNC_MISSING
    test -x /home/logan/radsat-output/target/usr/sbin/fram-get && echo FRAM_GET_OK
    grep -q env_mram /home/logan/radsat-output/build/uboot-1.1.0/common/Makefile && echo UBOOT_ENV_MRAM_OK
    test -f /home/logan/radsat-output/build/uboot-1.1.0/common/fram_mission.c && echo UBOOT_FRAM_OK
    exit 0
  fi
  if grep -q 'BUILD_FAILED' /tmp/build-watch.tail 2>/dev/null; then
    echo BUILD_FAILED
    grep -E 'BUILD_FAILED|Error|error:|malformed|adhoc|FAILED' /tmp/build-watch.tail | tail -50
    exit 1
  fi
  if (( i % 6 == 0 )); then
    echo "still building... $(date -Is) line=$(wc -l < "$LOG")"
    tail -2 "$LOG" || true
  fi
  sleep 30
done
echo TIMEOUT
tail -40 "$LOG"
exit 2
