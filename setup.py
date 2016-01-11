# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from setuptools.command.test import test as TestCommand

class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import sys
        import pytest
        errno = pytest.main(self.test_args)
        sys.exit(errno)

with open('README.rst', 'rb') as f:
    long_desc = f.read().decode('utf-8')

setup(name='ecbxrate',
      version='0.2.2',
      description='Exchange rates for Python',
      long_description=long_desc,
      author='Alastair Houghton',
      author_email='alastair@alastairs-place.net',
      url='http://bitbucket.org/al45tair/ecbxrate',
      license='MIT License',
      packages=['ecbxrate'],
      classifiers=[
          'Development Status :: 4 - Beta',
          'License :: OSI Approved :: MIT License',
          'Topic :: Software Development :: Libraries',
        ],
      tests_require=['pytest'],
      cmdclass={
          'test': PyTest
          },
      scripts=['scripts/ecbxrate'],
      install_requires=[
        'sqlalchemy >= 0.9.8',
        'lxml >= 3.4.1'
        ],
      provides=['ecbxrate']
)
