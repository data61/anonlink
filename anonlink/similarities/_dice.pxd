
cdef extern from "dice.cpp":

    int match_one_against_many_dice_k_top(
            const char[] one,
            const char[] many,
            const unsigned int[] counts_many,
            int n,
            int keybytes,
            unsigned int k,
            double threshold,
            unsigned int[] indices,
            double[] scores
    ) nogil

    double dice_coeff(const char[] array1, const char[] array2, int array_bytes) nogil

    double popcount_arrays(
            unsigned int[] counts,
            const char[] arrays,
            unsigned int narrays,
            unsigned int array_bytes
    ) nogil

