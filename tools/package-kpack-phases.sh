#!/bin/bash
# Collect Phase 1/3 kpack ITBs + checksums + ops checklist for serial deploy.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# Prefer WSL images dir when present; else local binaries path override.
IMAGES="${KPACK_IMAGES_DIR:-/home/logan/radsat-output/images}"
OUT="${1:-${ROOT}/deploy/kpack-phases}"

mkdir -p "$OUT"

copy_one() {
  local name=$1
  if [[ -f "$IMAGES/$name" ]]; then
    cp -f "$IMAGES/$name" "$OUT/$name"
    (cd "$OUT" && sha256sum "$name" > "${name}.sha256")
    echo "copied $name"
  else
    echo "MISSING: $IMAGES/$name" >&2
    return 1
  fi
}

echo "Packaging from $IMAGES -> $OUT"
copy_one kpack-rootfs.itb
copy_one kpack-uboot.itb
# Full package optional (has U-Boot — do not use for Phase 1)
if [[ -f "$IMAGES/../target/upgrade/kpack-base.itb" ]]; then
  :
fi
# post-image may leave base only inside intermediate; skip if absent
if [[ -f "$IMAGES/kpack-base.itb" ]]; then
  copy_one kpack-base.itb || true
fi

cat > "$OUT/PHASES.txt" <<'EOF'
RadSat phased kpack deploy
==========================

Phase 0 (DONE on live board): fstab PARTUUID 4b4c4e59; /envar+/home mounted.

Phase 1 — rootfs only (NO U-Boot)
  Host:  copy kpack-rootfs.itb to board /home/
  Board: apply via update_kubos / your usual kpack path (kernel+rootfs+dtb only)
  Reboot, then:
    mount | grep envar
    ls /usr/sbin/mram-env-sync /usr/sbin/fram-get
    ls /etc/init.d/S79mram-env-sync
    fw_printenv bootcmd
  Gate: old U-Boot still boots eMMC; tools present. NFS bootcmd in file is OK until Phase 2.

Phase 2 — sanitize + seed MRAM (still old U-Boot)
  Board:
    mram-env-sync --seed
    fw_printenv bootcmd
  Gate: bootcmd=run distro_bootcmd  (NOT bootp/nfs)
  Anti-passthrough: --seed builds Kubos template; refuses --seed-from-envar.

Phase 3 — U-Boot dual bak
  ONLY after Phase 2 gate.
  Host:  copy kpack-uboot.itb to board
  Apply; reboot without SD; banner Oct 30+; env from SPI MRAM.

Phase 4 — verify
  verify-mram-fram-boot
  (BusyBox-safe; fails if bootcmd still NFS)

Abort: never flash kpack-uboot.itb / kpack-base.itb before Phase 2.
EOF

echo "Wrote $OUT/PHASES.txt"
ls -la "$OUT"
