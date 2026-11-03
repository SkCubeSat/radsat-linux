#!/usr/bin/env bash
set -euo pipefail

# WSL inherits a Windows PATH with spaces; Buildroot rejects that.
export PATH=/home/logan/.cargo/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

OUT=/home/logan/radsat-output
SRC=/home/logan/code/radsat-linux
BR=/home/logan/code/buildroot-2025.02.14
WIN_IMG=/mnt/c/Users/logan/CubeSAT/kubos-linux.img.gz

install -D -m 0755 "$SRC/package/kubos/kubos-fram/kubos-fram" \
  "$OUT/target/etc/init.d/S80kubos-fram"
install -D -m 0755 "$SRC/package/kubos/kubos-mram/kubos-mram" \
  "$OUT/target/etc/init.d/S91kubos-mram"
rm -f "$OUT/target/etc/init.d/S90kubos-fram" "$OUT/target/etc/init.d/S90kubos-mram"

cat > "$OUT/target/etc/monit.d/kubos-fram.cfg" <<'EOF'
CHECK PROCESS kubos-fram PIDFILE /var/run/fram-service.pid
	START PROGRAM = "/etc/init.d/S80kubos-fram start"
	IF 3 RESTART WITHIN 10 CYCLES THEN TIMEOUT
EOF

cat > "$OUT/target/etc/monit.d/kubos-mram.cfg" <<'EOF'
CHECK PROCESS kubos-mram PIDFILE /var/run/mram-service.pid
	START PROGRAM = "/etc/init.d/S91kubos-mram start"
	IF 3 RESTART WITHIN 10 CYCLES THEN TIMEOUT
EOF

echo "=== init scripts ==="
ls -l "$OUT"/target/etc/init.d/*fram* "$OUT"/target/etc/init.d/*mram*

echo "=== rebuilding rootfs + image ==="
cd "$BR"
make O="$OUT" -j"$(nproc)"

# If Buildroot reinstalled packages and resurrected S90, strip again and remake images.
if ls "$OUT"/target/etc/init.d/S90kubos-* >/dev/null 2>&1; then
  echo "=== stripping resurrected S90 scripts; remaking images ==="
  rm -f "$OUT"/target/etc/init.d/S90kubos-fram "$OUT"/target/etc/init.d/S90kubos-mram
  install -D -m 0755 "$SRC/package/kubos/kubos-fram/kubos-fram" \
    "$OUT/target/etc/init.d/S80kubos-fram"
  install -D -m 0755 "$SRC/package/kubos/kubos-mram/kubos-mram" \
    "$OUT/target/etc/init.d/S91kubos-mram"
  # Force rootfs/image rebuild without full package rebuild
  rm -f "$OUT"/images/rootfs.ext4 "$OUT"/images/kubos-linux.img "$OUT"/images/kubos-linux.img.gz
  make O="$OUT" -j"$(nproc)"
fi

echo "=== packaging ==="
ls -lh "$OUT/images/kubos-linux.img.gz"
cp -f "$OUT/images/kubos-linux.img.gz" "$WIN_IMG"
sha256sum "$WIN_IMG"

echo "=== final target init ==="
ls -l "$OUT"/target/etc/init.d/*fram* "$OUT"/target/etc/init.d/*mram*
grep reconcile_on_start "$OUT/target/etc/kubos-config.toml"
grep announce-boot "$OUT/target/etc/inittab"
echo IMAGE_OK "$(date -Is)"
