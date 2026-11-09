from pathlib import Path
src_root = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux")
dst_root = Path("/home/logan/code/radsat-linux")
for rel in [
    "package/kubos/kubos.mk",
    "package/kubos/kubos-fram/kubos-fram.mk",
    "package/kubos/kubos-mram/kubos-mram.mk",
]:
    s = src_root / rel
    d = dst_root / rel
    d.parent.mkdir(parents=True, exist_ok=True)
    d.write_bytes(s.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
    print("synced", rel)
text = (dst_root / "package/kubos/kubos-fram/kubos-fram.mk").read_text()
assert "KUBOS_CARGO_CROSS_ENV" in text
print("ok")
