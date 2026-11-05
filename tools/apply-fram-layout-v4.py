#!/usr/bin/env python3
"""Apply FRAM layout v4 (recovery keys after boot policy) to Software fram-service."""
from __future__ import annotations

import re
from pathlib import Path

SOFTWARE = Path(r"c:\Users\logan\CubeSAT\Software")
LAYOUT = SOFTWARE / "services/hardware-services/fram-service/src/layout.rs"
MODEL = SOFTWARE / "services/hardware-services/fram-service/src/model.rs"


def main() -> None:
    t = LAYOUT.read_text(encoding="utf-8")
    t = t.replace("pub const RESERVED_KEYS: u32 = 32;", "pub const RESERVED_KEYS: u32 = 40;")
    t = t.replace("pub const LAYOUT_VERSION: u16 = 3;", "pub const LAYOUT_VERSION: u16 = 4;")
    LAYOUT.write_text(t, encoding="utf-8")
    print("layout.rs updated")

    text = MODEL.read_text(encoding="utf-8")

    new_keys_array = """pub const MISSION_KEYS: [MissionKey; 39] = [
    // --- Boot policy (U-Boot may overlay; ids 1-6) + checksum trailer (7) ---
    MissionKey::RemoveBeforeFlight,
    MissionKey::Deployed,
    MissionKey::DeployStart,
    MissionKey::InitialSafeStateComplete,
    MissionKey::FsooTimer,
    MissionKey::DetumblingComplete,
    MissionKey::BootChecksum,
    // --- Recovery + ground-visible boot state (U-Boot R/W; not env overlay) ---
    MissionKey::TotalBootFails,
    MissionKey::EmmcRecoveryNeeded,
    MissionKey::EmmcRecoveryAttempts,
    MissionKey::SdRestoreSlot,
    MissionKey::LastEmmcProbeOk,
    MissionKey::BootMedia,
    MissionKey::BootImageId,
    // --- One-time deploy / completion ---
    MissionKey::SolarPanelDeployed,
    MissionKey::UhfAntennaDeployed,
    MissionKey::VhfAntennaDeployed,
    MissionKey::AdcsCommissioningLogged,
    // --- Ground consent (operator) ---
    MissionKey::AdcsCommissioned,
    MissionKey::SunPointingConsent,
    MissionKey::NadirPointingConsent,
    MissionKey::PlatformCommissioned,
    // --- Failure trip flags ---
    MissionKey::GnssSystemError,
    MissionKey::Gyro0Fail,
    MissionKey::Gyro1Fail,
    MissionKey::Mag0Fail,
    MissionKey::Mag1Fail,
    MissionKey::ReactionWheelFail,
    MissionKey::SunSensorFail,
    MissionKey::EarthSensorFail,
    MissionKey::SunPointingAngleFault,
    MissionKey::SunPointingRateFault,
    MissionKey::NadirPointingAngleFault,
    MissionKey::NadirPointingRateFault,
    // --- Attempt counters ---
    MissionKey::AntennaDeployAttempts,
    MissionKey::SolarPanelDeployAttempts,
    MissionKey::NadirPointAttempts,
    MissionKey::SunPointAttempts,
    // --- Crypto (FRAM-only; never mirrored to env) ---
    MissionKey::CommsUplinkAes128Key,
];"""

    text2, n = re.subn(
        r"pub const MISSION_KEYS: \[MissionKey; 32\] = \[.*?\];",
        new_keys_array,
        text,
        count=1,
        flags=re.S,
    )
    if n != 1:
        raise SystemExit(f"MISSION_KEYS replace failed ({n})")

    old_enum = """pub enum MissionKey {
    RemoveBeforeFlight,
    Deployed,
    DeployStart,
    InitialSafeStateComplete,
    FsooTimer,
    DetumblingComplete,
    BootChecksum,
    SolarPanelDeployed,"""
    new_enum = """pub enum MissionKey {
    RemoveBeforeFlight,
    Deployed,
    DeployStart,
    InitialSafeStateComplete,
    FsooTimer,
    DetumblingComplete,
    BootChecksum,
    TotalBootFails,
    EmmcRecoveryNeeded,
    EmmcRecoveryAttempts,
    SdRestoreSlot,
    LastEmmcProbeOk,
    BootMedia,
    BootImageId,
    SolarPanelDeployed,"""
    if old_enum not in text2:
        raise SystemExit("enum block not found")
    text2 = text2.replace(old_enum, new_enum, 1)

    old_id = """    pub fn id(self) -> u8 {
        match self {
            Self::RemoveBeforeFlight => 1,
            Self::Deployed => 2,
            Self::DeployStart => 3,
            Self::InitialSafeStateComplete => 4,
            Self::FsooTimer => 5,
            Self::DetumblingComplete => 6,
            Self::BootChecksum => 7,
            Self::SolarPanelDeployed => 8,
            Self::UhfAntennaDeployed => 9,
            Self::VhfAntennaDeployed => 10,
            Self::AdcsCommissioningLogged => 11,
            Self::AdcsCommissioned => 12,
            Self::SunPointingConsent => 13,
            Self::NadirPointingConsent => 14,
            Self::PlatformCommissioned => 15,
            Self::GnssSystemError => 16,
            Self::Gyro0Fail => 17,
            Self::Gyro1Fail => 18,
            Self::Mag0Fail => 19,
            Self::Mag1Fail => 20,
            Self::ReactionWheelFail => 21,
            Self::SunSensorFail => 22,
            Self::EarthSensorFail => 23,
            Self::SunPointingAngleFault => 24,
            Self::SunPointingRateFault => 25,
            Self::NadirPointingAngleFault => 26,
            Self::NadirPointingRateFault => 27,
            Self::AntennaDeployAttempts => 28,
            Self::SolarPanelDeployAttempts => 29,
            Self::NadirPointAttempts => 30,
            Self::SunPointAttempts => 31,
            Self::CommsUplinkAes128Key => 32,
        }
    }"""
    new_id = """    pub fn id(self) -> u8 {
        match self {
            Self::RemoveBeforeFlight => 1,
            Self::Deployed => 2,
            Self::DeployStart => 3,
            Self::InitialSafeStateComplete => 4,
            Self::FsooTimer => 5,
            Self::DetumblingComplete => 6,
            Self::BootChecksum => 7,
            Self::TotalBootFails => 8,
            Self::EmmcRecoveryNeeded => 9,
            Self::EmmcRecoveryAttempts => 10,
            Self::SdRestoreSlot => 11,
            Self::LastEmmcProbeOk => 12,
            Self::BootMedia => 13,
            Self::BootImageId => 14,
            Self::SolarPanelDeployed => 15,
            Self::UhfAntennaDeployed => 16,
            Self::VhfAntennaDeployed => 17,
            Self::AdcsCommissioningLogged => 18,
            Self::AdcsCommissioned => 19,
            Self::SunPointingConsent => 20,
            Self::NadirPointingConsent => 21,
            Self::PlatformCommissioned => 22,
            Self::GnssSystemError => 23,
            Self::Gyro0Fail => 24,
            Self::Gyro1Fail => 25,
            Self::Mag0Fail => 26,
            Self::Mag1Fail => 27,
            Self::ReactionWheelFail => 28,
            Self::SunSensorFail => 29,
            Self::EarthSensorFail => 30,
            Self::SunPointingAngleFault => 31,
            Self::SunPointingRateFault => 32,
            Self::NadirPointingAngleFault => 33,
            Self::NadirPointingRateFault => 34,
            Self::AntennaDeployAttempts => 35,
            Self::SolarPanelDeployAttempts => 36,
            Self::NadirPointAttempts => 37,
            Self::SunPointAttempts => 38,
            Self::CommsUplinkAes128Key => 39,
        }
    }"""
    if old_id not in text2:
        raise SystemExit("id() not found")
    text2 = text2.replace(old_id, new_id, 1)

    old_env = """            Self::BootChecksum => "boot_checksum",
            Self::SolarPanelDeployed => "solar_panel_deployed","""
    new_env = """            Self::BootChecksum => "boot_checksum",
            Self::TotalBootFails => "total_boot_fails",
            Self::EmmcRecoveryNeeded => "emmc_recovery_needed",
            Self::EmmcRecoveryAttempts => "emmc_recovery_attempts",
            Self::SdRestoreSlot => "sd_restore_slot",
            Self::LastEmmcProbeOk => "last_emmc_probe_ok",
            Self::BootMedia => "boot_media",
            Self::BootImageId => "boot_image_id",
            Self::SolarPanelDeployed => "solar_panel_deployed","""
    if old_env not in text2:
        raise SystemExit("env_name not found")
    text2 = text2.replace(old_env, new_env, 1)

    old_vt = """            Self::FsooTimer
            | Self::BootChecksum
            | Self::AntennaDeployAttempts
            | Self::SolarPanelDeployAttempts
            | Self::NadirPointAttempts
            | Self::SunPointAttempts => ValueType::U64,"""
    new_vt = """            Self::FsooTimer
            | Self::BootChecksum
            | Self::TotalBootFails
            | Self::EmmcRecoveryAttempts
            | Self::SdRestoreSlot
            | Self::BootMedia
            | Self::BootImageId
            | Self::AntennaDeployAttempts
            | Self::SolarPanelDeployAttempts
            | Self::NadirPointAttempts
            | Self::SunPointAttempts => ValueType::U64,"""
    if old_vt not in text2:
        raise SystemExit("value_type not found")
    text2 = text2.replace(old_vt, new_vt, 1)

    old_ms = """    pub boot_checksum: i64,
    pub adcs_commissioning_logged: bool,"""
    new_ms = """    pub boot_checksum: i64,
    pub total_boot_fails: i64,
    pub emmc_recovery_needed: bool,
    pub emmc_recovery_attempts: i64,
    pub sd_restore_slot: i64,
    pub last_emmc_probe_ok: bool,
    pub boot_media: i64,
    pub boot_image_id: i64,
    pub adcs_commissioning_logged: bool,"""
    if old_ms not in text2:
        raise SystemExit("MissionState fields not found")
    text2 = text2.replace(old_ms, new_ms, 1)

    old_set = """            (MissionKey::BootChecksum, MissionValue::U64(v)) => self.boot_checksum = *v as i64,
            (MissionKey::AdcsCommissioningLogged, MissionValue::Bool(v)) => {"""
    new_set = """            (MissionKey::BootChecksum, MissionValue::U64(v)) => self.boot_checksum = *v as i64,
            (MissionKey::TotalBootFails, MissionValue::U64(v)) => self.total_boot_fails = *v as i64,
            (MissionKey::EmmcRecoveryNeeded, MissionValue::Bool(v)) => {
                self.emmc_recovery_needed = *v
            },
            (MissionKey::EmmcRecoveryAttempts, MissionValue::U64(v)) => {
                self.emmc_recovery_attempts = *v as i64
            },
            (MissionKey::SdRestoreSlot, MissionValue::U64(v)) => self.sd_restore_slot = *v as i64,
            (MissionKey::LastEmmcProbeOk, MissionValue::Bool(v)) => self.last_emmc_probe_ok = *v,
            (MissionKey::BootMedia, MissionValue::U64(v)) => self.boot_media = *v as i64,
            (MissionKey::BootImageId, MissionValue::U64(v)) => self.boot_image_id = *v as i64,
            (MissionKey::AdcsCommissioningLogged, MissionValue::Bool(v)) => {"""
    if old_set not in text2:
        raise SystemExit("set() not found")
    text2 = text2.replace(old_set, new_set, 1)

    old_boot = """    pub fn is_boot_key(self) -> bool {
        self.is_boot_policy_key() || matches!(self, Self::BootChecksum)
    }"""
    new_boot = """    pub fn is_boot_key(self) -> bool {
        self.is_boot_policy_key() || matches!(self, Self::BootChecksum)
    }

    /// Recovery / ground-visible boot state — U-Boot may read/write; never classic env.
    pub fn is_recovery_key(self) -> bool {
        matches!(
            self,
            Self::TotalBootFails
                | Self::EmmcRecoveryNeeded
                | Self::EmmcRecoveryAttempts
                | Self::SdRestoreSlot
                | Self::LastEmmcProbeOk
                | Self::BootMedia
                | Self::BootImageId
        )
    }"""
    if old_boot not in text2:
        raise SystemExit("is_boot_key not found")
    text2 = text2.replace(old_boot, new_boot, 1)

    MODEL.write_text(text2, encoding="utf-8")
    print("model.rs updated OK")


if __name__ == "__main__":
    main()
