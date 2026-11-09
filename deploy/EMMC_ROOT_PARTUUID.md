# eMMC-only boot — error catalog + workarounds

**Status:** manual workaround proven on **2 lab boards** (2026-11-09); autonomous fix not shipped  
**Image:** Software `v0.1.1-rc.5`, U-Boot 2016.09 (`Nov 09 2026 - 10:12:08`), Linux 4.4.23-KubOS  
**Related:** [`BLANK_BOARD.md`](BLANK_BOARD.md), [`FRAM_FLAGS.md`](FRAM_FLAGS.md)

---

## Error catalog (lab 2026-11-09)

| ID | Log / symptom | When | Root cause | Workaround | Code fix later |
|----|---------------|------|------------|------------|----------------|
| **E1** | `Waiting for root device /dev/mmcblk1p2...` | SD removed; eMMC is only disk (`mmcblk0`) | MRAM `bootargs` has `root=/dev/mmcblk1p2`. With SD out, eMMC renumbers to `mmcblk0`; `mmcblk1p2` never appears. | U-Boot: `setenv bootargs … root=PARTUUID=4b4c4e59-02 …` + **`saveenv`** | Always `args_mmc`/`finduuid` before `bootm`; never persist `root=/dev/mmcblk*` |
| **E2** | `fw_setenv bootargs` / delete looks OK; next boot still `mmcblk1p2` | After “clearing” env in Linux | `fw_env.config` → `/envar/uboot.env` only. U-Boot loads **SPI MRAM**. `S79` / `mram-env-sync` are MRAM→file one-way; never push envar→MRAM. | Only `saveenv` at U-Boot (or a future MRAM write tool) | `install-os` / `mram-env-sync` must write MRAM; or make `fw_setenv` hit MRAM; warn if file-only |
| **E3** | `hexdump … 440` → `58 4e 4c 4b` \|XNLK\| on eMMC | Before / without successful stamp | KLNX/XNLK is the **SD** image signature. eMMC must be **YNLK** (`59 4e 4c 4b`) or PARTUUID `4b4c4e59-02` won’t match. | `install-os sd-to-emmc -y` (calls `set_disk_signature_emmc`) | Assert YNLK in verify; fail install if not |
| **E4** | `OS Install: … latch cleared` then `fram-get` → `curl: (7) … 8091` | Right after `sd-to-emmc` | `stop_services` kills fram-service for dd; `fram_clear_recovery_after_verify` uses `fram-set` → GraphQL → **silent fail** (`\|\| true`). Latch stays `true`. | Reboot with SD; `/etc/init.d/S80kubos-fram start` if needed; `fram-set emmc_recovery_needed false` (+ offset 0, `last_emmc_probe_ok true`); **readback** | Clear latch with readback **before** stop, or restart service before clear, or write FRAM without GraphQL |
| **E5** | `FRAM: attempting U-Boot chunked SD->eMMC restore` → `Card did not respond` → `raw restore failed; boot SD` → **reset loop** | SD out + `emmc_recovery_needed=true` | E4 left latch set. U-Boot restore needs SD (`mmc 0`); no card → fail → force SD boot → reset. | Insert SD, clear latch (E4), then fix env (E6/E1) | Same as E4; on restore fail with no SD, boot eMMC if probe OK instead of hard-reset loop |
| **E6** | `Found SD card on mmc 0 (multi-copy image media)` → `** Bad device mmc 0 **` → `resetting ...` (no restore message) | Latch cleared; SD out | `saveenv` during recovery persisted `boot_targets=legacy_mmc0`, `mmcdev=0`, `bootpart=0:2`. Distro boot keeps trying SD. | U-Boot: set `boot_targets=legacy_mmc1`, `mmcdev=1`, `bootpart=1:2`, PARTUUID `bootargs`, `bootcmd=run distro_bootcmd`, **`saveenv`**, `boot` | Recovery must not `saveenv` SD targets; on exit clear them or set eMMC targets when eMMC probe OK |
| **E7** | `fsck.ext2: No such file or directory … /dev/mmcblk1p2` (and p3/p4) | eMMC-only boot (harmless) | `overlay/etc/inittab` hardcodes fsck on `mmcblk1p*` (assumes SD=`mmcblk0`, eMMC=`mmcblk1`) | Ignore, or comment those lines on lab images | Derive devices from cmdline PARTUUID / sysfs type |
| **E8** | `Boot media: unknown (root=/dev/mmcblk1p2)` | Older path / device-node root | `announce-boot-media` weak when root isn’t PARTUUID | Prefer PARTUUID cmdline (E1) | Keep PARTUUID; harden announce script |
| **E9** | `*** Warning - bad CRC, using default environment` / `Env: MRAM CRC/import failed, trying EXT4` | Virgin or corrupted MRAM | Env not seeded yet, or bad write | First successful U-Boot `saveenv` repairs; Linux `mram-env-sync --seed` if needed | S79 already seeds on bad CRC; ensure seed doesn’t leave E1/E6 bad keys |
| **E10** | `sh: can't execute 'saveenv'` | Typed at Linux shell | `saveenv` is **U-Boot only** | Stop autoboot; use U-Boot `saveenv` | N/A (docs) |
| **E11** | FIT `/kernel` loads from eMMC, **no** `Booting Linux from eMMC…`, then uses stale `bootargs` | Default path before env fix | Boot path skipped `mmcloados`/`args_mmc`/`announce_boot` and reused MRAM `bootargs` | Force good `bootargs` in MRAM (E1) or fix targets (E6) so `mmcloados` runs | Make FIT boot always `run args_mmc` before `bootm` |
| **E12** | `fram-get emmc_recovery_needed` → `boolValue: true` after install claimed clear | Post `sd-to-emmc` | Same as E4 | Clear + readback | Same as E4 |
| **E13** | Wrong PARTUUID if stamped for YNLK while disk is XNLK | Operator used `4b4c4e59-02` too early | Signature prefix must match MBR bytes | Wait for E3 YNLK, then PARTUUID | install-os gates PARTUUID/env write on YNLK verify |
| **E14** | `## Error: "distro_bootcmd" not defined` | U-Boot prompt, `run distro_bootcmd` | Active env has no `distro_bootcmd` variable (saved env replaced the default scripts) | Do not `run` it. Load kernel by hand (E16) or fix env with procedure **B** | Seed/save an env that actually defines `distro_bootcmd` before setting `bootcmd` to it |
| **E15** | `## Error: "mmcboot" not defined` | U-Boot prompt, `run mmcboot` | Same env has no `mmcboot` script. `fatls mmc 0:1` still works | Manual `fatload` + `bootm` (E16) | Same as E14 |
| **E16** | `** Unable to read file bea **` | `fatload … bea` | Name was truncated. Boot FAT file is `beaglebone-black.dtb`, not `am335x-boneblack.dtb` | `fatload mmc 0:1 ${fdtaddr} beaglebone-black.dtb` (or `mmc 1:1` for eMMC) | N/A |
| **E17** | `Waiting for root device PARTUUID=4b4c4e59-02...` and `mmc0` never prints `new high speed SDHC card` | SD inserted; kernel cmdline is that PARTUUID | SD host started at 400 kHz and never registered a card. eMMC (`IS008G`) became `mmcblk0`. Ctrl-C does not leave `rootwait` | Reset. If the goal is the SD rootfs, boot `root=/dev/mmcblk0p2` only after the log shows `mmcblk0: … SD32G` | Same class as E1: don’t leave a PARTUUID/device-node that isn’t on a disk that enumerated |
| **E18** | Same PARTUUID wait, but `mmcblk0` is `SD32G` and `mmcblk1` is `IS008G`, both `p1`–`p4` | Both cards up, eMMC not YNLK yet (or U-Boot `part uuid` of the SD was copied into `bootargs`) | Linux PARTUUID is the raw MBR signature. SD is `4b4c4e58-02`. `4b4c4e59-02` exists only after E3’s YNLK stamp | Don’t use `4b4c4e59-02` until `hexdump` shows `59 4e 4c 4b`. SD root for this boot: `root=/dev/mmcblk0p2` | E3/E11/E13 |
| **E19** | `mount: /home: can't find PARTUUID=4b4c4e59-04.` and `/envar` `…-03` | After a successful login (`root=/dev/mmcblkNp2`) | `common/busybox-kubos.config` has `CONFIG_FEATURE_MOUNT_LABEL` **unset**. `mount` cannot resolve `PARTUUID=` in fstab. `fsck` of those partitions already succeeded | `mount -t ext4 /dev/mmcblkNp3 /envar` and `…p4 /home` using the **same** `mmcblkN` as `/` (`awk '$2=="/"'` on `/proc/mounts`) | Mount by root-disk partition, or teach BusyBox PARTUUID; don’t assume fstab PARTUUID works |
| **E20** | `S79mram-env-sync: synced MRAM env -> /envar/uboot.env` while E19 just failed | Same boot as E19 | `/envar` is still the directory on the rootfs. The 10 KiB env file is **not** on p3 | Mount p3 first (E19), then re-run S79 if the mirror must live on the envar filesystem | E19; don’t start S79 until `/envar` is the real mount |
| **E21** | `Cannot initialize conversion from codepage 850 to ANSI_X3.4-1968` then `Using internal CP850 conversion table` | `fsck.fat` on the VFAT boot partition | No iconv CP850 table. fsck finishes (`/dev/mmcblk0p1: … files`) | None | Optional: ship the CP850 conversion, or ignore |
| **E22** | `umount: /home: not mounted.` `/home/kubos` empty; `cd kubos` from `~` → `No such file or directory` | Shell after E19 | `/home` was never mounted, so there is nothing to umount. `kubos`, `microsd`, `system` are rootfs directories. `~` is not `/home` | `ls /home/system` for the rootfs tree. `cd /home/kubos` only after E19’s real `/home` is mounted | E19 |

