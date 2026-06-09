################################################################################
#
# python-graphql-server
#
################################################################################

PYTHON_GRAPHQL_SERVER_VERSION = 3.0.0
PYTHON_GRAPHQL_SERVER_SOURCE = graphql_server-$(PYTHON_GRAPHQL_SERVER_VERSION).tar.gz
PYTHON_GRAPHQL_SERVER_SITE = https://files.pythonhosted.org/packages/d1/c1/d33490424627c99a760059012b3f7524292f799db432757370a6a8071ce0
PYTHON_GRAPHQL_SERVER_LICENSE = MIT
PYTHON_GRAPHQL_SERVER_DEPENDENCIES = python3 python-graphql-core

# graphql-server 3.0.0 uses uv_build, which is not available in Buildroot
# 2025.02. The release is pure Python, so install its package tree directly.
define PYTHON_GRAPHQL_SERVER_INSTALL_TARGET_CMDS
	$(INSTALL) -d \
		$(TARGET_DIR)/usr/lib/python$(PYTHON3_VERSION_MAJOR)/site-packages
	cp -a $(@D)/src/graphql_server \
		$(TARGET_DIR)/usr/lib/python$(PYTHON3_VERSION_MAJOR)/site-packages/
endef

$(eval $(generic-package))
