#!/usr/bin/env python3
"""Reserve high MRAM region for U-Boot env; expose via GraphQL; add sync helper."""
from __future__ import annotations

from pathlib import Path

MRAM = Path("/mnt/c/Users/logan/CubeSAT/Software/services/hardware-services/mram-service")
RAD = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux")
BBB = RAD / "board/kubos/beaglebone-black"
PKG = RAD / "package/kubos/kubos-mram"


def must_replace(text: str, old: str, new: str, label: str) -> str:
    if old not in text:
        raise SystemExit(f"missing block: {label}\n{old[:240]}")
    return text.replace(old, new, 1)


def write_env_mod() -> None:
    path = MRAM / "src/env_region.rs"
    path.write_text(
        """//! Reserved high MRAM region for the classic U-Boot environment blob.
//!
//! Layout (MR2xH40, 512 KiB):
//! - payload / littlefs: `[0, UBOOT_ENV_OFFSET)`
//! - U-Boot env blob:    `[UBOOT_ENV_OFFSET, CAPACITY)` size `UBOOT_ENV_SIZE` (0x2800)

use rust_mram::CAPACITY_BYTES;

/// Must match U-Boot `CONFIG_ENV_SIZE` / Linux `fw_env.config`.
pub const UBOOT_ENV_SIZE: u32 = 0x2800;
/// High-end reserved region so existing littlefs layouts keep low addresses.
pub const UBOOT_ENV_OFFSET: u32 = CAPACITY_BYTES - UBOOT_ENV_SIZE;
/// Bytes available to mram-service payload filesystem.
pub const PAYLOAD_CAPACITY_BYTES: u32 = UBOOT_ENV_OFFSET;

#[derive(Clone, Debug)]
pub struct EnvRegionInfo {
    pub offset: u32,
    pub size: u32,
    pub capacity_bytes: u32,
    pub payload_capacity_bytes: u32,
    pub crc_valid: bool,
    pub crc: u32,
}

/// U-Boot `env_t` CRC32 covers bytes after the leading 4-byte CRC field.
pub fn uboot_env_crc(blob: &[u8]) -> Option<(u32, bool)> {
    if blob.len() < 4 {
        return None;
    }
    let stored = u32::from_le_bytes(blob[0..4].try_into().ok()?);
    let calc = crc32(&blob[4..]);
    Some((stored, stored == calc))
}

fn crc32(data: &[u8]) -> u32 {
    // Same polynomial U-Boot uses (Ethernet / ISO 3309 reflected).
    let mut crc: u32 = 0xFFFF_FFFF;
    for &b in data {
        crc ^= u32::from(b);
        for _ in 0..8 {
            let mask = (!(crc & 1)).wrapping_add(1); // 0 or 0xFFFFFFFF
            // equivalent to if crc & 1 { (crc >> 1) ^ POLY } else { crc >> 1 }
            crc = (crc >> 1) ^ (0xEDB8_8320 & mask.wrapping_neg().wrapping_add(mask.wrapping_add(1).wrapping_mul(0)) );
            // clearer:
            let _ = mask;
        }
    }
    // Use a straightforward implementation:
    let _ = crc;
    crc32_uboot(data)
}

fn crc32_uboot(data: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &byte in data {
        crc ^= u32::from(byte);
        for _ in 0..8 {
            if (crc & 1) != 0 {
                crc = (crc >> 1) ^ 0xEDB8_8320;
            } else {
                crc >>= 1;
            }
        }
    }
    !crc
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn offsets_match_plan() {
        assert_eq!(UBOOT_ENV_SIZE, 10 * 1024);
        assert_eq!(UBOOT_ENV_OFFSET + UBOOT_ENV_SIZE, CAPACITY_BYTES);
        assert_eq!(PAYLOAD_CAPACITY_BYTES, UBOOT_ENV_OFFSET);
    }
}
"""
    )
    # Fix the messy crc32 function - rewrite cleanly
    path.write_text(
        """//! Reserved high MRAM region for the classic U-Boot environment blob.
//!
//! Layout (MR2xH40, 512 KiB):
//! - payload / littlefs: `[0, UBOOT_ENV_OFFSET)`
//! - U-Boot env blob:    `[UBOOT_ENV_OFFSET, CAPACITY)` size `UBOOT_ENV_SIZE` (0x2800)

use rust_mram::CAPACITY_BYTES;

/// Must match U-Boot `CONFIG_ENV_SIZE` / Linux `fw_env.config`.
pub const UBOOT_ENV_SIZE: u32 = 0x2800;
/// High-end reserved region so existing littlefs layouts keep low addresses.
pub const UBOOT_ENV_OFFSET: u32 = CAPACITY_BYTES - UBOOT_ENV_SIZE;
/// Bytes available to mram-service payload filesystem.
pub const PAYLOAD_CAPACITY_BYTES: u32 = UBOOT_ENV_OFFSET;

#[derive(Clone, Debug)]
pub struct EnvRegionInfo {
    pub offset: u32,
    pub size: u32,
    pub capacity_bytes: u32,
    pub payload_capacity_bytes: u32,
    pub crc_valid: bool,
    pub crc: u32,
}

/// U-Boot `env_t` CRC32 covers bytes after the leading 4-byte CRC field.
pub fn uboot_env_crc(blob: &[u8]) -> Option<(u32, bool)> {
    if blob.len() < 4 {
        return None;
    }
    let stored = u32::from_le_bytes(blob[0..4].try_into().ok()?);
    let calc = crc32_uboot(&blob[4..]);
    Some((stored, stored == calc))
}

fn crc32_uboot(data: &[u8]) -> u32 {
    let mut crc: u32 = 0xFFFF_FFFF;
    for &byte in data {
        crc ^= u32::from(byte);
        for _ in 0..8 {
            if (crc & 1) != 0 {
                crc = (crc >> 1) ^ 0xEDB8_8320;
            } else {
                crc >>= 1;
            }
        }
    }
    !crc
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn offsets_match_plan() {
        assert_eq!(UBOOT_ENV_SIZE, 10 * 1024);
        assert_eq!(UBOOT_ENV_OFFSET + UBOOT_ENV_SIZE, CAPACITY_BYTES);
        assert_eq!(PAYLOAD_CAPACITY_BYTES, UBOOT_ENV_OFFSET);
    }
}
"""
    )
    print("wrote", path)


