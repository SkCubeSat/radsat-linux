#!/usr/bin/env python3
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

p6 = OUT / "0006-bbb-env-on-spi-mram.patch"
t = p6.read_text()

old = """+/* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM. */
+#ifdef CONFIG_SPL_BUILD
 #define CONFIG_ENV_IS_NOWHERE
 #else
"""
new = """+#define CONFIG_ENV_SIZE			(10 * 1024)
+/* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM. */
+#ifdef CONFIG_SPL_BUILD
 #define CONFIG_ENV_IS_NOWHERE
 #else
"""
if old not in t:
    raise SystemExit("intro missing")
t = t.replace(old, new, 1)

# Remove ENV_SIZE from inside else
old2 = """+#define CONFIG_ENV_MRAM_OFFSET		0x7D800
+#define CONFIG_ENV_SIZE			(10 * 1024)
+#define CONFIG_EXT4_WRITE
"""
new2 = """+#define CONFIG_ENV_MRAM_OFFSET		0x7D800
+#define CONFIG_EXT4_WRITE
"""
if old2 not in t:
    raise SystemExit("env size inside missing")
t = t.replace(old2, new2, 1)

# Fix hunk counts: we added one + line and removed one + line => same + count.
# But we also need to update @@ if the tool is strict - counts should be unchanged.

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
    assert hdr.index("#define CONFIG_ENV_SIZE") < hdr.index("#ifdef CONFIG_SPL_BUILD")
    print("VERIFY_OK")
    print(hdr[hdr.index("CONFIG_ENV_SIZE") - 20 : hdr.index("CONFIG_ENV_IS_IN_MRAM") + 40])

if DST2.parent.exists():
    shutil.copy2(p6, DST2 / p6.name)
print("size", p6.stat().st_size)
