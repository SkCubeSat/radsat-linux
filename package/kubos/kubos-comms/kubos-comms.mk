###############################################
#
# RADSAT NXTRX4 Communications Service
#
###############################################

KUBOS_COMMS_POST_BUILD_HOOKS += COMMS_BUILD_CMDS
KUBOS_COMMS_INSTALL_STAGING = YES
KUBOS_COMMS_POST_INSTALL_STAGING_HOOKS += COMMS_INSTALL_STAGING_CMDS
KUBOS_COMMS_POST_INSTALL_TARGET_HOOKS += COMMS_INSTALL_TARGET_CMDS
KUBOS_COMMS_POST_INSTALL_TARGET_HOOKS += COMMS_INSTALL_INIT_SYSV

define COMMS_BUILD_CMDS
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	PKG_CONFIG_ALLOW_CROSS=1 CC=$(TARGET_CC) RUSTFLAGS="-Clinker=$(TARGET_CC)" cargo build --package comms-services --target $(CARGO_TARGET) --release
endef

# Generate the config settings for the service and add them to a fragment file
define COMMS_INSTALL_STAGING_CMDS
	$(INSTALL) -D -m 0644 $(BR2_EXTERNAL_KUBOS_LINUX_PATH)/package/kubos/kubos-comms/comms-services \
		$(KUBOS_CONFIG_FRAGMENT_DIR)/comms-services
	sed -i '0,/^port = /s/^port = .*/port = ${BR2_KUBOS_COMMS_PORT}/' $(KUBOS_CONFIG_FRAGMENT_DIR)/comms-services
endef

# Install the application into the rootfs file system
define COMMS_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/sbin
	PATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \
	$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/comms-services
	$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/comms-services \
		$(TARGET_DIR)/usr/sbin

	echo 'CHECK PROCESS kubos-comms PIDFILE /var/run/comms-services.pid' > $(TARGET_DIR)/etc/monit.d/kubos-comms.cfg
	echo '	START PROGRAM = "/etc/init.d/S${BR2_KUBOS_COMMS_INIT_LVL}kubos-comms start"' >> $(TARGET_DIR)/etc/monit.d/kubos-comms.cfg
	echo '	IF ${BR2_KUBOS_COMMS_RESTART_COUNT} RESTART WITHIN ${BR2_KUBOS_COMMS_RESTART_CYCLES} CYCLES THEN TIMEOUT' \
	>> $(TARGET_DIR)/etc/monit.d/kubos-comms.cfg
endef

# Install the init script
define COMMS_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(BR2_EXTERNAL_KUBOS_LINUX_PATH)/package/kubos/kubos-comms/kubos-comms \
		$(TARGET_DIR)/etc/init.d/S$(BR2_KUBOS_COMMS_INIT_LVL)kubos-comms
endef

kubos-comms-cargoclean: kubos-comms-dirclean
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	cargo clean --package comms-services

$(eval $(virtual-package))
