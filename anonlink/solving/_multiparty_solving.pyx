from libcpp.vector cimport vector

from cython.operator cimport dereference as deref

from anonlink.solving._multiparty_solving_inner cimport (
    Record, Group, greedy_solve_inner)

def greedy_solve(candidates):
    sims_arr, dset_is_arrs, rec_is_arrs = candidates

    dset_is0_arr, dset_is1_arr = dset_is_arrs
    rec_is0_arr, rec_is1_arr = rec_is_arrs

    cdef size_t n = <size_t>len(sims_arr)
    assert (n == <size_t>len(dset_is0_arr) == <size_t>len(dset_is1_arr)
              == <size_t>len(rec_is0_arr) == <size_t>len(rec_is1_arr))

    cdef unsigned int[::1] dset_is0 = dset_is0_arr
    cdef unsigned int[::1] dset_is1 = dset_is1_arr
    cdef unsigned int[::1] rec_is0 = rec_is0_arr
    cdef unsigned int[::1] rec_is1 = rec_is1_arr

    cdef vector[Group *] cpp_result
    if n:
        with nogil:
            cpp_result = greedy_solve_inner(
                &dset_is0[0],
                &dset_is1[0],
                &rec_is0[0],
                &rec_is1[0],
                n)

        result = []
        for group in cpp_result:
            group_result = []
            for record in deref(group):
                group_result.append((record.dset_i, record.rec_i))
            del group
            result.append(group_result)
        return result
    else:
        return []
