###############################################
#
# Kubos Master Package
#
# This package downloads the Kubos repo,
# globally links all the modules, and sets the
# target for the subsequent Kubos child 
# packages
#
###############################################
KUBOS_LICENSE = Apache-2.0
KUBOS_LICENSE_FILES = LICENSE.txt
KUBOS_SITE = https://github.com/SkCubeSat/Software.git
KUBOS_SITE_METHOD = git
KUBOS_GIT_SUBMODULES = YES
KUBOS_OVERRIDE_SRCDIR_RSYNC_EXCLUSIONS = \
	--exclude target \
	--exclude .venv \
	--exclude docs/node_modules \
	--exclude docs/.next \
	--exclude docs/out
KUBOS_PROVIDES = kubos-mai400
KUBOS_INSTALL_STAGING = YES
KUBOS_TARGET_FINALIZE_HOOKS += KUBOS_CREATE_CONFIG

KUBOS_CONFIG_FRAGMENT_DIR = $(STAGING_DIR)/etc/kubos
KUBOS_CONFIG_FILE = $(TARGET_DIR)/etc/kubos-config.toml

KUBOS_VERSION = $(call qstrip,$(BR2_KUBOS_VERSION))

# Cargo metadata lives at the Software repository root, while the Kubos source
# remains under kubos/. These paths are shared by the legacy child packages.
KUBOS_SOURCE_DIR = $(KUBOS_DIR)/kubos
KUBOS_CARGO_TARGET_DIR = \
	$(if $(CARGO_TARGET_DIR),$(CARGO_TARGET_DIR),$(KUBOS_DIR)/target)
KUBOS_CARGO_OUTPUT_DIR = $(KUBOS_CARGO_TARGET_DIR)/$(CARGO_TARGET)/release

KUBOS_BR_TARGET = $(lastword $(subst /, ,$(dir $(BR2_LINUX_KERNEL_CUSTOM_DTS_PATH))))
ifeq ($(KUBOS_BR_TARGET),at91sam9g20isis)
	KUBOS_TARGET = kubos-linux-isis-gcc
	CARGO_TARGET = armv5te-unknown-linux-gnueabi
else ifeq ($(KUBOS_BR_TARGET),pumpkin-mbm2)
	KUBOS_TARGET = kubos-linux-pumpkin-mbm2-gcc
	CARGO_TARGET = armv7-unknown-linux-gnueabihf
else ifeq ($(KUBOS_BR_TARGET),beaglebone-black)
	KUBOS_TARGET = kubos-linux-beaglebone-gcc
	CARGO_TARGET = armv7-unknown-linux-gnueabihf
else
	KUBOS_TARGET = unknown
endif


define KUBOS_INSTALL_STAGING_CMDS
	mkdir -p $(KUBOS_CONFIG_FRAGMENT_DIR)
endef

define KUBOS_INSTALL_TARGET_CMDS
	mkdir -p $(TARGET_DIR)/etc/monit.d
endef

define KUBOS_CREATE_CONFIG
	# Collect all config fragment files into the final master config.toml file
	cat $(KUBOS_CONFIG_FRAGMENT_DIR)/* > $(KUBOS_CONFIG_FILE)
endef


kubos-deepclean:
	rm -fR $(BUILD_DIR)/kubos-*
	rm -f $(DL_DIR)/kubos-*
	rm -f $(TARGET_DIR)/etc/init.d/*kubos*
	rm -f $(TARGET_DIR)/etc/monit.d/kubos*
	rm -fR $(KUBOS_CONFIG_FRAGMENT_DIR)
	rm -fR $(BUILD_DIR)/../staging/etc/kubos
	rm -f $(KUBOS_CONFIG_FILE)

kubos-fullclean: kubos-clean-for-reconfigure kubos-dirclean
	rm -f $(KUBOS_DIR)/.stamp_downloaded
	rm -f $(DL_DIR)/kubos-$(KUBOS_VERSION).tar.gz
	rm -fR $(KUBOS_CONFIG_FRAGMENT_DIR)
	rm -fR $(BUILD_DIR)/../staging/etc/kubos
	rm -f $(KUBOS_CONFIG_FILE)

kubos-clean: kubos-clean-for-rebuild
	rm -fR $(KUBOS_DIR)/target

$(eval $(generic-package))
