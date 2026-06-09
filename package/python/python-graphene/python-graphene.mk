################################################################################
#
# python-graphene
#
################################################################################

PYTHON_GRAPHENE_VERSION = 3.4.3
PYTHON_GRAPHENE_SOURCE = graphene-$(PYTHON_GRAPHENE_VERSION).tar.gz
PYTHON_GRAPHENE_SITE = https://files.pythonhosted.org/packages/cc/f6/bf62ff950c317ed03e77f3f6ddd7e34aaa98fe89d79ebd660c55343d8054
PYTHON_GRAPHENE_SETUP_TYPE = setuptools
PYTHON_GRAPHENE_LICENSE = MIT
PYTHON_GRAPHENE_LICENSE_FILES = LICENSE

$(eval $(python-package))
