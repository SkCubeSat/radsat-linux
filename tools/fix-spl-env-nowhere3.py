#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import tempfile

OUT = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot")
DST2 = Path("/home/logan/code/radsat-linux/common/patches/uboot")
BR_DL = Path("/home/logan/code/buildroot-2025.02.14/dl/uboot/uboot-1.1.0-git4.tar.gz")

p6 = OUT / "0006-bbb-env-on-spi-mram.patch"
t = p6.read_text()

# Fix header: SPL always NOWHERE
old = """+#if defined(CONFIG_SPL_BUILD) && defined(CONFIG_SPL_USBETH_SUPPORT)
+#define CONFIG_ENV_IS_NOWHERE
+#else
+/*
+ * Primary env: SPI MRAM high region (see mram-service env_offset/env_size).
+ * EXT4 /uboot.env remains a load fallback inside env_mram.c.
+ */
+#define CONFIG_ENV_IS_IN_MRAM		1
"""
new = """+#ifdef CONFIG_SPL_BUILD
+#define CONFIG_ENV_IS_NOWHERE
+#else
+/*
+ * Primary env: SPI MRAM high region (see mram-service env_offset/env_size).
+ * EXT4 /uboot.env remains a load fallback inside env_mram.c.
+ */
+#define CONFIG_ENV_IS_IN_MRAM		1
"""
if old not in t:
    # show nearby
    idx = t.find("CONFIG_ENV_IS_IN_MRAM")
    print(repr(t[idx - 200 : idx + 80]))
    raise SystemExit("header pattern missing")
t = t.replace(old, new, 1)

# Also remove SPL makefile addition of env_mram/fram_mission.
# Current patch adds them next to BOTH ENV_IS_IN_EXT4 occurrences.
# Keep only the first (non-SPL) addition by regenerating Makefile hunk cleanly later.
# Simpler immediate fix: change SPL section additions to not include mram —
# read the makefile hunk(s).

p6.write_text(t)
print("header fixed")

# Regenerate makefile portion: strip both makefile hunks and recreate single non-SPL add.
# Easiest path: rebuild 0006 makefile part via extract+edit.

PATCHES = [
    OUT / "0001-bbb-console-115200.patch",
    OUT / "0002-bbb-env-on-boot-mmc.patch",
    OUT / "0003-bbb-announce-boot-media.patch",
    OUT / "0004-bbb-spl-uboot-fallback.patch",
    OUT / "0005-bbb-dfu-dual-uboot.patch",
]

# For now header fix alone should stop SPL defining MRAM, so SPL won't build env_mram.o
# even if Makefile has the obj-$(CONFIG_ENV_IS_IN_MRAM) line (CONFIG unset => obj-).
# fram_mission similarly gated by CONFIG_RADSAT_FRAM_POLICY which is in #else.

# Verify by applying series and grepping generated config for SPL... hard.
# Quick check: apply and ensure beaglebone-black.h has SPL_BUILD => NOWHERE only.

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
    assert "#ifdef CONFIG_SPL_BUILD" in hdr
    assert "CONFIG_SPL_USBETH_SUPPORT" not in hdr.split("CONFIG_ENV_IS_IN_MRAM")[0][-200:]
    print("VERIFY_OK header")

if DST2.parent.exists():
    shutil.copy2(p6, DST2 / p6.name)
print("done", p6.stat().st_size)
