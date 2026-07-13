###############################################
#
# RADSAT MRAM Service
#
###############################################

KUBOS_MRAM_POST_BUILD_HOOKS += MRAM_BUILD_CMDS
KUBOS_MRAM_INSTALL_STAGING = YES
KUBOS_MRAM_POST_INSTALL_STAGING_HOOKS += MRAM_INSTALL_STAGING_CMDS
KUBOS_MRAM_POST_INSTALL_TARGET_HOOKS += MRAM_INSTALL_TARGET_CMDS
KUBOS_MRAM_POST_INSTALL_TARGET_HOOKS += MRAM_INSTALL_INIT_SYSV

define MRAM_BUILD_CMDS
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	PKG_CONFIG_ALLOW_CROSS=1 \
	CC=$(TARGET_CC) \
	RUSTFLAGS="-Clinker=$(TARGET_CC)" \
	BINDGEN_EXTRA_CLANG_ARGS="--sysroot=$(STAGING_DIR)" \
	cargo build --package mram-service --features spidev --target $(CARGO_TARGET) --release
endef

# Generate the config settings for the service and add them to a fragment file
define MRAM_INSTALL_STAGING_CMDS
	echo '[mram-service.addr]' > $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
	echo 'ip = ${BR2_KUBOS_MRAM_IP}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
	echo -e 'port = ${BR2_KUBOS_MRAM_PORT}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
	echo '[mram-service]' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
	echo 'backend = "spidev"' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
	echo 'spi_device = ${BR2_KUBOS_MRAM_SPI_DEVICE}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
	echo 'spi_speed_hz = ${BR2_KUBOS_MRAM_SPI_SPEED_HZ}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
	echo -e 'spi_mode = ${BR2_KUBOS_MRAM_SPI_MODE}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/mram-service
endef

# Install the application into the rootfs file system
define MRAM_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/sbin
	PATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \
	$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/mram-service
	$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/mram-service \
		$(TARGET_DIR)/usr/sbin

	echo 'CHECK PROCESS kubos-mram PIDFILE /var/run/mram-service.pid' > $(TARGET_DIR)/etc/monit.d/kubos-mram.cfg
	echo '	START PROGRAM = "/etc/init.d/S${BR2_KUBOS_MRAM_INIT_LVL}kubos-mram start"' >> $(TARGET_DIR)/etc/monit.d/kubos-mram.cfg
	echo '	IF ${BR2_KUBOS_MRAM_RESTART_COUNT} RESTART WITHIN ${BR2_KUBOS_MRAM_RESTART_CYCLES} CYCLES THEN TIMEOUT' \
	>> $(TARGET_DIR)/etc/monit.d/kubos-mram.cfg
endef

# Install the init script
define MRAM_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(BR2_EXTERNAL_KUBOS_LINUX_PATH)/package/kubos/kubos-mram/kubos-mram \
		$(TARGET_DIR)/etc/init.d/S$(BR2_KUBOS_MRAM_INIT_LVL)kubos-mram
endef

kubos-mram-cargoclean: kubos-mram-dirclean
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	cargo clean --package mram-service

$(eval $(virtual-package))
