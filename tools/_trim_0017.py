from pathlib import Path
p = Path(r"C:\Users\logan\CubeSAT\radsat-linux\common\patches\uboot\0017-bbb-fram-recovery-boot.patch")
text = p.read_text(encoding="utf-8")
marker = "--- a/include/configs/beaglebone-black.h"
if marker not in text:
    raise SystemExit("marker missing")
text = text.split(marker)[0].rstrip() + "\n"
p.write_text(text, encoding="utf-8", newline="\n")
print("trimmed 0017, size", p.stat().st_size)
# sync to wsl
d = Path("/home/logan/code/radsat-linux/common/patches/uboot/0017-bbb-fram-recovery-boot.patch")
# write via mount
Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0017-bbb-fram-recovery-boot.patch")
