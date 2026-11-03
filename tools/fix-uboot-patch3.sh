#!/bin/bash
set -euo pipefail
UB=/tmp/uboot-patchfix2
rm -rf "$UB"
mkdir -p "$UB"
cd "$UB"
tar -xzf /home/logan/code/buildroot-2025.02.14/dl/uboot/uboot-1.1.0-git4.tar.gz
SRC=$(find . -type f -name beaglebone-black.h | head -n1)
ROOT=$(cd "$(dirname "$SRC")/../.." && pwd)
cd "$ROOT"
PATCHDIR=/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot
sed 's/\r$//' "$PATCHDIR/0001-bbb-console-115200.patch" | patch -p1
sed 's/\r$//' "$PATCHDIR/0002-bbb-env-on-boot-mmc.patch" | patch -p1
cp include/configs/beaglebone-black.h /tmp/beaglebone-black.h.before3
python3 - <<'PY'
from pathlib import Path
p = Path("include/configs/beaglebone-black.h")
text = p.read_text()
old = '''    "bootfile=kernel\\0" \\
    "console=ttyS0,115200\\0" \\
    "optargs=\\0" \\
    "loadimage=fatload mmc ${mmcdev}:1 ${loadaddr} /${bootfile}\\0" \\
    "loadfdt=fatload mmc ${mmcdev}:1 ${fdtaddr} /${board}.dtb\\0" \\
    "mmcloados=run args_mmc; " \\
        "if run loadfdt; then " \\
            "bootm ${loadaddr} - ${fdtaddr}; " \\
        "else " \\
            "echo ERROR: Failed to load ${board}.dtb; " \\
        "fi;\\0" \\
    "mmcboot=mmc dev ${mmcdev}; " \\
        "if mmc rescan; then " \\
            "echo SD/MMC found on device ${mmcdev};" \\
            "if run loadimage; then " \\
                "run mmcloados;" \\
            "fi;" \\
        "fi;\\0" \\
'''
new = '''    "bootfile=kernel\\0" \\
    "console=ttyS0,115200\\0" \\
    "optargs=\\0" \\
    "announce_boot=" \\
        "if test ${mmcdev} -eq 0; then " \\
            "echo Booting Linux from SD card image copy \\\\(mmc ${bootpart}\\\\); " \\
        "else " \\
            "echo Booting Linux from eMMC \\\\(mmc ${bootpart}\\\\); " \\
        "fi\\0" \\
    "loadimage=fatload mmc ${mmcdev}:1 ${loadaddr} /${bootfile}\\0" \\
    "loadfdt=fatload mmc ${mmcdev}:1 ${fdtaddr} /${board}.dtb\\0" \\
    "mmcloados=run args_mmc; run announce_boot; " \\
        "if run loadfdt; then " \\
            "bootm ${loadaddr} - ${fdtaddr}; " \\
        "else " \\
            "echo ERROR: Failed to load ${board}.dtb; " \\
        "fi;\\0" \\
    "mmcboot=mmc dev ${mmcdev}; " \\
        "if mmc rescan; then " \\
            "if test ${mmcdev} -eq 0; then " \\
                "echo Found SD card on mmc ${mmcdev} \\\\(multi-copy image media\\\\); " \\
            "else " \\
                "echo Found eMMC on mmc ${mmcdev}; " \\
            "fi; " \\
            "if run loadimage; then " \\
                "run mmcloados;" \\
            "fi;" \\
        "fi;\\0" \\
'''
if old not in text:
    raise SystemExit('target block not found after patches 1+2')
p.write_text(text.replace(old, new, 1))
print('edited ok')
PY
set +e
diff -u /tmp/beaglebone-black.h.before3 include/configs/beaglebone-black.h > /tmp/0003.body.diff
diff_rc=$?
set -e
if [ "$diff_rc" -ne 1 ]; then
  echo "unexpected diff rc=$diff_rc"
  exit 1
fi
{
  echo 'From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001'
  echo 'From: Radsat Developers <dev@radsat.local>'
  echo 'Date: Thu, 29 Oct 2026 16:50:00 -0600'
  echo 'Subject: [PATCH] arm: am33xx: announce SD vs eMMC before starting Linux'
  echo
  echo 'The SD card may hold multiple image copies for backup/recovery. Print'
  echo 'the MMC bootpart (device:partition) clearly before bootm so operators'
  echo 'know which SD copy is starting Linux, versus a plain eMMC boot.'
  echo
  echo '---'
  sed 's#^--- /tmp/beaglebone-black.h.before3#--- a/include/configs/beaglebone-black.h#; s#^+++ include/configs/beaglebone-black.h#+++ b/include/configs/beaglebone-black.h#' /tmp/0003.body.diff
} > "$PATCHDIR/0003-bbb-announce-boot-media.patch"
# ensure trailing newline
printf '\n' >> "$PATCHDIR/0003-bbb-announce-boot-media.patch"
echo "wrote $(wc -l < "$PATCHDIR/0003-bbb-announce-boot-media.patch") lines"

# verify
rm -rf /tmp/uboot-verify
mkdir /tmp/uboot-verify
cd /tmp/uboot-verify
tar -xzf /home/logan/code/buildroot-2025.02.14/dl/uboot/uboot-1.1.0-git4.tar.gz
SRC=$(find . -type f -name beaglebone-black.h | head -n1)
ROOT=$(cd "$(dirname "$SRC")/../.." && pwd)
cd "$ROOT"
sed 's/\r$//' "$PATCHDIR/0001-bbb-console-115200.patch" | patch -p1
sed 's/\r$//' "$PATCHDIR/0002-bbb-env-on-boot-mmc.patch" | patch -p1
sed 's/\r$//' "$PATCHDIR/0003-bbb-announce-boot-media.patch" | patch -p1
echo PATCH_OK
