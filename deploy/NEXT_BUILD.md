# Notes for next build

**Seen:** 2026-11-09 lab board (`monit summary` from `~/obc-bins`)  
**Related:** monit packaging under `package/kubos/**/*.mk`, shutdown path `common/overlay/etc/init.d/rcK`

---

## `/etc/kubos-config.toml` — where to edit it

There is **no** checked-in full config file. The image file is assembled at build time:

1. Each enabled Kubos package writes a fragment into `$(STAGING_DIR)/etc/kubos/<service-name>` from its `*.mk` (`echo '[service…]' > …`).
2. Finalize hook `KUBOS_CREATE_CONFIG` in [`package/kubos/kubos.mk`](../package/kubos/kubos.mk) concatenates those fragments → `$(TARGET_DIR)/etc/kubos-config.toml` (on the board: `/etc/kubos-config.toml`).

**Edit the fragment for the service you care about**, e.g.:

| Service | Fragment writer | Tunables (menuconfig / `Config.in`) |
|---------|-----------------|--------------------------------------|
| fram | `package/kubos/kubos-fram/kubos-fram.mk` | `package/kubos/kubos-fram/Config.in` |
| mram | `package/kubos/kubos-mram/kubos-mram.mk` | `package/kubos/kubos-mram/Config.in` |
| telemetry | `package/kubos/kubos-core/kubos-core-telemetry-db/kubos-core-telemetry-db.mk` | sibling `Config.in` |
| gnss (oem6 today) | `package/kubos/kubos-novatel-oem6/kubos-novatel-oem6.mk` | sibling `Config.in` |
| comms / snn / … | matching `package/kubos/kubos-<name>/*.mk` | matching `Config.in` |

Defaults you change in `make menuconfig` land in `configs/beaglebone-black_defconfig` as `BR2_KUBOS_*`, then the `.mk` echoes them into the fragment. For keys that are hard-coded in the `.mk` (not a `BR2_` option), edit the `.mk` directly.

After changing fragments: rebuild the affected package(s) so `kubos` re-runs `KUBOS_CREATE_CONFIG` (or wipe staging `etc/kubos` + reinstall kubos packages).

---

## Monit: cnn, analog-ic, gnss, telemetry

These four need a packaged `/etc/monit.d/*.cfg` so `monit summary` includes them like the lab board:

| Need | Monit service name | Notes |
|------|--------------------|-------|
| cnn | `kubos-cnn` | Process check |
| analog-ic | `kubos-analog-ic` | Process check |
| gnss | `kubos-novatel-oem7` | Process check (lab showed `Data access error` — entry still required) |
| telemetry | `kubos-telemetry-db` | Process check |

Target shape (lab `monit summary`):

```text
~/obc-bins/obc-bins # monit summary
Monit 5.34.3 uptime: 3h 40m
┌─────────────────────────────────┬────────────────────────────┬───────────────┐
│ Service Name                    │ Status                     │ Type          │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ radsat                          │ OK                         │ System        │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ scheduler-service               │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-telemetry-db              │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-star-risc                 │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-snn                       │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-shell-service             │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-novatel-oem7              │ Data access error          │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-mram                      │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-monitor                   │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-fram                      │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ file-service                    │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-dosimeter                 │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-cube-adcs                 │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-comms                     │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-cnn                       │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-clyde-3g-eps              │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-app-service               │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ kubos-analog-ic                 │ OK                         │ Process       │
├─────────────────────────────────┼────────────────────────────┼───────────────┤
│ monit                           │ OK                         │ File          │
└─────────────────────────────────┴────────────────────────────┴───────────────┘
```

Packaging note: tree already has monit for `kubos-telemetry-db` and `kubos-novatel-oem6`; next build must cover **oem7**, **cnn**, and **analog-ic** the same way (CHECK PROCESS + START PROGRAM → matching `S??` init script + PIDFILE).

---

## rcK creates `null` files in cwd

`/etc/init.d/rcK` (and historically `rcS`) used `2>null` instead of `2>/dev/null`, which creates a regular file named `null` in whatever the current working directory is (often `/`, `/root`, or wherever the operator was).

Repo overlay is already corrected to `2>/dev/null` in:

- `common/overlay/etc/init.d/rcK`
- `common/overlay/etc/init.d/rcS`

**Next image/flash must ship those fixed scripts.** Until then, on a live board:

```sh
sed -i 's|2>null|2>/dev/null|g' /etc/init.d/rcS /etc/init.d/rcK
rm -f /null ~/null ./null
grep -n 'null' /etc/init.d/rcS /etc/init.d/rcK
```