def patch_lib() -> None:
    path = MRAM / "src/lib.rs"
    text = path.read_text()
    if "env_region" not in text:
        text = text.rstrip() + "\npub mod env_region;\n"
        # also need backend/fs/schema/subsystem already there
        path.write_text(text if text.endswith("\n") else text + "\n")
    print("lib.rs:", path.read_text())


def patch_fs_capacity() -> None:
    path = MRAM / "src/fs.rs"
    text = path.read_text()
    text = must_replace(
        text,
        """    pub fn mount(backend: Box<dyn ByteStorage>) -> Result<Self, FsError> {
        if backend.capacity() != rust_mram::CAPACITY_BYTES {
            return Err(FsError::CapacityMismatch {
                actual: backend.capacity(),
                expected: rust_mram::CAPACITY_BYTES,
            });
        }
""",
        """    pub fn mount(backend: Box<dyn ByteStorage>) -> Result<Self, FsError> {
        // Payload window excludes the high U-Boot env reservation.
        let expected = crate::env_region::PAYLOAD_CAPACITY_BYTES;
        if backend.capacity() != expected {
            return Err(FsError::CapacityMismatch {
                actual: backend.capacity(),
                expected,
            });
        }
""",
        "fs mount capacity",
    )
    # Fix unit tests that construct backends with CAPACITY_BYTES
    text = text.replace(
        "MemoryBackend::new(rust_mram::CAPACITY_BYTES)",
        "MemoryBackend::new(crate::env_region::PAYLOAD_CAPACITY_BYTES)",
    )
    text = text.replace(
        "FileImageBackend::new(path, rust_mram::CAPACITY_BYTES)",
        "FileImageBackend::new(path, crate::env_region::PAYLOAD_CAPACITY_BYTES)",
    )
    path.write_text(text)
    print("patched", path)


