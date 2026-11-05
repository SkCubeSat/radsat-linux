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

if [[ -f "$ROOT/deploy/kpack-phases/PHASES.txt" ]]; then
  cp -f "$ROOT/deploy/kpack-phases/PHASES.txt" "$OUT/PHASES.txt"
else
  echo "WARN: missing $ROOT/deploy/kpack-phases/PHASES.txt" >&2
fi

echo "Wrote $OUT/PHASES.txt"
ls -la "$OUT"
