#!/bin/bash
set -euo pipefail
export PATH=/home/logan/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export KUBOS_OVERRIDE_SRCDIR=/mnt/c/Users/logan/CubeSAT/Software
OUT=/home/logan/radsat-output
BR=/home/logan/code/buildroot-2025.02.14
LOG=$OUT/build-image.log
: > "$LOG"
: > "$OUT/build-image.nohup.out"
# Force Kubos source resync from Windows override, then rebuild fram + image.
cd "$BR"
echo "Resyncing kubos from override and rebuilding at $(date -Is)" | tee -a "$LOG"
make O="$OUT" kubos-dirclean || true
make O="$OUT" kubos-fram-dirclean || true
set +e
make O="$OUT" -j"$(nproc)" 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
set -e
if [[ "$rc" -ne 0 ]]; then
  echo "BUILD_FAILED rc=$rc" | tee -a "$LOG"
  exit "$rc"
fi
if [[ ! -f "$OUT/images/kubos-linux.img" ]]; then
  if [[ -f "$OUT/images/kubos-linux.tar.gz" ]]; then
    tar -xzf "$OUT/images/kubos-linux.tar.gz" -C "$OUT/images"
  fi
fi
if [[ ! -f "$OUT/images/kubos-linux.img" ]]; then
  echo "ERROR: kubos-linux.img missing" | tee -a "$LOG"
  ls -la "$OUT/images" | tee -a "$LOG"
  echo BUILD_FAILED | tee -a "$LOG"
  exit 1
fi
gzip -c -9 "$OUT/images/kubos-linux.img" > "$OUT/images/kubos-linux.img.gz"
cp -v "$OUT/images/kubos-linux.img.gz" /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz
sha256sum "$OUT/images/kubos-linux.img.gz" | tee -a "$LOG"
echo "BUILD_OK $(date -Is)" | tee -a "$LOG"
