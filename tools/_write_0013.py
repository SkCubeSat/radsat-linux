from pathlib import Path
TAB = chr(9)
hunk = [
"@@ -766,9 +766,16 @@",
" /*",
"  * eMMC (mmc1) is the flight default. SD (mmc0) is recovery only.",
"  */",
" void board_boot_order(u32 *spl_boot_list)",
" {",
" " + TAB + "spl_boot_list[0] = BOOT_DEVICE_MMC2;",
" " + TAB + "spl_boot_list[1] = BOOT_DEVICE_MMC1;",
"+}",
"+",
"+int board_mmc_init(bd_t *bis)",
"+{",
"+" + TAB + "omap_mmc_init(0, 0, 0, -1, -1);",
"+" + TAB + "omap_mmc_init(1, 0, 0, -1, -1);",
"+" + TAB + "return 0;",
" }",
" #endif",
]
header = """From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001
From: Radsat Developers <dev@radsat.local>
Date: Mon, 2 Nov 2026 21:45:00 -0600
Subject: [PATCH] arm: bbb: init both MMC in SPL (keep SD fallback)

When ROM loads SPL from SD, upstream board_mmc_init only registers
mmc0, so eMMC (mmc1) is invisible. Always init both controllers.
Keep eMMC-first with SD fallback for blank-board bring-up.

---
--- a/board/ti/am335x/board.c
+++ b/board/ti/am335x/board.c
"""
text = header + "\n".join(hunk) + "\n"
p = Path(r"C:\Users\logan\CubeSAT\radsat-linux\common\patches\uboot\0013-bbb-emmc-only-boot.patch")
p.write_text(text, encoding="utf-8", newline="\n")
for l in hunk:
    print(repr(l))
print("size", p.stat().st_size)
