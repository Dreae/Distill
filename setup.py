from setuptools import setup, Extension
from tests import test_suite
from os import path
import sys


setup(
    name='Distill',
    version='0.0.1',
    packages=['Distill'],
    url='',
    license='MIT License',
    author='Dreae',
    author_email='penitenttangentt@gmail.com',
    description='Just another python web framework',
    requires=['mako'],
    test_suite='tests.test_suite'
)
