from pathlib import Path
import subprocess
p = Path("/home/logan/radsat-output/build/uboot-1.1.0/board/ti/am335x/board.c")
text = p.read_text()
old = (
"#ifdef CONFIG_SPL_BUILD\n"
"/*\n"
" * eMMC (mmc1) is the flight default. SD (mmc0) is recovery only.\n"
" */\n"
"void board_boot_order(u32 *spl_boot_list)\n"
"{\n"
"\tspl_boot_list[0] = BOOT_DEVICE_MMC2;\n"
"\tspl_boot_list[1] = BOOT_DEVICE_MMC1;\n"
"}\n"
"#endif"
)
new = (
"#ifdef CONFIG_SPL_BUILD\n"
"/*\n"
" * eMMC (mmc1) is the flight default. SD (mmc0) is recovery only.\n"
" */\n"
"void board_boot_order(u32 *spl_boot_list)\n"
"{\n"
"\tspl_boot_list[0] = BOOT_DEVICE_MMC2;\n"
"\tspl_boot_list[1] = BOOT_DEVICE_MMC1;\n"
"}\n"
"\n"
"int board_mmc_init(bd_t *bis)\n"
"{\n"
"\tomap_mmc_init(0, 0, 0, -1, -1);\n"
"\tomap_mmc_init(1, 0, 0, -1, -1);\n"
"\treturn 0;\n"
"}\n"
"#endif"
)
print("found" if old in text else "MISSING")
Path("/tmp/board_old.c").write_text(text)
Path("/tmp/board_new.c").write_text(text.replace(old, new, 1))
# generate patch relative paths
r = subprocess.run(["diff","-u","/tmp/board_old.c","/tmp/board_new.c"], capture_output=True, text=True)
diff = r.stdout.replace("/tmp/board_old.c", "a/board/ti/am335x/board.c").replace("/tmp/board_new.c", "b/board/ti/am335x/board.c")
header = """From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001
From: Radsat Developers <dev@radsat.local>
Date: Mon, 2 Nov 2026 21:45:00 -0600
Subject: [PATCH] arm: bbb: init both MMC in SPL (keep SD fallback)

Always init both MMC controllers in SPL. Keep eMMC-first with SD fallback.

---
"""
out = header + diff
for dest in [
    Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0013-bbb-emmc-only-boot.patch"),
    Path("/home/logan/code/radsat-linux/common/patches/uboot/0013-bbb-emmc-only-boot.patch"),
]:
    dest.write_text(out, newline="\n")
    print("wrote", dest, dest.stat().st_size)
print(out)
