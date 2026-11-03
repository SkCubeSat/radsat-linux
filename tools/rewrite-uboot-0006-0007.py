#!/usr/bin/env python3
"""Rewrite 0006/0007 as valid unified diffs with correct hunk lengths."""
from __future__ import annotations

import shutil
import subprocess
import tempfile
from pathlib import Path

OUT = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/common/patches/uboot")
DST2 = Path("/home/logan/code/radsat-linux/common/patches/uboot")

# Use currently extracted failing tree if present, else extract-like from prior clean copy.
# Prefer regenerating by applying 0001-0005 to a fresh extract.

BR_DL = Path("/home/logan/code/buildroot-2025.02.14/dl/uboot/uboot-1.1.0-git4.tar.gz")
PATCHES = [
    OUT / "0001-bbb-console-115200.patch",
    OUT / "0002-bbb-env-on-boot-mmc.patch",
    OUT / "0003-bbb-announce-boot-media.patch",
    OUT / "0004-bbb-spl-uboot-fallback.patch",
    OUT / "0005-bbb-dfu-dual-uboot.patch",
]

ENV_MRAM_C = Path("/tmp/env_mram.c")
FRAM_C = Path("/tmp/fram_mission.c")

ENV_MRAM_C.write_text(r'''/*
 * SPI MRAM environment storage for RadSat (MR2xH40 protocol).
 *
 * Loads/saves the classic U-Boot env blob from a reserved high region on
 * McSPI2 CS0 (Linux /dev/spidev1.0). Falls back to EXT4 /uboot.env when the
 * MRAM CRC is invalid or SPI is unavailable.
 *
 * SPDX-License-Identifier:	GPL-2.0+
 */

#include <common.h>
#include <command.h>
#include <environment.h>
#include <errno.h>
#include <malloc.h>
#include <memalign.h>
#include <search.h>
#include <spi.h>
#include <ext4fs.h>
#include <mmc.h>

DECLARE_GLOBAL_DATA_PTR;

#ifndef CONFIG_ENV_MRAM_BUS
# define CONFIG_ENV_MRAM_BUS	1	/* McSPI2 == Linux spi1 */
#endif
#ifndef CONFIG_ENV_MRAM_CS
# define CONFIG_ENV_MRAM_CS	0
#endif
#ifndef CONFIG_ENV_MRAM_MAX_HZ
# define CONFIG_ENV_MRAM_MAX_HZ	10000000
#endif
#ifndef CONFIG_ENV_MRAM_MODE
# define CONFIG_ENV_MRAM_MODE	SPI_MODE_0
#endif
#ifndef CONFIG_ENV_MRAM_OFFSET
# define CONFIG_ENV_MRAM_OFFSET	0x7D800	/* capacity 0x80000 - 0x2800 */
#endif

#define MRAM_CMD_WREN	0x06
#define MRAM_CMD_READ	0x03
#define MRAM_CMD_WRITE	0x02

char *env_name_spec = "SPI MRAM";

env_t *env_ptr;

int env_init(void)
{
	gd->env_addr = (ulong)&default_environment[0];
	gd->env_valid = 1;
	return 0;
}

static int mram_xfer(struct spi_slave *slave, void *buf, unsigned int len)
{
	int ret;

	ret = spi_claim_bus(slave);
	if (ret)
		return ret;
	ret = spi_xfer(slave, len * 8, buf, buf,
		       SPI_XFER_BEGIN | SPI_XFER_END);
	spi_release_bus(slave);
	return ret;
}

static int mram_read(struct spi_slave *slave, u32 offset, void *buf, u32 len)
{
	u8 *frame;
	int ret;

	frame = malloc(4 + len);
	if (!frame)
		return -ENOMEM;
	frame[0] = MRAM_CMD_READ;
	frame[1] = (offset >> 16) & 0xff;
	frame[2] = (offset >> 8) & 0xff;
	frame[3] = offset & 0xff;
	memset(frame + 4, 0, len);

	ret = mram_xfer(slave, frame, 4 + len);
	if (!ret)
		memcpy(buf, frame + 4, len);
	free(frame);
	return ret;
}

static int mram_write(struct spi_slave *slave, u32 offset, const void *buf,
		      u32 len)
{
	u8 wren = MRAM_CMD_WREN;
	u8 *frame;
	int ret;

	ret = mram_xfer(slave, &wren, 1);
	if (ret)
		return ret;

	frame = malloc(4 + len);
	if (!frame)
		return -ENOMEM;
	frame[0] = MRAM_CMD_WRITE;
	frame[1] = (offset >> 16) & 0xff;
	frame[2] = (offset >> 8) & 0xff;
	frame[3] = offset & 0xff;
	memcpy(frame + 4, buf, len);

	ret = mram_xfer(slave, frame, 4 + len);
	free(frame);
	return ret;
}

static int env_import_ext4_fallback(void)
{
	ALLOC_CACHE_ALIGN_BUFFER(char, buf, CONFIG_ENV_SIZE);
	struct blk_desc *dev_desc = NULL;
	disk_partition_t info;
	int part, err;
	loff_t off;

	part = blk_get_device_part_str(EXT4_ENV_INTERFACE,
					EXT4_ENV_DEVICE_AND_PART,
					&dev_desc, &info, 1);
	if (part < 0)
		return -ENODEV;

	ext4fs_set_blk_dev(dev_desc, &info);
	if (!ext4fs_mount(info.size))
		return -ENODEV;

	err = ext4_read_file(EXT4_ENV_FILE, buf, 0, CONFIG_ENV_SIZE, &off);
	ext4fs_close();
	if (err == -1)
		return -EIO;

	return env_import(buf, 1);
}

#ifdef CONFIG_CMD_SAVEENV
int saveenv(void)
{
	env_t env_new;
	struct spi_slave *slave;
	int ret;

	ret = env_export(&env_new);
	if (ret)
		return ret;

	slave = spi_setup_slave(CONFIG_ENV_MRAM_BUS, CONFIG_ENV_MRAM_CS,
				CONFIG_ENV_MRAM_MAX_HZ, CONFIG_ENV_MRAM_MODE);
	if (!slave) {
		puts("MRAM: spi_setup_slave failed\n");
		return 1;
	}

	puts("Writing env to SPI MRAM...");
	ret = mram_write(slave, CONFIG_ENV_MRAM_OFFSET, &env_new,
			 CONFIG_ENV_SIZE);
	spi_free_slave(slave);
	if (ret) {
		printf("FAILED (%d)\n", ret);
		return 1;
	}
	puts("OK\n");
	return 0;
}
#endif

void env_relocate_spec(void)
{
	ALLOC_CACHE_ALIGN_BUFFER(char, buf, CONFIG_ENV_SIZE);
	struct spi_slave *slave;
	int ret;

	slave = spi_setup_slave(CONFIG_ENV_MRAM_BUS, CONFIG_ENV_MRAM_CS,
				CONFIG_ENV_MRAM_MAX_HZ, CONFIG_ENV_MRAM_MODE);
	if (slave) {
		ret = mram_read(slave, CONFIG_ENV_MRAM_OFFSET, buf,
				CONFIG_ENV_SIZE);
		spi_free_slave(slave);
		if (!ret && !env_import(buf, 1)) {
			puts("Env: loaded from SPI MRAM\n");
			return;
		}
		puts("Env: MRAM CRC/import failed, trying EXT4\n");
	} else {
		puts("Env: MRAM SPI unavailable, trying EXT4\n");
	}

	if (!env_import_ext4_fallback()) {
		puts("Env: loaded from EXT4 fallback\n");
		return;
	}

	puts("Env: using compiled-in defaults\n");
	set_default_env(NULL);
}
''')

