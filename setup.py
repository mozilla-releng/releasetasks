#!/usr/bin/env python
# -*- coding: utf-8 -*-


try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


readme = open('README.rst').read()
requirements = [
    "Jinja2",
    "taskcluster>=0.0.24",
    "arrow",
    "requests>=2.4.3,<=2.7.0",
    "PyYAML",
    "chunkify",
    "PGPy",
    "python-jose<=0.5.6",
    "redo",
]
test_requirements = [
    "pytest",
    "pytest-cov",
    "flake8",
    "mock",
    "voluptuous",
]

setup(
    name='releasetasks',
    version='0.4.0',
    description="""Mozilla Release Promotion Tasks contains code to generate
    release-related Taskcluster graphs.""",
    long_description=readme,
    author="Rail Aliiev",
    author_email='rail@mozilla.com',
    url='https://github.com/rail/releasetasks',
    packages=[
        'releasetasks',
    ],
    package_dir={'releasetasks':
                 'releasetasks'},
    include_package_data=True,
    install_requires=requirements,
    license="MPL",
    zip_safe=False,
    keywords='releasetasks',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
    tests_require=test_requirements,
)
