from pathlib import Path
src = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/package/kubos/kubos.mk")
dst = Path("/home/logan/code/radsat-linux/package/kubos/kubos.mk")
dst.write_bytes(src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
assert b"env \\" in dst.read_bytes() or b"\tenv \\" in dst.read_bytes() or "env" in dst.read_text()
print(dst.read_text().split("KUBOS_CARGO_CROSS_ENV")[1][:400])
