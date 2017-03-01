from setuptools import setup, find_packages

requirements = [
        "bitarray==0.8.1",
        "networkx==1.11",
        "cffi>=1.4.1",
        "click==6.2",
        "requests==2.12.4"
    ]

setup(
    name="anonlink",
    version='0.4.5',
    description='Anonymous linkage using cryptographic hashes and bloom filters',
    url='https://github.inside.nicta.com.au/magic/AnonymousLinking',
    license='Apache',
    setup_requires=requirements,
    install_requires=requirements,
    test_requires=requirements,
    packages=find_packages('anonlink', exclude=['cpp_code', 'cpp_code.*']),
    package_data={'anonlink': ['data/*.csv']},
    entry_points={
        'console_scripts': [
            'clkutil = anonlink.cli:cli'
        ],
    },

    # for cffi
    cffi_modules=["cpp_code/build_matcher.py:ffibuilder"],
    zip_safe=False,
    ext_package="anonlink"
)
