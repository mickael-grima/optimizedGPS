# -*- coding: utf-8 -*-
# !/bin/env python

from setuptools import setup
import os

dependency_links = [os.environ['GUROBI_HOME']] if 'GUROBI_HOME' in os.environ else []

setup(
    name='optimizedGPS',
    version='0.1',
    description='No description yet',
    url='https://github.com/mickael-grima/optimizedGPS.git',
    author='Mickael Grima',
    author_email='mickael.grima@tum.de',
    license='TUM',
    packages=[],
    dependency_links=dependency_links,
    install_requires=[
        'pyyaml',
        'networkx',
        'matplotlib',
        'requests',
        'osmapi'
    ],
    zip_safe=False
)
