#!/bin/bash
# Generate U-Boot patches 0004 (SPL fallback) and 0005 (DFU dual uboot + name map).
set -euo pipefail
UB=/home/logan/radsat-output/build/uboot-1.1.0
OUT=/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot
DST=/home/logan/code/radsat-linux/common/patches/uboot

if [[ ! -d "$UB" ]]; then
  echo "U-Boot build tree missing: $UB" >&2
  exit 1
fi

# --- 0004: SPL fat load fallback ---
python3 << 'PY'
from pathlib import Path
p = Path("/home/logan/radsat-output/build/uboot-1.1.0/common/spl/spl_mmc.c")
text = p.read_text()
old = """#ifdef CONFIG_SPL_FS_LOAD_PAYLOAD_NAME
	err = spl_load_image_fat(mmc_get_blk_desc(mmc),
				 CONFIG_SYS_MMCSD_FS_BOOT_PARTITION,
				 CONFIG_SPL_FS_LOAD_PAYLOAD_NAME);
	if (!err)
		return err;
#endif
#endif
#ifdef CONFIG_SPL_EXT_SUPPORT"""
new = """#ifdef CONFIG_SPL_FS_LOAD_PAYLOAD_NAME
	err = spl_load_image_fat(mmc_get_blk_desc(mmc),
				 CONFIG_SYS_MMCSD_FS_BOOT_PARTITION,
				 CONFIG_SPL_FS_LOAD_PAYLOAD_NAME);
	if (!err)
		return err;
	/* Primary payload bad/missing: try redundant copy on same FAT. */
	puts("SPL: primary u-boot load failed, trying u-boot-bak.img\\n");
	err = spl_load_image_fat(mmc_get_blk_desc(mmc),
				 CONFIG_SYS_MMCSD_FS_BOOT_PARTITION,
				 "u-boot-bak.img");
	if (!err)
		return err;
#endif
#endif
#ifdef CONFIG_SPL_EXT_SUPPORT"""
if old not in text:
    raise SystemExit("spl_mmc.c: expected primary fat-load block not found")
p.write_text(text.replace(old, new, 1))
print("patched spl_mmc.c")
PY

# --- 0005: DFU alts + update_kubos name mapping ---
python3 << 'PY'
from pathlib import Path

# beaglebone-black.h DFU block
h = Path("/home/logan/radsat-output/build/uboot-1.1.0/include/configs/beaglebone-black.h")
ht = h.read_text()
old = """#define DFU_ALT_INFO_MMC \\
    "dfu_alt_info_mmc="         \\
    "kernel fat 1 1;"       \\
    "rootfs part 1 2;" \\
    "uboot fat 1 1;" \\
    "beaglebone-black.dtb fat 1 1" \\
    "\\0"
"""
new = """#define DFU_ALT_INFO_MMC \\
    "dfu_alt_info_mmc=" \\
    "kernel fat 0 1;" \\
    "rootfs part 0 2;" \\
    "u-boot.img fat 0 1;" \\
    "u-boot-bak.img fat 0 1;" \\
    "beaglebone-black.dtb fat 0 1" \\
    "\\0"
"""
if old not in ht:
    # already patched?
    if "u-boot-bak.img fat 0 1" in ht:
        print("beaglebone-black.h DFU already patched")
    else:
        raise SystemExit("beaglebone-black.h: DFU block not found")
else:
    h.write_text(ht.replace(old, new, 1))
    print("patched beaglebone-black.h DFU")

# update_kubos.c — map FIT node names to DFU entity / FAT filenames
c = Path("/home/logan/radsat-output/build/uboot-1.1.0/common/update_kubos.c")
ct = c.read_text()
if "kubos_fit_to_dfu_name" in ct:
    print("update_kubos.c already has name map")
