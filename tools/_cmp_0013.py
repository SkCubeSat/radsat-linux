from pathlib import Path
board = Path("/home/logan/radsat-output/build/uboot-1.1.0/board/ti/am335x/board.c").read_text().splitlines()
for i,l in enumerate(board):
    if "board_boot_order" in l:
        for j in range(i-3, i+6):
            print("BOARD", j+1, repr(board[j]))
        break
patch = Path("/home/logan/code/radsat-linux/common/patches/uboot/0013-bbb-emmc-only-boot.patch").read_bytes()
print("patch has real tabs", b"\t" in patch)
for l in Path("/home/logan/code/radsat-linux/common/patches/uboot/0013-bbb-emmc-only-boot.patch").read_text().splitlines():
    if "spl_boot" in l or l.startswith("@@") or "board_boot" in l or l[1:].strip() in ("{", "}", "/*", "*/", "#endif"):
        print("PATCH", repr(l))
