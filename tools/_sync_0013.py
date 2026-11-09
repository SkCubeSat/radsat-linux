from pathlib import Path
s = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0013-bbb-emmc-only-boot.patch")
d = Path("/home/logan/code/radsat-linux/common/patches/uboot/0013-bbb-emmc-only-boot.patch")
d.write_bytes(s.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
print("synced", d.stat().st_size)
