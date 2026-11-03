/*
 * SPI MRAM environment storage for RadSat (MR2xH40 protocol).
 *
 * Boot path is fail-open: SPI MRAM load/save is skipped until the McSPI
 * transfer path is hardened (full-size xfers can wedge with no timeout).
 * Relocate uses EXT4 /uboot.env then compiled-in defaults.
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

/* Set to 1 only after SPI xfer is proven not to hang on this board. */
#ifndef CONFIG_ENV_MRAM_SPI_ENABLE
# define CONFIG_ENV_MRAM_SPI_ENABLE	0
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

#if CONFIG_ENV_MRAM_SPI_ENABLE
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
#endif /* CONFIG_ENV_MRAM_SPI_ENABLE */

static int env_import_ext4_one(const char *dev_part)
{
	ALLOC_CACHE_ALIGN_BUFFER(char, buf, CONFIG_ENV_SIZE);
	struct blk_desc *dev_desc = NULL;
	disk_partition_t info;
	int part, err;
	loff_t off;

	part = blk_get_device_part_str(EXT4_ENV_INTERFACE, (char *)dev_part,
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

static int env_import_ext4_fallback(void)
{
	/* SD boot uses mmc0; eMMC-only boot uses mmc1. Try both. */
	static const char *const parts[] = {
		EXT4_ENV_DEVICE_AND_PART,
		"0:3",
		"1:3",
		NULL
	};
	int i, ret;

	for (i = 0; parts[i]; i++) {
		ret = env_import_ext4_one(parts[i]);
		if (!ret)
			return 0;
	}
	return -ENODEV;
}

#ifdef CONFIG_CMD_SAVEENV
int saveenv(void)
{
#if CONFIG_ENV_MRAM_SPI_ENABLE
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
#else
	puts("MRAM: saveenv skipped (SPI disabled; use Linux fw_setenv)\n");
	return 1;
#endif
}
#endif

void env_relocate_spec(void)
{
#if CONFIG_ENV_MRAM_SPI_ENABLE
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
#else
	puts("Env: SPI MRAM load disabled (fail-open), trying EXT4\n");
#endif

	if (!env_import_ext4_fallback()) {
		puts("Env: loaded from EXT4 fallback\n");
		return;
	}

	puts("Env: using compiled-in defaults\n");
	set_default_env(NULL);
}