def patch_subsystem() -> None:
    path = MRAM / "src/subsystem.rs"
    text = path.read_text()
    text = must_replace(
        text,
        """use crate::backend::{ByteStorage, FileImageBackend};
use crate::fs::{FilePayload, FileRecord, StorageStats, TinyMramFs};
""",
        """use crate::backend::{ByteStorage, FileImageBackend, PayloadWindowBackend};
use crate::env_region::{
    self, EnvRegionInfo, PAYLOAD_CAPACITY_BYTES, UBOOT_ENV_OFFSET, UBOOT_ENV_SIZE,
};
use crate::fs::{FilePayload, FileRecord, StorageStats, TinyMramFs};
""",
        "subsystem imports",
    )
    text = must_replace(
        text,
        """pub struct Subsystem {
    fs: Arc<Mutex<TinyMramFs>>,
    backend_name: String,
}
""",
        """pub struct Subsystem {
    fs: Arc<Mutex<TinyMramFs>>,
    /// Full-device backend for reserved env region access (outside littlefs window).
    device: Arc<Mutex<Box<dyn ByteStorage>>>,
    backend_name: String,
    env_offset: u32,
    env_size: u32,
}
""",
        "subsystem fields",
    )

    # Replace from_config body mounting
    old = """        let fs = TinyMramFs::mount(storage).map_err(|e| e.to_string())?;

        Ok(Self {
            fs: Arc::new(Mutex::new(fs)),
            backend_name: backend,
        })
    }
"""
    new = """        let env_offset = config
            .get("env_offset")
            .and_then(|v| v.as_integer())
            .map(|v| v as u32)
            .unwrap_or(UBOOT_ENV_OFFSET);
        let env_size = config
            .get("env_size")
            .and_then(|v| v.as_integer())
            .map(|v| v as u32)
            .unwrap_or(UBOOT_ENV_SIZE);

        if env_size == 0 || env_offset.checked_add(env_size).unwrap_or(u32::MAX) > storage.capacity()
        {
            return Err(format!(
                "invalid env region offset={env_offset} size={env_size} for capacity {}",
                storage.capacity()
            ));
        }
        if env_offset != storage.capacity().saturating_sub(env_size) {
            // Require high-end reservation so payload stays contiguous at 0.
            return Err(format!(
                "env region must be high-end (offset={}, size={}); got offset={env_offset} size={env_size}",
                storage.capacity().saturating_sub(env_size),
                env_size
            ));
        }

        let payload_capacity = env_offset;
        if payload_capacity != PAYLOAD_CAPACITY_BYTES && env_size == UBOOT_ENV_SIZE {
            // Allow override only when env_size/offset explicitly change both ends.
        }

        let device: Arc<Mutex<Box<dyn ByteStorage>>> = Arc::new(Mutex::new(storage));
        // Clone is not available for Box<dyn ByteStorage>; remount window from a
        // second open when possible. For file/spidev we re-open below.
        // Instead: take storage back — restructure: keep device, wrap a clone path.

        // Re-open strategy: build window over a shared backend is hard without
        // interior mutability sharing. Use PayloadWindowBackend owning storage,
        // and keep a second handle via FileImageBackend path duplication.
        // Simpler approach implemented below in from_config rewrite.
        unreachable!();
    }
"""
    # The above approach is getting messy. Rewrite from_config more carefully.
    path.write_text(text)
    print("partial subsystem - rewriting from_config fully")
    rewrite_subsystem_from_config()


