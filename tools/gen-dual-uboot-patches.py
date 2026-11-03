#!/usr/bin/env python3
"""Generate U-Boot 0004/0005 patches from the current extracted tree via diff."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

UB = Path("/home/logan/radsat-output/build/uboot-1.1.0")
OUT = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot")
DST = Path("/home/logan/code/radsat-linux/common/patches/uboot")


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing block: {label}")
    return text.replace(old, new, 1)


def edit_spl(src: Path, dst: Path) -> None:
    t = src.read_text()
    old = (
        "\terr = spl_load_image_fat(mmc_get_blk_desc(mmc),\n"
        "\t\t\t\t CONFIG_SYS_MMCSD_FS_BOOT_PARTITION,\n"
        "\t\t\t\t CONFIG_SPL_FS_LOAD_PAYLOAD_NAME);\n"
        "\tif (!err)\n"
        "\t\treturn err;\n"
        "#endif\n"
        "#endif\n"
        "#ifdef CONFIG_SPL_EXT_SUPPORT\n"
    )
    new = (
        "\terr = spl_load_image_fat(mmc_get_blk_desc(mmc),\n"
        "\t\t\t\t CONFIG_SYS_MMCSD_FS_BOOT_PARTITION,\n"
        "\t\t\t\t CONFIG_SPL_FS_LOAD_PAYLOAD_NAME);\n"
        "\tif (!err)\n"
        "\t\treturn err;\n"
        "\t/* Primary payload bad/missing: try redundant copy on same FAT. */\n"
        '\tputs("SPL: primary u-boot load failed, trying u-boot-bak.img\\n");\n'
        "\terr = spl_load_image_fat(mmc_get_blk_desc(mmc),\n"
        "\t\t\t\t CONFIG_SYS_MMCSD_FS_BOOT_PARTITION,\n"
        '\t\t\t\t "u-boot-bak.img");\n'
        "\tif (!err)\n"
        "\t\treturn err;\n"
        "#endif\n"
        "#endif\n"
        "#ifdef CONFIG_SPL_EXT_SUPPORT\n"
    )
    dst.write_text(must_replace(t, old, new, "spl fat load"))


def edit_header(src: Path, dst: Path) -> None:
    t = src.read_text()
    old = (
        "#define DFU_ALT_INFO_MMC \\\n"
        '    "dfu_alt_info_mmc="         \\\n'
        '    "kernel fat 1 1;"       \\\n'
        '    "rootfs part 1 2;" \\\n'
        '    "uboot fat 1 1;" \\\n'
        '    "beaglebone-black.dtb fat 1 1" \\\n'
        '    "\\0"\n'
    )
    new = (
        "#define DFU_ALT_INFO_MMC \\\n"
        '    "dfu_alt_info_mmc=" \\\n'
        '    "kernel fat 0 1;" \\\n'
        '    "rootfs part 0 2;" \\\n'
        '    "u-boot.img fat 0 1;" \\\n'
        '    "u-boot-bak.img fat 0 1;" \\\n'
        '    "beaglebone-black.dtb fat 0 1" \\\n'
        '    "\\0"\n'
    )
    dst.write_text(must_replace(t, old, new, "dfu alts"))


def edit_update(src: Path, dst: Path) -> None:
    t = src.read_text()
    helper = (
        "\n"
        "/*\n"
        " * Map FIT image node names onto dfu_alt_info_mmc entity names (FAT filenames).\n"
        " * Strips trailing @unit (kernel@1 -> kernel). Maps uboot* onto u-boot*.img.\n"
        " */\n"
        "static void kubos_fit_to_dfu_name(const char *fit_name, char *out, size_t outlen)\n"
        "{\n"
        "\tchar base[64];\n"
        "\tconst char *at;\n"
        "\tsize_t n;\n"
        "\n"
        "\tif (!fit_name || !out || outlen == 0)\n"
        "\t\treturn;\n"
        "\n"
        "\tat = strchr(fit_name, '@');\n"
        "\tn = at ? (size_t)(at - fit_name) : strlen(fit_name);\n"
        "\tif (n >= sizeof(base))\n"
        "\t\tn = sizeof(base) - 1;\n"
        "\tmemcpy(base, fit_name, n);\n"
        "\tbase[n] = '\\0';\n"
        "\n"
        '\tif (!strcmp(base, "uboot"))\n'
        '\t\tsnprintf(out, outlen, "u-boot.img");\n'
        '\telse if (!strcmp(base, "uboot-bak"))\n'
        '\t\tsnprintf(out, outlen, "u-boot-bak.img");\n'
        "\telse\n"
        '\t\tsnprintf(out, outlen, "%s", base);\n'
        "}\n"
        "\n"
    )

    needle = "int update_kubos_count(void)\n{"
    if "kubos_fit_to_dfu_name" not in t:
        t = must_replace(t, needle, helper + needle, "update_kubos_count")

    old = (
        "        if (fit_image_check_type(fit, noffset,\n"
        "                        IH_TYPE_FIRMWARE)) {\n"
        "            ret = dfu_tftp_write(fit_image_name, (unsigned int) data_addr,\n"
        '                         update_size, "mmc", dev_num);\n'
    )
    new = (
        "        if (fit_image_check_type(fit, noffset,\n"
        "                        IH_TYPE_FIRMWARE)) {\n"
        "            char dfu_name[64];\n"
        "\n"
        "            kubos_fit_to_dfu_name(fit_image_name, dfu_name, sizeof(dfu_name));\n"
        '            printf(" -> DFU \'%s\'", dfu_name);\n'
        "            ret = dfu_tftp_write(dfu_name, (unsigned int) data_addr,\n"
        '                         update_size, "mmc", dev_num);\n'
    )
    t = must_replace(t, old, new, "dfu_tftp_write")
    dst.write_text(t)


def write_patch(path: Path, subject: str, body: str, diffs: list[tuple[str, Path, Path]]) -> None:
    chunks = [
        "From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001\n",
        "From: Radsat Developers <dev@radsat.local>\n",
        "Date: Fri, 30 Oct 2026 17:30:00 -0600\n",
        f"Subject: [PATCH] {subject}\n",
        "\n",
        body.rstrip() + "\n",
        "\n",
        "---\n",
    ]
    for rel, a, b in diffs:
        diff = subprocess.run(
            ["diff", "-u", str(a), str(b)],
            check=False,
            capture_output=True,
            text=True,
        )
        if diff.returncode not in (0, 1):
            raise SystemExit(f"diff failed for {rel}: {diff.stderr}")
        text = diff.stdout
        text = text.replace(f"--- {a}", f"--- a/{rel}")
        text = text.replace(f"+++ {b}", f"+++ b/{rel}")
        # strip timestamps from diff headers if present
        lines = []
        for line in text.splitlines(True):
            if line.startswith("--- ") or line.startswith("+++ "):
                line = line.split("\t")[0] + "\n"
            lines.append(line)
        chunks.append("".join(lines))
    path.write_text("".join(chunks), newline="\n")
    print(f"wrote {path} ({path.stat().st_size} bytes)")


def main() -> None:
    if not UB.is_dir():
        raise SystemExit(f"missing uboot tree {UB}")
    OUT.mkdir(parents=True, exist_ok=True)
    DST.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as td:
        td_path = Path(td)
        spl_a = td_path / "spl_mmc.c.orig"
        spl_b = td_path / "spl_mmc.c"
        hdr_a = td_path / "beaglebone-black.h.orig"
        hdr_b = td_path / "beaglebone-black.h"
        upd_a = td_path / "update_kubos.c.orig"
        upd_b = td_path / "update_kubos.c"

        shutil.copy(UB / "common/spl/spl_mmc.c", spl_a)
        shutil.copy(UB / "include/configs/beaglebone-black.h", hdr_a)
        shutil.copy(UB / "common/update_kubos.c", upd_a)

        edit_spl(spl_a, spl_b)
        edit_header(hdr_a, hdr_b)
        edit_update(upd_a, upd_b)

        p4 = OUT / "0004-bbb-spl-uboot-fallback.patch"
        p5 = OUT / "0005-bbb-dfu-dual-uboot.patch"
        write_patch(
            p4,
            "spl: mmc: fall back to u-boot-bak.img on FAT boot",
            "If primary u-boot.img fails to load/validate, try u-boot-bak.img.",
            [("common/spl/spl_mmc.c", spl_a, spl_b)],
        )
        write_patch(
            p5,
            "arm: am33xx: dual U-Boot DFU alts on boot MMC0",
            "DFU on mmc0 with u-boot.img + u-boot-bak.img; map FIT uboot* names.",
            [
                ("include/configs/beaglebone-black.h", hdr_a, hdr_b),
                ("common/update_kubos.c", upd_a, upd_b),
            ],
        )

        for src in (p4, p5):
            dst = DST / src.name
            shutil.copy(src, dst)
            print(f"synced {dst}")

        for patch in (p4, p5):
            r = subprocess.run(
                ["patch", "-p1", "--dry-run", "-i", str(patch)],
                cwd=UB,
                capture_output=True,
                text=True,
            )
            print(patch.name, "dry-run rc=", r.returncode)
            print(r.stdout)
            print(r.stderr)
            if r.returncode != 0:
                raise SystemExit(f"dry-run failed for {patch.name}")

    print("PATCHES_OK")


if __name__ == "__main__":
    main()
