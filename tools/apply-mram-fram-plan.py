#!/usr/bin/env python3
"""Apply MRAM env + FRAM anti-brick plan edits to Software + radsat-linux."""
from __future__ import annotations

import re
import textwrap
from pathlib import Path

SOFT = Path("/mnt/c/Users/logan/CubeSAT/Software")
RAD = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux")
FRAM = SOFT / "services/hardware-services/fram-service"
MRAM = SOFT / "services/hardware-services/mram-service"


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing block: {label}")
    return text.replace(old, new, 1)


def patch_fram_layout() -> None:
    path = FRAM / "src/layout.rs"
    text = path.read_text()
    text = must_replace(
        text,
        """pub const MISSION_REGION_END: u32 = RESERVED_KEYS * SLOTS_PER_KEY * RECORD_SIZE as u32;

const MAGIC: u16 = 0x4652; // \"FR\"
const VERSION: u8 = 1;
""",
        """pub const MISSION_REGION_END: u32 = RESERVED_KEYS * SLOTS_PER_KEY * RECORD_SIZE as u32;

/// Fixed layout header in free/scratch (never overlaps dual-slot records).
/// Wrong-image dumps fail this check instead of looking like valid policy.
pub const LAYOUT_HEADER_OFFSET: u32 = MISSION_REGION_END;
pub const LAYOUT_HEADER_SIZE: u32 = 16;
/// ASCII \"FRAM\" little-endian.
pub const LAYOUT_MAGIC: u32 = 0x4D_41_52_46;
/// Bump when mission key offsets / types change incompatibly.
pub const LAYOUT_VERSION: u16 = 1;

const MAGIC: u16 = 0x4652; // \"FR\"
const VERSION: u8 = 1;
""",
        "layout header consts",
    )
    text = must_replace(
        text,
        """    pub fn verify_boot_checksum(&mut self) -> Result<bool, LayoutError> {
        match self.stored_boot_checksum()? {
            Some(stored) => Ok(stored == self.compute_boot_checksum()?),
            None => Ok(false),
        }
    }
""",
        """    pub fn verify_boot_checksum(&mut self) -> Result<bool, LayoutError> {
        match self.stored_boot_checksum()? {
            Some(stored) => Ok(stored == self.compute_boot_checksum()?),
            None => Ok(false),
        }
    }

    /// Write layout magic/version if missing or blank. Never fatal for callers.
    pub fn ensure_layout_header(&mut self) -> Result<(), LayoutError> {
        if self.verify_layout_header()? {
            return Ok(());
        }
        let mut raw = [0u8; LAYOUT_HEADER_SIZE as usize];
        raw[0..4].copy_from_slice(&LAYOUT_MAGIC.to_le_bytes());
        raw[4..6].copy_from_slice(&LAYOUT_VERSION.to_le_bytes());
        self.storage
            .write(LAYOUT_HEADER_OFFSET, &raw)
            .map_err(LayoutError::Backend)?;
        Ok(())
    }

    pub fn verify_layout_header(&mut self) -> Result<bool, LayoutError> {
        let mut raw = [0u8; LAYOUT_HEADER_SIZE as usize];
        self.storage
            .read(LAYOUT_HEADER_OFFSET, &mut raw)
            .map_err(LayoutError::Backend)?;
        let magic = u32::from_le_bytes(raw[0..4].try_into().unwrap());
        let version = u16::from_le_bytes(raw[4..6].try_into().unwrap());
        Ok(magic == LAYOUT_MAGIC && version == LAYOUT_VERSION)
    }

    pub fn layout_version(&mut self) -> Result<Option<u16>, LayoutError> {
        if !self.verify_layout_header()? {
            return Ok(None);
        }
        Ok(Some(LAYOUT_VERSION))
    }
""",
        "layout header methods",
    )
    text = must_replace(
        text,
        """    MemoryMap {
        capacity_bytes: i64::from(capacity),
        mission_region_start: i64::from(MISSION_REGION_START),
        mission_region_end: i64::from(MISSION_REGION_END),
        free_region_start: i64::from(free_start),
        free_region_end: i64::from(free_end),
        regions: vec![
            MemoryMapRegion {
                name: \"boot_records\".to_string(),
                start_offset: i64::from(BOOT_REGION_START),
                end_offset: i64::from(BOOT_REGION_END),
                size_bytes: i64::from(BOOT_REGION_END - BOOT_REGION_START),
            },
            MemoryMapRegion {
                name: \"mission_records\".to_string(),
                start_offset: i64::from(BOOT_REGION_END),
                end_offset: i64::from(MISSION_REGION_END),
                size_bytes: i64::from(MISSION_REGION_END - BOOT_REGION_END),
            },
            MemoryMapRegion {
                name: \"free_scratch\".to_string(),
                start_offset: i64::from(free_start),
                end_offset: i64::from(free_end),
                size_bytes: i64::from(free_end.saturating_sub(free_start)),
            },
        ],
""",
        """    MemoryMap {
        capacity_bytes: i64::from(capacity),
        layout_magic: i64::from(LAYOUT_MAGIC),
        layout_version: i64::from(LAYOUT_VERSION),
        mission_region_start: i64::from(MISSION_REGION_START),
        mission_region_end: i64::from(MISSION_REGION_END),
        free_region_start: i64::from(free_start),
        free_region_end: i64::from(free_end),
        regions: vec![
            MemoryMapRegion {
                name: \"boot_records\".to_string(),
                start_offset: i64::from(BOOT_REGION_START),
                end_offset: i64::from(BOOT_REGION_END),
                size_bytes: i64::from(BOOT_REGION_END - BOOT_REGION_START),
            },
            MemoryMapRegion {
                name: \"mission_records\".to_string(),
                start_offset: i64::from(BOOT_REGION_END),
                end_offset: i64::from(MISSION_REGION_END),
                size_bytes: i64::from(MISSION_REGION_END - BOOT_REGION_END),
            },
            MemoryMapRegion {
                name: \"layout_header\".to_string(),
                start_offset: i64::from(LAYOUT_HEADER_OFFSET),
                end_offset: i64::from(LAYOUT_HEADER_OFFSET + LAYOUT_HEADER_SIZE),
                size_bytes: i64::from(LAYOUT_HEADER_SIZE),
            },
            MemoryMapRegion {
                name: \"free_scratch\".to_string(),
                start_offset: i64::from(LAYOUT_HEADER_OFFSET + LAYOUT_HEADER_SIZE),
                end_offset: i64::from(free_end),
                size_bytes: i64::from(
                    free_end.saturating_sub(LAYOUT_HEADER_OFFSET + LAYOUT_HEADER_SIZE),
                ),
            },
        ],
""",
        "memory_map regions",
    )
    text = must_replace(
        text,
        """    fn boot_checksum_tracks_policy_writes() {
        let (_tmp, mut storage) = storage();
        assert!(!storage.verify_boot_checksum().unwrap());
""",
        """    fn layout_header_round_trip() {
        let (_tmp, mut storage) = storage();
        assert!(!storage.verify_layout_header().unwrap());
        storage.ensure_layout_header().unwrap();
        assert!(storage.verify_layout_header().unwrap());
        assert_eq!(storage.layout_version().unwrap(), Some(LAYOUT_VERSION));
        assert_eq!(LAYOUT_HEADER_OFFSET, 2048);
    }

    #[test]
    fn boot_checksum_tracks_policy_writes() {
        let (_tmp, mut storage) = storage();
        assert!(!storage.verify_boot_checksum().unwrap());
""",
        "layout header test",
    )
    path.write_text(text)
    print("patched", path)


