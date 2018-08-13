"""Solvers.

Solvers accept candidate pairs and return a concrete matching. In other
words, they accept a similarity for every candidate pair and turn it
into a boolean for every candidate pair.
"""

import collections as _collections
import itertools as _itertools
import typing as _typing

import anonlink.typechecking as _typechecking


def greedy_solve(
    candidates: _typechecking.CandidatePairs
) -> _typing.Sequence[_typing.Sequence[_typing.Tuple[int, int]]]:
    """ Select matches from candidate pairs using the greedy algorithm.

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

    :return: An iterable of groups. Each group is an iterable of
        records. Two records are in the same group iff they represent
        the same entity. Here, a record is a two-tuple of dataset index
        and record index.
    """
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

        if i0 in matches and i1 in matches:
            # Both records are assigned to a group.
            i0_matches = matches[i0]
            i1_matches = matches[i1]
            i0_mid = id(i0_matches)
            i1_mid = id(i1_matches)

            # Check if mergeable. matchable_pairs[i0_mid][i1_mid] is the
            # number of pairs they have in common not including the
            # current pair--we add one to include it. The total number
            # of pairs is len(i0_matches) * len(i1_matches)). When this
            # is the number of matchable pairs, then every pair is
            # matchable.
            if (matchable_pairs[i0_mid][i1_mid] + 1
                == len(i0_matches) * len(i1_matches)):
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
            if len(i0_matches) == 1:
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
            # Neither is in a group, so let's just make one.
            matches[i0] = matches[i1] = [i0, i1]
            continue

        raise RuntimeError('non-exhaustive cases')
                
    # Return all nontrivial groups without duplication
    deduplicated_groups = {id(group): group
                           for group in matches.values()
                           if len(group) > 1}
    return tuple(deduplicated_groups.values())
