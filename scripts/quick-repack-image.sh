#!/bin/bash
set -euo pipefail
export PATH=/home/logan/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export KUBOS_OVERRIDE_SRCDIR=/mnt/c/Users/logan/CubeSAT/Software

OUT=/home/logan/radsat-output
BR=/home/logan/code/buildroot-2025.02.14
LOG=/home/logan/radsat-output/build-image.log

: > "$LOG"
{
  echo "QUICK_REPACK_START $(date -Is)"
  # Ensure FRAM/MRAM order
  install -D -m 0755 /home/logan/code/radsat-linux/package/kubos/kubos-fram/kubos-fram \
    "$OUT/target/etc/init.d/S80kubos-fram"
  install -D -m 0755 /home/logan/code/radsat-linux/package/kubos/kubos-mram/kubos-mram \
    "$OUT/target/etc/init.d/S91kubos-mram"
  rm -f "$OUT/target/etc/init.d/S90kubos-fram" "$OUT/target/etc/init.d/S90kubos-mram"

  rm -f "$OUT/images/rootfs.ext4" "$OUT/images/kubos-linux.img" \
        "$OUT/images/kubos-linux.img.gz" "$OUT/images/kubos-linux.tar.gz"
  cd "$BR"
  make O="$OUT" -j"$(nproc)"

  if [[ ! -f "$OUT/images/kubos-linux.img" ]]; then
    tar -xzf "$OUT/images/kubos-linux.tar.gz" -C "$OUT/images"
  fi
  gzip -c -9 "$OUT/images/kubos-linux.img" > "$OUT/images/kubos-linux.img.gz"
  cp -f "$OUT/images/kubos-linux.img.gz" /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz
  sha256sum /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz
  grep -n 'set +e' "$OUT/target/usr/sbin/install-os" | head -3
  echo "BUILD_OK $(date -Is)"
} 2>&1 | tee -a "$LOG"
