###############################################
#
# RADSAT Cube ADCS Service
#
###############################################

KUBOS_CUBE_ADCS_POST_BUILD_HOOKS += CUBE_ADCS_BUILD_CMDS
KUBOS_CUBE_ADCS_INSTALL_STAGING = YES
KUBOS_CUBE_ADCS_POST_INSTALL_STAGING_HOOKS += CUBE_ADCS_INSTALL_STAGING_CMDS
KUBOS_CUBE_ADCS_POST_INSTALL_TARGET_HOOKS += CUBE_ADCS_INSTALL_TARGET_CMDS
KUBOS_CUBE_ADCS_POST_INSTALL_TARGET_HOOKS += CUBE_ADCS_INSTALL_INIT_SYSV

define CUBE_ADCS_BUILD_CMDS
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	PKG_CONFIG_ALLOW_CROSS=1 CC=$(TARGET_CC) RUSTFLAGS="-Clinker=$(TARGET_CC)" cargo build --package cube-adcs-service --target $(CARGO_TARGET) --release
endef

# Generate the config settings for the service and add them to a fragment file
define CUBE_ADCS_INSTALL_STAGING_CMDS
	echo '[cube-adcs-service.addr]' > $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
	echo 'ip = ${BR2_KUBOS_CUBE_ADCS_IP}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
	echo -e 'port = ${BR2_KUBOS_CUBE_ADCS_PORT}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
	echo '[cube-adcs-service]' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
	echo 'can_interface = ${BR2_KUBOS_CUBE_ADCS_CAN_INTERFACE}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
	echo 'can_bitrate = ${BR2_KUBOS_CUBE_ADCS_CAN_BITRATE}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
	echo 'source_address = ${BR2_KUBOS_CUBE_ADCS_SOURCE_ADDRESS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
	echo 'destination_address = ${BR2_KUBOS_CUBE_ADCS_DESTINATION_ADDRESS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
	echo -e 'timeout_ms = ${BR2_KUBOS_CUBE_ADCS_TIMEOUT_MS}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/cube-adcs-service
endef

# Install the application into the rootfs file system
define CUBE_ADCS_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/sbin
	PATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \
	$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/cube-adcs-service
	$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/cube-adcs-service \
		$(TARGET_DIR)/usr/sbin

	echo 'CHECK PROCESS kubos-cube-adcs PIDFILE /var/run/cube-adcs-service.pid' > $(TARGET_DIR)/etc/monit.d/kubos-cube-adcs.cfg
	echo '	START PROGRAM = "/etc/init.d/S${BR2_KUBOS_CUBE_ADCS_INIT_LVL}kubos-cube-adcs start"' >> $(TARGET_DIR)/etc/monit.d/kubos-cube-adcs.cfg
	echo '	IF ${BR2_KUBOS_CUBE_ADCS_RESTART_COUNT} RESTART WITHIN ${BR2_KUBOS_CUBE_ADCS_RESTART_CYCLES} CYCLES THEN TIMEOUT' \
	>> $(TARGET_DIR)/etc/monit.d/kubos-cube-adcs.cfg
endef

# Install the init script
define CUBE_ADCS_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(BR2_EXTERNAL_KUBOS_LINUX_PATH)/package/kubos/kubos-cube-adcs/kubos-cube-adcs \
		$(TARGET_DIR)/etc/init.d/S$(BR2_KUBOS_CUBE_ADCS_INIT_LVL)kubos-cube-adcs
endef

kubos-cube-adcs-cargoclean: kubos-cube-adcs-dirclean
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	cargo clean --package cube-adcs-service

$(eval $(virtual-package))
