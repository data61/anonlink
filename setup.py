from setuptools import setup, find_packages

requirements = [
        "bitarray==0.8.1",
        "networkx==1.11",
        "cffi>=1.4.1",
    ]

setup(
    name="anonlink",
    version='0.6.0',
    description='Anonymous linkage using cryptographic hashes and bloom filters',
    url='https://github.inside.nicta.com.au/magic/AnonymousLinking',
    license='Apache',
    setup_requires=requirements,
    install_requires=requirements,
    test_requires=requirements,
    packages=find_packages(exclude=['cpp_code', 'cpp_code.*', 'tests']),
    package_data={'anonlink': ['data/*.csv']},
    # for cffi
    cffi_modules=["cpp_code/build_matcher.py:ffibuilder"],
    zip_safe=False,
    ext_package="anonlink"
)
