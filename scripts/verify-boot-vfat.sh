#!/bin/bash
set -e
export PATH=/home/logan/radsat-output/host/bin:/usr/bin:/bin
OUT=/home/logan/radsat-output/images
ls -lh "$OUT"/u-boot.img "$OUT"/u-boot-bak.img "$OUT"/kpack-uboot.itb
if [[ -f "$OUT/boot.vfat" ]]; then
  mdir -i "$OUT/boot.vfat" ::
else
  echo "boot.vfat cleaned; extracting from tar"
  tar -xzf "$OUT/kubos-linux.tar.gz" -C "$OUT" kubos-linux.img
  # partition 1 is boot vfat — use mcopy from genimage leftover or losetup
  # Fall back: strings/search in img for filename
  strings "$OUT/kubos-linux.img" | grep -E 'U-BOOT|u-boot' | head
fi
# Confirm both names were requested by genimage.cfg in tree
grep -A8 'boot.vfat' /home/logan/code/radsat-linux/board/kubos/beaglebone-black/genimage.cfg
echo FAT_VERIFY_DONE
