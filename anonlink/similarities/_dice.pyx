cimport cython

from cpython cimport array
import array


from anonlink.similarities._dice cimport popcount_arrays as c_popcount_arrays
from anonlink.similarities._dice cimport dice_coeff as c_dice_coeff
from anonlink.similarities._dice cimport match_one_against_many_dice_k_top as c_match_one_against_many_dice_k_top

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cpdef unsigned int[::1] popcount_arrays(const char[::1] input_data, unsigned int array_bytes = 128):
    """
    Compute the popcount of a flattened array of data where each element
    is array_bytes long.
    """
    cdef array.array unsigned_int_array_template = array.array('I', [])
    cdef array.array output_counts
    if array_bytes == 0 or len(input_data) == 0:
        return array.clone(unsigned_int_array_template, 0, zero=True)
    else:
        output_size = len(input_data) // array_bytes
    # The CPP code reasonably assumes the length of the data is evenly divided by the array_bytes
    assert len(input_data) % array_bytes == 0, "input data length not divisible by array_bytes"
    output_counts = array.clone(unsigned_int_array_template, output_size, zero=True)
    popcount_arrays_preallocated_output(output_counts, input_data, array_bytes)
    return output_counts


@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
def popcount_arrays_preallocated_output(
        unsigned int[::1] output_counts,
        const char[::1] input_data,
        unsigned int array_bytes = 128
):
    """
    :param input_data: flattened contiguous char input of ARRAY_BYTES elements
    """
    cdef double elapsed_time

    # Create a memoryview of the input data and preallocated count results
    cdef const char[::1] arr_memview = input_data
    cdef unsigned int[::1] counts_memview = output_counts
    cdef unsigned int num_elements = <unsigned int>arr_memview.shape[0] // array_bytes

    with nogil:
        elapsed_time = c_popcount_arrays(
            &counts_memview[0],
            &arr_memview[0],
            num_elements,
            array_bytes)

    return elapsed_time


@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
def dice_coeff(
        const char[::1] input_data_1,
        const char[::1] input_data_2,
        int array_bytes = 128
):
    assert array_bytes % 8 == 0
    cdef const char[::1] memview_1 = input_data_1
    cdef const char[::1] memview_2 = input_data_2
    cdef double score

    with nogil:
        score = c_dice_coeff(
            &memview_1[0],
            &memview_2[0],
            array_bytes)

    return score


@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
cpdef int match_one_to_many_dice_preallocated_output(
        const char[::1] one,
        const char[::1] many,
        unsigned int[::1] counts_many,
        int n,
        int array_bytes,
        int k,
        double threshold,
        unsigned int[::1] output_indicies,
        double[::1] output_scores
) nogil:
    cdef int number_matched

    # Create a memoryview of the input data and preallocated results arrays
    cdef const char[::1] one_memview = one
    cdef const char[::1] many_memview = many
    cdef unsigned int[::1] counts_memview = counts_many
    cdef unsigned int[::1] indicies_memview = output_indicies
    cdef double[::1] scores_memview = output_scores

    cdef unsigned int num_elements = <unsigned int>many_memview.shape[0] // array_bytes

    number_matched = c_match_one_against_many_dice_k_top(
        &one_memview[0],
        &many_memview[0],
        &counts_memview[0],
        num_elements,
        array_bytes,
        k,
        threshold,
        &indicies_memview[0],
        &scores_memview[0]
    )

    return number_matched

@cython.boundscheck(False)  # Deactivate bounds checking
@cython.wraparound(False)   # Deactivate negative indexing.
def dice_many_to_many(
        const char[::1] carr0,
        const char[::1] carr1,
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
