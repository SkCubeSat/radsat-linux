#!/usr/bin/env python3
"""Continue FRAM/MRAM/Linux changes for the MRAM env + FRAM mission plan."""
from __future__ import annotations

from pathlib import Path

SOFT = Path("/mnt/c/Users/logan/CubeSAT/Software")
RAD = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux")
FRAM = SOFT / "services/hardware-services/fram-service"
MRAM = SOFT / "services/hardware-services/mram-service"
BBB = RAD / "board/kubos/beaglebone-black"


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing block: {label}\n--- looking for ---\n{old[:200]}")
    return text.replace(old, new, 1)


def patch_fram_subsystem() -> None:
    path = FRAM / "src/subsystem.rs"
    text = path.read_text()
    text = must_replace(
        text,
        "        let fram = FramStorage::mount(storage).map_err(|err| err.to_string())?;\n",
        "        let mut fram = FramStorage::mount(storage).map_err(|err| err.to_string())?;\n"
        "        // Layout magic is advisory; never brick boot if FRAM is blank/corrupt.\n"
        "        if let Err(err) = fram.ensure_layout_header() {\n"
        '            eprintln!("fram-service: layout header write skipped: {err}");\n'
        "        }\n",
        "ensure layout header on mount",
    )
    path.write_text(text)
    print("patched", path)


def patch_fram_env() -> None:
    path = FRAM / "src/env.rs"
    text = path.read_text()
    if "is_forbidden_boot_env_name" in text:
        print("env already guarded")
        return
    text = must_replace(
        text,
        "use std::collections::HashMap;\nuse std::process::Command;\n",
        "use std::collections::HashMap;\nuse std::process::Command;\n\n"
        "use crate::model::MissionKey;\n",
        "env import",
    )
    text = must_replace(
        text,
        "    fn write(&mut self, name: &str, value: Option<&str>) -> Result<(), String> {\n"
        "        let mut command = Command::new(&self.setenv_path);\n",
        "    fn write(&mut self, name: &str, value: Option<&str>) -> Result<(), String> {\n"
        "        if MissionKey::is_forbidden_boot_env_name(name) {\n"
        "            return Err(format!(\n"
        '                "refusing to mirror forbidden boot env name `{name}` from FRAM"\n'
        "            ));\n"
        "        }\n"
        "        let mut command = Command::new(&self.setenv_path);\n",
        "command env write guard",
    )
    text = must_replace(
        text,
        "    fn write(&mut self, name: &str, value: Option<&str>) -> Result<(), String> {\n"
        "        match value {\n",
        "    fn write(&mut self, name: &str, value: Option<&str>) -> Result<(), String> {\n"
        "        if MissionKey::is_forbidden_boot_env_name(name) {\n"
        "            return Err(format!(\n"
        '                "refusing to mirror forbidden boot env name `{name}` from FRAM"\n'
        "            ));\n"
        "        }\n"
        "        match value {\n",
        "memory env write guard",
    )
    path.write_text(text)
    print("patched", path)


