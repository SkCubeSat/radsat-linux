from pathlib import Path
root = Path(r"C:\Users\logan\CubeSAT\radsat-linux\common\patches\uboot")
fixed = []
for p in sorted(root.glob("*.patch")):
    data = p.read_bytes()
    if b"\r\n" in data or b"\r" in data:
        p.write_bytes(data.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
        fixed.append(p.name)
print("fixed", len(fixed), "patches:")
for n in fixed:
    print(" ", n)
# also verify 0018 hunk header
p = root / "0018-bbb-fram-restore-resume.patch"
lines = p.read_text(encoding="utf-8", errors="replace").splitlines()
for i, ln in enumerate(lines[20:35], start=21):
    print(f"{i}: {ln!r}")
