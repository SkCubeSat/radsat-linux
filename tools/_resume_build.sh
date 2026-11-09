#!/bin/bash
set -euo pipefail
export PATH=/home/logan/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export BUILD_FLIGHT_IMAGE=0
# Local Software tree — never git-fetch GitHub for KubOS.
export KUBOS_OVERRIDE_SRCDIR=/mnt/c/Users/logan/CubeSAT/Software
BR=/home/logan/code/buildroot-2025.02.14
DST=/home/logan/code/radsat-linux
OUT=/home/logan/radsat-output
LOG=$OUT/build-image.console.log
cd "$BR"
make O="$OUT" BR2_EXTERNAL="$DST" beaglebone-black_defconfig
# Keep existing kubos-custom rsync; only rebuild fram package that failed.
make O="$OUT" kubos-fram-dirclean || true
echo "Starting make at $(date -Is) (KUBOS_OVERRIDE_SRCDIR=$KUBOS_OVERRIDE_SRCDIR)" > "$LOG"
set +e
make O="$OUT" -j"$(nproc)" >>"$LOG" 2>&1
rc=$?
echo "BUILD_RC=$rc $(date -Is)" >>"$LOG"
# finish packaging if make succeeded
if [[ "$rc" -eq 0 ]]; then
  install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/etc/init.d/S92radsat-boot-stamp" \
    "$OUT/target/etc/init.d/S92radsat-boot-stamp" || true
  if [[ ! -f "$OUT/images/kubos-linux.img" && -f "$OUT/images/kubos-linux.tar.gz" ]]; then
    tar -xzf "$OUT/images/kubos-linux.tar.gz" -C "$OUT/images"
  fi
  if [[ -f "$OUT/images/kubos-linux.img" ]]; then
    gzip -c -9 "$OUT/images/kubos-linux.img" > "$OUT/images/kubos-linux.img.gz"
    cp -v "$OUT/images/kubos-linux.img.gz" /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz
    sha256sum "$OUT/images/kubos-linux.img.gz" | tee -a "$LOG"
    echo "BUILD_OK $(date -Is)" >>"$LOG"
  else
    echo "ERROR: no kubos-linux.img" >>"$LOG"
    rc=1
  fi
fi
exit $rc
