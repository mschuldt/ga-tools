#!/usr/bin/env python3

from distutils.core import setup, Extension
import sys

version = '0.1'

assert not sys.version_info.major < 3, 'ga-tools requires python3'

setup(name='ga-tools',
      version=version,
      description='Alternative tools for the GA144 multicomputer chip',
      author='Michael Schuldt',
      author_email='mbschuldt@gmail.com',
      packages=['ga_tools'],
      url='https://github.com/mschuldt/ga-tools',
      download_url='https://github.com/mschuldt/ga-tools_wizard/archive/{}.tar.gz'.format(version),
      scripts=['ga'])
