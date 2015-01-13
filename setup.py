from __future__ import unicode_literals

import re
from setuptools import find_packages, setup


def get_version(filename):
    content = open(filename).read()
    metadata = dict(re.findall("__([a-z]+)__ = '([^']+)'", content))
    return metadata['version']


setup(
    name='Mopidy-Packages',
    version=get_version('mopidy_packages/__init__.py'),
    url='https://github.com/mopidy/mopidy-packages',
    license='Apache License, Version 2.0',
    author='Stein Magnus Jodal',
    author_email='stein.magnus@jodal.no',
    description='Tools for tracking projects in the Mopidy ecosystem',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests', 'tests.*']),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'setuptools',
        'Flask',
        'jsonschema',
        'natsort',
        'requests',
        'rfc3987',
    ],
    entry_points={
        'console_scripts': [
            'mopidy-packages = mopidy_packages.__main__:main',
        ],
    },
    classifiers=[
        'Environment :: Console',
        'Environment :: No Input/Output (Daemon)',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Utilities',
    ],
)