FRAM_C.write_text(r'''/*
 * Overlay allowlisted mission/boot-policy keys from I2C2 FRAM (FM24CL64B @ 0x50).
 *
 * Anti-brick rules:
 * - Never set bootcmd/bootargs/DFU/root from FRAM.
 * - Bad layout magic, bad boot CRC, or I2C failure: warn and continue.
 *
 * SPDX-License-Identifier:	GPL-2.0+
 */

#include <common.h>
#include <environment.h>
#include <i2c.h>

#ifndef CONFIG_FRAM_I2C_BUS
# define CONFIG_FRAM_I2C_BUS	2	/* Linux /dev/i2c-2 — NOT cape EEPROM bus */
#endif
#ifndef CONFIG_FRAM_I2C_ADDR
# define CONFIG_FRAM_I2C_ADDR	0x50
#endif

#define FRAM_RECORD_SIZE	32
#define FRAM_SLOTS_PER_KEY	2
#define FRAM_BOOT_POLICY_KEYS	6
#define FRAM_BOOT_DATA_END	(FRAM_BOOT_POLICY_KEYS * FRAM_SLOTS_PER_KEY * FRAM_RECORD_SIZE)
#define FRAM_LAYOUT_MAGIC	0x4D415246u	/* "FRAM" LE */
#define FRAM_LAYOUT_VERSION	1
#define FRAM_LAYOUT_OFFSET	2048
#define FRAM_REC_MAGIC		0x4652

struct fram_key {
	u8 id;
	const char *name;
	u8 vtype;	/* 1=bool 2=timestamp 3=u64 */
};

static const struct fram_key fram_keys[] = {
	{ 1, "remove_before_flight", 1 },
	{ 2, "deployed", 1 },
	{ 3, "deploy_start", 2 },
	{ 4, "initial_safe_state_complete", 1 },
	{ 5, "fsoo_timer", 3 },
	{ 6, "detumbling_complete", 1 },
};

static u32 crc32_fram(const u8 *data, u32 len)
{
	u32 crc = 0xffffffff;
	u32 i, b;

	for (i = 0; i < len; i++) {
		crc ^= data[i];
		for (b = 0; b < 8; b++) {
			if (crc & 1)
				crc = (crc >> 1) ^ 0xedb88320;
			else
				crc >>= 1;
		}
	}
	return ~crc;
}

static int fram_read(u16 offset, u8 *buf, int len)
{
	return i2c_read(CONFIG_FRAM_I2C_ADDR, offset, 2, buf, len);
}

static int fram_layout_present_invalid(void)
{
	u8 hdr[16];
	u32 magic;
	u16 ver;
	int i, blank = 1;

	if (fram_read(FRAM_LAYOUT_OFFSET, hdr, sizeof(hdr)))
		return 0;
	for (i = 0; i < 16; i++) {
		if (hdr[i] != 0x00 && hdr[i] != 0xff)
			blank = 0;
	}
	if (blank)
		return 0;
	magic = hdr[0] | (hdr[1] << 8) | (hdr[2] << 16) | (hdr[3] << 24);
	ver = hdr[4] | (hdr[5] << 8);
	return !(magic == FRAM_LAYOUT_MAGIC && ver == FRAM_LAYOUT_VERSION);
}

static int fram_boot_crc_ok(void)
{
	u8 data[FRAM_BOOT_DATA_END];
	u8 rec[FRAM_RECORD_SIZE];
	u32 stored, calc;
	u16 off;

	if (fram_read(0, data, sizeof(data)))
		return 0;
	calc = crc32_fram(data, sizeof(data));

	off = 6 * FRAM_SLOTS_PER_KEY * FRAM_RECORD_SIZE;
	if (fram_read(off, rec, sizeof(rec)))
		return 0;
	if ((rec[0] | (rec[1] << 8)) != FRAM_REC_MAGIC)
		return 0;
	if (rec[3] != 7 || rec[4] != 3 || rec[5] != 8)
		return 0;
	stored = rec[10] | (rec[11] << 8) | (rec[12] << 16) | (rec[13] << 24);
	return stored == calc;
}

static int decode_and_set(const struct fram_key *key, const u8 *raw)
{
	char val[32];
	u16 magic = raw[0] | (raw[1] << 8);
	u32 seq_a, seq_b;
	u8 slot_b[FRAM_RECORD_SIZE];
	const u8 *best = raw;
	u16 off_b;

	if (magic != FRAM_REC_MAGIC || raw[2] != 1 || raw[3] != key->id)
		return -1;
	if (crc32_fram(raw, 28) !=
	    (u32)(raw[28] | (raw[29] << 8) | (raw[30] << 16) | (raw[31] << 24)))
		return -1;

	off_b = ((key->id - 1) * FRAM_SLOTS_PER_KEY + 1) * FRAM_RECORD_SIZE;
	if (!fram_read(off_b, slot_b, sizeof(slot_b))) {
		u16 mb = slot_b[0] | (slot_b[1] << 8);
		if (mb == FRAM_REC_MAGIC && slot_b[3] == key->id &&
		    crc32_fram(slot_b, 28) ==
			(u32)(slot_b[28] | (slot_b[29] << 8) |
			      (slot_b[30] << 16) | (slot_b[31] << 24))) {
			seq_a = raw[6] | (raw[7] << 8) | (raw[8] << 16) |
				(raw[9] << 24);
			seq_b = slot_b[6] | (slot_b[7] << 8) |
				(slot_b[8] << 16) | (slot_b[9] << 24);
			if (seq_b > seq_a)
				best = slot_b;
		}
	}

	if (best[4] != key->vtype)
		return -1;

	if (key->vtype == 1) {
		if (best[5] != 1)
			return -1;
		strcpy(val, best[10] ? "true" : "false");
	} else if (key->vtype == 2) {
		if (best[5] == 0) {
			setenv(key->name, NULL);
			return 0;
		}
		if (best[5] != 8)
			return -1;
		sprintf(val, "%llu",
			(unsigned long long)best[10] |
			((unsigned long long)best[11] << 8) |
			((unsigned long long)best[12] << 16) |
			((unsigned long long)best[13] << 24) |
			((unsigned long long)best[14] << 32) |
			((unsigned long long)best[15] << 40) |
			((unsigned long long)best[16] << 48) |
			((unsigned long long)best[17] << 56));
	} else if (key->vtype == 3) {
		if (best[5] != 8)
			return -1;
		sprintf(val, "%llu",
			(unsigned long long)best[10] |
			((unsigned long long)best[11] << 8) |
			((unsigned long long)best[12] << 16) |
			((unsigned long long)best[13] << 24) |
			((unsigned long long)best[14] << 32) |
			((unsigned long long)best[15] << 40) |
			((unsigned long long)best[16] << 48) |
			((unsigned long long)best[17] << 56));
	} else {
		return -1;
	}

	setenv(key->name, val);
	return 0;
}

void radsat_fram_overlay_env(void)
{
	unsigned int old_bus = i2c_get_bus_num();
	u8 raw[FRAM_RECORD_SIZE];
	int i;

	if (i2c_set_bus_num(CONFIG_FRAM_I2C_BUS)) {
		puts("FRAM: cannot select I2C2; skipping mission overlay\n");
		return;
	}

	if (fram_layout_present_invalid()) {
		puts("FRAM: layout magic/version mismatch; skipping mission overlay\n");
		goto out;
	}
	if (!fram_boot_crc_ok()) {
		puts("FRAM: boot-region CRC invalid; skipping mission overlay\n");
		goto out;
	}

	for (i = 0; i < ARRAY_SIZE(fram_keys); i++) {
		u16 off = (fram_keys[i].id - 1) * FRAM_SLOTS_PER_KEY *
			  FRAM_RECORD_SIZE;
		if (fram_read(off, raw, sizeof(raw)))
			continue;
		decode_and_set(&fram_keys[i], raw);
	}
	puts("FRAM: mission policy keys overlaid\n");

out:
	i2c_set_bus_num(old_bus);
}
''')


