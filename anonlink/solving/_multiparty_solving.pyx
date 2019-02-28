from libcpp cimport bool
from libcpp.vector cimport vector

from cython.operator cimport dereference as deref

from anonlink.solving._multiparty_solving_inner cimport (
    Record, Group, greedy_solve_inner)


def probabilistic_greedy_solve_native(
    candidates,
    *,
    merge_threshold=.5,
    deduplicated=True
):
    """Select matches using the probabilistic greedy algorithm.

    This solver is similar to `greedy_solve_native`, but may match
    records that do not have corresponding candidate pairs when there is
    enough other evidence that they are a match. This usually results in
    better accuracy.

    We assign each record to exactly one 'group' of records that are
    pairwise matched together. We iterate over `candidates` in order of
    decreasing similarity. When we encounter a pair of records (let s be
    their similarity) that do not already belong to the same group, we
    merge their groups iff (a) the proportion of pairs that are
    permitted to be matched in the groups' records is at least
    `merge_threshold`, and (b) the proportion of pairs whose similarity
    is above s in the groups' records is at least `merge_threshold`. The
    latter requirement is only for tie-breaking: we prefer groups whose
    minimum pairwise similarity is highest. Any group merge rejected due
    to requirement (b) will be revisited later with that requirement
    relaxed.

    :param tuple candidates: Candidates, as returned by
        `find_candidates`.
    :param float merge_threshold: Proportion of agreement between groups
        required to merge them. In (0, 1].
            When considering whether to merge two groups, we compute the
        groups' Cartesian product. We count the pairs in that product
        whose similarity is above the threshold. We merge the groups if
        our count is at least `merge_threshold` of the total number of
        pairs between the two groups.
            For example, suppose that we have two groups of records: 
        {A, B} and {C, D}. Let A-C, A-D and B-C be candidate pairs.
        Setting `merge_threshold` to any value not greater than .75 will
        permit the two groups to be merged since they share three
        candidate pairs out of all four pairs. Even though the
        similarity of B-D is below the threshold, there is enough
        evidence in the other pairs to conclude that it must be a match.
        The `merge_threshold` can be thought of as the inverse of the
        weight we place on that evidence.
            Higher values increase precision, but decrease recall.
            A `merge_threshold` lower than one permits two records to be
        matched without having a corresponding candidate pair. Set it to
        1.0 to ensure that two records will only be matched if their
        similarity is above the similarity threshold.
    :param bool deduplicated: When True, two records that belong to the
        same dataset will never be in the same group. Default True.

    :return: An sequence of groups. Each group is an sequence of
        records. Two records are in the same group iff they represent
        the same entity. Here, a record is a two-tuple of dataset index
        and record index.
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

    cdef double merge_threshold_double = merge_threshold
    cdef bool deduplicated_bool = deduplicated

    if n:  # Prevent dereferencing empty arrays.
        with nogil:
            cpp_result = greedy_solve_inner(
                &dset_is0[0],
                &dset_is1[0],
                &rec_is0[0],
                &rec_is1[0],
                n,
                merge_threshold_double,
                deduplicated_bool)

        # Save groups of size > 1.
        result = tuple(tuple((record.dset_i, record.rec_i)
                             for record in deref(group))
                       for group in cpp_result if deref(group).size() > 1)
        # Free all the memory!
        for group in cpp_result:
            del group
        return result
    else:
        return ()


def greedy_solve_native(candidates):
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

    :return: An sequence of groups. Each group is an sequence of
        records. Two records are in the same group iff they represent
        the same entity. Here, a record is a two-tuple of dataset index
        and record index.
    """
    return probabilistic_greedy_solve_native(
        candidates, merge_threshold=1.0, deduplicated=False)
