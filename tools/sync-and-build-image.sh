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
sync_one board/kubos/beaglebone-black/kpack.its
sync_one board/kubos/beaglebone-black/kpack-rootfs.its
sync_one board/kubos/beaglebone-black/kpack-uboot.its
sync_one board/kubos/beaglebone-black/overlay/etc/inittab
sync_one board/kubos/beaglebone-black/overlay/etc/monitrc
sync_one board/kubos/beaglebone-black/overlay/etc/rsyslog.conf
sync_one board/kubos/beaglebone-black/overlay/etc/rsyslog.d/kubos-services.conf
sync_one board/kubos/beaglebone-black/overlay/etc/rsyslog.d/kubos-apps.conf
sync_one board/kubos/beaglebone-black/overlay/etc/profile.d/umask.sh
sync_one board/kubos/beaglebone-black/overlay/etc/kubos/log-rotate.sh
sync_one board/kubos/beaglebone-black/overlay/usr/sbin/install-os
sync_one board/kubos/beaglebone-black/overlay/etc/fstab
sync_one board/kubos/beaglebone-black/overlay/etc/network/interfaces
sync_one board/kubos/beaglebone-black/overlay/etc/init.d/S50dropbear
sync_one board/kubos/beaglebone-black/overlay/sbin/monit-respawn
sync_one board/kubos/beaglebone-black/overlay/sbin/ensure-system-log
sync_one board/kubos/beaglebone-black/overlay/sbin/announce-boot-media
sync_one board/kubos/beaglebone-black/overlay/usr/sbin/install-os
sync_one board/kubos/beaglebone-black/overlay/usr/sbin/fram-get
sync_one board/kubos/beaglebone-black/overlay/usr/sbin/fram-set
sync_one board/kubos/beaglebone-black/overlay/usr/sbin/mram
sync_one board/kubos/beaglebone-black/overlay/usr/sbin/disable-usb-eth-ssh
sync_one board/kubos/beaglebone-black/overlay/usr/sbin/verify-mram-fram-boot
sync_one board/kubos/beaglebone-black/overlay/etc/init.d/S79mram-env-sync
sync_one configs/beaglebone-black_defconfig
sync_one board/kubos/beaglebone-black/beaglebone-black_config
sync_one common/device_table.txt
sync_one common/busybox-kubos.config
sync_one tools/package-kpack-phases.sh

# Common reboot harden
sync_one common/overlay/sbin/flush-filesystems
sync_one common/overlay/sbin/reboot

# FRAM / MRAM packaging (init order + reconcile_on_start)
sync_one package/kubos/kubos-fram/Config.in
sync_one package/kubos/kubos-fram/kubos-fram.mk
sync_one package/kubos/kubos-mram/Config.in
sync_one package/kubos/kubos-mram/kubos-mram.mk

# U-Boot patches (baud, env, announce, SPL dual u-boot, DFU dual uboot).
rm -f "$DST/common/patches/uboot/0001-bbb-console-500000.patch"
sync_one common/patches/uboot/0001-bbb-console-115200.patch
sync_one common/patches/uboot/0002-bbb-env-on-boot-mmc.patch
sync_one common/patches/uboot/0003-bbb-announce-boot-media.patch
sync_one common/patches/uboot/0004-bbb-spl-uboot-fallback.patch
sync_one common/patches/uboot/0005-bbb-dfu-dual-uboot.patch
sync_one common/patches/uboot/0006-bbb-env-on-spi-mram.patch
sync_one common/patches/uboot/0007-bbb-fram-mission-policy.patch
sync_one common/patches/uboot/0008-bbb-mram-env-failopen.patch
sync_one common/patches/uboot/0009-bbb-fram-i2c2-clock-restore.patch
sync_one common/patches/uboot/0010-bbb-emmc-default-sd-fallback.patch
sync_one common/patches/uboot/0011-bbb-usb-optional-no-musb.patch
sync_one common/patches/uboot/0012-bbb-spl-emmc-init-retry.patch
sync_one common/patches/uboot/0013-bbb-emmc-only-boot.patch
sync_one common/patches/uboot/0014-bbb-mram-env-spi-chunked-enable.patch
sync_one common/patches/uboot/0015-bbb-spi1-pindir-d0-in-d1-out.patch
sync_one common/patches/uboot/0016-bbb-mram-env-import-polarity.patch
sync_one common/patches/uboot/0017-bbb-fram-recovery-boot.patch
sync_one common/patches/uboot/0018-bbb-fram-restore-resume.patch
sync_one common/patches/uboot/0019-bbb-fram-virgin-failopen.patch
sync_one common/patches/uboot/0020-bbb-fram-boot-count-v6.patch
sync_one common/patches/uboot/0021-bbb-root-by-mmc-host.patch
sync_one common/patches/linux/0006-arm-omap-am33xx-watchdog-restart.patch
sync_one common/patches/linux/0007-i2c-omap-force-restart.patch
sync_one common/patches/linux/0008-watchdog-quiet-restart-nowayout.patch
sync_one common/patches/linux/0009-mmc-block-name-by-host-index.patch
sync_one board/kubos/beaglebone-black/overlay/etc/init.d/S92radsat-boot-stamp
sync_one board/kubos/beaglebone-black/overlay/etc/radsat-image-id
sync_one deploy/FRAM_FLAGS.md
sync_one deploy/kpack-phases/PHASES.txt

