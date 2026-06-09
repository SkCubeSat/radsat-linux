#####################################################
#
# Kubos Python Service Library Installation
#
#####################################################
KUBOS_SERVICE_LIB_VERSION = $(KUBOS_VERSION)
KUBOS_SERVICE_LIB_LICENSE = Apache-2.0
KUBOS_SERVICE_LIB_LICENSE_FILES = LICENSE
KUBOS_SERVICE_LIB_SITE = $(KUBOS_SOURCE_DIR)/libs/kubos-service
KUBOS_SERVICE_LIB_SITE_METHOD = local
KUBOS_SERVICE_LIB_SETUP_TYPE = distutils
KUBOS_SERVICE_LIB_DEPENDENCIES = kubos

define KUBOS_SERVICE_LIB_ADD_LEGACY_SETUP
	$(INSTALL) -D -m 0644 $(KUBOS_SERVICE_LIB_PKGDIR)/setup.py \
		$(KUBOS_SERVICE_LIB_DIR)/setup.py
endef
KUBOS_SERVICE_LIB_POST_RSYNC_HOOKS += KUBOS_SERVICE_LIB_ADD_LEGACY_SETUP

$(eval $(python-package))
