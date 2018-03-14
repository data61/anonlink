import os.path

from cffi import FFI

ffibuilder = FFI()

_path = os.path.dirname(__file__)
sourcefile = os.path.join(_path, 'dice_one_against_many.cpp')

with open(sourcefile, 'r') as f:
    source = f.read()


ffibuilder.set_source(
    "_entitymatcher",
    source,
    source_extension='.cpp',
    extra_compile_args=['-Wall', '-Wextra', '-Werror', '-O3', '-std=c++11', '-march=native', '-mssse3', '-mpopcnt', '-fvisibility=hidden'
    ],
)

ffibuilder.cdef("""
    int match_one_against_many_dice_k_top(const char *one, const char *many, const uint32_t *counts_many, int n, int keybytes, uint32_t k, double threshold, int *indices, double *scores);
    double dice_coeff(const char *array1, const char *array2, int array_bytes);
    double popcount_arrays(uint32_t *counts, const char *arrays, int narrays, int array_bytes);
""")


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