def run(cmd, cwd=None):
    subprocess.check_call(cmd, cwd=cwd)


def apply_patch(tree: Path, patch: Path):
    run(["patch", "-p1", "--forward", "--batch", "-i", str(patch)], cwd=tree)


def udiff(a: Path, b: Path, rel: str) -> str:
    r = subprocess.run(["diff", "-u", str(a), str(b)], capture_output=True, text=True)
    if not r.stdout:
        return ""
    lines = r.stdout.splitlines(True)
    lines[0] = f"--- a/{rel}\n"
    lines[1] = f"+++ b/{rel}\n"
    return f"diff --git a/{rel} b/{rel}\n" + "".join(lines)


def newfile_diff(rel: str, content: str) -> str:
    body = content.splitlines(True)
    if body and not body[-1].endswith("\n"):
        body[-1] += "\n"
    out = [
        f"diff --git a/{rel} b/{rel}\n",
        "new file mode 100644\n",
        "--- /dev/null\n",
        f"+++ b/{rel}\n",
        f"@@ -0,0 +1,{len(body)} @@\n",
    ]
    for ln in body:
        out.append("+" + ln)
    return "".join(out)


def edit_tree(root: Path, stage: str) -> None:
    # Makefile
    mk = root / "common/Makefile"
    t = mk.read_text()
    if "env_mram.o" not in t:
        t = t.replace(
            "obj-$(CONFIG_ENV_IS_IN_EXT4) += env_ext4.o\n",
            "obj-$(CONFIG_ENV_IS_IN_EXT4) += env_ext4.o\n"
            "obj-$(CONFIG_ENV_IS_IN_MRAM) += env_mram.o\n"
            "obj-$(CONFIG_RADSAT_FRAM_POLICY) += fram_mission.o\n",
        )
        mk.write_text(t)

    if stage == "mram":
        (root / "common/env_mram.c").write_text(ENV_MRAM_C.read_text())
    if stage == "fram":
        (root / "common/fram_mission.c").write_text(FRAM_C.read_text())

    hdr = root / "include/configs/beaglebone-black.h"
    t = hdr.read_text()
    if stage == "mram" and "CONFIG_ENV_IS_IN_MRAM" not in t:
        import re

        t2, n = re.subn(
            r"/\* If we're compiling for the SPL[\s\S]*?#endif /\* CONFIG_SPL_BUILD \*/",
            """/* SPL has no SPI MRAM env driver; U-Boot proper owns MRAM/FRAM. */
#ifdef CONFIG_SPL_BUILD
#define CONFIG_ENV_IS_NOWHERE
#else
/*
 * Primary env: SPI MRAM high region (see mram-service env_offset/env_size).
 * EXT4 /uboot.env remains a load fallback inside env_mram.c.
 */
#define CONFIG_ENV_IS_IN_MRAM		1
#define CONFIG_ENV_MRAM_BUS		1
#define CONFIG_ENV_MRAM_CS		0
#define CONFIG_ENV_MRAM_MAX_HZ		10000000
#define CONFIG_ENV_MRAM_MODE		0
#define CONFIG_ENV_MRAM_OFFSET		0x7D800
#define CONFIG_ENV_SIZE			(10 * 1024)
#define CONFIG_EXT4_WRITE
#define EXT4_ENV_INTERFACE		"mmc"
#define EXT4_ENV_DEVICE_AND_PART	"0:3"
#define EXT4_ENV_FILE			"/uboot.env"
#define CONFIG_RADSAT_FRAM_POLICY	1
#define CONFIG_FRAM_I2C_BUS		2
#define CONFIG_FRAM_I2C_ADDR		0x50
#endif /* CONFIG_SPL_BUILD */""",
            t,
            count=1,
        )
        if n != 1:
            raise SystemExit("header env block replace failed")
        hdr.write_text(t2)

    envh = root / "include/environment.h"
    t = envh.read_text()
    if stage == "mram" and "CONFIG_ENV_IS_IN_MRAM" not in t:
        t = t.replace(
            "!defined(CONFIG_ENV_IS_IN_SPI_FLASH)",
            "!defined(CONFIG_ENV_IS_IN_SPI_FLASH) && \\\n"
            "\t!defined(CONFIG_ENV_IS_IN_MRAM)",
        )
        envh.write_text(t)

    mux = root / "board/ti/am335x/mux.c"
    t = mux.read_text()
    if stage == "mram" and "spi1_pin_mux" not in t:
        insert = """
static struct module_pin_mux spi1_pin_mux[] = {
	{OFFSET(mcasp0_aclkx), (MODE(3) | RXACTIVE | PULLUDEN)},	/* SPI1_SCLK */
	{OFFSET(mcasp0_fsx), (MODE(3) | RXACTIVE | PULLUDEN | PULLUP_EN)}, /* SPI1_D0 */
	{OFFSET(mcasp0_axr0), (MODE(3) | RXACTIVE | PULLUDEN)},	/* SPI1_D1 */
	{OFFSET(mcasp0_ahclkr), (MODE(3) | RXACTIVE | PULLUDEN | PULLUP_EN)}, /* SPI1_CS0 */
	{-1},
};

static struct module_pin_mux i2c2_pin_mux[] = {
	{OFFSET(uart1_ctsn), (MODE(3) | RXACTIVE | PULLUDEN | PULLUP_EN)}, /* I2C2_SDA */
	{OFFSET(uart1_rtsn), (MODE(3) | RXACTIVE | PULLUDEN | PULLUP_EN)}, /* I2C2_SCL */
	{-1},
};

"""
        t = t.replace(
            "static struct module_pin_mux spi0_pin_mux[] = {\n",
            insert + "static struct module_pin_mux spi0_pin_mux[] = {\n",
            1,
        )
        t = t.replace(
            "void enable_i2c0_pin_mux(void)\n{\n",
            "void enable_spi1_pin_mux(void)\n"
            "{\n"
            "\tconfigure_module_pin_mux(spi1_pin_mux);\n"
            "}\n\n"
            "void enable_i2c2_pin_mux(void)\n"
            "{\n"
            "\tconfigure_module_pin_mux(i2c2_pin_mux);\n"
            "}\n\n"
            "void enable_i2c0_pin_mux(void)\n{\n",
            1,
        )
        mux.write_text(t)

    bh = root / "board/ti/am335x/board.h"
    t = bh.read_text()
    if stage == "mram" and "enable_spi1_pin_mux" not in t:
        t = t.replace(
            "void enable_i2c0_pin_mux(void);\n",
            "void enable_i2c0_pin_mux(void);\n"
            "void enable_spi1_pin_mux(void);\n"
            "void enable_i2c2_pin_mux(void);\n",
            1,
        )
        bh.write_text(t)

    board = root / "board/ti/am335x/board.c"
    t = board.read_text()
    if stage == "mram" and "enable_spi1_pin_mux();" not in t:
        t = t.replace(
            "\tenable_i2c0_pin_mux();\n"
            "\ti2c_init(CONFIG_SYS_OMAP24_I2C_SPEED, CONFIG_SYS_OMAP24_I2C_SLAVE);\n",
            "\tenable_i2c0_pin_mux();\n"
            "\tenable_i2c2_pin_mux();\n"
            "\tenable_spi1_pin_mux();\n"
            "\ti2c_init(CONFIG_SYS_OMAP24_I2C_SPEED, CONFIG_SYS_OMAP24_I2C_SLAVE);\n",
            1,
        )
        board.write_text(t)
    if stage == "fram" and "radsat_fram_overlay_env" not in t:
        t = "void radsat_fram_overlay_env(void);\n" + t
        t = t.replace(
            "int board_late_init(void)\n{\n",
            "int board_late_init(void)\n{\n"
            "#ifdef CONFIG_RADSAT_FRAM_POLICY\n"
            "\tradsat_fram_overlay_env();\n"
            "#endif\n",
            1,
        )
        board.write_text(t)


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        base = td / "base"
        mram = td / "mram"
        fram = td / "fram"
        base.mkdir()
        run(
            [
                "bash",
                "-lc",
                f"gzip -d -c {BR_DL} | tar --strip-components=1 -C {base} -xf -",
            ]
        )
        for p in PATCHES:
            apply_patch(base, p)

        shutil.copytree(base, mram)
        edit_tree(mram, "mram")

        parts = [
            "From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001\n"
            "From: Radsat Developers <dev@radsat.local>\n"
            "Date: Fri, 30 Oct 2026 18:00:00 -0600\n"
            "Subject: [PATCH] arm: bbb: load/save U-Boot env from SPI MRAM\n"
            "\n"
            "Store the classic env blob in the high 0x2800 bytes of McSPI2 MRAM\n"
            "(Linux spidev1.0). Fall back to EXT4 /uboot.env, then defaults.\n"
            "\n"
            "---\n",
            newfile_diff("common/env_mram.c", (mram / "common/env_mram.c").read_text()),
        ]
        for rel in [
            "common/Makefile",
            "include/configs/beaglebone-black.h",
            "include/environment.h",
            "board/ti/am335x/mux.c",
            "board/ti/am335x/board.h",
            "board/ti/am335x/board.c",
        ]:
            d = udiff(base / rel, mram / rel, rel)
            if d:
                parts.append(d)
        p6 = "".join(parts)
        (OUT / "0006-bbb-env-on-spi-mram.patch").write_text(p6)

        shutil.copytree(mram, fram)
        edit_tree(fram, "fram")
        parts7 = [
            "From 0000000000000000000000000000000000000000 Mon Sep 17 00:00:00 2001\n"
            "From: Radsat Developers <dev@radsat.local>\n"
            "Date: Fri, 30 Oct 2026 18:10:00 -0600\n"
            "Subject: [PATCH] arm: bbb: overlay FRAM mission policy keys after env\n"
            "\n"
            "Read allowlisted mission keys from I2C2 FRAM @ 0x50. Fail-open on bad\n"
            "layout/CRC/I2C. Never set bootcmd.\n"
            "\n"
            "---\n",
            newfile_diff(
                "common/fram_mission.c", (fram / "common/fram_mission.c").read_text()
            ),
            udiff(mram / "board/ti/am335x/board.c", fram / "board/ti/am335x/board.c", "board/ti/am335x/board.c"),
        ]
        p7 = "".join(parts7)
        (OUT / "0007-bbb-fram-mission-policy.patch").write_text(p7)

        # verify apply
        verify = td / "verify"
        shutil.copytree(base, verify)
        apply_patch(verify, OUT / "0006-bbb-env-on-spi-mram.patch")
        apply_patch(verify, OUT / "0007-bbb-fram-mission-policy.patch")
        assert (verify / "common/env_mram.c").exists()
        assert (verify / "common/fram_mission.c").exists()
        print("VERIFY_OK patches apply cleanly")

        if DST2.parent.exists():
            DST2.mkdir(parents=True, exist_ok=True)
            shutil.copy2(OUT / "0006-bbb-env-on-spi-mram.patch", DST2 / "0006-bbb-env-on-spi-mram.patch")
            shutil.copy2(OUT / "0007-bbb-fram-mission-policy.patch", DST2 / "0007-bbb-fram-mission-policy.patch")
        print("wrote", OUT / "0006-bbb-env-on-spi-mram.patch", (OUT / "0006-bbb-env-on-spi-mram.patch").stat().st_size)
        print("wrote", OUT / "0007-bbb-fram-mission-policy.patch", (OUT / "0007-bbb-fram-mission-policy.patch").stat().st_size)


if __name__ == "__main__":
    main()