def patch_fram_readme() -> None:
    path = FRAM / "README.md"
    text = path.read_text()
    # Update boot flow section
    old = "The intended boot flow is:\n\n1. Set system time from the RTC.\n2. `fram-service` auto-runs a **one-shot** reconcile on start when the FRAM boot\n   policy region is empty (first boot / blank chip). Seed values come from the\n   U-Boot env on the boot media (`fw_printenv`). Once any boot-policy record\n   exists, later service restarts skip this; use `reconcileMissionState` only\n   when you want an explicit sync. Disable with `reconcile_on_start = false`.\n3. Read `missionState`.\n4. Run deployment logic from the reconciled state.\n5. Set completion flags through `setMissionFlag` or `setFlag`.\n"
    new = """The intended boot flow is:

1. U-Boot loads the classic env blob from **SPI MRAM** (with EXT4 `/envar` fallback).
2. U-Boot overlays **mission/boot-policy keys only** from I2C2 FRAM (`0x50`) when
   the layout magic and boot-region CRC are valid. FRAM never supplies `bootcmd`,
   `bootargs`, DFU alts, or root/PARTUUID. Bad CRC / I2C failure is fail-open.
3. Linux `S79mram-env-sync` mirrors a CRC-valid MRAM env blob to `/envar/uboot.env`
   so `fw_printenv` / `fw_setenv` keep working.
4. Set system time from the RTC.
5. `fram-service` auto-runs a **one-shot** reconcile on start when the FRAM boot
   policy region is empty (first boot / blank chip). Seed values come from the
   U-Boot env mirror (`fw_printenv`). Mutations default to `mirrorToEnv: false`
   once MRAM owns classic env; pass `mirrorToEnv: true` only for allowlisted
   mission key names. Disable startup reconcile with `reconcile_on_start = false`.
6. Read `missionState` / run deployment logic / set completion flags via GraphQL.

### Writing FRAM variables (do not use raw `i2cset`)

```sh
# helpers (serial-friendly)
fram-get
fram-get fsoo_timer
fram-set fsoo_timer 42
fram-set deployed true

# or GraphQL directly on port 8091
curl -s http://127.0.0.1:8091/ -H 'Content-Type: application/json' \\
  -d '{"query":"{ missionState { removeBeforeFlight deployed fsooTimer } }"}'

curl -s http://127.0.0.1:8091/ -H 'Content-Type: application/json' \\
  -d '{"query":"mutation { setFlag(name:\\"fsoo_timer\\", intValue:42, mirrorToEnv:false) { success errors } }"}'
```

A fixed **layout magic/version** header lives at offset `0x0800` (`LAYOUT_MAGIC` /
`LAYOUT_VERSION`) so a wrong image is not mistaken for valid policy.
"""
    if old in text:
        text = text.replace(old, new, 1)
    else:
        # insert after first paragraph block if exact text drifted
        marker = "### Per-flag GraphQL\n"
        if marker in text and "Writing FRAM variables" not in text:
            text = text.replace(marker, new.split("### Writing")[0] + "### Writing" + new.split("### Writing", 1)[1].split("### Per-flag")[0] + marker, 1)
        print("WARN: boot flow text drifted; attempted alternate insert")
    # Fix MVP table wording
    text = text.replace(
        "Boot-critical U-Boot/mission variables sit at the top of FRAM so early boot\nonly needs the first 384 bytes.",
        "Mission / boot-**policy** keys sit at the top of FRAM so U-Boot only overlays\nallowlisted names (never classic bootcmd). First 384 bytes + checksum trailer.",
    )
    path.write_text(text)
    print("patched", path)


def write_fram_helpers() -> None:
    out = BBB / "overlay/usr/sbin"
    out.mkdir(parents=True, exist_ok=True)
    (out / "fram-get").write_text(
        """#!/bin/sh
# Query fram-service GraphQL (port 8091). Usage: fram-get [name]
set -eu
URL="${FRAM_URL:-http://127.0.0.1:8091/}"
NAME="${1:-}"
if [ -z "$NAME" ]; then
  curl -s "$URL" -H 'Content-Type: application/json' \\
    -d '{"query":"{ missionState { removeBeforeFlight deployed deployStart initialSafeStateComplete fsooTimer detumblingComplete solarPanelDeployed uhfAntennaDeployed vhfAntennaDeployed bootChecksum } memoryMap { layoutMagic layoutVersion } }"}'
  echo
  exit 0
fi
curl -s "$URL" -H 'Content-Type: application/json' \\
  -d "{\"query\":\"{ flag(name: \\\"${NAME}\\\") { name keyId valueType present boolValue intValue } }\"}"
echo
"""
    )
    (out / "fram-set").write_text(
        """#!/bin/sh
# Set one FRAM flag via fram-service. Usage: fram-set <name> <value> [mirror]
# mirror defaults to false (MRAM owns classic U-Boot env).
set -eu
URL="${FRAM_URL:-http://127.0.0.1:8091/}"
NAME="${1:?usage: fram-set <name> <value> [mirrorToEnv]}"
VALUE="${2:?usage: fram-set <name> <value> [mirrorToEnv]}"
MIRROR="${3:-false}"
case "$VALUE" in
  true|TRUE|True|false|FALSE|False)
    BODY="{\\\"query\\\":\\\"mutation { setFlag(name:\\\\\\\"${NAME}\\\\\\\", boolValue:${VALUE}, mirrorToEnv:${MIRROR}) { success errors flag { present boolValue intValue } } }\\\"}"
    ;;
  *)
    BODY="{\\\"query\\\":\\\"mutation { setFlag(name:\\\\\\\"${NAME}\\\\\\\", intValue:${VALUE}, mirrorToEnv:${MIRROR}) { success errors flag { present boolValue intValue } } }\\\"}"
    ;;
esac
curl -s "$URL" -H 'Content-Type: application/json' -d "$BODY"
echo
"""
    )
    print("wrote fram-get/fram-set")


