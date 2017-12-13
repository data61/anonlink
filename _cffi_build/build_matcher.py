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
    extra_compile_args=['-Wall', '-Wextra', '-Werror', '-O3', '-std=c++11', '-mssse3', '-mpopcnt'],
)

ffibuilder.cdef("""
    int match_one_against_many_dice(const char * one, const char * many, int n, double * score);
    int match_one_against_many_dice_1024_k_top(const char *one, const char *many, const uint32_t *counts_many, int n, uint32_t k, double threshold, int *indices, double *scores);
    double dice_coeff_1024(const char *e1, const char *e2);
""")


if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
