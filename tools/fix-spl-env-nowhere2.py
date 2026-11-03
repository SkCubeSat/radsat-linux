#!/usr/bin/env python3
from pathlib import Path

p6 = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0006-bbb-env-on-spi-mram.patch")
t = p6.read_text()
print("has USBETH guard", "CONFIG_SPL_USBETH_SUPPORT" in t)
# Find the exact lines
for i, ln in enumerate(t.splitlines()):
    if "SPL" in ln or "ENV_IS_IN_MRAM" in ln or "ENV_IS_NOWHERE" in ln:
        if ln.startswith("+") or ln.startswith("-") or "SPL" in ln:
            if any(k in ln for k in ("SPL", "MRAM", "NOWHERE", "USBETH")):
                print(f"{i}: {ln}")
