from cffi import FFI
ffi = FFI()

ffi.set_source("_entitymatcher",
               open('dice_one_against_many.cpp', 'r').read(),
               source_extension='.cpp',
               extra_compile_args=['-std=c++11', '-mssse3', '-mpopcnt'])

ffi.cdef("""
    int match_one_against_many_dice_c(const char * one, const char * many, int n, int l, double * score);
    int match_one_against_many_dice_1024_k_top(const char *one, const char *many, const uint32_t *counts_many, int n, uint32_t k, double threshold, int *indices, double *scores);
    double dice_coeff_1024(const char *e1, const char *e2);
    void popcount_1024_array(const char *many, int n, uint32_t *counts_many);
""")

if __name__ == "__main__":
    ffi.compile()
