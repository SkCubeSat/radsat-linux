#!/bin/bash
set -euo pipefail
export PATH=/usr/bin:/bin
TMP=$(mktemp -d)
cd "$TMP"
mkdir -p include/configs
curl -fsSL https://raw.githubusercontent.com/SkCubeSat/kubos-uboot/1.1.0/include/configs/beaglebone-black.h \
  -o include/configs/beaglebone-black.h
PATCHDIR=/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot
sed 's/\r$//' "$PATCHDIR/0001-bbb-console-115200.patch" | patch -p1
cp -a include/configs/beaglebone-black.h before.h

python3 - <<'PY'
from pathlib import Path
text = Path("include/configs/beaglebone-black.h").read_text()
old1 = '#define EXT4_ENV_DEVICE_AND_PART "1:3"'
new1 = '#define EXT4_ENV_DEVICE_AND_PART "0:3"'
old2 = '#define KUBOS_UPGRADE_PART   1'
new2 = '#define KUBOS_UPGRADE_PART   4'
if old1 not in text or old2 not in text:
    raise SystemExit("expected strings missing")
Path("include/configs/beaglebone-black.h").write_text(
    text.replace(old1, new1, 1).replace(old2, new2, 1)
)
PY

diff -u before.h include/configs/beaglebone-black.h > /tmp/0002-raw.diff || true
sed \
  -e '1s|--- before.h|--- a/include/configs/beaglebone-black.h|' \
  -e '2s|+++ include/configs/beaglebone-black.h|+++ b/include/configs/beaglebone-black.h|' \
  /tmp/0002-raw.diff > /tmp/0002-exact.diff
cat /tmp/0002-exact.diff

# Rebuild a proper git-style patch file for the repo.
OUT=/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0002-bbb-env-on-boot-mmc.patch
{
  cat <<'HDR'
From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001
From: Radsat Developers <dev@radsat.local>
Date: Sun, 25 Oct 2026 21:30:00 -0600
Subject: [PATCH] arm: am33xx: load Kubos env and upgrades from the boot MMC

The flight image boots from MMC0 and stores /envar on partition 3 of
that same card. U-Boot was still looking for uboot.env on MMC1:3 and
for upgrade packages on partition 1 (the VFAT boot partition). With
only one card present, every fw_setenv was ignored and kpack installs
never ran.

Point the environment and the default upgrade partition at the boot
card: MMC0 partition 3 for env, MMC0 partition 4 (/home) for packages.

---
HDR
  cat /tmp/0002-exact.diff
} > "$OUT"

# Verify exact apply with no fuzz after 0001.
rm -rf include
mkdir -p include/configs
curl -fsSL https://raw.githubusercontent.com/SkCubeSat/kubos-uboot/1.1.0/include/configs/beaglebone-black.h \
  -o include/configs/beaglebone-black.h
sed 's/\r$//' "$PATCHDIR/0001-bbb-console-115200.patch" | patch -p1
sed 's/\r$//' "$OUT" | patch -p1 --fuzz=0
grep -n 'EXT4_ENV_DEVICE_AND_PART\|KUBOS_UPGRADE_PART' include/configs/beaglebone-black.h
echo FIXED_OK
