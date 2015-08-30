#! /usr/bin/env python

from setuptools import setup

exec(open("./s3_log_parser/_version.py").read())

setup(name="s3-log-parser",
      version=__version__,
      author="monkeemagic",
      author_email="lyndon.swan@cloudtrek.com.au",
      packages=['s3_log_parser'],
      install_requires = [
          'user-agents',
      ],
      license='GPLv3+',
      description="Parse lines from an s3 log file",
      test_suite='s3_log_parser.tests',
      classifiers=[
          'Development Status :: 5 - Production/Stable',
          'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
          'Environment :: Console',
          'Intended Audience :: Developers',
          'Operating System :: OS Independent',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.3',
          'Programming Language :: Python :: 3.4',
      ]
      )