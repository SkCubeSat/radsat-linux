#!/bin/bash
set -e
LOG=/home/logan/radsat-output/build-image.log
OUT=/home/logan/radsat-output
for i in $(seq 1 90); do
  if grep -q 'BUILD_OK' "$LOG" 2>/dev/null; then
    echo "=== BUILD_OK ==="
    grep -E 'BUILD_OK|sha256' "$LOG" | tail -5
    break
  fi
  if grep -q 'BUILD_FAILED' "$LOG" 2>/dev/null; then
    echo BUILD_FAILED
    tail -60 "$LOG"
    exit 1
  fi
  if ! pgrep -f 'sync-and-build-image.sh|make O=/home/logan/radsat-output' >/dev/null; then
    # may have just finished
    if grep -q 'BUILD_OK' "$LOG" 2>/dev/null; then
      break
    fi
    echo BUILD_PROCESS_GONE
    tail -60 "$LOG"
    exit 1
  fi
  echo "still_building minute=$i"
  tail -2 "$LOG" 2>/dev/null | sed 's/^/  /'
  sleep 60
done

test -f /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz
test -f /mnt/c/Users/logan/CubeSAT/install-os
sha256sum /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz

# Extract boot.vfat / image and list FAT for dual u-boot
IMG="$OUT/images/kubos-linux.img"
if [[ ! -f "$IMG" ]]; then
  tar -xzf "$OUT/images/kubos-linux.tar.gz" -C "$OUT/images"
fi
# boot.vfat may still exist
if [[ -f "$OUT/images/boot.vfat" ]]; then
  echo "=== boot.vfat listing ==="
  mdir -i "$OUT/images/boot.vfat" :: || true
fi

echo "=== kpack-uboot ==="
ls -lh "$OUT/images/kpack-uboot.itb" 2>/dev/null || ls -lh "$OUT"/images/kpack*.itb 2>/dev/null || true
# Copy uboot itb to Windows for install
if [[ -f "$OUT/images/kpack-uboot.itb" ]]; then
  cp -f "$OUT/images/kpack-uboot.itb" /mnt/c/Users/logan/CubeSAT/kpack-uboot.itb
  ls -lh /mnt/c/Users/logan/CubeSAT/kpack-uboot.itb
  # smoke: list FIT contents
  if [[ -x "$OUT/build/uboot-1.1.0/tools/mkimage" ]]; then
    "$OUT/build/uboot-1.1.0/tools/mkimage" -l "$OUT/images/kpack-uboot.itb" | head -40
  fi
fi

# Confirm patches applied in built tree
grep -n 'u-boot-bak.img' "$OUT/build/uboot-1.1.0/common/spl/spl_mmc.c" | head
grep -n 'u-boot-bak.img fat' "$OUT/build/uboot-1.1.0/include/configs/beaglebone-black.h" | head
grep -n 'kubos_fit_to_dfu_name' "$OUT/build/uboot-1.1.0/common/update_kubos.c" | head
grep -n 'set +e' "$OUT/target/usr/sbin/install-os" | head

echo VERIFY_OK
