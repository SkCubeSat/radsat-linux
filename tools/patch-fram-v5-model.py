#!/usr/bin/env python3
"""Patch Software fram-service model.rs for layout v5 + emmc_restore_offset."""
from __future__ import annotations

import re
from pathlib import Path

model_path = Path(r"c:\Users\logan\CubeSAT\Software\services\hardware-services\fram-service\src\model.rs")
text = model_path.read_text(encoding="utf-8")

mission_keys_new = """pub const MISSION_KEYS: [MissionKey; 40] = [
    // --- Boot policy (U-Boot may overlay; ids 1-6) + checksum trailer (7) ---
    MissionKey::RemoveBeforeFlight,
    MissionKey::Deployed,
    MissionKey::DeployStart,
    MissionKey::InitialSafeStateComplete,
    MissionKey::FsooTimer,
    MissionKey::DetumblingComplete,
    MissionKey::BootChecksum,
    // --- Recovery + ground-visible boot state (ids 8-14) ---
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
    // --- Resumable SD->eMMC restore progress ---
    MissionKey::EmmcRestoreOffset,
];"""

text, n = re.subn(
    r"pub const MISSION_KEYS: \[MissionKey; \d+\] = \[.*?\];",
    mission_keys_new,
    text,
    count=1,
    flags=re.S,
)
assert n == 1, f"MISSION_KEYS replace failed ({n})"

enum_new = """pub enum MissionKey {
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
    SolarPanelDeployed,
    UhfAntennaDeployed,
    VhfAntennaDeployed,
    AdcsCommissioningLogged,
    AdcsCommissioned,
    SunPointingConsent,
    NadirPointingConsent,
    PlatformCommissioned,
    GnssSystemError,
    Gyro0Fail,
    Gyro1Fail,
    Mag0Fail,
    Mag1Fail,
    ReactionWheelFail,
    SunSensorFail,
    EarthSensorFail,
    SunPointingAngleFault,
    SunPointingRateFault,
    NadirPointingAngleFault,
    NadirPointingRateFault,
    AntennaDeployAttempts,
    SolarPanelDeployAttempts,
    NadirPointAttempts,
    SunPointAttempts,
    CommsUplinkAes128Key,
    EmmcRestoreOffset,
}"""

text, n = re.subn(
    r"pub enum MissionKey \{.*?\}",
    enum_new,
    text,
    count=1,
    flags=re.S,
)
assert n == 1, f"enum replace failed ({n})"

id_new = """pub fn id(self) -> u8 {
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
            Self::EmmcRestoreOffset => 40,
        }
    }"""

text, n = re.subn(
    r"pub fn id\(self\) -> u8 \{.*?\}",
    id_new,
    text,
    count=1,
    flags=re.S,
)
assert n == 1, f"id replace failed ({n})"

env_new = """pub fn env_name(self) -> &'static str {
        match self {
            Self::RemoveBeforeFlight => "remove_before_flight",
            Self::Deployed => "deployed",
            Self::DeployStart => "deploy_start",
            Self::InitialSafeStateComplete => "initial_safe_state_complete",
            Self::FsooTimer => "fsoo_timer",
            Self::DetumblingComplete => "detumbling_complete",
            Self::BootChecksum => "boot_checksum",
            Self::TotalBootFails => "total_boot_fails",
            Self::EmmcRecoveryNeeded => "emmc_recovery_needed",
            Self::EmmcRecoveryAttempts => "emmc_recovery_attempts",
            Self::SdRestoreSlot => "sd_restore_slot",
            Self::LastEmmcProbeOk => "last_emmc_probe_ok",
            Self::BootMedia => "boot_media",
            Self::BootImageId => "boot_image_id",
            Self::SolarPanelDeployed => "solar_panel_deployed",
            Self::UhfAntennaDeployed => "uhf_antenna_deployed",
            Self::VhfAntennaDeployed => "vhf_antenna_deployed",
            Self::AdcsCommissioningLogged => "adcs_commissioning_logged",
            Self::AdcsCommissioned => "adcs_commissioned",
            Self::SunPointingConsent => "sun_pointing_consent",
            Self::NadirPointingConsent => "nadir_pointing_consent",
            Self::PlatformCommissioned => "platform_commissioned",
            Self::GnssSystemError => "gnss_system_error",
            Self::Gyro0Fail => "gyro0_fail",
            Self::Gyro1Fail => "gyro1_fail",
            Self::Mag0Fail => "mag0_fail",
            Self::Mag1Fail => "mag1_fail",
            Self::ReactionWheelFail => "reaction_wheel_fail",
            Self::SunSensorFail => "sun_sensor_fail",
            Self::EarthSensorFail => "earth_sensor_fail",
            Self::SunPointingAngleFault => "sun_pointing_angle_fault",
            Self::SunPointingRateFault => "sun_pointing_rate_fault",
            Self::NadirPointingAngleFault => "nadir_pointing_angle_fault",
            Self::NadirPointingRateFault => "nadir_pointing_rate_fault",
            Self::AntennaDeployAttempts => "antenna_deploy_attempts",
            Self::SolarPanelDeployAttempts => "solar_panel_deploy_attempts",
            Self::NadirPointAttempts => "nadir_point_attempts",
            Self::SunPointAttempts => "sun_point_attempts",
            Self::CommsUplinkAes128Key => "comms_uplink_aes128_key",
            Self::EmmcRestoreOffset => "emmc_restore_offset",
        }
    }"""

