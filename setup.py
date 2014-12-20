from setuptools import setup

setup(
    name='distill_framework',
    version='0.1.11',
    packages=['distill'],
    url='https://github.com/Dreae/Distill',
    license='MIT License',
    author='Dreae',
    author_email='penitenttangentt@gmail.com',
    description='Just another python web framework',
    install_requires=['mako', 'routes'],
    test_suite='nose.collector',
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.6",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.2",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ]
)