def rewrite_subsystem_from_config() -> None:
    path = MRAM / "src/subsystem.rs"
    text = path.read_text()
    # Write a clean subsystem.rs based on current file structure
    path.write_text(
        """use std::sync::{Arc, Mutex};

use crate::backend::{ByteStorage, FileImageBackend, PayloadWindowBackend};
use crate::env_region::{
    EnvRegionInfo, PAYLOAD_CAPACITY_BYTES, UBOOT_ENV_OFFSET, UBOOT_ENV_SIZE, uboot_env_crc,
};
use crate::fs::{FilePayload, FileRecord, StorageStats, TinyMramFs};

#[derive(Clone)]
pub struct Subsystem {
    fs: Arc<Mutex<TinyMramFs>>,
    device: Arc<Mutex<Box<dyn ByteStorage>>>,
    backend_name: String,
    env_offset: u32,
    env_size: u32,
}

impl Subsystem {
    pub fn from_config(config: &kubos_service::Config) -> Result<Self, String> {
        let backend = config
            .get("backend")
            .and_then(|v| v.as_str().map(|s| s.to_string()))
            .unwrap_or_else(|| "file".to_string());

        let env_offset = config
            .get("env_offset")
            .and_then(|v| v.as_integer())
            .map(|v| v as u32)
            .unwrap_or(UBOOT_ENV_OFFSET);
        let env_size = config
            .get("env_size")
            .and_then(|v| v.as_integer())
            .map(|v| v as u32)
            .unwrap_or(UBOOT_ENV_SIZE);

        let storage: Box<dyn ByteStorage> = match backend.as_str() {
            "file" => {
                let path = config
                    .get("image_path")
                    .and_then(|v| v.as_str().map(|s| s.to_string()))
                    .unwrap_or_else(|| "/tmp/mram-service.img".to_string());

                let capacity = config
                    .get("image_capacity_bytes")
                    .and_then(|v| v.as_integer())
                    .map(|v| v as u32)
                    .unwrap_or(rust_mram::CAPACITY_BYTES);

                Box::new(FileImageBackend::new(&path, capacity).map_err(|e| e.to_string())?)
            }
            "spidev" => {
                #[cfg(feature = "spidev")]
                {
                    let device = config
                        .get("spi_device")
                        .and_then(|v| v.as_str().map(|s| s.to_string()))
                        .unwrap_or_else(|| "/dev/spidev1.0".to_string());

                    let speed_hz = config
                        .get("spi_speed_hz")
                        .and_then(|v| v.as_integer())
                        .map(|v| v as u32)
                        .unwrap_or(10_000_000);

                    let mode = config
                        .get("spi_mode")
                        .and_then(|v| v.as_integer())
                        .map(|v| v as u8)
                        .unwrap_or(0);

                    Box::new(
                        crate::backend::SpidevBackend::new(&device, speed_hz, mode)
                            .map_err(|e| e.to_string())?,
                    )
                }

                #[cfg(not(feature = "spidev"))]
                {
                    return Err(
                        "backend='spidev' requested but service was built without 'spidev' feature"
                            .to_string(),
                    );
                }
            }
            other => {
                return Err(format!(
                    "unsupported backend '{other}'. expected 'file' or 'spidev'"
                ));
            }
        };

        let capacity = storage.capacity();
        if env_size == 0 || env_offset.checked_add(env_size).unwrap_or(u32::MAX) > capacity {
            return Err(format!(
                "invalid env region offset={env_offset} size={env_size} for capacity {capacity}"
            ));
        }
        if env_offset + env_size != capacity {
            return Err(format!(
                "U-Boot env region must be at high end of MRAM (offset={}, size={env_size})",
                capacity - env_size
            ));
        }
        if env_offset != PAYLOAD_CAPACITY_BYTES && env_size == UBOOT_ENV_SIZE {
            // Default constants must stay in sync with rust_mram capacity.
            if env_offset != capacity - env_size {
                return Err("env_offset mismatch".to_string());
            }
        }

        // Shared full-device handle for env region reads.
        let device: Arc<Mutex<Box<dyn ByteStorage>>> = Arc::new(Mutex::new(storage));

        // Build a second full-device backend for the payload window.
        let storage2: Box<dyn ByteStorage> = match backend.as_str() {
            "file" => {
                let path = config
                    .get("image_path")
                    .and_then(|v| v.as_str().map(|s| s.to_string()))
                    .unwrap_or_else(|| "/tmp/mram-service.img".to_string());
                let capacity = config
                    .get("image_capacity_bytes")
                    .and_then(|v| v.as_integer())
                    .map(|v| v as u32)
                    .unwrap_or(rust_mram::CAPACITY_BYTES);
                Box::new(FileImageBackend::new(&path, capacity).map_err(|e| e.to_string())?)
            }
            "spidev" => {
                #[cfg(feature = "spidev")]
                {
                    let spi_device = config
                        .get("spi_device")
                        .and_then(|v| v.as_str().map(|s| s.to_string()))
                        .unwrap_or_else(|| "/dev/spidev1.0".to_string());
                    let speed_hz = config
                        .get("spi_speed_hz")
                        .and_then(|v| v.as_integer())
                        .map(|v| v as u32)
                        .unwrap_or(10_000_000);
                    let mode = config
                        .get("spi_mode")
                        .and_then(|v| v.as_integer())
                        .map(|v| v as u8)
                        .unwrap_or(0);
                    Box::new(
                        crate::backend::SpidevBackend::new(&spi_device, speed_hz, mode)
                            .map_err(|e| e.to_string())?,
                    )
                }
                #[cfg(not(feature = "spidev"))]
                {
                    return Err("spidev feature required".to_string());
                }
            }
            _ => unreachable!(),
        };

        let window = PayloadWindowBackend::new(storage2, env_offset).map_err(|e| e.to_string())?;
        let fs = TinyMramFs::mount(Box::new(window)).map_err(|e| e.to_string())?;

        Ok(Self {
            fs: Arc::new(Mutex::new(fs)),
            device,
            backend_name: backend,
            env_offset,
            env_size,
        })
    }

    pub fn backend_name(&self) -> &str {
        &self.backend_name
    }

    pub fn env_region_info(&self) -> Result<EnvRegionInfo, String> {
        let mut device = self.device.lock().map_err(lock_error)?;
        let mut blob = vec![0u8; self.env_size as usize];
        device
            .read(self.env_offset, &mut blob)
            .map_err(|e| e.to_string())?;
        let (crc, crc_valid) = uboot_env_crc(&blob).unwrap_or((0, false));
        Ok(EnvRegionInfo {
            offset: self.env_offset,
            size: self.env_size,
            capacity_bytes: device.capacity(),
            payload_capacity_bytes: self.env_offset,
            crc_valid,
            crc,
        })
    }

    pub fn read_env_blob(&self) -> Result<Vec<u8>, String> {
        let mut device = self.device.lock().map_err(lock_error)?;
        let mut blob = vec![0u8; self.env_size as usize];
        device
            .read(self.env_offset, &mut blob)
            .map_err(|e| e.to_string())?;
        Ok(blob)
    }

    /// Refuse any raw payload write that would touch the reserved env region.
    /// Littlefs is already windowed; this guards explicit helpers.
    pub fn ensure_payload_range(&self, offset: u32, len: u32) -> Result<(), String> {
        let end = offset
            .checked_add(len)
            .ok_or_else(|| "offset overflow".to_string())?;
        if end > self.env_offset {
            return Err(format!(
                "refusing write into U-Boot env region (offset={offset} len={len}; env starts at {})",
                self.env_offset
            ));
        }
        Ok(())
    }

    pub fn list_files(&self) -> Result<Vec<FileRecord>, String> {
        let mut fs = self.fs.lock().map_err(lock_error)?;
        fs.list_files().map_err(|e| e.to_string())
    }

    pub fn file(&self, name: &str) -> Result<Option<FileRecord>, String> {
        let mut fs = self.fs.lock().map_err(lock_error)?;
        fs.file(name).map_err(|e| e.to_string())
    }

    pub fn read_file(
        &self,
        name: &str,
        offset: u32,
        length: Option<u32>,
    ) -> Result<FilePayload, String> {
        let mut fs = self.fs.lock().map_err(lock_error)?;
        fs.read_file(name, offset, length)
            .map_err(|e| e.to_string())
    }

    pub fn write_file(
        &self,
        name: &str,
        mime_type: Option<&str>,
        compressed: bool,
        data: &[u8],
    ) -> Result<FileRecord, String> {
        let mut fs = self.fs.lock().map_err(lock_error)?;
        fs.write_file(name, mime_type, compressed, data)
            .map_err(|e| e.to_string())
    }

    pub fn delete_file(&self, name: &str) -> Result<bool, String> {
        let mut fs = self.fs.lock().map_err(lock_error)?;
        fs.delete_file(name).map_err(|e| e.to_string())
    }

    pub fn format(&self) -> Result<(), String> {
        let mut fs = self.fs.lock().map_err(lock_error)?;
        fs.format().map_err(|e| e.to_string())
    }

    pub fn stats(&self) -> Result<StorageStats, String> {
        let mut fs = self.fs.lock().map_err(lock_error)?;
        fs.stats().map_err(|e| e.to_string())
    }
}

fn lock_error<E>(_: E) -> String {
    "subsystem lock poisoned".to_string()
}
"""
    )
    print("rewrote subsystem.rs")


