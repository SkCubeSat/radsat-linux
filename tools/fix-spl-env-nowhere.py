#!/usr/bin/env python3
"""Force CONFIG_ENV_IS_NOWHERE for all SPL builds so env_mram is U-Boot-proper only."""
from pathlib import Path
import re

p6 = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0006-bbb-env-on-spi-mram.patch")
t = p6.read_text()

old = """+/* If we're compiling for the SPL, we don't have an env area */
+#if defined(CONFIG_SPL_BUILD) && defined(CONFIG_SPL_USBETH_SUPPORT)
+#define CONFIG_ENV_IS_NOWHERE
+#else
+/*
+ * Primary env: SPI MRAM high region (see mram-service env_offset/env_size).
+ * EXT4 /uboot.env remains a load fallback inside env_mram.c.
+ */
+#define CONFIG_ENV_IS_IN_MRAM		1
"""

new = """+/* SPL has no SPI MRAM env driver linked; use compiled-in defaults there. */
+#ifdef CONFIG_SPL_BUILD
+#define CONFIG_ENV_IS_NOWHERE
+#else
+/*
+ * Primary env: SPI MRAM high region (see mram-service env_offset/env_size).
+ * EXT4 /uboot.env remains a load fallback inside env_mram.c.
+ */
+#define CONFIG_ENV_IS_IN_MRAM		1
"""

if old not in t:
    raise SystemExit("header block missing in 0006")
t = t.replace(old, new, 1)

# Also fix the removed side context if present in the hunk - the - lines still show old USBETH guard
# The unified diff - side may still be the original USBETH form which is fine.

p6.write_text(t)

# Sync to WSL tree
dst = Path("/home/logan/code/radsat-linux/common/patches/uboot/0006-bbb-env-on-spi-mram.patch")
if dst.parent.exists():
    dst.write_text(t)

print("fixed SPL env nowhere")
