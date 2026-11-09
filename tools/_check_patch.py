from pathlib import Path
import re
path = Path(r"C:\Users\logan\CubeSAT\radsat-linux\common\patches\uboot\0018-bbb-fram-restore-resume.patch")
lines = path.read_text(encoding="utf-8").splitlines()
for idx, line in enumerate(lines):
    if not line.startswith("@@"):
        continue
    m = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
    old_c = int(m.group(2) or 1)
    new_c = int(m.group(4) or 1)
    old = new = 0
    problems = []
    j = idx + 1
    while j < len(lines) and not lines[j].startswith("@@"):
        l = lines[j]
        if l.startswith("\\"):
            j += 1
            continue
        if l.startswith("--- ") or l.startswith("+++ "):
            break
        if l.startswith("-"):
            old += 1
        elif l.startswith("+"):
            new += 1
        elif l.startswith(" "):
            old += 1
            new += 1
        elif l == "":
            problems.append(f"empty-unprefixed at {j+1}")
            # patch treats this badly
        else:
            problems.append(f"weird {j+1}: {l!r}")
        j += 1
    print(f"hunk {idx+1}: expect old={old_c} new={new_c}; got old={old} new={new}; problems={problems}")