### Not failures (normal on this 4.4.23 BBB boot)

| Log line | Why it is harmless |
|----------|--------------------|
| `omap_hwmod: tptc*: using broken dt data from edma` | Stock AM335x warning for the EDMA channels |
| `omap_hwmod: debugss: _wait_target_disable failed` | Debug subsystem has nothing to clock-gate |
| `omap_i2c … could not find pctldev … deferring probe` | I2C probes before pinctrl; the buses come back (`bus N rev0.11`) |
| `cpufreq … unlisted freq: 1000000 KHz` then `720000` | OPP table has no 1 GHz entry |
| `rtc-rv3028 … setting system clock to 2000-01-03` | RTC has not been set |
| `mmc1: MAN_BKOPS_EN bit is not set` | This eMMC does not advertise background ops |
| `omap_voltage_late_init: Voltage driver support not added` | No voltage driver in the image |

SPL `Trying to boot from MMC2` plus U-Boot `reading /kernel` from `mmc1` means the eMMC bootloader and kernel already loaded. A hang after `Starting kernel` is the root device (E1, E17, E18), not a dead eMMC.

### Signature cheat sheet

| On-disk `@440` | ASCII | u32 LE name | PARTUUID prefix | Role |
|----------------|-------|-------------|-----------------|------|
| `58 4e 4c 4b` | XNLK | KLNX `0x4b4c4e58` | `4b4c4e58` | SD primary image |
| `59 4e 4c 4b` | YNLK | YNLK `0x4b4c4e59` | `4b4c4e59` | eMMC after `sd-to-emmc` |

