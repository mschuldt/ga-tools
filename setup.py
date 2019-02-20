#!/usr/bin/env python3

from distutils.core import setup, Extension
import sys

version = '0.2'

assert not sys.version_info.major < 3, 'ga-tools requires python3'

setup(name='ga-tools',
      version=version,
      description='Tools for the GA144 multi-computer chip',
      author='Michael Schuldt',
      author_email='mbschuldt@gmail.com',
      license='GNU General Public License v3 (GPLv3)',
      packages=['ga_tools'],
      url='https://github.com/mschuldt/ga-tools',
      download_url='https://github.com/mschuldt/ga-tools_wizard/archive/{}.tar.gz'.format(version),

      scripts=['ga'],
      install_requires=['pyserial'],
      classifiers=[
          'Environment :: Console',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
          'Operating System :: POSIX :: Linux',
          'Operating System :: Microsoft :: Windows',
          'Programming Language :: Python :: 3',
          'Topic :: Software Development :: Libraries :: Python Modules',
          'Topic :: Software Development :: Assemblers',
          'Topic :: Software Development :: Disassemblers',
          'Topic :: System :: Distributed Computing',
      ])