def patch_fram_model() -> None:
    path = FRAM / "src/model.rs"
    text = path.read_text()
    text = must_replace(
        text,
        """    pub fn mirrors_to_env(self) -> bool {
        !matches!(self, Self::BootChecksum)
    }
""",
        """    pub fn mirrors_to_env(self) -> bool {
        !matches!(self, Self::BootChecksum)
    }

    /// Names U-Boot/Linux must never accept from FRAM as classic boot env.
    pub fn is_forbidden_boot_env_name(name: &str) -> bool {
        matches!(
            name.trim().to_ascii_lowercase().as_str(),
            "bootcmd"
            | "bootargs"
            | "bootdelay"
            | "bootfile"
            | "dfu_alt_info"
            | "dfu_alt_info_mmc"
            | "dfu_alt_info_nor"
            | "distro_bootcmd"
            | "mmcboot"
            | "uuid"
            | "bootpart"
            | "root"
            | "loaduimage"
            | "loadfdt"
        )
    }
""",
        "forbidden boot env names",
    )
    text = must_replace(
        text,
        """pub struct MemoryMap {
    pub capacity_bytes: i64,
    pub mission_region_start: i64,
    pub mission_region_end: i64,
    pub free_region_start: i64,
    pub free_region_end: i64,
    pub regions: Vec<MemoryMapRegion>,
    pub flags: Vec<MemoryMapEntry>,
}
""",
        """pub struct MemoryMap {
    pub capacity_bytes: i64,
    pub layout_magic: i64,
    pub layout_version: i64,
    pub mission_region_start: i64,
    pub mission_region_end: i64,
    pub free_region_start: i64,
    pub free_region_end: i64,
    pub regions: Vec<MemoryMapRegion>,
    pub flags: Vec<MemoryMapEntry>,
}
""",
        "MemoryMap fields",
    )
    path.write_text(text)
    print("patched", path)


