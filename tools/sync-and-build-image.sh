#!/bin/bash
set -euo pipefail

# WSL inherits a Windows PATH with spaces; Buildroot rejects that.
export PATH=/home/logan/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export KUBOS_OVERRIDE_SRCDIR=/mnt/c/Users/logan/CubeSAT/Software

SRC=/mnt/c/Users/logan/CubeSAT/radsat-linux
DST=/home/logan/code/radsat-linux
BR=/home/logan/code/buildroot-2025.02.14
OUT=/home/logan/radsat-output
LOG=/home/logan/radsat-output/build-image.log

cp -v "$SRC/board/kubos/beaglebone-black/beaglebone-black.dts" \
  "$DST/board/kubos/beaglebone-black/"
cp -v "$SRC/board/kubos/beaglebone-black/beaglebone-black_config" \
  "$DST/board/kubos/beaglebone-black/"
cp -v "$SRC/board/kubos/beaglebone-black/linux-kubos.config" \
  "$DST/board/kubos/beaglebone-black/"
cp -v "$SRC/common/patches/uboot/0002-bbb-env-on-boot-mmc.patch" \
  "$DST/common/patches/uboot/"

# Verify the new U-Boot patch applies on top of the baudrate patch.
UBOOT_SRC=$(ls -d "$OUT"/build/uboot-* 2>/dev/null | head -n1 || true)
if [[ -n "${UBOOT_SRC}" && -f "${UBOOT_SRC}/include/configs/beaglebone-black.h" ]]; then
  echo "Checking U-Boot patch against ${UBOOT_SRC}"
  TMP=$(mktemp -d)
  cp "${UBOOT_SRC}/include/configs/beaglebone-black.h" "$TMP/"
  # Re-apply from clean: extract original from git if available, else dry-run the hunks.
  if ! grep -q 'EXT4_ENV_DEVICE_AND_PART "0:3"' \
    "${UBOOT_SRC}/include/configs/beaglebone-black.h"; then
    echo "Current U-Boot tree still has the old env path; rebuild will re-extract and patch."
    grep -n 'EXT4_ENV_DEVICE_AND_PART\|KUBOS_UPGRADE_PART' \
      "${UBOOT_SRC}/include/configs/beaglebone-black.h" || true
  fi
  rm -rf "$TMP"
fi

cd "$BR"
make O="$OUT" BR2_EXTERNAL="$DST" beaglebone-black_defconfig

# Only wipe packages we changed if they are still present.
[[ -d "$OUT/build/uboot-1.1.0" ]] && make O="$OUT" uboot-dirclean || true
[[ -d "$OUT/build/linux-4.4.23" ]] && make O="$OUT" linux-dirclean || true

echo "Starting full image build at $(date -Is)" | tee "$LOG"
set +e
make O="$OUT" -j"$(nproc)" 2>&1 | tee -a "$LOG"
rc=${PIPESTATUS[0]}
set -e
if [[ "$rc" -ne 0 ]]; then
  echo "BUILD_FAILED rc=$rc" | tee -a "$LOG"
  exit "$rc"
fi

# post-image.sh deletes kubos-linux.img after packaging tar.gz
if [[ ! -f "$OUT/images/kubos-linux.img" ]]; then
  if [[ -f "$OUT/images/kubos-linux.tar.gz" ]]; then
    echo "Extracting kubos-linux.img from tar.gz"
    tar -xzf "$OUT/images/kubos-linux.tar.gz" -C "$OUT/images"
  fi
fi

if [[ ! -f "$OUT/images/kubos-linux.img" ]]; then
  echo "ERROR: kubos-linux.img was not produced" >&2
  ls -la "$OUT/images" >&2
  exit 1
fi

gzip -c -9 "$OUT/images/kubos-linux.img" > "$OUT/images/kubos-linux.img.gz"
cp -v "$OUT/images/kubos-linux.img.gz" /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz
ls -lh "$OUT/images/kubos-linux.img.gz" /mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz
sha256sum "$OUT/images/kubos-linux.img.gz" | tee -a "$LOG"
echo "BUILD_OK $(date -Is)" | tee -a "$LOG"
