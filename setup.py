import platform

from setuptools import setup, Extension
from Cython.Build import cythonize

current_os = platform.system()
if current_os == "Windows":
    extra_compile_args = ['/std:c++17', '/O2']
    extra_link_args = []
else:
    extra_compile_args = ['-O3', '-std=c++11']
    extra_link_args = []

extensions = [
    Extension(
        name="anonlink.solving._multiparty_solving",
        sources=["anonlink/solving/_multiparty_solving.pyx",
                 "anonlink/solving/_multiparty_solving_inner.cpp"],
        include_dirs=["anonlink/solving"],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_compile_args,
        define_macros=[('NDEBUG', None)]
    ),
    Extension(
        name="anonlink.similarities._dice",
        sources=[
            "anonlink/similarities/_dice.pyx"
        ],
        include_dirs=["anonlink/similarities"],
        language="c++",
        extra_compile_args=extra_compile_args,
        extra_link_args=extra_link_args,
        define_macros=[('NDEBUG', None)]
    )
]

setup(
    ext_modules=cythonize(extensions),
)
