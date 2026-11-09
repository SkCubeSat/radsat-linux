from pathlib import Path
src = Path(r"/mnt/c/Users/logan/CubeSAT/radsat-linux/tools/sync-and-build-image.sh")
dst = Path("/tmp/sync-and-build-image.sh")
data = src.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
dst.write_bytes(data)
print("wrote", dst, "bytes", len(data))
