from setuptools import setup, find_packages
import os

here = os.path.abspath(os.path.dirname(__file__))


requirements = [
        "bitarray==0.8.1",
        "networkx==1.11",
        "cffi>=1.7",
        "clkhash>=0.10"
    ]

setup(
    name="anonlink",
    version='0.7.0',
    description='Anonymous linkage using cryptographic hashes and bloom filters',
    url='https://github.com/n1analytics/anonlink',
    license='Apache',
    setup_requires=['cffi>=1.7'],
    install_requires=requirements,
    packages=find_packages(exclude=[
        '_cffi_build', '_cffi_build/*',
        'tests'
    ]),
    package_data={'anonlink': ['data/*.csv', '_cffi_build']},

    ext_package="anonlink",
    classifiers=[
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Topic :: Security :: Cryptography",
    ],

    # for cffi
    cffi_modules=["_cffi_build/build_matcher.py:ffibuilder"],
    zip_safe=False,
)
