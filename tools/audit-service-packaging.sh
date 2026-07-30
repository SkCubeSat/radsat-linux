#!/usr/bin/env bash

# Audit relationships between packaged Kubos service binaries, SysV init
# scripts, and Monit configurations. Findings are advisory: warnings are
# reported to GitHub Actions, but they do not make this script fail.

set -uo pipefail

if [[ $# -ne 2 ]]; then
    echo "Usage: $0 <buildroot-target-dir> <report-path>" >&2
    exit 2
fi

rootfs="${1%/}"
report="$2"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
packages_dir="${script_dir}/../package/kubos"

if [[ ! -d "${rootfs}" ]]; then
    echo "Buildroot target directory does not exist: ${rootfs}" >&2
    exit 2
fi

if [[ ! -d "${packages_dir}" ]]; then
    echo "Kubos package directory does not exist: ${packages_dir}" >&2
    exit 2
fi

mkdir -p "$(dirname "${report}")"

warnings=0
passes=0
infos=0
service_count=0
monit_count=0
package_binary_count=0

{
    echo "# Kubos service packaging audit"
    echo
    echo "- Root filesystem: \`${rootfs}\`"
    echo "- Package recipes: \`${packages_dir}\`"
    echo
    echo "## Findings"
    echo
} > "${report}"

annotation_escape() {
    local value="$1"
    value="${value//'%'/'%25'}"
    value="${value//$'\r'/'%0D'}"
    value="${value//$'\n'/'%0A'}"
    printf '%s' "${value}"
}

record_pass() {
    local message="$1"
    ((passes += 1))
    echo "PASS: ${message}"
    echo "- PASS: ${message}" >> "${report}"
}

record_info() {
    local message="$1"
    ((infos += 1))
    echo "INFO: ${message}"
    echo "- INFO: ${message}" >> "${report}"
}

record_warning() {
    local message="$1"
    local escaped
    ((warnings += 1))
    echo "WARNING: ${message}"
    echo "- WARNING: ${message}" >> "${report}"

    if [[ "${GITHUB_ACTIONS:-false}" == "true" ]]; then
        escaped="$(annotation_escape "${message}")"
        echo "::warning title=Kubos service packaging audit::${escaped}"
    fi
}

strip_quotes() {
    local value="$1"
    value="${value#\"}"
    value="${value%\"}"
    value="${value#\'}"
    value="${value%\'}"
    printf '%s' "${value}"
}

expand_service_name() {
    local value="$1"
    local service_name="$2"
    value="${value//\$\{NAME\}/${service_name}}"
    printf '%s' "${value}"
}

declare -A init_for_binary=()
declare -A pid_for_init=()
declare -A monit_for_init=()

shopt -s nullglob
init_scripts=("${rootfs}"/etc/init.d/S??kubos-*)
monit_configs=("${rootfs}"/etc/monit.d/*.cfg)

for config_path in "${monit_configs[@]}"; do
    ((monit_count += 1))
done

for init_path in "${init_scripts[@]}"; do
    init_name="$(basename "${init_path}")"
    service_name="$(
        sed -n 's/^[[:space:]]*NAME=//p' "${init_path}" | head -n 1
    )"
    service_name="$(strip_quotes "${service_name}")"
    program="$(
        sed -n 's/^[[:space:]]*PROG=//p' "${init_path}" | head -n 1
    )"
    program="$(strip_quotes "${program}")"
    pidfile="$(
        sed -n 's/^[[:space:]]*PID=//p' "${init_path}" | head -n 1
    )"
    pidfile="$(strip_quotes "${pidfile}")"

    matching_monit=()
    for config_path in "${monit_configs[@]}"; do
        if grep -Fq \
            "START PROGRAM = \"/etc/init.d/${init_name} start\"" \
            "${config_path}"; then
            matching_monit+=("${config_path}")
        fi
    done

    if [[ "${init_name}" == "S99kubos-verify" ]]; then
        record_info \
            "${init_name} is an allowlisted one-shot boot-finalization script; Monit is not required"
        continue
    fi

    ((service_count += 1))

    if [[ -z "${service_name}" ]]; then
        record_warning \
            "${init_name} does not declare NAME, so its packaged service executable and PID file cannot be audited"
    else
        if [[ -n "${init_for_binary[${service_name}]:-}" ]]; then
            record_warning \
                "${service_name} is referenced by more than one init script: ${init_for_binary[${service_name}]} and ${init_name}"
        else
            init_for_binary["${service_name}"]="${init_name}"
        fi

        if [[ -z "${program}" ]]; then
            record_warning \
                "${init_name} does not declare PROG for service ${service_name}"
        else
            program="$(expand_service_name "${program}" "${service_name}")"
            if [[ "${program}" != /* ]]; then
                record_warning \
                    "${init_name} declares a non-absolute program path: ${program}"
            elif [[ ! -x "${rootfs}${program}" ]]; then
                record_warning \
                    "${init_name} references missing or non-executable program ${program}"
            else
                record_pass \
                    "${init_name} references executable service ${program}"
            fi
        fi

        if [[ -z "${pidfile}" ]]; then
            record_warning \
                "${init_name} does not declare PID for service ${service_name}"
        else
            pidfile="$(expand_service_name "${pidfile}" "${service_name}")"
            pid_for_init["${init_name}"]="${pidfile}"
        fi
    fi

    if [[ ${#matching_monit[@]} -eq 0 ]]; then
        record_warning \
            "${init_name} has no Monit configuration whose START PROGRAM references it"
    elif [[ ${#matching_monit[@]} -gt 1 ]]; then
        record_warning \
            "${init_name} is referenced by multiple Monit configurations"
    else
        config_name="$(basename "${matching_monit[0]}")"
        monit_for_init["${init_name}"]="${config_name}"
        record_pass \
            "${init_name} is supervised by ${config_name}"

        if [[ -n "${pid_for_init[${init_name}]:-}" ]] &&
            ! grep -Fq \
                "PIDFILE ${pid_for_init[${init_name}]}" \
                "${matching_monit[0]}"; then
            record_warning \
                "${config_name} PIDFILE does not match ${init_name} (${pid_for_init[${init_name}]})"
        fi
    fi
done

for config_path in "${monit_configs[@]}"; do
    config_name="$(basename "${config_path}")"
    start_program="$(
        sed -n \
            's/.*START PROGRAM[[:space:]]*=[[:space:]]*"\([^"]*\)[[:space:]]start".*/\1/p' \
            "${config_path}" | head -n 1
    )"
    pidfile="$(
        sed -n \
            's/.*[[:space:]]PIDFILE[[:space:]]\([^[:space:]]*\).*/\1/p' \
            "${config_path}" | head -n 1
    )"

    if ! grep -Eq '^[[:space:]]*CHECK[[:space:]]+PROCESS[[:space:]]+' \
        "${config_path}"; then
        record_warning \
            "${config_name} does not contain a CHECK PROCESS declaration"
    fi

    if [[ -z "${pidfile}" ]]; then
        record_warning \
            "${config_name} does not declare a PIDFILE"
    fi

    if [[ -z "${start_program}" ]]; then
        record_warning \
            "${config_name} does not declare a START PROGRAM ending in 'start'"
        continue
    fi

    if [[ "${start_program}" != /etc/init.d/* ]]; then
        record_warning \
            "${config_name} starts ${start_program}, which is outside /etc/init.d"
    elif [[ ! -x "${rootfs}${start_program}" ]]; then
        record_warning \
            "${config_name} references missing or non-executable init script ${start_program}"
    fi
done

while IFS= read -r recipe; do
    while IFS= read -r binary; do
        [[ -z "${binary}" ]] && continue

        if [[ -x "${rootfs}/usr/sbin/${binary}" ]]; then
            ((package_binary_count += 1))
            recipe_name="${recipe#"${packages_dir}/"}"

            if [[ -z "${init_for_binary[${binary}]:-}" ]]; then
                record_warning \
                    "${recipe_name} installs service /usr/sbin/${binary}, but no Kubos init script declares NAME=${binary}"
            else
                record_pass \
                    "${recipe_name} service ${binary} is linked to ${init_for_binary[${binary}]}"
            fi
        elif [[ -x "${rootfs}/usr/bin/${binary}" ]]; then
            ((package_binary_count += 1))
            recipe_name="${recipe#"${packages_dir}/"}"
            record_info \
                "${recipe_name} installs operator tool /usr/bin/${binary}; Monit is not required"
        fi
    done < <(
        sed -n \
            's@.*$(KUBOS_CARGO_OUTPUT_DIR)/\([A-Za-z0-9._-]*\).*@\1@p' \
            "${recipe}" | sort -u
    )
done < <(find "${packages_dir}" -type f -name '*.mk' | sort)

{
    echo
    echo "## Summary"
    echo
    echo "- Kubos service init scripts audited: ${service_count}"
    echo "- Monit configurations audited: ${monit_count}"
    echo "- Installed Cargo package binaries audited: ${package_binary_count}"
    echo "- Passes: ${passes}"
    echo "- Informational findings: ${infos}"
    echo "- Warnings: ${warnings}"
    echo
    echo "This audit is advisory. Warnings do not block image publication."
} >> "${report}"

echo
echo "Audit report: ${report}"
echo "Audit summary: ${passes} pass(es), ${infos} info item(s), ${warnings} warning(s)"

exit 0
