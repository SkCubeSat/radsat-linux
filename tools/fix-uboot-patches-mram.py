#!/usr/bin/env python3
from pathlib import Path
import shutil

# Fix 0007: layout missing is OK (migration); wrong magic skips
p = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0007-bbb-fram-mission-policy.patch")
t = p.read_text()
old = (
    "+\tif (!fram_layout_ok()) {\n"
    '+\t\tputs("FRAM: layout magic/version missing; skipping mission overlay\\n");\n'
    "+\t\tgoto out;\n"
    "+\t}\n"
)
new = (
    "+\t/* Wrong magic/version => refuse. Missing header => allow (migration). */\n"
    "+\tif (fram_layout_present_invalid()) {\n"
    '+\t\tputs("FRAM: layout magic/version mismatch; skipping mission overlay\\n");\n'
    "+\t\tgoto out;\n"
    "+\t}\n"
)
old_fn = (
    "+static int fram_layout_ok(void)\n"
    "+{\n"
    "+\tu8 hdr[16];\n"
    "+\tu32 magic;\n"
    "+\tu16 ver;\n"
    "+\n"
    "+\tif (fram_read(FRAM_LAYOUT_OFFSET, hdr, sizeof(hdr)))\n"
    "+\t\treturn 0;\n"
    "+\tmagic = hdr[0] | (hdr[1] << 8) | (hdr[2] << 16) | (hdr[3] << 24);\n"
    "+\tver = hdr[4] | (hdr[5] << 8);\n"
    "+\treturn magic == FRAM_LAYOUT_MAGIC && ver == FRAM_LAYOUT_VERSION;\n"
    "+}\n"
)
new_fn = (
    "+/* Returns 1 when a non-blank header exists but does not match. */\n"
    "+static int fram_layout_present_invalid(void)\n"
    "+{\n"
    "+\tu8 hdr[16];\n"
    "+\tu32 magic;\n"
    "+\tu16 ver;\n"
    "+\tint i, blank = 1;\n"
    "+\n"
    "+\tif (fram_read(FRAM_LAYOUT_OFFSET, hdr, sizeof(hdr)))\n"
    "+\t\treturn 0;\n"
    "+\tfor (i = 0; i < 16; i++) {\n"
    "+\t\tif (hdr[i] != 0x00 && hdr[i] != 0xff)\n"
    "+\t\t\tblank = 0;\n"
    "+\t}\n"
    "+\tif (blank)\n"
    "+\t\treturn 0;\n"
    "+\tmagic = hdr[0] | (hdr[1] << 8) | (hdr[2] << 16) | (hdr[3] << 24);\n"
    "+\tver = hdr[4] | (hdr[5] << 8);\n"
    "+\treturn !(magic == FRAM_LAYOUT_MAGIC && ver == FRAM_LAYOUT_VERSION);\n"
    "+}\n"
)
if old_fn not in t:
    raise SystemExit("fn missing")
if old not in t:
    raise SystemExit("call missing")
t = t.replace(old_fn, new_fn).replace(old, new)
p.write_text(t)
print("0007 updated")

p6 = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot/0006-bbb-env-on-spi-mram.patch")
t6 = p6.read_text()
old_xfer = (
    "+static int mram_xfer(struct spi_slave *slave, const void *dout, void *din,\n"
    "+\t\t     unsigned int len)\n"
    "+{\n"
    "+\tint ret;\n"
    "+\n"
    "+\tret = spi_claim_bus(slave);\n"
    "+\tif (ret)\n"
    "+\t\treturn ret;\n"
    "+\tret = spi_xfer(slave, len * 8, dout, din,\n"
    "+\t\t       SPI_XFER_BEGIN | SPI_XFER_END);\n"
    "+\tspi_release_bus(slave);\n"
    "+\treturn ret;\n"
    "+}\n"
)
new_xfer = (
    "+static int mram_xfer(struct spi_slave *slave, void *buf, unsigned int len)\n"
    "+{\n"
    "+\tint ret;\n"
    "+\n"
    "+\tret = spi_claim_bus(slave);\n"
    "+\tif (ret)\n"
    "+\t\treturn ret;\n"
    "+\tret = spi_xfer(slave, len * 8, buf, buf,\n"
    "+\t\t       SPI_XFER_BEGIN | SPI_XFER_END);\n"
    "+\tspi_release_bus(slave);\n"
    "+\treturn ret;\n"
    "+}\n"
)
if old_xfer not in t6:
    raise SystemExit("xfer missing")
t6 = t6.replace(old_xfer, new_xfer)
t6 = t6.replace(
    "+\tret = mram_xfer(slave, frame, frame, 4 + len);\n",
    "+\tret = mram_xfer(slave, frame, 4 + len);\n",
)
t6 = t6.replace(
    "+\tret = mram_xfer(slave, &wren, NULL, 1);\n",
    "+\tret = mram_xfer(slave, &wren, 1);\n",
)
t6 = t6.replace(
    "+\tret = mram_xfer(slave, frame, NULL, 4 + len);\n",
    "+\tret = mram_xfer(slave, frame, 4 + len);\n",
)
p6.write_text(t6)
print("0006 xfer fixed")

dst = Path("/home/logan/code/radsat-linux/common/patches/uboot")
if dst.parent.exists():
    dst.mkdir(parents=True, exist_ok=True)
    shutil.copy2(p, dst / p.name)
    shutil.copy2(p6, dst / p6.name)
    print("synced to", dst)
