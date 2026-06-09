#!/usr/bin/env python3

from setuptools import find_packages, setup


setup(
    name="kubos_app",
    version="1.22.0",
    description="Mission Application API for KubOS",
    packages=find_packages(),
    install_requires=["toml"],
)