def patch_schema() -> None:
    path = MRAM / "src/schema.rs"
    text = path.read_text()
    if "env_region" in text and "EnvRegion" in text:
        print("schema already has env_region")
        return
    text = must_replace(
        text,
        """#[derive(SimpleObject)]
pub struct StorageInfo {
    pub backend: String,
    pub capacity_bytes: i64,
    pub allocated_bytes: i64,
    pub live_bytes: i64,
    pub reclaimable_bytes: i64,
    pub free_bytes: i64,
    pub file_count: i64,
}
""",
        """#[derive(SimpleObject)]
pub struct StorageInfo {
    pub backend: String,
    pub capacity_bytes: i64,
    pub allocated_bytes: i64,
    pub live_bytes: i64,
    pub reclaimable_bytes: i64,
    pub free_bytes: i64,
    pub file_count: i64,
}

#[derive(SimpleObject)]
pub struct EnvRegion {
    pub offset: i64,
    pub size: i64,
    pub capacity_bytes: i64,
    pub payload_capacity_bytes: i64,
    pub crc_valid: bool,
    pub crc: i64,
}
""",
        "EnvRegion type",
    )
    # Add query after storage()
    text = must_replace(
        text,
        """    async fn storage(&self, ctx: &Context<'_>) -> Result<StorageInfo> {
        let context = ctx.data::<kubos_service::Context<Subsystem>>()?;
        let stats = context
            .subsystem()
            .stats()
            .map_err(async_graphql::Error::new)?;

        Ok(StorageInfo {
            backend: context.subsystem().backend_name().to_string(),
            capacity_bytes: stats.capacity_bytes as i64,
            allocated_bytes: stats.allocated_bytes as i64,
            live_bytes: stats.live_bytes as i64,
            reclaimable_bytes: stats.reclaimable_bytes as i64,
            free_bytes: stats.free_bytes as i64,
            file_count: stats.file_count as i64,
        })
    }
""",
        """    async fn storage(&self, ctx: &Context<'_>) -> Result<StorageInfo> {
        let context = ctx.data::<kubos_service::Context<Subsystem>>()?;
        let stats = context
            .subsystem()
            .stats()
            .map_err(async_graphql::Error::new)?;

        Ok(StorageInfo {
            backend: context.subsystem().backend_name().to_string(),
            capacity_bytes: stats.capacity_bytes as i64,
            allocated_bytes: stats.allocated_bytes as i64,
            live_bytes: stats.live_bytes as i64,
            reclaimable_bytes: stats.reclaimable_bytes as i64,
            free_bytes: stats.free_bytes as i64,
            file_count: stats.file_count as i64,
        })
    }

    /// Reserved high MRAM region used for the U-Boot environment blob.
    async fn env_region(&self, ctx: &Context<'_>) -> Result<EnvRegion> {
        let context = ctx.data::<kubos_service::Context<Subsystem>>()?;
        let info = context
            .subsystem()
            .env_region_info()
            .map_err(async_graphql::Error::new)?;
        Ok(EnvRegion {
            offset: info.offset as i64,
            size: info.size as i64,
            capacity_bytes: info.capacity_bytes as i64,
            payload_capacity_bytes: info.payload_capacity_bytes as i64,
            crc_valid: info.crc_valid,
            crc: info.crc as i64,
        })
    }
""",
        "env_region query",
    )
    path.write_text(text)
    print("patched", path)


