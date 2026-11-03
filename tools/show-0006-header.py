#!/usr/bin/env python3
from pathlib import Path
t = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0006-bbb-env-on-spi-mram.patch").read_text()
# find beaglebone-black.h section
idx = t.find("include/configs/beaglebone-black.h")
print(t[idx:idx+1200])
