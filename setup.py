from setuptools import setup, find_packages

setup(
    name="anonlink",
    version='0.1.0.dev1',
    description='Anonymous linkage using cryptographic hashes and bloom filters',
    url='https://github.inside.nicta.com.au/magic/AnonymousLinking',
    license='Apache',
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["build_matcher.py:ffi"],
    install_requires=["cffi>=1.0.0"],
    packages=find_packages(exclude=['tests*']),
)