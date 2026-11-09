from pathlib import Path
import re

def check(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    print("==", path.name)
    for idx, line in enumerate(lines):
        if not line.startswith("@@"):
            continue
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$", line)
        old_c = int(m.group(2) or 1)
        new_c = int(m.group(4) or 1)
        old = new = 0
        j = idx + 1
        while j < len(lines) and not lines[j].startswith("@@"):
            l = lines[j]
            if l.startswith("--- ") or l.startswith("+++ "):
                break
            if l.startswith("\\"):
                j += 1
                continue
            if l.startswith("-"):
                old += 1
            elif l.startswith("+"):
                new += 1
            elif l.startswith(" "):
                old += 1
                new += 1
            elif l == "":
                print(f"  EMPTY unprefixed line {j+1}")
            else:
                print(f"  weird {j+1}: {l!r}")
            j += 1
        ok = (old == old_c and new == new_c)
        print(f"  line {idx+1}: expect {old_c}/{new_c} got {old}/{new} {'OK' if ok else 'BAD'}")

def fix(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.startswith("@@"):
            out.append(line)
            i += 1
            continue
        m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$", line)
        start_old = int(m.group(1))
        start_new = int(m.group(3))
        suffix = m.group(5) or ""
        body = []
        j = i + 1
        while j < len(lines) and not lines[j].startswith("@@"):
            l = lines[j]
            if l.startswith("--- ") or l.startswith("+++ "):
                break
            body.append(l)
            j += 1
        old = new = 0
        for l in body:
            if l.startswith("\\"):
                continue
            if l.startswith("-"):
                old += 1
            elif l.startswith("+"):
                new += 1
            elif l.startswith(" "):
                old += 1
                new += 1
            elif l == "":
                # treat accidental blank as context blank
                old += 1
                new += 1
        out.append(f"@@ -{start_old},{old} +{start_new},{new} @@{suffix}")
        out.extend(body)
        i = j
    text = "\n".join(out) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    print("fixed", path.name)

root = Path(r"C:\Users\logan\CubeSAT\radsat-linux\common\patches\uboot")
for name in [
    "0018-bbb-fram-restore-resume.patch",
    "0019-bbb-fram-virgin-failopen.patch",
    "0020-bbb-fram-boot-count-v6.patch",
]:
    check(root / name)
print("--- fixing ---")
for name in [
    "0018-bbb-fram-restore-resume.patch",
    "0019-bbb-fram-virgin-failopen.patch",
    "0020-bbb-fram-boot-count-v6.patch",
]:
    fix(root / name)
print("--- recheck ---")
for name in [
    "0018-bbb-fram-restore-resume.patch",
    "0019-bbb-fram-virgin-failopen.patch",
    "0020-bbb-fram-boot-count-v6.patch",
]:
    check(root / name)
