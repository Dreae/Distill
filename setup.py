from distutils.core import setup, Extension
from os import path
import sys

PYPY = False
CYTHON = False
try:
    sys.pypy_version_info
except AttributeError:
    PYPY = False

if not PYPY:
    try:
        from Cython.Distutils import build_ext
        CYTHON = True
    except ImportError:
        CYTHON = False

if CYTHON:
    src_files = (
        'application.py',
        'exceptions.py',
        'request.py',
        'response.py',
        'templates.py'
    )
    ext_modules = [Extension('Distill.' + ext, [path.join('Distill', ext)]) for ext in src_files]
    cmdclass = {'build_ext': build_ext}
else:
    ext_modules = []
    cmdclass = {}


setup(
    name='Distill',
    version='0.0.1',
    packages=['Distill'],
    ext_modules=ext_modules,
    cmdclass=cmdclass,
    url='',
    license='MIT License',
    author='Dreae',
    author_email='penitenttangentt@gmail.com',
    description='Just another python web framework',
    requires=['mako']
)
