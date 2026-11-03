#!/usr/bin/env python3
from pathlib import Path

# Fix mram graphql capacity expectation (payload window)
p = Path("/mnt/c/Users/logan/CubeSAT/Software/services/hardware-services/mram-service/tests/graphql.rs")
t = p.read_text()
t2 = t.replace(
    'image_capacity_bytes = 524288\n',
    'image_capacity_bytes = 524288\nenv_offset = 514048\nenv_size = 10240\n',
)
# capacityBytes in storage stats is littlefs payload capacity
if 'assert_eq!(storage["capacityBytes"], 524288)' in t2:
    t2 = t2.replace(
        'assert_eq!(storage["capacityBytes"], 524288)',
        'assert_eq!(storage["capacityBytes"], 514048)',
    )
elif "capacityBytes" in t2 and "524288" in t2:
    # find assertion more loosely
    import re
    t2, n = re.subn(
        r'assert_eq!\(storage\["capacityBytes"\],\s*524288\)',
        'assert_eq!(storage["capacityBytes"], 514048)',
        t2,
    )
    print("capacity assert replacements", n)
p.write_text(t2)
print("mram graphql test patched")

# Update sync-and-build-image.sh
s = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/tools/sync-and-build-image.sh")
st = s.read_text()
if "0006-bbb-env-on-spi-mram.patch" not in st:
    st = st.replace(
        "sync_one common/patches/uboot/0005-bbb-dfu-dual-uboot.patch\n",
        "sync_one common/patches/uboot/0005-bbb-dfu-dual-uboot.patch\n"
        "sync_one common/patches/uboot/0006-bbb-env-on-spi-mram.patch\n"
        "sync_one common/patches/uboot/0007-bbb-fram-mission-policy.patch\n",
    )
if "S79mram-env-sync" not in st:
    st = st.replace(
        "sync_one board/kubos/beaglebone-black/overlay/usr/sbin/install-os\n",
        "sync_one board/kubos/beaglebone-black/overlay/usr/sbin/install-os\n"
        "sync_one board/kubos/beaglebone-black/overlay/usr/sbin/fram-get\n"
        "sync_one board/kubos/beaglebone-black/overlay/usr/sbin/fram-set\n"
        "sync_one board/kubos/beaglebone-black/overlay/etc/init.d/S79mram-env-sync\n",
    )
if "fram-get" in st and "chmod +x" in st:
    if "fram-get" not in st.split("chmod +x")[1][:800]:
        st = st.replace(
            'chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/install-os"\n',
            'chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/install-os"\n'
            'chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-get"\n'
            'chmod +x "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set"\n'
            'chmod +x "$DST/board/kubos/beaglebone-black/overlay/etc/init.d/S79mram-env-sync"\n',
        )
# Force kubos fram/mram rebuild by default for this change set
st = st.replace(
    'if [[ "${FORCE_KUBOS:-0}" == "1" ]]; then\n'
    '  make O="$OUT" kubos-dirclean || true\n'
    '  make O="$OUT" kubos-fram-dirclean || true\n'
    "fi\n",
    'if [[ "${FORCE_KUBOS:-1}" == "1" ]]; then\n'
    '  make O="$OUT" kubos-dirclean || true\n'
    '  make O="$OUT" kubos-fram-dirclean || true\n'
    '  make O="$OUT" kubos-mram-dirclean || true\n'
    "fi\n",
)
# Ensure S79 installed into target after build
if "S79mram-env-sync" not in st[st.find("Keep FRAM") :]:
    st = st.replace(
        'install -D -m 0755 "$DST/package/kubos/kubos-mram/kubos-mram" \\\n'
        '  "$OUT/target/etc/init.d/S91kubos-mram"\n'
        'rm -f "$OUT/target/etc/init.d/S90kubos-fram" "$OUT/target/etc/init.d/S90kubos-mram"\n',
        'install -D -m 0755 "$DST/package/kubos/kubos-mram/kubos-mram" \\\n'
        '  "$OUT/target/etc/init.d/S91kubos-mram"\n'
        'install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/etc/init.d/S79mram-env-sync" \\\n'
        '  "$OUT/target/etc/init.d/S79mram-env-sync"\n'
        'install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-get" \\\n'
        '  "$OUT/target/usr/sbin/fram-get"\n'
        'install -D -m 0755 "$DST/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set" \\\n'
        '  "$OUT/target/usr/sbin/fram-set"\n'
        'rm -f "$OUT/target/etc/init.d/S90kubos-fram" "$OUT/target/etc/init.d/S90kubos-mram"\n',
    )
s.write_text(st)
print("sync script updated")
