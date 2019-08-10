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
        "bitarray>=0.8.1",
        "cffi>=1.7",
        "clkhash>=0.11",
        "numpy>=1.14",
        "mypy-extensions>=0.3",
        "Cython>=0.29.10"
    ]

test_requirements = [
        "pytest",
        "pytest-timeout",
        "pytest-cov",
        "codecov"
    ]

extensions = [Extension(
    name="solving._multiparty_solving",
    sources=["anonlink/solving/_multiparty_solving." + cython_cpp_ext,
             "anonlink/solving/_multiparty_solving_inner.cpp"],
    include_dirs=["anonlink/solving"],
    language="c++",
    extra_compile_args=["-std=c++11"],
    extra_link_args=["-std=c++11"],
    define_macros=[('NDEBUG', None)]
    )]

with open('README.rst', 'r', encoding='utf-8') as f:
    readme = f.read()

setup(
    name="anonlink",
    version='0.12.4',
    description='Anonymous linkage using cryptographic hashes and bloom filters',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/data61/anonlink',
    license='Apache',
    setup_requires=["cffi>=1.7", "pytest-runner"],
    install_requires=requirements,
    tests_require=test_requirements,
    extras_require={
        "test": test_requirements
    },
    packages=find_packages(exclude=[
        '_cffi_build', '_cffi_build/*',
        'tests'
    ]),
    package_data={'anonlink': ['_cffi_build']},
    ext_modules = maybe_cythonize(extensions),

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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: Implementation :: CPython",
        "Topic :: Scientific/Engineering :: Information Analysis",
        "Topic :: Security :: Cryptography",
    ],

    # for cffi
    cffi_modules=["_cffi_build/build_matcher.py:ffibuilder"],
    zip_safe=False,
)