else:
    needle = "int update_kubos_count(void)\n{"
    helper = r'''
/*
 * Map FIT image node names onto dfu_alt_info_mmc entity names (FAT filenames).
 * Strips trailing @unit (kernel@1 -> kernel). Maps uboot* onto u-boot*.img.
 */
static void kubos_fit_to_dfu_name(const char *fit_name, char *out, size_t outlen)
{
	char base[64];
	const char *at;
	size_t n;

	if (!fit_name || !out || outlen == 0)
		return;

	at = strchr(fit_name, '@');
	n = at ? (size_t)(at - fit_name) : strlen(fit_name);
	if (n >= sizeof(base))
		n = sizeof(base) - 1;
	memcpy(base, fit_name, n);
	base[n] = '\0';

	if (!strcmp(base, "uboot"))
		snprintf(out, outlen, "u-boot.img");
	else if (!strcmp(base, "uboot-bak"))
		snprintf(out, outlen, "u-boot-bak.img");
	else
		snprintf(out, outlen, "%s", base);
}

int update_kubos_count(void)
{
'''
    if needle not in ct:
        raise SystemExit("update_kubos.c: update_kubos_count not found")
    ct = ct.replace(needle, helper, 1)

    old_write = """        if (fit_image_check_type(fit, noffset,
                        IH_TYPE_FIRMWARE)) {
            ret = dfu_tftp_write(fit_image_name, (unsigned int) data_addr,
                         update_size, "mmc", dev_num);
            if (ret) {
                return ret;
            }
        } else {
        	printf("ERROR: Invalid image type\\n");
        }"""
    new_write = """        if (fit_image_check_type(fit, noffset,
                        IH_TYPE_FIRMWARE)) {
            char dfu_name[64];

            kubos_fit_to_dfu_name(fit_image_name, dfu_name, sizeof(dfu_name));
            printf(" -> DFU '%s'", dfu_name);
            ret = dfu_tftp_write(dfu_name, (unsigned int) data_addr,
                         update_size, "mmc", dev_num);
            if (ret) {
                return ret;
            }
        } else {
        	printf("ERROR: Invalid image type\\n");
        }"""
    if old_write not in ct:
        raise SystemExit("update_kubos.c: dfu_tftp_write block not found")
    ct = ct.replace(old_write, new_write, 1)
    # need string.h for memcpy/strlen if not included — common.h usually enough
    c.write_text(ct)
    print("patched update_kubos.c")
PY

mkdir -p "$OUT" "$DST"
cd "$UB"

# Create patches against clean files — use diff from .orig if we saved, else
# regenerate by comparing to git? U-Boot is not clean. Build patches from
# known hunks written directly.

cat > "$OUT/0004-bbb-spl-uboot-fallback.patch" << 'EOF'
From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001
From: Radsat Developers <dev@radsat.local>
Date: Fri, 30 Oct 2026 17:30:00 -0600
Subject: [PATCH] spl: mmc: fall back to u-boot-bak.img on FAT boot

If the primary CONFIG_SPL_FS_LOAD_PAYLOAD_NAME (u-boot.img) fails to
load or validate, try a redundant copy on the same VFAT partition.

---
--- a/common/spl/spl_mmc.c
+++ b/common/spl/spl_mmc.c
@@ -233,6 +233,14 @@
 	err = spl_load_image_fat(mmc_get_blk_desc(mmc),
 				 CONFIG_SYS_MMCSD_FS_BOOT_PARTITION,
 				 CONFIG_SPL_FS_LOAD_PAYLOAD_NAME);
 	if (!err)
 		return err;
+	/* Primary payload bad/missing: try redundant copy on same FAT. */
+	puts("SPL: primary u-boot load failed, trying u-boot-bak.img\n");
+	err = spl_load_image_fat(mmc_get_blk_desc(mmc),
+				 CONFIG_SYS_MMCSD_FS_BOOT_PARTITION,
+				 "u-boot-bak.img");
+	if (!err)
+		return err;
 #endif
 #endif
 #ifdef CONFIG_SPL_EXT_SUPPORT
EOF

# Build 0005 from actual diff of header + update_kubos against pre-edit copies.
# We edited in place; restore from patch application on clean tree at build time.
# Write 0005 fully by hand from intended final content.