def patch_fram_schema_mirror_default() -> None:
    path = FRAM / "src/schema.rs"
    text = path.read_text()
    text = text.replace("mirror_to_env.unwrap_or(true)", "mirror_to_env.unwrap_or(false)")
    path.write_text(text)
    print("patched", path)


def patch_fram_subsystem_header() -> None:
    path = FRAM / "src/subsystem.rs"
    text = path.read_text()
    # ensure layout header on mount/init if there is a clear init path
    if "ensure_layout_header" in text:
        print("subsystem already has layout header call")
        return
    # After FramStorage::mount success paths, call ensure_layout_header.
    # Look for mount usage.
    m = re.search(
        r"(let mut storage = FramStorage::mount\([^;]+;\n)",
        text,
    )
    if not m:
        # try alternate
        if "FramStorage::mount" not in text:
            print("WARN: no FramStorage::mount in subsystem; skip ensure call")
            return
        text = must_replace(
            text,
            "FramStorage::mount(",
            "FramStorage::mount(",
            "noop",
        )
        # Find first mount assignment block more loosely
        text2 = text
        needle = "FramStorage::mount"
        idx = text2.find(needle)
        # Find end of that statement
        semi = text2.find(";", idx)
        line_end = text2.find("\n", semi)
        insert = (
            "\n        // Mission layout marker (fail-open if write fails later).\n"
            "        let _ = storage.ensure_layout_header();\n"
            if "let mut storage" in text2[idx - 80 : idx]
            else None
        )
        # Better approach: patch write_key path to ensure header once
        path.write_text(text)
        print("skipped automatic ensure; will patch write path")
        return

    path.write_text(text)


def patch_fram_env_guard() -> None:
    path = FRAM / "src/env.rs"
    text = path.read_text()
    if "is_forbidden_boot_env_name" in text:
        print("env.rs already guarded")
        return
    # Add guard in setenv-like functions
    if "fw_setenv" in text or "set_env" in text:
        # Prepend helper usage near top after imports
        if "use crate::model::" in text and "MissionKey" in text:
            text = must_replace(
                text,
                "use crate::model::",
                "use crate::model::",
                "noop-env-import",
            )
        # Find pub fn that writes env
        for fn_name in ("set_value", "write_env", "set_env_var", "fw_set"):
            pass
        # Insert check into any function that takes key name string for set
        text2 = text
        # Common pattern: fn set( ... name
        if "pub fn set(" in text2 or "fn set_var" in text2 or "pub fn write" in text2:
            pass
        path.write_text(text)
    # Read file to do smarter patch
    text = path.read_text()
    print("env.rs preview keys:", [l for l in text.splitlines() if "fn " in l and "pub" in l][:20])


def main() -> None:
    patch_fram_layout()
    patch_fram_model()
    patch_fram_schema_mirror_default()
    patch_fram_subsystem_header()
    patch_fram_env_guard()


if __name__ == "__main__":
    main()
