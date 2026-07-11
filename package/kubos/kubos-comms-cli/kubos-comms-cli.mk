###############################################
#
# RADSAT Comms CLI
#
###############################################

KUBOS_COMMS_CLI_POST_BUILD_HOOKS += COMMS_CLI_BUILD_CMDS
KUBOS_COMMS_CLI_POST_INSTALL_TARGET_HOOKS += COMMS_CLI_INSTALL_TARGET_CMDS

define COMMS_CLI_BUILD_CMDS
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	PKG_CONFIG_ALLOW_CROSS=1 CC=$(TARGET_CC) RUSTFLAGS="-Clinker=$(TARGET_CC)" cargo build --package comms-cli --target $(CARGO_TARGET) --release
endef

# Install the CLI into the rootfs file system. This is an operator tool, not a
# daemon, so there is no init script, monit config, or config fragment.
define COMMS_CLI_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/usr/bin
	PATH=$(PATH):~/.cargo/bin:$(HOST_DIR)/bin && \
	$(TARGET_STRIP) $(KUBOS_CARGO_OUTPUT_DIR)/comms-cli
	$(INSTALL) -D -m 0755 $(KUBOS_CARGO_OUTPUT_DIR)/comms-cli \
		$(TARGET_DIR)/usr/bin
endef

kubos-comms-cli-cargoclean: kubos-comms-cli-dirclean
	cd $(KUBOS_DIR) && \
	PATH=$(PATH):~/.cargo/bin && \
	cargo clean --package comms-cli

$(eval $(virtual-package))