def patch_config_readme() -> None:
    path = MRAM / "config.toml"
    text = path.read_text()
    if "env_offset" not in text:
        text = text.replace(
            'image_capacity_bytes = 524288\n',
            'image_capacity_bytes = 524288\n'
            '# High-end U-Boot env reservation (must match U-Boot CONFIG_ENV_*).\n'
            'env_offset = 514048\n'
            'env_size = 10240\n',
        )
        path.write_text(text)
    readme = MRAM / "README.md"
    if readme.exists():
        t = readme.read_text()
        if "U-Boot env" not in t:
            t += """

## U-Boot environment reservation

The high `0x2800` (10240) bytes of MRAM are reserved for the classic U-Boot
environment blob (`env_offset = capacity - env_size`). littlefs / GraphQL file
APIs only see the payload window below that offset and cannot overwrite it.

Query reserved region / CRC:

```graphql
{ envRegion { offset size payloadCapacityBytes crcValid crc } }
```
"""
            readme.write_text(t)
    print("config/readme updated")


def write_sync_bin() -> None:
    bin_dir = MRAM / "src/bin"
    bin_dir.mkdir(exist_ok=True)
    (bin_dir / "mram_env_sync.rs").write_text(
        r"""//! Copy CRC-valid U-Boot env blob from SPI/file MRAM to /envar/uboot.env.
//!
//! Used by S79mram-env-sync before fram-service starts.

use std::env;
use std::fs;
use std::io::Write;
use std::path::Path;
use std::process::ExitCode;

use mram_service::backend::{ByteStorage, FileImageBackend};
use mram_service::env_region::{uboot_env_crc, UBOOT_ENV_OFFSET, UBOOT_ENV_SIZE};

fn main() -> ExitCode {
    let mut args = env::args().skip(1);
    let mut out = "/envar/uboot.env".to_string();
    let mut backend = "spidev".to_string();
    let mut device = "/dev/spidev1.0".to_string();
    let mut image = String::new();
    let mut speed = 10_000_000u32;
    let mut mode = 0u8;
    let mut offset = UBOOT_ENV_OFFSET;
    let mut size = UBOOT_ENV_SIZE;

    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--out" => out = args.next().unwrap_or(out),
            "--backend" => backend = args.next().unwrap_or(backend),
            "--device" => device = args.next().unwrap_or(device),
            "--image" => image = args.next().unwrap_or(image),
            "--speed" => speed = args.next().and_then(|s| s.parse().ok()).unwrap_or(speed),
            "--mode" => mode = args.next().and_then(|s| s.parse().ok()).unwrap_or(mode),
            "--offset" => offset = args.next().and_then(|s| s.parse().ok()).unwrap_or(offset),
            "--size" => size = args.next().and_then(|s| s.parse().ok()).unwrap_or(size),
            "-h" | "--help" => {
                eprintln!(
                    "usage: mram-env-sync [--backend spidev|file] [--device PATH] [--image PATH] [--out PATH]"
                );
                return ExitCode::SUCCESS;
            }
            other => {
                eprintln!("unknown arg: {other}");
                return ExitCode::from(2);
            }
        }
    }

    let mut storage: Box<dyn ByteStorage> = match backend.as_str() {
        "file" => {
            if image.is_empty() {
                eprintln!("file backend requires --image");
                return ExitCode::from(2);
            }
            match FileImageBackend::new(&image, rust_mram::CAPACITY_BYTES) {
                Ok(b) => Box::new(b),
                Err(e) => {
                    eprintln!("open image: {e}");
                    return ExitCode::from(1);
                }
            }
        }
        "spidev" => {
            #[cfg(feature = "spidev")]
            {
                match mram_service::backend::SpidevBackend::new(&device, speed, mode) {
                    Ok(b) => Box::new(b),
                    Err(e) => {
                        eprintln!("open spidev: {e}");
                        return ExitCode::from(1);
                    }
                }
            }
            #[cfg(not(feature = "spidev"))]
            {
                eprintln!("mram-env-sync built without spidev feature");
                return ExitCode::from(1);
            }
        }
        other => {
            eprintln!("unsupported backend {other}");
            return ExitCode::from(2);
        }
    };

    let mut blob = vec![0u8; size as usize];
    if let Err(e) = storage.read(offset, &mut blob) {
        eprintln!("MRAM env read failed: {e}");
        return ExitCode::from(1);
    }

    match uboot_env_crc(&blob) {
        Some((_, true)) => {}
        Some((crc, false)) => {
            eprintln!("MRAM env CRC invalid (stored/calc mismatch around {crc:#x}); leaving {out}");
            return ExitCode::from(0);
        }
        None => {
            eprintln!("MRAM env blob too small");
            return ExitCode::from(1);
        }
    }

    if let Some(parent) = Path::new(&out).parent() {
        let _ = fs::create_dir_all(parent);
    }
    match fs::File::create(&out).and_then(|mut f| f.write_all(&blob).and(f.sync_all())) {
        Ok(()) => {
            eprintln!("synced MRAM env -> {out} ({size} bytes)");
            ExitCode::SUCCESS
        }
        Err(e) => {
            eprintln!("write {out}: {e}");
            ExitCode::from(1)
        }
    }
}
"""
    )
    cargo = MRAM / "Cargo.toml"
    ctext = cargo.read_text()
    if "mram-env-sync" not in ctext:
        ctext += """
[[bin]]
name = "mram-service"
path = "src/main.rs"

[[bin]]
name = "mram-env-sync"
path = "src/bin/mram_env_sync.rs"
"""
        # Avoid duplicate [[bin]] if package already implies main
        # Check if explicit bins needed - with src/main.rs, adding [[bin]] for main is fine
        cargo.write_text(ctext)
    print("wrote mram-env-sync bin")


