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

sync_one() {
  local rel=$1
  mkdir -p "$(dirname "$DST/$rel")"
  # Windows checkout may be CRLF; Buildroot scripts must be LF.
  tr -d '\r' < "$SRC/$rel" > "$DST/$rel"
  echo "synced $rel"
}

echo "=== Syncing sources Windows -> WSL tree ==="
# Board overlays + configs
sync_one board/kubos/beaglebone-black/beaglebone-black.dts
sync_one board/kubos/beaglebone-black/beaglebone-black_config
sync_one board/kubos/beaglebone-black/linux-kubos.config
sync_one board/kubos/beaglebone-black/genimage.cfg
sync_one board/kubos/beaglebone-black/post-image.sh
sync_one board/kubos/beaglebone-black/overlay/etc/inittab
sync_one board/kubos/beaglebone-black/overlay/sbin/monit-respawn
sync_one board/kubos/beaglebone-black/overlay/usr/sbin/install-os

# Common reboot harden
sync_one common/overlay/sbin/flush-filesystems
sync_one common/overlay/sbin/reboot

# U-Boot patches (115200 + env on boot MMC). Drop any stale 500000 patch.
rm -f "$DST/common/patches/uboot/0001-bbb-console-500000.patch"
sync_one common/patches/uboot/0001-bbb-console-115200.patch
sync_one common/patches/uboot/0002-bbb-env-on-boot-mmc.patch

chmod +x "$DST/board/kubos/beaglebone-black/overlay/sbin/monit-respawn"
chmod +x "$DST/common/overlay/sbin/flush-filesystems"
chmod +x "$DST/common/overlay/sbin/reboot"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/install-os"

cd "$BR"
make O="$OUT" BR2_EXTERNAL="$DST" beaglebone-black_defconfig

# Force rebuild of pieces that carry the baud / reboot changes.
[[ -d "$OUT/build/uboot-1.1.0" ]] && make O="$OUT" uboot-dirclean || true
[[ -d "$OUT/build/linux-4.4.23" ]] && make O="$OUT" linux-dirclean || true

# If target rootfs was wiped earlier, force every package to reinstall into it.
if [[ ! -f "$OUT/target/etc/inittab" ]]; then
  echo "target rootfs incomplete; clearing install stamps for reinstall"
  find "$OUT/build" -name '.stamp_target_installed' -delete
  find "$OUT/build" -name '.stamp_images_installed' -delete
  mkdir -p "$OUT/target"
fi

# Fresh log for this run (avoid the waiter matching a prior BUILD_FAILED).
: > "$LOG"
echo "Starting full image build at $(date -Is)" | tee -a "$LOG"
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
