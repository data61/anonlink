# cython: language_level=3

cimport cython
from libc.stdint cimport int8_t

from cpython cimport array
import array


cdef extern from "dice.cpp":

    int c_match_one_against_many_dice_k_top "match_one_against_many_dice_k_top" (
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

    double c_dice_coeff "dice_coeff" (const char[] array1, const char[] array2, int array_bytes) nogil

    double c_popcount_arrays "popcount_arrays" (
            unsigned int[] counts,
            const char[] arrays,
            unsigned int narrays,
            unsigned int array_bytes
    ) nogil


# Use signed char (int8_t) for memoryview types to match Python's array('b')
# which is always signed char, regardless of platform default char signedness.

@cython.boundscheck(False)
@cython.wraparound(False)
def popcount_arrays(const int8_t[::1] input_data, unsigned int array_bytes = 128):
    """
    Compute the popcount of a flattened array of data where each element
    is array_bytes long.
    """
    cdef array.array unsigned_int_array_template = array.array('I', [])
    cdef array.array output_counts
    if array_bytes == 0 or len(input_data) == 0:
        return array.clone(unsigned_int_array_template, 0, zero=True)
    cdef unsigned int output_size = len(input_data) // array_bytes
    # The CPP code reasonably assumes the length of the data is evenly divided by the array_bytes
    assert len(input_data) % array_bytes == 0, "input data length not divisible by array_bytes"
    output_counts = array.clone(unsigned_int_array_template, output_size, zero=True)
    popcount_arrays_preallocated_output(output_counts, input_data, array_bytes)
    return output_counts


@cython.boundscheck(False)
@cython.wraparound(False)
def popcount_arrays_preallocated_output(
        unsigned int[::1] output_counts,
        const int8_t[::1] input_data,
        unsigned int array_bytes = 128
):
    """
    :param input_data: flattened contiguous char input of ARRAY_BYTES elements
    """
    cdef double elapsed_time

    # Create a memoryview of the input data and preallocated count results
    cdef const int8_t[::1] arr_memview = input_data
    cdef unsigned int[::1] counts_memview = output_counts
    cdef unsigned int num_elements = <unsigned int>arr_memview.shape[0] // array_bytes

    with nogil:
        elapsed_time = c_popcount_arrays(
            &counts_memview[0],
            <const char*>&arr_memview[0],
            num_elements,
            array_bytes)

    return elapsed_time


@cython.boundscheck(False)
@cython.wraparound(False)
def dice_coeff(
        const int8_t[::1] input_data_1,
        const int8_t[::1] input_data_2,
        int array_bytes = 128
):
    assert array_bytes % 8 == 0
    cdef const int8_t[::1] memview_1 = input_data_1
    cdef const int8_t[::1] memview_2 = input_data_2
    cdef double score

    with nogil:
        score = c_dice_coeff(
            <const char*>&memview_1[0],
            <const char*>&memview_2[0],
            array_bytes)

    return score


@cython.boundscheck(False)
@cython.wraparound(False)
cdef int match_one_to_many_dice_preallocated_output(
        const int8_t[::1] one,
        const int8_t[::1] many,
        unsigned int[::1] counts_many,
        int n,
        int array_bytes,
        int k,
        double threshold,
        unsigned int[::1] output_indicies,
        double[::1] output_scores
):
    cdef int number_matched
    cdef unsigned int num_elements

    if array_bytes == 0:
        return 0

    # Create a memoryview of the input data and preallocated results arrays
    cdef const int8_t[::1] one_memview = one
    cdef const int8_t[::1] many_memview = many
    cdef unsigned int[::1] counts_memview = counts_many
    cdef unsigned int[::1] indicies_memview = output_indicies
    cdef double[::1] scores_memview = output_scores

    num_elements = <unsigned int>many_memview.shape[0] // array_bytes

    with nogil:
        number_matched = c_match_one_against_many_dice_k_top(
            <const char*>&one_memview[0],
            <const char*>&many_memview[0],
            &counts_memview[0],
            num_elements,
            array_bytes,
            k,
            threshold,
            &indicies_memview[0],
            &scores_memview[0]
        )

    return number_matched

@cython.boundscheck(False)
@cython.wraparound(False)
def dice_many_to_many(
        const int8_t[::1] carr0,
        const int8_t[::1] carr1,
        unsigned int length_f0,
        unsigned int length_f1,
        unsigned int[::1] c_popcounts,
        int filter_bytes,
        int k,
        double threshold,
        array.array result_sims,
        array.array result_indices0,
        array.array result_indices1
):
    cdef size_t i
    cdef int matches
    cdef int total_matches = 0
    if filter_bytes == 0:
        return 0
    assert len(carr1) == filter_bytes * length_f1
    assert len(c_popcounts) == length_f1

    # do all buffer allocations in Python and pass a memoryview to C
    cdef array.array double_array_template = array.array('d', [])
    cdef array.array int_array_template = array.array('I', [])

    cdef array.array c_scores
    cdef array.array c_indicies

    c_scores = array.clone(double_array_template, k, zero=True)
    c_indices = array.clone(int_array_template, k, zero=True)
    i_buffer = array.clone(int_array_template, k, zero=True)

    cdef double[::1] scores_memview = c_scores
    cdef unsigned int[::1] indicies_memview = c_indices
    cdef unsigned int[::1] i_buffer_memview = i_buffer

    for i in range(length_f0):
        matches = match_one_to_many_dice_preallocated_output(
            carr0[i * filter_bytes:(i + 1) * filter_bytes],
            carr1,
            c_popcounts,
            length_f1,
            filter_bytes,
            k,
            threshold,
            indicies_memview,
            scores_memview
        )
        total_matches += matches
        i_buffer_memview[:] = i

        assert matches <= k
        result_sims.extend(c_scores[:matches])
        result_indices0.extend(i_buffer[:matches])
        result_indices1.extend(c_indices[:matches])

    return total_matches
