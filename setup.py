import platform

from setuptools import setup, Extension, find_packages
import os

try:
    from Cython.Build import cythonize, build_ext
except ImportError:
    # No Cython but we may have pre-converted the files
    maybe_cythonize = lambda x: x
    cython_cpp_ext = 'cpp'
else:
    maybe_cythonize = cythonize
    cython_cpp_ext = 'pyx'

here = os.path.abspath(os.path.dirname(__file__))

requirements = [
        "bitarray-hardbyte>=0.8.0",
        "numpy>=1.14",
        "mypy-extensions>=0.4",
        "Cython>=0.29.10"
    ]

test_requirements = [
        "pytest",
        "pytest-timeout",
        "pytest-cov",
        "codecov",
        "hypothesis",
        "clkhash>=0.15.0",
    ]

current_os = platform.system()
if current_os == "Windows":
    extra_compile_args = ['/std:c++17', '/O2']
    extra_link_args = []
else:
    extra_compile_args = ['-O3', '-std=c++11']
    extra_link_args = []

extensions = [
    Extension(
        name="solving._multiparty_solving",
        sources=["anonlink/solving/_multiparty_solving." + cython_cpp_ext,
                 "anonlink/solving/_multiparty_solving_inner.cpp"],
        include_dirs=["anonlink/solving"],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_compile_args,
        define_macros=[('NDEBUG', None)]
        ),
    Extension(
        name="similarities._dice",
        sources=[
            "anonlink/similarities/_dice." + cython_cpp_ext
        ],
        include_dirs=["anonlink/similarities"],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        define_macros=[('NDEBUG', None)]
        )
]

with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name="anonlink",
    version='0.14.0',
    description='Anonymous linkage using cryptographic hashes and bloom filters',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/data61/anonlink',
    license='Apache',
    setup_requires=["pytest-runner"],
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require={
        "test": test_requirements
    },
    packages=find_packages(exclude=[
        'tests'
    ]),
    package_data={'anonlink': []},
    ext_modules=maybe_cythonize(extensions),
    ext_package="anonlink",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Security :: Cryptography",
    ],
    zip_safe=False,
)
