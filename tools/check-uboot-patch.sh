#!/bin/bash
set -euo pipefail
export PATH=/usr/bin:/bin
TMP=$(mktemp -d)
cd "$TMP"
mkdir -p include/configs
curl -fsSL https://raw.githubusercontent.com/SkCubeSat/kubos-uboot/1.1.0/include/configs/beaglebone-black.h \
  -o include/configs/beaglebone-black.h
PATCHDIR=/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot
sed 's/\r$//' "$PATCHDIR/0001-bbb-console-500000.patch" | patch -p1
sed 's/\r$//' "$PATCHDIR/0002-bbb-env-on-boot-mmc.patch" | patch -p1
grep -n 'EXT4_ENV_DEVICE_AND_PART\|KUBOS_UPGRADE_PART\|CONFIG_BAUDRATE\|500000' \
  include/configs/beaglebone-black.h
echo PATCH_OK
