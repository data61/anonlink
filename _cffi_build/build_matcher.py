import os.path
import platform
from cffi import FFI

ffibuilder = FFI()

_path = os.path.dirname(__file__)
sourcefile = os.path.join(_path, 'dice_one_against_many.cpp')

with open(sourcefile, 'r') as f:
    source = f.read()

current_os = platform.system()
if current_os == "Windows":
    extra_compile_args = ['-Wall', '/std:c++17', '/O2']         # '/arch:AVX512' or '/arch:AVX2'
else:
    extra_compile_args = ['-Wall', '-Wextra', '-Werror', '-O3', '-std=c++11', '-fvisibility=hidden']


ffibuilder.set_source(
    "_entitymatcher",
    source,
    source_extension='.cpp',
    extra_compile_args=extra_compile_args,
    include_dirs=[_path]
)

ffibuilder.cdef("""
    int match_one_against_many_dice_k_top(const char *one, const char *many, const uint32_t *counts_many, int n, int keybytes, uint32_t k, double threshold, int *indices, double *scores);
    double dice_coeff(const char *array1, const char *array2, int array_bytes);
    double popcount_arrays(uint32_t *counts, const char *arrays, int narrays, int array_bytes);
    uint64_t popcnt(const void* data, uint64_t size);
""")


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
