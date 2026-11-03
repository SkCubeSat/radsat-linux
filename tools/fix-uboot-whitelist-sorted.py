#!/usr/bin/env python3
"""Rebuild 0006 ending whitelist hunk with sorted config_whitelist.txt."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

OUT = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot")
DST2 = Path("/home/logan/code/radsat-linux/common/patches/uboot")
BR_DL = Path("/home/logan/code/buildroot-2025.02.14/dl/uboot/uboot-1.1.0-git4.tar.gz")

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

PATCHES = [
    OUT / "0001-bbb-console-115200.patch",
    OUT / "0002-bbb-env-on-boot-mmc.patch",
    OUT / "0003-bbb-announce-boot-media.patch",
    OUT / "0004-bbb-spl-uboot-fallback.patch",
    OUT / "0005-bbb-dfu-dual-uboot.patch",
]


def main() -> None:
    p6 = OUT / "0006-bbb-env-on-spi-mram.patch"
    text = p6.read_text()
    # Drop any prior whitelist hunk(s)
    marker = "diff --git a/scripts/config_whitelist.txt b/scripts/config_whitelist.txt\n"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n"
    # Persist stripped 0006 so subsequent apply uses no whitelist hunk.
    p6.write_text(text)

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
        # Apply 0006 without whitelist
        subprocess.check_call(
            ["patch", "-p1", "--forward", "--batch", "-i", str(p6)],
            cwd=base,
        )
        shutil.copytree(base, work)
        wl = work / "scripts/config_whitelist.txt"
        lines = [ln for ln in wl.read_text().splitlines() if ln.strip()]
        for n in NEW:
            if n not in lines:
                lines.append(n)
        lines = sorted(set(lines))
        wl.write_text("\n".join(lines) + "\n")

        r = subprocess.run(
            ["diff", "-u", str(base / "scripts/config_whitelist.txt"), str(wl)],
            capture_output=True,
            text=True,
        )
        if not r.stdout.strip():
            raise SystemExit("no whitelist diff?")
        dlines = r.stdout.splitlines(True)
        dlines[0] = "--- a/scripts/config_whitelist.txt\n"
        dlines[1] = "+++ b/scripts/config_whitelist.txt\n"
        hunk = marker + "".join(dlines)

    p6.write_text(text + hunk)

    # Verify series + that comm would be happy
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
        wlines = (v / "scripts/config_whitelist.txt").read_text().splitlines()
        assert wlines == sorted(wlines), "whitelist not sorted"
        for n in NEW:
            assert n in wlines
        print("VERIFY_OK sorted whitelist")

    if DST2.parent.exists():
        DST2.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p6, DST2 / p6.name)
    print("updated", p6, p6.stat().st_size)


if __name__ == "__main__":
    main()
