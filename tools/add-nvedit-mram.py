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
    OUT / "0006-bbb-env-on-spi-mram.patch",
]


def main() -> None:
    p6 = OUT / "0006-bbb-env-on-spi-mram.patch"
    if "cmd/nvedit.c" in p6.read_text():
        print("nvedit already in 0006")
        return

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
        shutil.copytree(base, work)
        nvedit = work / "cmd/nvedit.c"
        t = nvedit.read_text()
        old = "\t!defined(CONFIG_ENV_IS_IN_UBI)\t\t&& \\\n\t!defined(CONFIG_ENV_IS_NOWHERE)\n"
        new = (
            "\t!defined(CONFIG_ENV_IS_IN_UBI)\t\t&& \\\n"
            "\t!defined(CONFIG_ENV_IS_IN_MRAM)\t&& \\\n"
            "\t!defined(CONFIG_ENV_IS_NOWHERE)\n"
        )
        if old not in t:
            raise SystemExit("nvedit pattern missing")
        nvedit.write_text(t.replace(old, new, 1))
        # also update error string
        t = nvedit.read_text()
        t = t.replace(
            "SATA|SPI_FLASH|NVRAM|MMC|FAT|EXT4|REMOTE|UBI} or CONFIG_ENV_IS_NOWHERE",
            "SATA|SPI_FLASH|NVRAM|MMC|FAT|EXT4|REMOTE|UBI|MRAM} or CONFIG_ENV_IS_NOWHERE",
        )
        nvedit.write_text(t)

        r = subprocess.run(
            ["diff", "-u", str(base / "cmd/nvedit.c"), str(nvedit)],
            capture_output=True,
            text=True,
        )
        lines = r.stdout.splitlines(True)
        lines[0] = "--- a/cmd/nvedit.c\n"
        lines[1] = "+++ b/cmd/nvedit.c\n"
        hunk = "diff --git a/cmd/nvedit.c b/cmd/nvedit.c\n" + "".join(lines)

    p6.write_text(p6.read_text().rstrip() + "\n" + hunk + "\n")

    # verify
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        v = td / "v"
        v.mkdir()
        subprocess.check_call(
            ["bash", "-lc", f"gzip -d -c {BR_DL} | tar --strip-components=1 -C {v} -xf -"]
        )
        for p in [
            *PATCHES[:-1],
            p6,
            OUT / "0007-bbb-fram-mission-policy.patch",
        ]:
            subprocess.check_call(
                ["patch", "-p1", "--forward", "--batch", "-i", str(p)], cwd=v
            )
        assert "CONFIG_ENV_IS_IN_MRAM" in (v / "cmd/nvedit.c").read_text()
        print("VERIFY_OK nvedit")

    if DST2.parent.exists():
        shutil.copy2(p6, DST2 / p6.name)
    print("updated", p6.stat().st_size)


if __name__ == "__main__":
    main()
