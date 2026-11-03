#!/bin/bash
set -eu
echo "=== last BUILD markers ==="
grep -n 'BUILD_\|adhoc\|Applying 0006\|config_whitelist\|new CONFIG' \
  /home/logan/radsat-output/build-image.nohup.out | tail -60
echo "=== whitelist in build tree ==="
grep -E 'ENV_MRAM|RADSAT_FRAM|FRAM_I2C|ENV_IS_IN_MRAM' \
  /home/logan/radsat-output/build/uboot-1.1.0/scripts/config_whitelist.txt || echo MISSING
echo "=== patch has whitelist? ==="
grep -c config_whitelist /mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0006-bbb-env-on-spi-mram.patch || true
grep -c config_whitelist /home/logan/code/radsat-linux/common/patches/uboot/0006-bbb-env-on-spi-mram.patch || true
echo "=== log size / mtime ==="
ls -l /home/logan/radsat-output/build-image.nohup.out
