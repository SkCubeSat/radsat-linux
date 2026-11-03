#!/usr/bin/env python3
"""Ensure CONFIG_ENV_SIZE is defined for SPL as well as U-Boot proper."""
from pathlib import Path
import shutil
import subprocess
import tempfile

OUT = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot")
DST2 = Path("/home/logan/code/radsat-linux/common/patches/uboot")
BR_DL = Path("/home/logan/code/buildroot-2025.02.14/dl/uboot/uboot-1.1.0-git4.tar.gz")
PATCHES = [
    OUT / "0001-bbb-console-115200.patch",
    OUT / "0002-bbb-env-on-boot-mmc.patch",
    OUT / "0003-bbb-announce-boot-media.patch",
    OUT / "0004-bbb-spl-uboot-fallback.patch",
    OUT / "0005-bbb-dfu-dual-uboot.patch",
]

# Patch the extracted tree's beaglebone header after 0001-0006 conceptually by
# editing the 0006 patch text: move ENV_SIZE before the SPL ifdef.
p6 = OUT / "0006-bbb-env-on-spi-mram.patch"
t = p6.read_text()

old = """+/* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM. */
+#ifdef CONFIG_SPL_BUILD
+#define CONFIG_ENV_IS_NOWHERE
+#else
+/*
+ * Primary env: SPI MRAM high region (see mram-service env_offset/env_size).
+ * EXT4 /uboot.env remains a load fallback inside env_mram.c.
+ */
+#define CONFIG_ENV_IS_IN_MRAM		1
+#define CONFIG_ENV_MRAM_BUS		1
+#define CONFIG_ENV_MRAM_CS		0
+#define CONFIG_ENV_MRAM_MAX_HZ		10000000
+#define CONFIG_ENV_MRAM_MODE		0
+#define CONFIG_ENV_MRAM_OFFSET		0x7D800
+#define CONFIG_ENV_SIZE			(10 * 1024)
"""

new = """+#define CONFIG_ENV_SIZE			(10 * 1024)
+/* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM. */
+#ifdef CONFIG_SPL_BUILD
+#define CONFIG_ENV_IS_NOWHERE
+#else
+/*
+ * Primary env: SPI MRAM high region (see mram-service env_offset/env_size).
+ * EXT4 /uboot.env remains a load fallback inside env_mram.c.
+ */
+#define CONFIG_ENV_IS_IN_MRAM		1
+#define CONFIG_ENV_MRAM_BUS		1
+#define CONFIG_ENV_MRAM_CS		0
+#define CONFIG_ENV_MRAM_MAX_HZ		10000000
+#define CONFIG_ENV_MRAM_MODE		0
+#define CONFIG_ENV_MRAM_OFFSET		0x7D800
"""

if old not in t:
    raise SystemExit("block missing")
# Also need to bump hunk +count by 0 (moved line, same count)
t = t.replace(old, new, 1)
p6.write_text(t)

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    v = td / "v"
    v.mkdir()
    subprocess.check_call(
        ["bash", "-lc", f"gzip -d -c {BR_DL} | tar --strip-components=1 -C {v} -xf -"]
    )
    for p in PATCHES + [p6, OUT / "0007-bbb-fram-mission-policy.patch"]:
        subprocess.check_call(
            ["patch", "-p1", "--forward", "--batch", "-i", str(p)], cwd=v
        )
    hdr = (v / "include/configs/beaglebone-black.h").read_text()
    # ENV_SIZE before SPL ifdef
    assert hdr.index("CONFIG_ENV_SIZE") < hdr.index("CONFIG_SPL_BUILD")
    print("VERIFY_OK")

if DST2.parent.exists():
    shutil.copy2(p6, DST2 / p6.name)
print("updated", p6.stat().st_size)
