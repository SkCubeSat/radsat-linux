###############################################
#
# RADSAT FRAM Service
#
###############################################

KUBOS_FRAM_POST_BUILD_HOOKS += FRAM_BUILD_CMDS
KUBOS_FRAM_INSTALL_STAGING = YES
KUBOS_FRAM_POST_INSTALL_STAGING_HOOKS += FRAM_INSTALL_STAGING_CMDS
KUBOS_FRAM_POST_INSTALL_TARGET_HOOKS += FRAM_INSTALL_TARGET_CMDS
KUBOS_FRAM_POST_INSTALL_TARGET_HOOKS += FRAM_INSTALL_INIT_SYSV

define FRAM_BUILD_CMDS
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	PKG_CONFIG_ALLOW_CROSS=1 CC=$(TARGET_CC) RUSTFLAGS="-Clinker=$(TARGET_CC)" cargo build --package fram-service --features i2c --target $(CARGO_TARGET) --release
endef

# Generate the config settings for the service and add them to a fragment file
define FRAM_INSTALL_STAGING_CMDS
	echo '[fram-service.addr]' > $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo 'ip = ${BR2_KUBOS_FRAM_IP}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo -e 'port = ${BR2_KUBOS_FRAM_PORT}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo '[fram-service]' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo 'backend = "i2c"' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo 'i2c_bus = ${BR2_KUBOS_FRAM_I2C_BUS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo 'i2c_addr = ${BR2_KUBOS_FRAM_I2C_ADDR}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo 'capacity_bytes = ${BR2_KUBOS_FRAM_CAPACITY_BYTES}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo 'address_width_bytes = ${BR2_KUBOS_FRAM_ADDRESS_WIDTH_BYTES}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo 'max_transfer_bytes = ${BR2_KUBOS_FRAM_MAX_TRANSFER_BYTES}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo 'fw_printenv = ${BR2_KUBOS_FRAM_FW_PRINTENV}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
	echo -e 'fw_setenv = ${BR2_KUBOS_FRAM_FW_SETENV}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/fram-service
endef

# Install the application into the rootfs file system
define FRAM_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/sbin
	PATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \
	$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/fram-service
	$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/fram-service \
		$(TARGET_DIR)/usr/sbin

	echo 'CHECK PROCESS kubos-fram PIDFILE /var/run/fram-service.pid' > $(TARGET_DIR)/etc/monit.d/kubos-fram.cfg
	echo '	START PROGRAM = "/etc/init.d/S${BR2_KUBOS_FRAM_INIT_LVL}kubos-fram start"' >> $(TARGET_DIR)/etc/monit.d/kubos-fram.cfg
	echo '	IF ${BR2_KUBOS_FRAM_RESTART_COUNT} RESTART WITHIN ${BR2_KUBOS_FRAM_RESTART_CYCLES} CYCLES THEN TIMEOUT' \
	>> $(TARGET_DIR)/etc/monit.d/kubos-fram.cfg
endef

# Install the init script
define FRAM_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(BR2_EXTERNAL_KUBOS_LINUX_PATH)/package/kubos/kubos-fram/kubos-fram \
		$(TARGET_DIR)/etc/init.d/S$(BR2_KUBOS_FRAM_INIT_LVL)kubos-fram
endef

kubos-fram-cargoclean: kubos-fram-dirclean
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	cargo clean --package fram-service

$(eval $(virtual-package))
