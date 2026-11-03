#!/bin/bash
set -euo pipefail
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

OUT=/home/logan/radsat-output
WIN=/mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz

cd "$OUT/images"
test -f kubos-linux.tar.gz
tar -xzf kubos-linux.tar.gz
test -f kubos-linux.img
gzip -c -9 kubos-linux.img > kubos-linux.img.gz
cp -f kubos-linux.img.gz "$WIN"
ls -lh kubos-linux.img.gz "$WIN"
sha256sum "$WIN"

echo "=== target init (source of packaged rootfs) ==="
ls -l "$OUT"/target/etc/init.d/S*fram* "$OUT"/target/etc/init.d/S*mram*
ls "$OUT"/target/etc/init.d/S90kubos-* 2>/dev/null && echo BAD_S90 || echo no_S90_ok
grep reconcile_on_start "$OUT/target/etc/kubos-config.toml"
grep announce-boot "$OUT/target/etc/inittab"
test -x "$OUT/target/usr/sbin/install-os" && echo install-os_ok
test -x "$OUT/target/sbin/announce-boot-media" && echo announce_ok

# Spot-check packaged rootfs partition for init scripts
OFF=$(sfdisk -d kubos-linux.img | awk '/Id=83/ {print $4; exit}' | tr -d ',')
OFF_BYTES=$((OFF * 512))
MNT=$(mktemp -d)
if mount -o loop,ro,offset="$OFF_BYTES" kubos-linux.img "$MNT" 2>/dev/null; then
  echo "=== inside image rootfs ==="
  ls -l "$MNT"/etc/init.d/S*fram* "$MNT"/etc/init.d/S*mram*
  ls "$MNT"/etc/init.d/S90kubos-* 2>/dev/null && echo BAD_S90_IN_IMG || echo no_S90_in_img_ok
  umount "$MNT"
else
  echo "mount_skipped (need root); relying on target listing"
fi
rmdir "$MNT" 2>/dev/null || true

echo "IMAGE_OK $(date -Is)"
