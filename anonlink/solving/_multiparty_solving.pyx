from libcpp.vector cimport vector
from cython.operator cimport dereference as deref
from anonlink.solving._multiparty_solving_inner cimport (
    Record, Group, greedy_solve_inner)

import typing as _typing
import anonlink.typechecking as _typechecking


def greedy_solve(
    candidates: _typechecking.CandidatePairs
) -> _typing.Sequence[_typing.Sequence[_typing.Tuple[int, int]]]:
    """Select matches from candidate pairs using the greedy algorithm.

    We assign each record to exactly one 'group' of records that are
    pairwise matched together. We iterate over `candidates` in order of
    decreasing similarity. When we encounter a pair of records (let s be
    their similarity) that do not already belong to the same group, we
    merge their groups iff (a) every pair of records is permitted to be
    matched, and (b) the similarity of every pair of records is above s.
    The latter requirement is only for tie-breaking: we prefer groups
    whose minimum pairwise similarity is highest. Any group merge
    rejected due to requirement (b) will be revisited later with that
    requirement relaxed.

    :param tuple candidates: Candidates, as returned by
        `find_candidates`.

    :return: An tuple of groups. Each group is an tuple of records. Two
        records are in the same group iff they represent the same
        entity. Here, a record is a two-tuple of dataset index and
        record index.
    """
    sims_arr, dset_is_arrs, rec_is_arrs = candidates
    if len(dset_is_arrs) != len(rec_is_arrs):
        raise ValueError('inconsistent shape of index arrays')
    if len(dset_is_arrs) != 2:
        raise NotImplementedError('only binary solving is supported')

    dset_is0_arr, dset_is1_arr = dset_is_arrs
    rec_is0_arr, rec_is1_arr = rec_is_arrs
    cdef size_t n = <size_t>len(sims_arr)
    if not (n
            == len(dset_is0_arr) == len(dset_is1_arr)
            == len(rec_is0_arr) == len(rec_is1_arr)):
        raise ValueError('inconsistent shape of index arrays')

    # NB: [::1] makes sure that the array is C-contiguous
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

        result = tuple(tuple((record.dset_i, record.rec_i)
                             for record in deref(group))
                       for group in cpp_result)
        for group in cpp_result:
            del group
        return result
    else:
        return ()
