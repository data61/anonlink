import collections as _collections
import itertools as _itertools
import typing as _typing

import anonlink.typechecking as _typechecking


def probabilistic_greedy_solve_python(
    candidates: _typechecking.CandidatePairs,
    *,
    merge_threshold: float = .5,
    deduplicated: bool = True
) -> _typechecking.MatchGroups:
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
    if merge_threshold < 0 or merge_threshold > 1:
        raise ValueError(
            f'merge_threshold must be between 0 and 1 (got {merge_threshold})') 

    sims, dset_is, rec_is = candidates
    if len(dset_is) != len(rec_is):
        raise ValueError('inconsistent shape of index arrays')
    if len(dset_is) != 2:
        raise NotImplementedError('only binary solving is supported')

    dset_is0, dset_is1 = dset_is
    rec_is0, rec_is1 = rec_is
    if not (len(sims)
            == len(dset_is0) == len(dset_is1)
            == len(rec_is0) == len(rec_is1)):
        raise ValueError('inconsistent shape of index arrays')

    # Map (dataset index, record index) to its group.
    matches: _typing.Dict[_typing.Tuple[int, int],
                          _typing.List[_typing.Tuple[int, int]]] = {}

    # Each group is a set of records. We merge two groups when 
    # pair of their records is matchable. A pair is matchable if we have
    # seen it. Store the number of matchable pairs between two groups.
    # This is a sparse matrix: the default number of matchable pairs is
    # 0. Since the groups themselves are not hashable, we use their id
    # as the key.
    matchable_pairs: _typing.DefaultDict[int, _typing.Counter[int]] \
        = _collections.defaultdict(_collections.Counter)

    for dset_i0, dset_i1, rec_i0, rec_i1 in zip(
            dset_is0, dset_is1, rec_is0, rec_is1):
        i0 = dset_i0, rec_i0
        i1 = dset_i1, rec_i1

        if i0 == i1:
            continue

        if i0 in matches and i1 in matches:
            # Both records are assigned to a group.
            i0_matches = matches[i0]
            i1_matches = matches[i1]
            i0_mid = id(i0_matches)
            i1_mid = id(i1_matches)

            if i0_mid == i1_mid:
                continue

            # Check if mergeable. matchable_pairs[i0_mid][i1_mid] is the
            # number of pairs they have in common not including the
            # current pair--we add one to include it. The total number
            # of pairs is len(i0_matches) * len(i1_matches)). When this
            # is the number of matchable pairs, then every pair is
            # matchable.
            overlap = matchable_pairs[i0_mid][i1_mid] + 1
            total_pairs = len(i0_matches) * len(i1_matches)
            duplicates_ok = (not deduplicated or all(m0 != m1
                                                     for m0, _ in i0_matches
                                                     for m1, _ in i1_matches))
            if overlap >= merge_threshold * total_pairs and duplicates_ok:
                # Optimise by always extending the bigger group.
                if len(i0_matches) < len(i1_matches):
                    i0, i1 = i1, i0
                    i0_mid, i1_mid = i1_mid, i0_mid
                    i0_matches, i1_matches = i1_matches, i0_matches
                # Merge groups.
                i0_matches.extend(i1_matches)
                matches.update(zip(i1_matches, _itertools.repeat(i0_matches)))
                
                # Update matchable pairs.
                del matchable_pairs[i0_mid][i1_mid]
                del matchable_pairs[i1_mid][i0_mid]
                for j_mid, j_count in matchable_pairs[i1_mid].items():
                    matchable_pairs[i0_mid][j_mid] += j_count
                    matchable_pairs[j_mid][i0_mid] += j_count
                    del matchable_pairs[j_mid][i1_mid]
                del matchable_pairs[i1_mid]
                if not matchable_pairs[i0_mid]:  # Empty. Can delete.
                    del matchable_pairs[i0_mid]

            else:
                # Don't merge. Mark: they have another edge in common.
                matchable_pairs[i0_mid][i1_mid] += 1
                matchable_pairs[i1_mid][i0_mid] += 1
            continue

        if i0 not in matches and i1 in matches:
            i0, i1 = i1, i0
            # Symmetry. Fall through.
        if i0 in matches and i1 not in matches:
            # i0 is in a group, but i1 is not.
            # See if we may assign i0 to that group.
            i0_matches = matches[i0]
            overlap = 1
            total_pairs = len(i0_matches)
            duplicates_ok = not deduplicated or all(m0 != i1[0]
                                                    for m0, _ in i0_matches)
            if overlap >= merge_threshold * total_pairs and duplicates_ok:
                # i0 is a group of 1, so trivially we can merge.
                i0_matches.append(i1)
                matches[i1] = i0_matches
            else:
                # i0 is a group of >1. i1 is not in a group, so this is
                # the first time we're seeing it. Hence, it is not
                # matchable with the other elements of i0.
                i1_matches = [i1]
                matches[i1] = i1_matches

                matchable_pairs[id(i1_matches)][id(i0_matches)] = 1
                matchable_pairs[id(i0_matches)][id(i1_matches)] = 1
            continue

        if i0 not in matches and i1 not in matches:
            duplicates_ok = not deduplicated or i0[0] != i1[0]
            if duplicates_ok:
                # Neither is in a group, so let's just make one.
                matches[i0] = matches[i1] = [i0, i1]
            continue

        raise RuntimeError('non-exhaustive cases')
                
    # Return all nontrivial groups without duplication
    deduplicated_groups = {id(group): group
                           for group in matches.values()
                           if len(group) > 1}
    return tuple(map(tuple, deduplicated_groups.values()))


def greedy_solve_python(
    candidates: _typechecking.CandidatePairs
) -> _typechecking.MatchGroups:
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
    return probabilistic_greedy_solve_python(
        candidates, merge_threshold=1.0, deduplicated=False)
