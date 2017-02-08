# -*- coding: utf-8 -*-
# !/bin/env python

from setuptools import setup, find_packages
import os

dependency_links = [os.environ['GUROBI_HOME']] if 'GUROBI_HOME' in os.environ else []

setup(
    name='optimizedGPS',
    version='1.0.0',
    description='An optimized GPS using the Operation Research theory for optimizing the path of several drivers.'
                'It includes a package for extracting data (see optimizedGPS/data), a structure folder for building'
                'graphs and including drivers, and a folder problems for optimization',
    long_description=open("README.md").read(),
    url='https://github.com/mickael-grima/optimizedGPS.git',
    author='Mickael Grima',
    author_email='mickael.grima@tum.de',
    license='TUM',
    packages=find_packages(),
    include_package_data=True,
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