def write_s79_and_package() -> None:
    init = BBB / "overlay/etc/init.d/S79mram-env-sync"
    init.parent.mkdir(parents=True, exist_ok=True)
    init.write_text(
        """#!/bin/sh
#
# S79mram-env-sync — Mirror CRC-valid U-Boot env from SPI MRAM to /envar/uboot.env
# so fw_printenv/fw_setenv keep working. Runs before fram-service (S80).
#

ENVAR_FILE="/envar/uboot.env"
SYNC="/usr/sbin/mram-env-sync"

case "$1" in
  start)
    mkdir -p /run/lock /envar
    chmod 1777 /run/lock 2>/dev/null || true
    if [ -x "$SYNC" ]; then
      echo "S79mram-env-sync: syncing MRAM env -> ${ENVAR_FILE}"
      "$SYNC" --backend spidev --device /dev/spidev1.0 --out "$ENVAR_FILE" || true
    else
      echo "S79mram-env-sync: ${SYNC} missing; leaving ${ENVAR_FILE}"
    fi
    ;;
  stop)
    ;;
  *)
    echo "Usage: $0 {start|stop}"
    exit 1
    ;;
esac

exit 0
"""
    )
    # Update package install to also install mram-env-sync
    mk = PKG / "kubos-mram.mk"
    text = mk.read_text()
    if "mram-env-sync" not in text:
        text = must_replace(
            text,
            """define MRAM_INSTALL_TARGET_CMDS
\tmkdir -p $(TARGET_DIR)/usr/sbin
\tPATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \\
\t$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/mram-service
\t$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/mram-service \\
\t\t$(TARGET_DIR)/usr/sbin
""",
            """define MRAM_INSTALL_TARGET_CMDS
\tmkdir -p $(TARGET_DIR)/usr/sbin
\tPATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \\
\t$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/mram-service
\t$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/mram-service \\
\t\t$(TARGET_DIR)/usr/sbin
\tif [ -f $(KUBOS_CARGO_OUTPUT_DIR)/mram-env-sync ]; then \\
\t\t$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/mram-env-sync ; \\
\t\t$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/mram-env-sync \\
\t\t\t$(TARGET_DIR)/usr/sbin ; \\
\tfi
""",
            "install mram-env-sync",
        )
        # Also add env_offset to config fragment
        text = must_replace(
            text,
            """\techo 'spi_mode = ${BR2_KUBOS_MRAM_SPI_MODE}\\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
endef
""",
            """\techo 'spi_mode = ${BR2_KUBOS_MRAM_SPI_MODE}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
\techo 'env_offset = 514048' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
\techo -e 'env_size = 10240\\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
endef
""",
            "env config fragment",
        )
        mk.write_text(text)
    print("wrote S79 + package bits")


def fix_tests() -> None:
    path = MRAM / "tests/graphql.rs"
    if not path.exists():
        return
    text = path.read_text()
    if "env_offset" not in text:
        text = text.replace(
            'image_capacity_bytes = 524288\n',
            'image_capacity_bytes = 524288\nenv_offset = 514048\nenv_size = 10240\n',
        )
        path.write_text(text)
    print("tests updated")


def main() -> None:
    write_env_mod()
    patch_lib()
    patch_fs_capacity()
    rewrite_subsystem_from_config()
    patch_schema()
    patch_config_readme()
    write_sync_bin()
    write_s79_and_package()
    fix_tests()


if __name__ == "__main__":
    main()
