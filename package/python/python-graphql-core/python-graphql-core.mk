################################################################################
#
# python-graphql-core
#
################################################################################

PYTHON_GRAPHQL_CORE_VERSION = 3.2.7
PYTHON_GRAPHQL_CORE_SOURCE = graphql_core-$(PYTHON_GRAPHQL_CORE_VERSION).tar.gz
PYTHON_GRAPHQL_CORE_SITE = https://files.pythonhosted.org/packages/ac/9b/037a640a2983b09aed4a823f9cf1729e6d780b0671f854efa4727a7affbe
PYTHON_GRAPHQL_CORE_SETUP_TYPE = poetry
PYTHON_GRAPHQL_CORE_LICENSE = MIT
PYTHON_GRAPHQL_CORE_LICENSE_FILES = LICENSE

$(eval $(python-package))
