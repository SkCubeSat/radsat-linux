#!/bin/bash
# Stage fixed install-os for SD-drop onto a live board (eMMC).
# Usage (Windows): copy C:\Users\logan\CubeSAT\install-os onto the SD card.
# On BBB (rooted on eMMC, SD inserted):
#   mount the SD FAT or ext partition, then:
#     cp /mnt/sd/install-os /usr/sbin/install-os && chmod +x /usr/sbin/install-os
#     install-os status
set -euo pipefail
SRC=/mnt/c/Users/logan/CubeSAT/radsat-linux/board/kubos/beaglebone-black/overlay/usr/sbin/install-os
DEST=/mnt/c/Users/logan/CubeSAT/install-os
tr -d '\r' < "$SRC" > "$DEST"
chmod +x "$DEST"
echo "Staged $DEST"
wc -l "$DEST"
grep -n 'set +e\|essential_span\|basename()' "$DEST" | head -10
