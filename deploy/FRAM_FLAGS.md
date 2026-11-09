# RadSat FRAM mission flags (layout v7)

eMMC-only and lab-serial errors E1–E22 (PARTUUID, MRAM vs `fw_setenv`, recovery latch, `legacy_mmc0`, missing `distro_bootcmd`/`mmcboot`, fstab `PARTUUID` mounts):  
[`EMMC_ROOT_PARTUUID.md`](EMMC_ROOT_PARTUUID.md). Blank-board bring-up: [`BLANK_BOARD.md`](BLANK_BOARD.md).

All mission flags are **dual-slot (A/B)** with a **per-record CRC32**.  
Writes mirror B then A with readback; reads pick any CRC-valid copy and  
auto-repair the other. Put **bulk commissioning logs / dumps in MRAM**  
(`mram put …`), not FRAM.

U-Boot overlays boot-policy keys **1–6** into env (only if boot-region CRC  
`boot_checksum` matches).  
U-Boot **reads/writes** recovery keys **8–16** (never as `bootcmd`).  
Consent / faults / counters / AES are **FRAM-only** (never `bootcmd`).

Layout v7 **regroups** recovery keys so related fields are contiguous  
(`boot_count` next to `total_boot_fails`, `emmc_restore_offset` with the  
other eMMC restore state). Prior chips are not binary-compatible —  
blank/reconcile or wipe + re-init.

`RESERVED_KEYS=42`. `LAYOUT_VERSION=7`.

`boot_count` is seeded to **0** on virgin reconcile / `initializeFlightState`,  
then **+1** on every `fram-service` start (baked into Software, not an init script).

## Boot policy (ids 1–7)

| id | name | type | notes |
|----|------|------|-------|
| 1 | `remove_before_flight` | bool | boot / U-Boot overlay |
| 2 | `deployed` | bool | boot |
| 3 | `deploy_start` | timestamp | boot |
| 4 | `initial_safe_state_complete` | bool | boot |
| 5 | `fsoo_timer` | u64 | **30‑minute timer** |
| 6 | `detumbling_complete` | bool | boot |
| 7 | `boot_checksum` | u64 | CRC trailer over keys 1–6 raw dual-slots |

## Boot health / recovery (ids 8–16)

| id | name | type | notes |
|----|------|------|-------|
| 8 | `total_boot_fails` | u64 | lifetime; increment on eMMC probe/boot failure; **never clear** on healthy boot |
| 9 | `boot_count` | u64 | lifetime successful Linux boots; **+1** each `fram-service` start; seed **0** on new image |
| 10 | `emmc_recovery_needed` | bool | latch: force SD boot / restore until verified |
| 11 | `emmc_recovery_attempts` | u64 | restore attempt counter (bumped only when offset==0) |
| 12 | `emmc_restore_offset` | u64 | SD→eMMC copy resume sector; **0** = start/cleared |
| 13 | `sd_restore_slot` | u64 | which SD image slot to restore from |
| 14 | `last_emmc_probe_ok` | bool | last U-Boot eMMC FAT/kernel probe |
| 15 | `boot_media` | u64 | 0=eMMC, 1=SD primary, 2+=SD backup slot |
| 16 | `boot_image_id` | u64 | compact image identity (stamped when usable) |

## One-time deploy / completion (ids 17–20)

| id | name | type |
|----|------|------|
| 17 | `solar_panel_deployed` | bool |
| 18 | `uhf_antenna_deployed` | bool |
| 19 | `vhf_antenna_deployed` | bool |
| 20 | `adcs_commissioning_logged` | bool |

## Ground consent (ids 21–24)

| id | name | type |
|----|------|------|
| 21 | `adcs_commissioned` | bool |
| 22 | `sun_pointing_consent` | bool |
| 23 | `nadir_pointing_consent` | bool |
| 24 | `platform_commissioned` | bool |

## Failure trip flags (ids 25–36)

| id | name | type |
|----|------|------|
| 25 | `gnss_system_error` | bool |
| 26–27 | `gyro0_fail`, `gyro1_fail` | bool |
| 28–29 | `mag0_fail`, `mag1_fail` | bool |
| 30 | `reaction_wheel_fail` | bool |
| 31 | `sun_sensor_fail` | bool |
| 32 | `earth_sensor_fail` | bool |
| 33–34 | `sun_pointing_angle_fault`, `sun_pointing_rate_fault` | bool |
| 35–36 | `nadir_pointing_angle_fault`, `nadir_pointing_rate_fault` | bool |

## Attempt counters (ids 37–40)

| id | name | type |
|----|------|------|
| 37 | `antenna_deploy_attempts` | u64 |
| 38 | `solar_panel_deploy_attempts` | u64 |
| 39 | `nadir_point_attempts` | u64 |
| 40 | `sun_point_attempts` | u64 |

## Crypto (id 41)

| id | name | type | notes |
|----|------|------|-------|
| 41 | `comms_uplink_aes128_key` | bytes | write-once AES-128; never U-Boot-mirrored |

## CLI

```sh
fram-get
fram-get total_boot_fails
fram-get boot_count
fram-get boot_media
fram-get emmc_restore_offset
fram-set emmc_recovery_needed true
fram-set emmc_restore_offset 0
fram-set adcs_commissioned true
# commissioning log body:
mram put adcs_commissioning.log /tmp/log.txt text/plain
fram-set adcs_commissioning_logged true
```
