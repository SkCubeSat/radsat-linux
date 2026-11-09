#!/bin/sh

set -e

BOARD_DIR="$(dirname "$0")"
CURR_DIR="$(pwd)"
BRANCH=$2
OUTPUT=$(basename "${BASE_DIR}")

GENIMAGE_CFG="${BOARD_DIR}/genimage.cfg"
GENIMAGE_FLIGHT_CFG="${BOARD_DIR}/genimage-flight.cfg"
GENIMAGE_TMP="${BUILD_DIR}/genimage.tmp"
# Flight slim image is opt-in for now (lab image is the default deliverable).
BUILD_FLIGHT_IMAGE="${BUILD_FLIGHT_IMAGE:-0}"

rm -rf "${GENIMAGE_TMP}"

# Create the kernel FIT file
cp "${BOARD_DIR}/kubos-kernel.its" "${BINARIES_DIR}/"
cd "${BR2_EXTERNAL_KUBOS_LINUX_PATH}/tools"
./kubos-kernel.sh -b "${BRANCH}" \
    -i "${BINARIES_DIR}/kubos-kernel.its" -o "${OUTPUT}"

mv kubos-kernel.itb "${BINARIES_DIR}/kernel"

# Dual U-Boot copies on the VFAT boot partition (SPL primary + bak).
cp -f "${BINARIES_DIR}/u-boot.img" "${BINARIES_DIR}/u-boot-bak.img"

# Upgrade ITBs live only in the genimage /upgrade partition. Clear any
# leftovers so Buildroot's rootfs.ext2 (256M) is never poisoned by ~520M
# of kpacks from an interrupted previous post-image run.
mkdir -p "${TARGET_DIR}/upgrade"
find "${TARGET_DIR}/upgrade" -mindepth 1 -maxdepth 1 -delete

# Create the base upgrade file (kernel + rootfs + dtb + dual U-Boot)
cd "${BR2_EXTERNAL_KUBOS_LINUX_PATH}/tools"
./kubos-package.sh -b "${BRANCH}" -t beaglebone-black -v base \
    -i "${BOARD_DIR}/kpack.its"

mv kpack-base.itb "${TARGET_DIR}/upgrade"

# Rootfs+kernel+dtb only (no U-Boot) — Phase 1 safe deploy
./kubos-package.sh -b "${BRANCH}" -t beaglebone-black -v rootfs \
    -i "${BOARD_DIR}/kpack-rootfs.its"
mv kpack-rootfs.itb "${TARGET_DIR}/upgrade/"
cp -f "${TARGET_DIR}/upgrade/kpack-rootfs.itb" "${BINARIES_DIR}/kpack-rootfs.itb"

# U-Boot-only upgrade package for bootloader-redundant updates
./kubos-package.sh -b "${BRANCH}" -t beaglebone-black -v uboot \
    -i "${BOARD_DIR}/kpack-uboot.its"
mv kpack-uboot.itb "${TARGET_DIR}/upgrade/"
# Also keep a copy next to images for PC-side install/tests
cp -f "${TARGET_DIR}/upgrade/kpack-uboot.itb" "${BINARIES_DIR}/kpack-uboot.itb"

mkdir -p "${TARGET_DIR}/microsd"

cd "${CURR_DIR}"

# Seed the U-Boot environment file for fw_printenv/fw_setenv.
# Size must match CONFIG_ENV_SIZE (0x2800 = 10240 bytes).
dd if=/dev/zero of="${TARGET_DIR}/envar/uboot.env" bs=1 count=10240 2>/dev/null

# Generate the lab/dev images (includes 3G /home + aux-sd)
genimage \
    --rootpath "${TARGET_DIR}" \
    --tmppath "${GENIMAGE_TMP}" \
    --inputpath "${BINARIES_DIR}" \
    --outputpath "${BINARIES_DIR}" \
    --config "${GENIMAGE_CFG}"

# Package it all up for easy transfer
tar -czf "${BINARIES_DIR}/kubos-linux.tar.gz" \
    -C "${BINARIES_DIR}" kubos-linux.img
tar -czf "${BINARIES_DIR}/aux-sd.tar.gz" \
    -C "${BINARIES_DIR}" aux-sd.img

# Slim flight disk: boot + 256M rootfs + envar + 32M empty upgrade (~310M).
# Lab aux-sd already packaged the kpacks; flight card stays golden/bootable only.
if [ "${BUILD_FLIGHT_IMAGE}" = "1" ] && [ -f "${GENIMAGE_FLIGHT_CFG}" ]; then
    FLIGHT_FSTAB="$(cd "${BOARD_DIR}" && pwd)/overlay-flight/etc/fstab"
    if [ ! -f "${BINARIES_DIR}/rootfs.ext4" ]; then
        echo "post-image: rootfs.ext4 missing; skipping flight image" >&2
    elif [ ! -f "${FLIGHT_FSTAB}" ]; then
        echo "post-image: ${FLIGHT_FSTAB} missing; skipping flight image" >&2
    else
        cp -f "${BINARIES_DIR}/rootfs.ext4" "${BINARIES_DIR}/rootfs-flight.ext4"
        # Inject flight fstab into the copied rootfs (lab rootfs stays untouched).
        debugfs -w -R "rm /etc/fstab" "${BINARIES_DIR}/rootfs-flight.ext4" || true
        debugfs -w -R "write ${FLIGHT_FSTAB} /etc/fstab" \
            "${BINARIES_DIR}/rootfs-flight.ext4"

        # Keep p4 for U-Boot, but do not stuff multi-hundred-MB ITBs onto flight media.
        mkdir -p "${TARGET_DIR}/upgrade" "${TARGET_DIR}/envar"
        find "${TARGET_DIR}/upgrade" -mindepth 1 -maxdepth 1 -delete
        dd if=/dev/zero of="${TARGET_DIR}/envar/uboot.env" bs=1 count=10240 2>/dev/null

        rm -rf "${GENIMAGE_TMP}"
        genimage \
            --rootpath "${TARGET_DIR}" \
            --tmppath "${GENIMAGE_TMP}" \
            --inputpath "${BINARIES_DIR}" \
            --outputpath "${BINARIES_DIR}" \
            --config "${GENIMAGE_FLIGHT_CFG}"

        tar -czf "${BINARIES_DIR}/kubos-linux-flight.tar.gz" \
            -C "${BINARIES_DIR}" kubos-linux-flight.img
        gzip -c -9 "${BINARIES_DIR}/kubos-linux-flight.img" \
            > "${BINARIES_DIR}/kubos-linux-flight.img.gz"

        rm -f "${BINARIES_DIR}/upgrade-flight"
        rm -f "${BINARIES_DIR}/rootfs-flight.ext4"
        rm -f "${BINARIES_DIR}/kubos-linux-flight.img"
    fi
fi

# Clean up
find "${TARGET_DIR}/upgrade" -mindepth 1 -maxdepth 1 -delete
rmdir "${TARGET_DIR}/microsd"
rm -f "${TARGET_DIR}/envar/uboot.env"

# Removing these just to free up disk space...
rm -f "${BINARIES_DIR}/user"
rm -f "${BINARIES_DIR}/aux-user"
rm -f "${BINARIES_DIR}/upgrade"
rm -f "${BINARIES_DIR}/kubos-linux.img"
rm -f "${BINARIES_DIR}/aux-sd.img"
