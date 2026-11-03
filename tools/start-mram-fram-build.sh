#!/bin/bash
set -eu
export PATH=/home/logan/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
LOG=/home/logan/radsat-output/build-image.nohup.out
mkdir -p /home/logan/radsat-output
tr -d '\r' < /mnt/c/Users/logan/CubeSAT/radsat-linux/tools/sync-and-build-image.sh > /tmp/sync-and-build-image.sh
chmod +x /tmp/sync-and-build-image.sh
# Kill any prior sync if stuck
pkill -f '/tmp/sync-and-build-image.sh' 2>/dev/null || true
pkill -f 'sync-and-build-image.sh' 2>/dev/null || true
sleep 1
: > "$LOG"
setsid bash /tmp/sync-and-build-image.sh </dev/null >"$LOG" 2>&1 &
echo "started pid $!"
sleep 3
pgrep -af sync-and-build-image || echo "WARNING: sync process not found"
tail -20 "$LOG"
