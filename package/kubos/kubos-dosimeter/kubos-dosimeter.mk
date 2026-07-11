###############################################
#
# RADSAT Dosimeter Service
#
###############################################

KUBOS_DOSIMETER_POST_BUILD_HOOKS += DOSIMETER_BUILD_CMDS
KUBOS_DOSIMETER_INSTALL_STAGING = YES
KUBOS_DOSIMETER_POST_INSTALL_STAGING_HOOKS += DOSIMETER_INSTALL_STAGING_CMDS
KUBOS_DOSIMETER_POST_INSTALL_TARGET_HOOKS += DOSIMETER_INSTALL_TARGET_CMDS
KUBOS_DOSIMETER_POST_INSTALL_TARGET_HOOKS += DOSIMETER_INSTALL_INIT_SYSV

define DOSIMETER_BUILD_CMDS
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	PKG_CONFIG_ALLOW_CROSS=1 CC=$(TARGET_CC) RUSTFLAGS="-Clinker=$(TARGET_CC)" cargo build --package dosimeter --target $(CARGO_TARGET) --release
endef

# Generate the config settings for the service and add them to a fragment file
define DOSIMETER_INSTALL_STAGING_CMDS
	echo '[dosimeter.addr]' > $(KUBOS_CONFIG_FRAGMENT_DIR)/dosimeter
	echo 'ip = ${BR2_KUBOS_DOSIMETER_IP}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/dosimeter
	echo -e 'port = ${BR2_KUBOS_DOSIMETER_PORT}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/dosimeter
	echo '[dosimeter]' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/dosimeter
	echo 'i2c_bus = ${BR2_KUBOS_DOSIMETER_I2C_BUS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/dosimeter
	echo -e 'device_addr = ${BR2_KUBOS_DOSIMETER_DEVICE_ADDR}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/dosimeter
endef

# Install the application into the rootfs file system
define DOSIMETER_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/sbin
	PATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \
	$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/dosimeter
	$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/dosimeter \
		$(TARGET_DIR)/usr/sbin

	echo 'CHECK PROCESS kubos-dosimeter PIDFILE /var/run/dosimeter.pid' > $(TARGET_DIR)/etc/monit.d/kubos-dosimeter.cfg
	echo '	START PROGRAM = "/etc/init.d/S${BR2_KUBOS_DOSIMETER_INIT_LVL}kubos-dosimeter start"' >> $(TARGET_DIR)/etc/monit.d/kubos-dosimeter.cfg
	echo '	IF ${BR2_KUBOS_DOSIMETER_RESTART_COUNT} RESTART WITHIN ${BR2_KUBOS_DOSIMETER_RESTART_CYCLES} CYCLES THEN TIMEOUT' \
	>> $(TARGET_DIR)/etc/monit.d/kubos-dosimeter.cfg
endef

# Install the init script
define DOSIMETER_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(BR2_EXTERNAL_KUBOS_LINUX_PATH)/package/kubos/kubos-dosimeter/kubos-dosimeter \
		$(TARGET_DIR)/etc/init.d/S$(BR2_KUBOS_DOSIMETER_INIT_LVL)kubos-dosimeter
endef

kubos-dosimeter-cargoclean: kubos-dosimeter-dirclean
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	cargo clean --package dosimeter

$(eval $(virtual-package))