def patch_mram_backend_window() -> None:
    path = MRAM / "src/backend.rs"
    text = path.read_text()
    if "struct PayloadWindow" in text or "PayloadWindowBackend" in text:
        print("backend already has window")
        return
    # Append window backend before end of file
    text += """
/// Restricts littlefs/payload access to `[0, payload_capacity)` so the high
/// MRAM region reserved for the U-Boot env blob cannot be overwritten.
pub struct PayloadWindowBackend {
    inner: Box<dyn ByteStorage>,
    payload_capacity: u32,
}

impl PayloadWindowBackend {
    pub fn new(inner: Box<dyn ByteStorage>, payload_capacity: u32) -> Result<Self, BackendError> {
        if payload_capacity == 0 || payload_capacity > inner.capacity() {
            return Err(BackendError::InvalidConfig(format!(
                "payload_capacity {payload_capacity} invalid for device capacity {}",
                inner.capacity()
            )));
        }
        Ok(Self {
            inner,
            payload_capacity,
        })
    }

    pub fn into_inner(self) -> Box<dyn ByteStorage> {
        self.inner
    }

    pub fn inner_mut(&mut self) -> &mut dyn ByteStorage {
        self.inner.as_mut()
    }
}

impl ByteStorage for PayloadWindowBackend {
    fn capacity(&self) -> u32 {
        self.payload_capacity
    }

    fn read(&mut self, offset: u32, out: &mut [u8]) -> Result<(), BackendError> {
        let len_u32 = u32::try_from(out.len()).map_err(|_| BackendError::OutOfBounds {
            offset,
            len: out.len(),
            capacity: self.payload_capacity,
        })?;
        let end = offset
            .checked_add(len_u32)
            .ok_or(BackendError::OutOfBounds {
                offset,
                len: out.len(),
                capacity: self.payload_capacity,
            })?;
        if end > self.payload_capacity {
            return Err(BackendError::OutOfBounds {
                offset,
                len: out.len(),
                capacity: self.payload_capacity,
            });
        }
        self.inner.read(offset, out)
    }

    fn write(&mut self, offset: u32, data: &[u8]) -> Result<(), BackendError> {
        let len_u32 = u32::try_from(data.len()).map_err(|_| BackendError::OutOfBounds {
            offset,
            len: data.len(),
            capacity: self.payload_capacity,
        })?;
        let end = offset
            .checked_add(len_u32)
            .ok_or(BackendError::OutOfBounds {
                offset,
                len: data.len(),
                capacity: self.payload_capacity,
            })?;
        if end > self.payload_capacity {
            return Err(BackendError::OutOfBounds {
                offset,
                len: data.len(),
                capacity: self.payload_capacity,
            });
        }
        self.inner.write(offset, data)
    }
}
"""
    # Need InvalidConfig variant - check
    if "InvalidConfig" not in path.read_text() and "InvalidConfig" not in text[:2000]:
        # check original
        pass
    path.write_text(text)
    # Ensure InvalidConfig exists
    text = path.read_text()
    if "InvalidConfig" not in text.split("enum BackendError")[1].split("}")[0]:
        text = must_replace(
            text,
            "pub enum BackendError {\n",
            "pub enum BackendError {\n"
            "    #[error(\"{0}\")]\n"
            "    InvalidConfig(String),\n",
            "InvalidConfig variant",
        )
        path.write_text(text)
    print("patched", path)


def main() -> None:
    patch_fram_subsystem()
    patch_fram_env()
    patch_fram_readme()
    write_fram_helpers()
    patch_mram_backend_window()


if __name__ == "__main__":
    main()