Rootfs partition is always `-02` → eMMC root = **`PARTUUID=4b4c4e59-02`**.

### Storage authority (do not confuse)

| Actor | Reads/writes |
|-------|----------------|
| U-Boot | SPI MRAM (`Env: loaded from SPI MRAM` / `saveenv`) |
| Linux `fw_printenv` / `fw_setenv` | `/envar/uboot.env` **only** (`/etc/fw_env.config`) |
| `S79mram-env-sync` | MRAM → `/envar/uboot.env` |
| `mram-env-sync` | Explicitly **never** copies envar file into MRAM |

---

## Known-good manual recovery (per board)

### A. After `install-os sd-to-emmc` (SD still in)

```sh
hexdump -C -s 440 -n 4 /dev/mmcblk1    # must be 59 4e 4c 4b
fram-get emmc_recovery_needed           # must be false; if true:
# /etc/init.d/S80kubos-fram start
fram-set emmc_recovery_needed false
fram-set emmc_restore_offset 0
fram-set last_emmc_probe_ok true
fram-get emmc_recovery_needed
```

### B. eMMC-only env (SD out, U-Boot prompt)

```text
printenv boot_targets mmcdev bootpart bootargs bootcmd
setenv boot_targets legacy_mmc1
setenv mmcdev 1
setenv bootpart 1:2
setenv bootargs console=ttyS0,115200 root=PARTUUID=4b4c4e59-02 ro rootfstype=ext4 rootwait
setenv bootcmd run distro_bootcmd
saveenv
boot
```

