#!/usr/bin/env python3
from pathlib import Path

p = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/tools/sync-and-build-image.sh")
t = p.read_text()
if "verify-mram-fram-boot" not in t:
    t = t.replace(
        "sync_one board/kubos/beaglebone-black/overlay/usr/sbin/fram-set\n",
        "sync_one board/kubos/beaglebone-black/overlay/usr/sbin/fram-set\n"
        "sync_one board/kubos/beaglebone-black/overlay/usr/sbin/verify-mram-fram-boot\n",
    )
    t = t.replace(
        'chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set"\n',
        'chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set"\n'
        'chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/verify-mram-fram-boot"\n',
    )
    t = t.replace(
        'install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set" \\\n'
        '  "$OUT/target/usr/sbin/fram-set"\n',
        'install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set" \\\n'
        '  "$OUT/target/usr/sbin/fram-set"\n'
        'install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/verify-mram-fram-boot" \\\n'
        '  "$OUT/target/usr/sbin/verify-mram-fram-boot"\n',
    )
    p.write_text(t)
print("ok", "verify-mram-fram-boot" in p.read_text())
