#!/usr/bin/env python3
from pathlib import Path
import shutil
import subprocess
import tempfile
import re

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
idx = t.find("SPL has no SPI MRAM")
print(repr(t[idx:idx+450]))

# Replace using regex on the + lines block
pat = re.compile(
    r"\+/\* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM\. \*/\n"
    r"\+#ifdef CONFIG_SPL_BUILD\n"
    r"\+#define CONFIG_ENV_IS_NOWHERE\n"
    r"\+#else\n"
    r"\+/\*\n"
    r"\+ \* Primary env: SPI MRAM high region \(see mram-service env_offset/env_size\)\.\n"
    r"\+ \* EXT4 /uboot\.env remains a load fallback inside env_mram\.c\.\n"
    r"\+ \*/\n"
    r"\+#define CONFIG_ENV_IS_IN_MRAM\t\t1\n"
    r"\+#define CONFIG_ENV_MRAM_BUS\t\t1\n"
    r"\+#define CONFIG_ENV_MRAM_CS\t\t0\n"
    r"\+#define CONFIG_ENV_MRAM_MAX_HZ\t\t10000000\n"
    r"\+#define CONFIG_ENV_MRAM_MODE\t\t0\n"
    r"\+#define CONFIG_ENV_MRAM_OFFSET\t\t0x7D800\n"
    r"\+#define CONFIG_ENV_SIZE\t\t\t\(10 \* 1024\)\n"
)
m = pat.search(t)
if not m:
    raise SystemExit("regex miss")

repl = (
    "+#define CONFIG_ENV_SIZE\t\t\t(10 * 1024)\n"
    "+/* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM. */\n"
    "+#ifdef CONFIG_SPL_BUILD\n"
    "+#define CONFIG_ENV_IS_NOWHERE\n"
    "+#else\n"
    "+/*\n"
    "+ * Primary env: SPI MRAM high region (see mram-service env_offset/env_size).\n"
    "+ * EXT4 /uboot.env remains a load fallback inside env_mram.c.\n"
    "+ */\n"
    "+#define CONFIG_ENV_IS_IN_MRAM\t\t1\n"
    "+#define CONFIG_ENV_MRAM_BUS\t\t1\n"
    "+#define CONFIG_ENV_MRAM_CS\t\t0\n"
    "+#define CONFIG_ENV_MRAM_MAX_HZ\t\t10000000\n"
    "+#define CONFIG_ENV_MRAM_MODE\t\t0\n"
    "+#define CONFIG_ENV_MRAM_OFFSET\t\t0x7D800\n"
)
t2, n = pat.subn(repl, t, count=1)
print("replacements", n)
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
    assert hdr.index("CONFIG_ENV_SIZE") < hdr.index("#ifdef CONFIG_SPL_BUILD")
    print("VERIFY_OK")

if DST2.parent.exists():
    shutil.copy2(p6, DST2 / p6.name)
