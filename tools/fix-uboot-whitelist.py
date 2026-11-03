#!/usr/bin/env python3
"""Append new CONFIG_* names to U-Boot config whitelist inside 0006 patch."""
from pathlib import Path
import shutil
import subprocess
import tempfile

OUT = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot")
DST2 = Path("/home/logan/code/radsat-linux/common/patches/uboot")
BR_DL = Path("/home/logan/code/buildroot-2025.02.14/dl/uboot/uboot-1.1.0-git4.tar.gz")
PATCHES = [OUT / f"000{i}-bbb-{n}.patch" for i, n in [
    (1, "console-115200"),
    (2, "env-on-boot-mmc"),
    (3, "announce-boot-media"),
    (4, "spl-uboot-fallback"),
    (5, "dfu-dual-uboot"),
]]
# Plus regenerated 0006/0007 without whitelist — we'll rebuild 0006 including whitelist

NEW = [
    "CONFIG_ENV_IS_IN_MRAM",
    "CONFIG_ENV_MRAM_BUS",
    "CONFIG_ENV_MRAM_CS",
    "CONFIG_ENV_MRAM_MAX_HZ",
    "CONFIG_ENV_MRAM_MODE",
    "CONFIG_ENV_MRAM_OFFSET",
    "CONFIG_FRAM_I2C_ADDR",
    "CONFIG_FRAM_I2C_BUS",
    "CONFIG_RADSAT_FRAM_POLICY",
]


def main() -> None:
    # Append a small 0006b-style hunk onto 0006 by regenerating with whitelist edit.
    # Simpler: create 0006a whitelist patch applied after 0006? Order: add to 0006 itself.

    p6 = OUT / "0006-bbb-env-on-spi-mram.patch"
    text = p6.read_text()
    if "config_whitelist.txt" in text:
        print("already has whitelist")
        return

    # Build whitelist hunk against post-0005 tree
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        base = td / "base"
        work = td / "work"
        base.mkdir()
        subprocess.check_call(
            ["bash", "-lc", f"gzip -d -c {BR_DL} | tar --strip-components=1 -C {base} -xf -"]
        )
        for p in PATCHES:
            subprocess.check_call(
                ["patch", "-p1", "--forward", "--batch", "-i", str(p)], cwd=base
            )
        # apply existing 0006/0007
        subprocess.check_call(
            ["patch", "-p1", "--forward", "--batch", "-i", str(OUT / "0006-bbb-env-on-spi-mram.patch")],
            cwd=base,
        )
        shutil.copytree(base, work)
        wl = work / "scripts/config_whitelist.txt"
        cur = wl.read_text()
        add = "".join(f"{n}\n" for n in NEW if n not in cur)
        if not add:
            print("nothing to add")
            return
        # Keep sorted-ish: append at end before last blank if any
        wl.write_text(cur.rstrip() + "\n" + add)
        r = subprocess.run(
            ["diff", "-u", str(base / "scripts/config_whitelist.txt"), str(wl)],
            capture_output=True,
            text=True,
        )
        lines = r.stdout.splitlines(True)
        lines[0] = "--- a/scripts/config_whitelist.txt\n"
        lines[1] = "+++ b/scripts/config_whitelist.txt\n"
        hunk = "diff --git a/scripts/config_whitelist.txt b/scripts/config_whitelist.txt\n" + "".join(
            lines
        )

    # Insert whitelist hunk into 0006 before end — append to patch file
    p6.write_text(text.rstrip() + "\n" + hunk)
    # Also apply whitelist into 0007? No — 0006 is enough if applied before build.

    # Verify full series including whitelist
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        v = td / "v"
        v.mkdir()
        subprocess.check_call(
            ["bash", "-lc", f"gzip -d -c {BR_DL} | tar --strip-components=1 -C {v} -xf -"]
        )
        for p in PATCHES + [OUT / "0006-bbb-env-on-spi-mram.patch", OUT / "0007-bbb-fram-mission-policy.patch"]:
            subprocess.check_call(
                ["patch", "-p1", "--forward", "--batch", "-i", str(p)], cwd=v
            )
        for n in NEW:
            assert n in (v / "scripts/config_whitelist.txt").read_text(), n
        print("VERIFY_OK whitelist + patches")

    if DST2.parent.exists():
        DST2.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p6, DST2 / p6.name)
        shutil.copy2(OUT / "0007-bbb-fram-mission-policy.patch", DST2 / "0007-bbb-fram-mission-policy.patch")
    print("updated", p6, p6.stat().st_size)


if __name__ == "__main__":
    main()
