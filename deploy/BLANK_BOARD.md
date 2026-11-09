# Blank FRAM / MRAM board bring-up

## Why old images “wouldn’t boot”

On a never-commissioned board:

1. **Empty eMMC** makes U-Boot’s FRAM recovery path latch `emmc_recovery_needed`.
2. U-Boot then tried a **~768 MB chunked SD→eMMC restore** before falling back to SD.
3. That looks like a hang / no boot, especially with blank FRAM + blank MRAM.

## What this image does automatically

| Layer | Behavior |
|-------|----------|
| **U-Boot 0019** | Virgin FRAM (blank layout header) → **no recovery latch / no raw restore**. Distro boot continues (SD works). |
| **S79 mram-env-sync** | If MRAM env CRC is bad/missing → auto `--seed` with `bootcmd=run distro_bootcmd`. |
| **fram-service** | `reconcile_on_start=true` → one-shot init of empty boot-policy keys (layout **v7**). Seeds `boot_count=0`, then **`boot_count += 1`** on every start (A/B+CRC). |
| **S92 stamp** | After Linux is up, stamps `boot_media` / `boot_image_id`. Only runs `install-os auto-recover` if the recovery latch was **explicitly** set. |

## Flash a blank board

1. Build lab image (not flight):
   ```sh
   # WSL
   export FORCE_UBOOT=1 FORCE_KUBOS=1
   bash tools/sync-and-build-image.sh
   ```
2. Write **`kubos-linux.img`** (decompress `kubos-linux.img.gz`) to an **SD card as a raw disk image**:
   - **Rufus**: select the `.img`, mode **DD** (not ISO).
   - Or WSL: `gzip -dc kubos-linux.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync`
   - Do **not** just copy files onto a FAT-formatted card.
3. Insert SD and power on. SPL tries **eMMC first**, then **falls back to SD** (blank eMMC is OK).
   Expect U-Boot log like `Trying to boot from MMC2` then a successful SD load, then:
   - `FRAM: blank chip - layout header initialized`
   - `FRAM: virgin board; skipping recovery latch/restore`
4. After Linux:
   ```sh
   curl -s http://127.0.0.1:8091/ -H 'Content-Type: application/json' \
     -d '{"query":"{ memoryMap { layoutVersion } missionState { emmcRecoveryNeeded bootMedia bootCount } }"}'
   # expect layoutVersion 7; bootCount increments each reboot
   fram-get boot_count
   verify-mram-fram-boot
   ```

## Software source

- Tag / branch: **`v0.1.1-rc.5`** (`BR2_KUBOS_VERSION`)
- Local override: `KUBOS_OVERRIDE_SRCDIR=/mnt/c/Users/logan/CubeSAT/Software`
- FRAM layout **v7** (`RESERVED_KEYS=42`, regrouped recovery ids, `boot_count` id 9) is applied in that tree for this build.

## After first boot: transfer to eMMC

Still booted from SD (blank/lab board):

```sh
install-os status
install-os sd-to-emmc -y
# wait for copy + verify; latch clears on success
reboot
# expect boot_media=0 (eMMC); boot_count continues incrementing
```

**Before pulling the SD** — full error catalog + recovery: **[`EMMC_ROOT_PARTUUID.md`](EMMC_ROOT_PARTUUID.md)** (E1–E13). Until autonomous patch lands, every board needs U-Boot **`saveenv`** (not Linux `fw_setenv`).

```sh
hexdump -C -s 440 -n 4 /dev/mmcblk1   # SD in: eMMC → 59 4e 4c 4b (YNLK)
fram-get emmc_recovery_needed          # must be false
```

Then power off, remove SD, stop U-Boot:

```text
setenv boot_targets legacy_mmc1
setenv mmcdev 1
setenv bootpart 1:2
setenv bootargs console=ttyS0,115200 root=PARTUUID=4b4c4e59-02 ro rootfstype=ext4 rootwait
setenv bootcmd run distro_bootcmd
saveenv
reset
```

## Manual recovery (if an old latch is stuck)

```sh
fram-set emmc_recovery_needed false
fram-set emmc_restore_offset 0
# optional full wipe + re-init via fram-service reconcile
```

Do **not** flash a new U-Boot while `fw_printenv bootcmd` shows `bootp`/`nfs`.
