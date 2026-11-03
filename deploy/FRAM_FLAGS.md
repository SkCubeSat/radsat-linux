# RadSat FRAM mission flags (layout v2)

All of these **belong in FRAM** (dual-slot, power-cycle durable).  
Put **bulk commissioning logs / dumps in MRAM** (`mram put …`), not FRAM.

U-Boot only overlays boot-policy keys **1–6**. Consent / faults / counters are **FRAM-only** (never `bootcmd`).

## Already present (v1)

| id | name | type | notes |
|----|------|------|-------|
| 1 | `remove_before_flight` | bool | boot |
| 2 | `deployed` | bool | boot |
| 3 | `deploy_start` | timestamp | boot |
| 4 | `initial_safe_state_complete` | bool | boot |
| 5 | `fsoo_timer` | u64 | **30‑minute timer** |
| 6 | `detumbling_complete` | bool | boot |
| 7 | `boot_checksum` | u64 | CRC trailer |
| 8 | `solar_panel_deployed` | bool | one-time |
| 9 | `uhf_antenna_deployed` | bool | one-time |
| 10 | `vhf_antenna_deployed` | bool | one-time |

## Added in v2

### One-time / completion
| id | name | type |
|----|------|------|
| 11 | `adcs_commissioning_logged` | bool | ADCS commissioning log captured (blob → MRAM) |

### Ground consent
| id | name | type | gates |
|----|------|------|-------|
| 12 | `adcs_commissioned` | bool | operator → may detumble |
| 13 | `sun_pointing_consent` | bool | |
| 14 | `nadir_pointing_consent` | bool | |
| 15 | `platform_commissioned` | bool | → payload check allowed |

### Failure trips
| id | name |
|----|------|
| 16 | `gnss_system_error` |
| 17–18 | `gyro0_fail`, `gyro1_fail` |
| 19–20 | `mag0_fail`, `mag1_fail` |
| 21 | `reaction_wheel_fail` |
| 22 | `sun_sensor_fail` |
| 23 | `earth_sensor_fail` |
| 24–25 | `sun_pointing_angle_fault`, `sun_pointing_rate_fault` |
| 26–27 | `nadir_pointing_angle_fault`, `nadir_pointing_rate_fault` |

### Attempt counters (u64)
| id | name |
|----|------|
| 28 | `antenna_deploy_attempts` |
| 29 | `solar_panel_deploy_attempts` |
| 30 | `nadir_point_attempts` |
| 31 | `sun_point_attempts` |

`RESERVED_KEYS=32` → one spare slot.

## CLI

```sh
fram-get
fram-get adcs_commissioned
fram-set adcs_commissioned true
fram-set antenna_deploy_attempts 3
# commissioning log body:
mram put adcs_commissioning.log /tmp/log.txt text/plain
fram-set adcs_commissioning_logged true
```
