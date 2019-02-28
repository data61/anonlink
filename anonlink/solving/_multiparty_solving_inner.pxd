from libcpp cimport bool
from libcpp.vector cimport vector
from libcpp.unordered_set cimport unordered_set


cdef extern from "_multiparty_solving_inner.h":
    cdef struct Record:
        unsigned int dset_i
        unsigned int rec_i

    ctypedef vector[Record] Group

    unordered_set[Group *] greedy_solve_inner(
        unsigned int[],
        unsigned int[],
        unsigned int[],
        unsigned int[],
        size_t,
        double,
        bool
    ) nogil except +
    # `except +` asks Cython to propagate C++ exceptions to Python land
