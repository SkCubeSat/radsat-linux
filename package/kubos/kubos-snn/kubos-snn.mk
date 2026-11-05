###############################################
#
# RADSAT SNN Service
#
###############################################

KUBOS_SNN_POST_BUILD_HOOKS += SNN_BUILD_CMDS
KUBOS_SNN_INSTALL_STAGING = YES
KUBOS_SNN_POST_INSTALL_STAGING_HOOKS += SNN_INSTALL_STAGING_CMDS
KUBOS_SNN_POST_INSTALL_TARGET_HOOKS += SNN_INSTALL_TARGET_CMDS
KUBOS_SNN_POST_INSTALL_TARGET_HOOKS += SNN_INSTALL_INIT_SYSV

define SNN_BUILD_CMDS
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	PKG_CONFIG_ALLOW_CROSS=1 CC=$(TARGET_CC) RUSTFLAGS="-Clinker=$(TARGET_CC)" cargo build --package snn-service --target $(CARGO_TARGET) --release
endef

# Generate the config settings for the service and add them to a fragment file
define SNN_INSTALL_STAGING_CMDS
	echo '[snn-service.addr]' > $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'ip = ${BR2_KUBOS_SNN_IP}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo -e 'port = ${BR2_KUBOS_SNN_PORT}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo '[snn-service]' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'uart_bus = ${BR2_KUBOS_SNN_UART_BUS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'uart_baud = ${BR2_KUBOS_SNN_UART_BAUD}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'read_line_timeout_ms = ${BR2_KUBOS_SNN_READ_LINE_TIMEOUT_MS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'ready_timeout_ms = ${BR2_KUBOS_SNN_READY_TIMEOUT_MS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'rx_ok_timeout_ms = ${BR2_KUBOS_SNN_RX_OK_TIMEOUT_MS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'processing_timeout_ms = ${BR2_KUBOS_SNN_PROCESSING_TIMEOUT_MS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'result_info_timeout_ms = ${BR2_KUBOS_SNN_RESULT_INFO_TIMEOUT_MS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'result_header_timeout_ms = ${BR2_KUBOS_SNN_RESULT_HEADER_TIMEOUT_MS}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'queue_capacity = ${BR2_KUBOS_SNN_QUEUE_CAPACITY}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo 'result_retention = ${BR2_KUBOS_SNN_RESULT_RETENTION}' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
	echo -e 'max_image_bytes = ${BR2_KUBOS_SNN_MAX_IMAGE_BYTES}\n' >> $(KUBOS_CONFIG_FRAGMENT_DIR)/snn-service
endef

# Install the application into the rootfs file system
define SNN_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/sbin
	PATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \
	$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/snn-service
	$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/snn-service \
		$(TARGET_DIR)/usr/sbin

	echo 'CHECK PROCESS kubos-snn PIDFILE /var/run/snn-service.pid' > $(TARGET_DIR)/etc/monit.d/kubos-snn.cfg
	echo '	START PROGRAM = "/etc/init.d/S${BR2_KUBOS_SNN_INIT_LVL}kubos-snn start"' >> $(TARGET_DIR)/etc/monit.d/kubos-snn.cfg
	echo '	IF ${BR2_KUBOS_SNN_RESTART_COUNT} RESTART WITHIN ${BR2_KUBOS_SNN_RESTART_CYCLES} CYCLES THEN TIMEOUT' \
	>> $(TARGET_DIR)/etc/monit.d/kubos-snn.cfg
endef

# Install the init script
define SNN_INSTALL_INIT_SYSV
	$(INSTALL) -D -m 0755 $(BR2_EXTERNAL_KUBOS_LINUX_PATH)/package/kubos/kubos-snn/kubos-snn \
		$(TARGET_DIR)/etc/init.d/S$(BR2_KUBOS_SNN_INIT_LVL)kubos-snn
endef

kubos-snn-cargoclean: kubos-snn-dirclean
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	cargo clean --package snn-service

$(eval $(virtual-package))
