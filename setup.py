from setuptools import setup, find_packages

setup(
    name="anonlink",
    version='0.4.1',
    description='Anonymous linkage using cryptographic hashes and bloom filters',
    url='https://github.inside.nicta.com.au/magic/AnonymousLinking',
    license='Apache',
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["build_matcher.py:ffi"],
    install_requires=open('requirements.txt').readlines(),
    packages=['anonlink'],
    package_data={'anonlink': ['data/*.csv']},
    entry_points={
        'console_scripts': [
            'clkutil = anonlink.hashdata_cli:cli'
        ],
    },
)