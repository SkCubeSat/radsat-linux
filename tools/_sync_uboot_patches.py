from pathlib import Path
src = Path(r"C:\Users\logan\CubeSAT\radsat-linux\common\patches\uboot")
dst = Path("/home/logan/code/radsat-linux/common/patches/uboot")
# This script is executed inside WSL via path mount
src = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot")
dst = Path("/home/logan/code/radsat-linux/common/patches/uboot")
dst.mkdir(parents=True, exist_ok=True)
for p in sorted(src.glob("*.patch")):
    data = p.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
    (dst / p.name).write_bytes(data)
    print("synced", p.name, "bytes", len(data))
# verify
t = (dst / "0018-bbb-fram-restore-resume.patch").read_text()
assert "fram_mission" in t and "From" in t and "radsat" in t
print("verify OK")
