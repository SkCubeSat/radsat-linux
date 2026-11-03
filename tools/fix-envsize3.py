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

# Ensure ENV_SIZE is before SPL ifdef once
if t.count("+#define CONFIG_ENV_SIZE") != 1:
    print("ENV_SIZE count", t.count("+#define CONFIG_ENV_SIZE"))

idx = t.find("CONFIG_ENV_MRAM_OFFSET")
print(repr(t[idx:idx+120]))

# Remove the ENV_SIZE line that follows OFFSET if present
needle = "+#define CONFIG_ENV_MRAM_OFFSET\t\t0x7D800\n+#define CONFIG_ENV_SIZE\t\t\t(10 * 1024)\n"
needle2 = "+#define CONFIG_ENV_MRAM_OFFSET\t\t0x7D800\n+#define CONFIG_ENV_SIZE\t\t\t(10 * 1024)\n"
# try spaces/tabs variants
import re
t2, n = re.subn(
    r"(\+#define CONFIG_ENV_MRAM_OFFSET\t+0x7D800\n)\+#define CONFIG_ENV_SIZE\t+\(10 \* 1024\)\n",
    r"\1",
    t,
    count=1,
)
print("removed inner ENV_SIZE", n)

# Ensure leading ENV_SIZE exists before SPL comment
if "+#define CONFIG_ENV_SIZE" not in t2.split("SPL has no SPI")[0][-80:]:
    t2 = t2.replace(
        "+/* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM. */\n",
        "+#define CONFIG_ENV_SIZE\t\t\t(10 * 1024)\n"
        "+/* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM. */\n",
        1,
    )
    print("inserted leading ENV_SIZE")

p6.write_text(t2)

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
    # ENV_SIZE only once at top level
    assert hdr.count("#define CONFIG_ENV_SIZE") == 1
    print("VERIFY_OK")

if DST2.parent.exists():
    shutil.copy2(p6, DST2 / p6.name)
print("size", p6.stat().st_size)
