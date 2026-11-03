#!/bin/bash
set -euo pipefail
# WSL inherits a Windows PATH with spaces; Buildroot rejects that.
export PATH=/home/logan/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
export KUBOS_OVERRIDE_SRCDIR=/mnt/c/Users/logan/CubeSAT/Software

OUT=/home/logan/radsat-output
SRC=/home/logan/code/radsat-linux
BR=/home/logan/code/buildroot-2025.02.14
LOG=/home/logan/radsat-output/remake-image.log
WIN=/mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz

: > "$LOG"
exec > >(tee -a "$LOG") 2>&1

echo "START $(date -Is)"

# Ensure FRAM starts before MRAM; drop stale S90 leftovers from older builds.
install -D -m 0755 "$SRC/package/kubos/kubos-fram/kubos-fram" \
  "$OUT/target/etc/init.d/S80kubos-fram"
install -D -m 0755 "$SRC/package/kubos/kubos-mram/kubos-mram" \
  "$OUT/target/etc/init.d/S91kubos-mram"
rm -f "$OUT/target/etc/init.d/S90kubos-fram" "$OUT/target/etc/init.d/S90kubos-mram"

cat > "$OUT/target/etc/monit.d/kubos-fram.cfg" <<'CFG'
CHECK PROCESS kubos-fram PIDFILE /var/run/fram-service.pid
	START PROGRAM = "/etc/init.d/S80kubos-fram start"
	IF 3 RESTART WITHIN 10 CYCLES THEN TIMEOUT
CFG

cat > "$OUT/target/etc/monit.d/kubos-mram.cfg" <<'CFG'
CHECK PROCESS kubos-mram PIDFILE /var/run/mram-service.pid
	START PROGRAM = "/etc/init.d/S91kubos-mram start"
	IF 3 RESTART WITHIN 10 CYCLES THEN TIMEOUT
CFG

ls -l "$OUT"/target/etc/init.d/S*fram* "$OUT"/target/etc/init.d/S*mram*

# Drop failed non-override kubos download state if present.
rm -rf "$OUT"/build/kubos-v0.1.1-rc.2 "$OUT"/build/.kubos-v0.1.1-rc.2*

# Force rootfs + final image rebuild from current TARGET_DIR.
rm -f "$OUT"/images/rootfs.ext4 \
      "$OUT"/images/kubos-linux.img \
      "$OUT"/images/kubos-linux.img.gz \
      "$OUT"/images/rootfs.tar \
      "$OUT"/images/rootfs.tar.lzma

cd "$BR"
make O="$OUT" -j"$(nproc)"

# If package reinstall resurrected S90, strip and rebuild images once more.
if ls "$OUT"/target/etc/init.d/S90kubos-* >/dev/null 2>&1; then
  echo "resurrected S90 - stripping and remaking images"
  rm -f "$OUT"/target/etc/init.d/S90kubos-fram "$OUT"/target/etc/init.d/S90kubos-mram
  install -D -m 0755 "$SRC/package/kubos/kubos-fram/kubos-fram" \
    "$OUT/target/etc/init.d/S80kubos-fram"
  install -D -m 0755 "$SRC/package/kubos/kubos-mram/kubos-mram" \
    "$OUT/target/etc/init.d/S91kubos-mram"
  rm -f "$OUT"/images/rootfs.ext4 \
        "$OUT"/images/kubos-linux.img \
        "$OUT"/images/kubos-linux.img.gz
  make O="$OUT" -j"$(nproc)"
fi

ls -lh "$OUT/images/kubos-linux.img.gz"
cp -f "$OUT/images/kubos-linux.img.gz" "$WIN"
sha256sum "$WIN"
echo "=== final init ==="
ls -l "$OUT"/target/etc/init.d/S*fram* "$OUT"/target/etc/init.d/S*mram*
grep reconcile_on_start "$OUT/target/etc/kubos-config.toml"
grep announce-boot "$OUT/target/etc/inittab"
echo "IMAGE_OK $(date -Is)"
