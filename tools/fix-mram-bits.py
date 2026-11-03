#!/usr/bin/env python3
from pathlib import Path
import os

# Fix backend.rs - remove duplicate InvalidConfig and duplicate PayloadWindowBackend
path = Path("/mnt/c/Users/logan/CubeSAT/Software/services/hardware-services/mram-service/src/backend.rs")
text = path.read_text()
text = text.replace(
    """pub enum BackendError {
    #[error("{0}")]
    InvalidConfig(String),
    #[error("{0}")]
    InvalidConfig(String),
""",
    """pub enum BackendError {
    #[error("{0}")]
    InvalidConfig(String),
""",
)
marker = "/// Restricts littlefs/payload access"
idxs = []
start = 0
while True:
    i = text.find(marker, start)
    if i < 0:
        break
    idxs.append(i)
    start = i + 1
print("PayloadWindow markers", idxs)
if len(idxs) >= 2:
    text = text[: idxs[1]].rstrip() + "\n"
path.write_text(text)
print("backend lines", len(text.splitlines()))

# Fix fs BLOCK_COUNT
fs = Path("/mnt/c/Users/logan/CubeSAT/Software/services/hardware-services/mram-service/src/fs.rs")
ft = fs.read_text()
ft = ft.replace(
    "const BLOCK_COUNT: usize = rust_mram::CAPACITY_BYTES as usize / BLOCK_SIZE;",
    "const BLOCK_COUNT: usize = crate::env_region::PAYLOAD_CAPACITY_BYTES as usize / BLOCK_SIZE;",
)
fs.write_text(ft)
print("fs BLOCK_COUNT fixed")

# Rewrite package mk staging/install sections carefully
mk = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/package/kubos/kubos-mram/kubos-mram.mk")
mt = mk.read_text()
if "env_offset" not in mt:
    mt = mt.replace(
        "echo -e 'spi_mode = ${BR2_KUBOS_MRAM_SPI_MODE}\\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service\nendef\n",
        "echo 'spi_mode = ${BR2_KUBOS_MRAM_SPI_MODE}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service\n"
        "\techo 'env_offset = 514048' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service\n"
        "\techo -e 'env_size = 10240\\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service\n"
        "endef\n",
    )
if "mram-env-sync" not in mt:
    mt = mt.replace(
        "\t$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/mram-service \\\n"
        "\t\t$(TARGET_DIR)/usr/sbin\n\n"
        "\techo 'CHECK PROCESS kubos-mram",
        "\t$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/mram-service \\\n"
        "\t\t$(TARGET_DIR)/usr/sbin\n"
        "\tif [ -f $(KUBOS_CARGO_OUTPUT_DIR)/mram-env-sync ]; then \\\n"
        "\t\t$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/mram-env-sync ; \\\n"
        "\t\t$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/mram-env-sync \\\n"
        "\t\t\t$(TARGET_DIR)/usr/sbin ; \\\n"
        "\tfi\n\n"
        "\techo 'CHECK PROCESS kubos-mram",
    )
mk.write_text(mt)
print("mk env_offset", "env_offset" in mt, "mram-env-sync", "mram-env-sync" in mt)

for p in [
    "/mnt/c/Users/logan/CubeSAT/radsat-linux/board/kubos/beaglebone-black/overlay/usr/sbin/fram-get",
    "/mnt/c/Users/logan/CubeSAT/radsat-linux/board/kubos/beaglebone-black/overlay/usr/sbin/fram-set",
    "/mnt/c/Users/logan/CubeSAT/radsat-linux/board/kubos/beaglebone-black/overlay/etc/init.d/S79mram-env-sync",
]:
    os.chmod(p, 0o755)
print("chmod ok")
