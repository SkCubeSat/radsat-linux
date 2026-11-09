from pathlib import Path
s = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/tools/_resume_build.sh")
d = Path("/tmp/_resume_build.sh")
d.write_bytes(s.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
assert b"KUBOS_OVERRIDE_SRCDIR" in d.read_bytes()
print("ready")
