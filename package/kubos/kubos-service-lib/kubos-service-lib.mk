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
KUBOS_SERVICE_LIB_SETUP_TYPE = hatch
KUBOS_SERVICE_LIB_DEPENDENCIES = kubos

$(eval $(python-package))