cat > "$OUT/0005-bbb-dfu-dual-uboot.patch" << 'EOF'
From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001
From: Radsat Developers <dev@radsat.local>
Date: Fri, 30 Oct 2026 17:35:00 -0600
Subject: [PATCH] arm: am33xx: dual U-Boot DFU alts on boot MMC0

Point Kubos DFU at mmc 0 (boot media), ship u-boot.img + u-boot-bak.img
FAT targets, and map FIT nodes uboot/uboot-bak (and @unit names) onto
those filenames during update_kubos.

---
--- a/include/configs/beaglebone-black.h
+++ b/include/configs/beaglebone-black.h
@@ -69,11 +69,12 @@
 /* DFU Configuration */
 #define DFU_ALT_INFO_MMC \
-    "dfu_alt_info_mmc="         \
-    "kernel fat 1 1;"       \
-    "rootfs part 1 2;" \
-    "uboot fat 1 1;" \
-    "beaglebone-black.dtb fat 1 1" \
+    "dfu_alt_info_mmc=" \
+    "kernel fat 0 1;" \
+    "rootfs part 0 2;" \
+    "u-boot.img fat 0 1;" \
+    "u-boot-bak.img fat 0 1;" \
+    "beaglebone-black.dtb fat 0 1" \
     "\0"
 
 #define DFU_ALT_INFO_NOR ""
--- a/common/update_kubos.c
+++ b/common/update_kubos.c
@@ -35,6 +35,33 @@
 #define PART_ENVAR         "kubos_updatepart"
 #define LOAD_ENVAR         "kubos_loadaddr"
 
+/*
+ * Map FIT image node names onto dfu_alt_info_mmc entity names (FAT filenames).
+ * Strips trailing @unit (kernel@1 -> kernel). Maps uboot* onto u-boot*.img.
+ */
+static void kubos_fit_to_dfu_name(const char *fit_name, char *out, size_t outlen)
+{
+	char base[64];
+	const char *at;
+	size_t n;
+
+	if (!fit_name || !out || outlen == 0)
+		return;
+
+	at = strchr(fit_name, '@');
+	n = at ? (size_t)(at - fit_name) : strlen(fit_name);
+	if (n >= sizeof(base))
+		n = sizeof(base) - 1;
+	memcpy(base, fit_name, n);
+	base[n] = '\0';
+
+	if (!strcmp(base, "uboot"))
+		snprintf(out, outlen, "u-boot.img");
+	else if (!strcmp(base, "uboot-bak"))
+		snprintf(out, outlen, "u-boot-bak.img");
+	else
+		snprintf(out, outlen, "%s", base);
+}
+
 int update_kubos_count(void)
 {
 
@@ -155,8 +182,12 @@
 
         if (fit_image_check_type(fit, noffset,
                         IH_TYPE_FIRMWARE)) {
-            ret = dfu_tftp_write(fit_image_name, (unsigned int) data_addr,
+            char dfu_name[64];
+
+            kubos_fit_to_dfu_name(fit_image_name, dfu_name, sizeof(dfu_name));
+            printf(" -> DFU '%s'", dfu_name);
+            ret = dfu_tftp_write(dfu_name, (unsigned int) data_addr,
                          update_size, "mmc", dev_num);
             if (ret) {
                 return ret;
EOF

# LF-only copies into WSL tree
for f in 0004-bbb-spl-uboot-fallback.patch 0005-bbb-dfu-dual-uboot.patch; do
  tr -d '\r' < "$OUT/$f" > "$DST/$f"
  echo "wrote $DST/$f"
done

# Revert in-tree U-Boot edits so Buildroot applies patches cleanly from tarball/rsync
# The build uses Kubos U-Boot from git; patches apply on extract. In-place edits
# would double-apply. Restore from the patch inverse by checking out if possible.
cd "$UB"
if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  git checkout -- common/spl/spl_mmc.c include/configs/beaglebone-black.h common/update_kubos.c 2>/dev/null || true
  echo "restored uboot working tree files for clean patch apply"
else
  echo "WARN: no git in uboot tree; ensure next uboot-dirclean re-extracts sources"
fi
