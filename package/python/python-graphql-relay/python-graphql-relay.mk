################################################################################
#
# python-graphql-relay
#
################################################################################

PYTHON_GRAPHQL_RELAY_VERSION = 3.2.0
PYTHON_GRAPHQL_RELAY_SOURCE = graphql-relay-$(PYTHON_GRAPHQL_RELAY_VERSION).tar.gz
PYTHON_GRAPHQL_RELAY_SITE = https://files.pythonhosted.org/packages/d1/13/98fbf8d67552f102488ffc16c6f559ce71ea15f6294728d33928ab5ff14d
PYTHON_GRAPHQL_RELAY_SETUP_TYPE = poetry
PYTHON_GRAPHQL_RELAY_LICENSE = MIT
PYTHON_GRAPHQL_RELAY_LICENSE_FILES = LICENSE

$(eval $(python-package))
