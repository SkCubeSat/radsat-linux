#####################################################
#
# Kubos Python I2C HAL Installation
#
#####################################################
KUBOS_HAL_I2C_VERSION = $(KUBOS_VERSION)
KUBOS_HAL_I2C_LICENSE = Apache-2.0
KUBOS_HAL_I2C_LICENSE_FILES = LICENSE
KUBOS_HAL_I2C_SITE = $(KUBOS_SOURCE_DIR)/hal/python-hal/i2c
KUBOS_HAL_I2C_SITE_METHOD = local
KUBOS_HAL_I2C_SETUP_TYPE = setuptools
KUBOS_HAL_I2C_DEPENDENCIES = kubos

define KUBOS_HAL_I2C_ADD_LEGACY_SETUP
	$(INSTALL) -D -m 0644 $(KUBOS_HAL_I2C_PKGDIR)/setup.py \
		$(KUBOS_HAL_I2C_DIR)/setup.py
endef
KUBOS_HAL_I2C_POST_RSYNC_HOOKS += KUBOS_HAL_I2C_ADD_LEGACY_SETUP

$(eval $(python-package))