text, n = re.subn(
    r"pub fn env_name\(self\) -> &'static str \{.*?\}",
    env_new,
    text,
    count=1,
    flags=re.S,
)
assert n == 1, f"env_name replace failed ({n})"

decl_new = """pub fn declared_value_type(self) -> ValueType {
        match self {
            Self::DeployStart => ValueType::Timestamp,
            Self::FsooTimer
            | Self::BootChecksum
            | Self::TotalBootFails
            | Self::EmmcRecoveryAttempts
            | Self::SdRestoreSlot
            | Self::BootMedia
            | Self::BootImageId
            | Self::EmmcRestoreOffset
            | Self::AntennaDeployAttempts
            | Self::SolarPanelDeployAttempts
            | Self::NadirPointAttempts
            | Self::SunPointAttempts => ValueType::U64,
            Self::CommsUplinkAes128Key => ValueType::Bytes,
            _ => ValueType::Bool,
        }
    }"""

text, n = re.subn(
    r"pub fn declared_value_type\(self\) -> ValueType \{.*?\}",
    decl_new,
    text,
    count=1,
    flags=re.S,
)
assert n == 1, f"declared_value_type replace failed ({n})"

old_struct = """pub struct MissionState {
    pub remove_before_flight: bool,
    pub deployed: bool,
    pub deploy_start: Option<i64>,
    pub solar_panel_deployed: bool,
    pub uhf_antenna_deployed: bool,
    pub vhf_antenna_deployed: bool,
    pub initial_safe_state_complete: bool,
    pub detumbling_complete: bool,
    pub fsoo_timer: i64,
    pub boot_checksum: i64,
    pub adcs_commissioning_logged: bool,"""

new_struct = """pub struct MissionState {
    pub remove_before_flight: bool,
    pub deployed: bool,
    pub deploy_start: Option<i64>,
    pub solar_panel_deployed: bool,
    pub uhf_antenna_deployed: bool,
    pub vhf_antenna_deployed: bool,
    pub initial_safe_state_complete: bool,
    pub detumbling_complete: bool,
    pub fsoo_timer: i64,
    pub boot_checksum: i64,
    pub total_boot_fails: i64,
    pub emmc_recovery_needed: bool,
    pub emmc_recovery_attempts: i64,
    pub sd_restore_slot: i64,
    pub last_emmc_probe_ok: bool,
    pub boot_media: i64,
    pub boot_image_id: i64,
    pub emmc_restore_offset: i64,
    pub adcs_commissioning_logged: bool,"""

if old_struct not in text:
    raise SystemExit("MissionState struct needle missing")
text = text.replace(old_struct, new_struct, 1)

needle = """            (MissionKey::BootChecksum, MissionValue::U64(v)) => self.boot_checksum = *v as i64,
            (MissionKey::AdcsCommissioningLogged, MissionValue::Bool(v)) => {
                self.adcs_commissioning_logged = *v
            }"""

insert = """            (MissionKey::BootChecksum, MissionValue::U64(v)) => self.boot_checksum = *v as i64,
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
            (MissionKey::EmmcRestoreOffset, MissionValue::U64(v)) => {
                self.emmc_restore_offset = *v as i64
            },
            (MissionKey::AdcsCommissioningLogged, MissionValue::Bool(v)) => {
                self.adcs_commissioning_logged = *v
            }"""

if needle not in text:
    raise SystemExit("MissionState::set needle missing")
text = text.replace(needle, insert, 1)

model_path.write_text(text, encoding="utf-8", newline="\n")
print("model.rs updated OK")