### C. Pass criteria

```text
Found eMMC on mmc 1
Booting Linux from eMMC (mmc 1:2)
Kernel command line: ... root=PARTUUID=4b4c4e59-02 ...
Boot media: eMMC partition 2 (mmcblk0p2)
Boot root PARTUUID=4b4c4e59-02
```

Then `reboot` once more SD-out with **no** keypress.

**Lab:** Board 1 (E1/E2 only) and Board 2 (E3→E4→E5→E6 then A+B) both passed C.

---

## Nth-board checklist

| Step | Action | Pass |
|------|--------|------|
| 1 | SD boot blank/lab image | login; FRAM layout 7 |
| 2 | `install-os sd-to-emmc -y` | Done + YNLK on eMMC |
| 3 | `fram-get emmc_recovery_needed` | `false` (fix E4 if true) |
| 4 | Power off, remove SD, stop U-Boot | prompt |
| 5 | Apply **B** (targets + PARTUUID + `saveenv`) | eMMC announce + PARTUUID cmdline |
| 6 | Unattended reboot SD-out | login; no E1/E5/E6 |

---

## Autonomous patch plan (all boards)

1. **`install-os`**
   - Assert YNLK after copy (fail = E3).
   - Clear FRAM latch with **readback** while fram-service is up (fix E4/E5/E12).
   - Write scrubbed boot env to **SPI MRAM**: eMMC `boot_targets`/`mmcdev`/`bootpart` + PARTUUID `bootargs` (fix E1/E2/E6) — not `fw_setenv`.
2. **U-Boot**
   - Always `run args_mmc` (PARTUUID via `finduuid`) before FIT `bootm` (fix E11).
   - Reject/clear saved `root=/dev/mmcblk*` (fix E1).
   - Recovery failure: do not leave persisted `legacy_mmc0` if eMMC probe OK; don’t reset-loop with no SD (fix E5/E6).
3. **Linux**
   - `inittab` fsck by PARTUUID/sysfs (fix E7).
   - `fw_setenv` → MRAM or hard warning (fix E2/E10).

### Acceptance

Fresh board: SD → `sd-to-emmc -y` → pull SD → reboot → login, zero U-Boot interaction, cmdline PARTUUID only.

---

## Do not ship without retest

`common/patches/uboot/0021-bbb-root-by-mmc-host.patch` (dated same lab day) forces `root=/dev/mmcblk${mmcdev}p2` and claims PARTUUID is broken on 4.4. **Lab board 1 and 2 booted eMMC-only successfully with `PARTUUID=4b4c4e59-02`.** Treat 0021 as conflicting with this catalog until revalidated; prefer PARTUUID + fixed `mmcdev`/`boot_targets`.
