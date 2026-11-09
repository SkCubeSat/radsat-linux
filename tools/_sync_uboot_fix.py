from pathlib import Path
s = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot")
d = Path("/home/logan/code/radsat-linux/common/patches/uboot")
for name in ["0013-bbb-emmc-only-boot.patch", "0017-bbb-fram-recovery-boot.patch"]:
    data = (s/name).read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    (d/name).write_bytes(data)
    print("synced", name, len(data))
