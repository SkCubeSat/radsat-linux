#!/bin/bash
set -euo pipefail
export PATH=/home/logan/radsat-output/host/bin:/usr/bin:/bin
MKIMAGE=/home/logan/radsat-output/build/uboot-1.1.0/tools/mkimage

OUT=/tmp/sample-kpack
IMG=/home/logan/radsat-output/images
DEST=/mnt/c/Users/logan/CubeSAT

mkdir -p "$OUT"
cp "$IMG/beaglebone-black.dtb" "$OUT/"
sed 's/\r$//' /mnt/c/Users/logan/CubeSAT/radsat-linux/tools/kpack-sample.its \
  > "$OUT/kpack.its"

cd "$OUT"
"$MKIMAGE" -E -f kpack.its kpack-sample.itb
"$MKIMAGE" -l kpack-sample.itb
cp -v kpack-sample.itb "$DEST/kpack-sample.itb"
ls -lh "$DEST/kpack-sample.itb"
sha256sum "$DEST/kpack-sample.itb"
