# -*- coding: utf-8 -*-
# !/bin/env python

from setuptools import setup, find_packages

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
    install_requires=[
        'pyyaml==3.12',
        'networkx==1.11',
        'requests==2.12.3',
        'osmapi==0.8.1',
        'sortedcontainers==1.5.7',
        'mock==2.0.0',
        'pytest==3.1.2'
    ],
    zip_safe=False
)
