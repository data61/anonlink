from libcpp.vector cimport vector


cdef extern from "_multiparty_solving_inner.h":
    cdef struct Record:
        unsigned int dset_i
        unsigned int rec_i

    ctypedef vector[Record] Group

    vector[Group *] greedy_solve_inner(
        unsigned int[],
        unsigned int[],
        unsigned int[],
        unsigned int[],
        size_t n
    ) nogil except +
    # `except +` asks Cython to propagate C++ exceptions to Python land
