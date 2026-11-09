# Flight SD image (slim)

Lab/dev still builds the big `kubos-linux.img` (~3.5 G+ with `/home` + aux-sd).  
Flight builds **`kubos-linux-flight.img`** (~310 M packed) for industrial / SLC cards.

## Layout

| Part | Contents | Size |
|------|----------|------|
| p1 | VFAT boot (`MLO`, dual U-Boot, kernel, dtb) | 16 M |
| p2 | rootfs | 256 M |
| p3 | `/envar` (`uboot.env`) — U-Boot `mmcX:3` | 2 M |
| p4 | `/upgrade` (empty placeholder) — U-Boot `KUBOS_UPGRADE_PART=4` | 32 M |

No 3 G `/home`, no aux-sd, no kpack ITBs on the flight card.  
`/home/system/...` stays **inside rootfs**. Apply kpacks from ground / lab aux-sd when needed.

## Build

```sh
# lab + flight
bash tools/sync-and-build-image.sh

# lab only
BUILD_FLIGHT_IMAGE=0 bash tools/sync-and-build-image.sh
```

Artifacts:

- `kubos-linux-flight.img.gz`
- `kubos-linux-flight.tar.gz`

Also copied to `C:\Users\logan\CubeSAT\kubos-linux-flight.img.gz` by the sync script.

## Flash

```sh
gzip -dc kubos-linux-flight.img.gz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
```

## Card (true SLC, DigiKey in stock)

| Priority | DigiKey | MFR | Notes |
|----------|---------|-----|-------|
| **1** | [`1282-AF8GUDI-WACXM-ND`](https://www.digikey.com/en/products/detail/atp-electronics-inc/AF8GUDI-WACXM/4271271) | ATP `AF8GUDI-WACXM` | **8 GB SLC**, −40…+85 °C |
| **2** | `1282-AF4GUDI-WACXM-ND` | ATP `AF4GUDI-WACXM` | **4 GB SLC**, cheaper, still fits ~310 M |
| **3** | `3247-S304TLNJM-U1000-3-ND` | Delkin `S304TLNJM-U1000-3` | **4 GB SLC** alt |

Buy **×3** of the same PN.

## Next shrink levers

1. Measure real rootfs: `du -sh output/target` — may drop p2 from 256 M → 128 M.
2. Drop heavy packages (`PYTHON_NUMPY`, unused Python) if flight software allows.
3. Longer-term: squashfs root + tmpfs overlay (read-only golden image).