chmod +x "$DST/board/kubos/beaglebone-black/overlay/sbin/monit-respawn"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/sbin/ensure-system-log"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/sbin/announce-boot-media"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/etc/kubos/log-rotate.sh"
chmod +x "$DST/common/overlay/sbin/flush-filesystems"
chmod +x "$DST/common/overlay/sbin/reboot"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/install-os"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-get"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/mram"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/disable-usb-eth-ssh"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/verify-mram-fram-boot"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/etc/init.d/S79mram-env-sync"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/etc/init.d/S92radsat-boot-stamp"
chmod +x "$DST/board/kubos/beaglebone-black/overlay/etc/init.d/S50dropbear"
chmod +x "$DST/board/kubos/beaglebone-black/post-image.sh"
chmod +x "$DST/tools/kubos-package.sh" 2>/dev/null || true
chmod +x "$DST/tools/package-kpack-phases.sh" 2>/dev/null || true
chmod +x "$SRC/tools/package-kpack-phases.sh" 2>/dev/null || true

# Stage install-os for SD-drop onto a live board
mkdir -p /mnt/c/Users/logan/CubeSAT
tr -d '\r' < "$SRC/board/kubos/beaglebone-black/overlay/usr/sbin/install-os" \
  > /mnt/c/Users/logan/CubeSAT/install-os
chmod +x /mnt/c/Users/logan/CubeSAT/install-os
echo "staged /mnt/c/Users/logan/CubeSAT/install-os"

cd "$BR"
make O="$OUT" BR2_EXTERNAL="$DST" beaglebone-black_defconfig

# Rebuild BusyBox when applet set changes (e.g. basename).
if [[ "${FORCE_BUSYBOX:-0}" == "1" ]]; then
  make O="$OUT" busybox-dirclean || true
fi

# Optional heavy cleans — set FORCE_UBOOT=1 / FORCE_KUBOS=1 to rebuild those.
# Default FORCE_UBOOT=1 when dual-uboot patches change (caller may override).
if [[ "${FORCE_UBOOT:-1}" == "1" ]]; then
  [[ -d "$OUT/build/uboot-1.1.0" ]] && make O="$OUT" uboot-dirclean || true
fi
if [[ "${FORCE_KUBOS:-1}" == "1" ]]; then
  make O="$OUT" kubos-dirclean || true
  make O="$OUT" kubos-fram-dirclean || true
  make O="$OUT" kubos-mram-dirclean || true
fi

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

# Keep FRAM before MRAM; drop stale S90 leftovers from older packages.
install -D -m 0755 "$DST/package/kubos/kubos-fram/kubos-fram" \
  "$OUT/target/etc/init.d/S80kubos-fram"
install -D -m 0755 "$DST/package/kubos/kubos-mram/kubos-mram" \
  "$OUT/target/etc/init.d/S91kubos-mram"
install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/etc/init.d/S79mram-env-sync" \
  "$OUT/target/etc/init.d/S79mram-env-sync"
install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/etc/init.d/S92radsat-boot-stamp" \
  "$OUT/target/etc/init.d/S92radsat-boot-stamp"
install -D -m 0644 "$DST/board/kubos/beaglebone-black/overlay/etc/radsat-image-id" \
  "$OUT/target/etc/radsat-image-id"
install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-get" \
  "$OUT/target/usr/sbin/fram-get"
install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set" \
  "$OUT/target/usr/sbin/fram-set"
install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/mram" \
  "$OUT/target/usr/sbin/mram"
install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/verify-mram-fram-boot" \
  "$OUT/target/usr/sbin/verify-mram-fram-boot"
rm -f "$OUT/target/etc/init.d/S90kubos-fram" "$OUT/target/etc/init.d/S90kubos-mram"

# If init scripts changed after image gen, rebuild images once more.
if ! tar -tzf "$OUT/images/kubos-linux.tar.gz" >/dev/null 2>&1 || \
   [[ "$(stat -c %Y "$OUT/target/etc/init.d/S80kubos-fram")" -gt "$(stat -c %Y "$OUT/images/kubos-linux.tar.gz" 2>/dev/null || echo 0)" ]]; then
  echo "Refreshing images with corrected init order" | tee -a "$LOG"
  rm -f "$OUT/images/rootfs.ext4" "$OUT/images/kubos-linux.img" \
        "$OUT/images/kubos-linux.img.gz" "$OUT/images/kubos-linux.tar.gz"
  make O="$OUT" -j"$(nproc)" 2>&1 | tee -a "$LOG"
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
if [[ -f "$OUT/images/kubos-linux-flight.img.gz" ]]; then
  cp -v "$OUT/images/kubos-linux-flight.img.gz" \
    /mnt/c/Users/logan/CubeSAT/kubos-linux-flight.img.gz
  ls -lh "$OUT/images/kubos-linux-flight.img.gz" \
    /mnt/c/Users/logan/CubeSAT/kubos-linux-flight.img.gz
  sha256sum "$OUT/images/kubos-linux-flight.img.gz" | tee -a "$LOG"
fi
# Quick sanity: install-os has basename fallback / no pv byte multiply
grep -q 'basename()' "$OUT/target/usr/sbin/install-os"
grep -q 'overflows on 32-bit ash' "$OUT/target/usr/sbin/install-os"
echo "BUILD_OK $(date -Is)" | tee -a "$LOG"
