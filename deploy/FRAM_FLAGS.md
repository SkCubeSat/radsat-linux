# RadSat FRAM mission flags (layout v5)

All of these **belong in FRAM** (dual-slot, power-cycle durable).  
Put **bulk commissioning logs / dumps in MRAM** (`mram put …`), not FRAM.

U-Boot overlays boot-policy keys **1–6** into env.  
U-Boot **reads/writes** recovery keys **8–14** and **40** (never as `bootcmd`).  
Consent / faults / counters / AES are **FRAM-only** (never `bootcmd`).

Layout v4 **repacks** key IDs vs v2/v3 (recovery sits after boot policy).  
Layout v5 adds `emmc_restore_offset` (id 40) for resumable SD→eMMC restore.  
Prior chips are not binary-compatible — blank/reconcile or wipe + re-init.

`RESERVED_KEYS=41`. `LAYOUT_VERSION=5`.

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

## Recovery + ground-visible boot state (ids 8–14, 40)

| id | name | type | notes |
|----|------|------|-------|
| 8 | `total_boot_fails` | u64 | lifetime; increment on eMMC probe/boot failure; **never clear** on healthy boot |
| 9 | `emmc_recovery_needed` | bool | latch: force SD boot / restore until verified |
| 10 | `emmc_recovery_attempts` | u64 | restore attempt counter (bumped only when offset==0) |
| 11 | `sd_restore_slot` | u64 | which SD image slot to restore from |
| 12 | `last_emmc_probe_ok` | bool | last U-Boot eMMC FAT/kernel probe |
| 13 | `boot_media` | u64 | 0=eMMC, 1=SD primary, 2+=SD backup slot |
| 14 | `boot_image_id` | u64 | compact image identity (stamped when usable) |
| 40 | `emmc_restore_offset` | u64 | SD→eMMC copy resume sector; **0** = start/cleared |

## Mission / consent / faults / counters / AES (ids 15–39)

| id | name | type |
|----|------|------|
| 15 | `solar_panel_deployed` | bool |
| 16 | `uhf_antenna_deployed` | bool |
| 17 | `vhf_antenna_deployed` | bool |
| 18 | `adcs_commissioning_logged` | bool |
| 19 | `adcs_commissioned` | bool |
| 20 | `sun_pointing_consent` | bool |
| 21 | `nadir_pointing_consent` | bool |
| 22 | `platform_commissioned` | bool |
| 23 | `gnss_system_error` | bool |
| 24–25 | `gyro0_fail`, `gyro1_fail` | bool |
| 26–27 | `mag0_fail`, `mag1_fail` | bool |
| 28 | `reaction_wheel_fail` | bool |
| 29 | `sun_sensor_fail` | bool |
| 30 | `earth_sensor_fail` | bool |
| 31–32 | `sun_pointing_angle_fault`, `sun_pointing_rate_fault` | bool |
| 33–34 | `nadir_pointing_angle_fault`, `nadir_pointing_rate_fault` | bool |
| 35 | `antenna_deploy_attempts` | u64 |
| 36 | `solar_panel_deploy_attempts` | u64 |
| 37 | `nadir_point_attempts` | u64 |
| 38 | `sun_point_attempts` | u64 |
| 39 | `comms_uplink_aes128_key` | bytes | write-once AES-128; never U-Boot-mirrored |

## CLI

```sh
fram-get
fram-get total_boot_fails
fram-get boot_media
fram-get emmc_restore_offset
fram-set emmc_recovery_needed true
fram-set emmc_restore_offset 0
fram-set adcs_commissioned true
# commissioning log body:
mram put adcs_commissioning.log /tmp/log.txt text/plain
fram-set adcs_commissioning_logged true
```
