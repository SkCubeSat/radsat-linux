###############################################
#
# RADSAT Star RISC Service
#
###############################################

KUBOS_STAR_RISC_POST_BUILD_HOOKS += STAR_RISC_BUILD_CMDS
KUBOS_STAR_RISC_INSTALL_STAGING = YES
KUBOS_STAR_RISC_POST_INSTALL_STAGING_HOOKS += STAR_RISC_INSTALL_STAGING_CMDS
KUBOS_STAR_RISC_POST_INSTALL_TARGET_HOOKS += STAR_RISC_INSTALL_TARGET_CMDS
KUBOS_STAR_RISC_POST_INSTALL_TARGET_HOOKS += STAR_RISC_INSTALL_INIT_SYSV

define STAR_RISC_BUILD_CMDS
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	PKG_CONFIG_ALLOW_CROSS=1 CC=$(TARGET_CC) RUSTFLAGS="-Clinker=$(TARGET_CC)" cargo build --package star-risc --target $(CARGO_TARGET) --release
endef

# Generate the config settings for the service and add them to a fragment file
define STAR_RISC_INSTALL_STAGING_CMDS
	echo '[star-risc.addr]' > $(KUBOS_CONFIG_FRAGMENT_DIR)/star-risc
	echo 'ip = ${BR2_KUBOS_STAR_RISC_IP}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/star-risc
	echo -e 'port = ${BR2_KUBOS_STAR_RISC_PORT}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/star-risc
	echo '[star-risc]' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/star-risc
	echo 'uart_bus = ${BR2_KUBOS_STAR_RISC_UART_BUS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/star-risc
	echo -e 'uart_baud = ${BR2_KUBOS_STAR_RISC_UART_BAUD}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/star-risc
endef

# Install the application into the rootfs file system
define STAR_RISC_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/sbin
	PATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \
	$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/star-risc
	$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/star-risc \
		$(TARGET_DIR)/usr/sbin

	echo 'CHECK PROCESS kubos-star-risc PIDFILE /var/run/star-risc.pid' > $(TARGET_DIR)/etc/monit.d/kubos-star-risc.cfg
	echo '	START PROGRAM = "/etc/init.d/S${BR2_KUBOS_STAR_RISC_INIT_LVL}kubos-star-risc start"' >> $(TARGET_DIR)/etc/monit.d/kubos-star-risc.cfg
	echo '	IF ${BR2_KUBOS_STAR_RISC_RESTART_COUNT} RESTART WITHIN ${BR2_KUBOS_STAR_RISC_RESTART_CYCLES} CYCLES THEN TIMEOUT' \
	>> $(TARGET_DIR)/etc/monit.d/kubos-star-risc.cfg
endef

# Install the init script
define STAR_RISC_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(BR2_EXTERNAL_KUBOS_LINUX_PATH)/package/kubos/kubos-star-risc/kubos-star-risc \
		$(TARGET_DIR)/etc/init.d/S$(BR2_KUBOS_STAR_RISC_INIT_LVL)kubos-star-risc
endef

kubos-star-risc-cargoclean: kubos-star-risc-dirclean
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	cargo clean --package star-risc

$(eval $(virtual-package))
