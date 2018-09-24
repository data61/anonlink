from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))


requirements = [
        "bitarray>=0.8.1",
        "networkx>=1.11,<=2",
        "cffi>=1.7",
        "clkhash>=0.11",
        "numpy>=1.14",
        "mypy-extensions>=0.3"
    ]

with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name="anonlink",
    version='0.10.0',
    description='Anonymous linkage using cryptographic hashes and bloom filters',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/n1analytics/anonlink',
    license='Apache',
    setup_requires=['cffi>=1.7'],
    install_requires=requirements,
    packages=find_packages(exclude=[
        '_cffi_build', '_cffi_build/*',
        'tests'
    ]),
    package_data={'anonlink': ['_cffi_build']},

    ext_package="anonlink",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Security :: Cryptography",
    ],

    # for cffi
    cffi_modules=["_cffi_build/build_matcher.py:ffibuilder"],
    zip_safe=False,
)
