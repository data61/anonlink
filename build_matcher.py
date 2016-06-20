from cffi import FFI
ffi = FFI()

ffi.set_source("_entitymatcher",
               open('dice_one_against_many.cpp', 'r').read(),
               source_extension='.cpp',
               extra_compile_args=['-std=c++11', '-mssse3', '-mpopcnt'])

ffi.cdef("""
    int match_one_against_many_dice_c(const char * one, const char * many, int n, int l, double * score);
    void match_one_against_many_dice_1024_k_top(const char *one, const char *many, int n, int k, int *indices, double *scores);
    double dice_coeff_1024(const char *e1, const char *e2);
""")

if __name__ == "__main__":
    ffi.compile()
