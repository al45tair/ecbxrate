# -*- coding: utf-8 -*-
from setuptools import setup

with open('README.rst', 'r') as f:
    long_desc = f.read().decode('utf-8')

setup(name='ecbxrate',
      version='0.1.0',
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
      scripts=['scripts/ecbxrate'],
      install_requires=[
        'sqlalchemy >= 0.9.8',
        'lxml >= 3.4.1'
        ],
      provides=['ecbxrate']
)
