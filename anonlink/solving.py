import collections
from itertools import repeat
from typing import DefaultDict, Dict, Iterable, List, Tuple

import numpy as np

from .typechecking import CandidatePairs


def greedy_solve(
    candidates: CandidatePairs,
    threshold: float
) -> Iterable[Iterable[Tuple[int, int]]]:
    """ Select matches from candidate pairs using the greedy algorithm.

        We assign each record to exactly one 'group' of records that are
        pairwise matched together. We iterate over `candidates` in order
        of decreasing similarity. When we encounter a pair of records
        (let s be their similarity) that do not already belong to the
        same group, we merge their groups iff (a) every pair of records
        is permitted to be matched, and (b) the similarity of every pair
        of records is above s. The latter requirement is only for
        tie-breaking: we prefer groups whose minimum pairwise similarity
        is highest. Any group merge rejected due to requirement (b) will
        be revisited later with that requirement relaxed.

        :param tuple candidates: Candidates, as returned by
            `find_candidates`.
        :param float threshold: The similarity threshold. This is
            ignored in this implementation.

        :return: An iterable of groups. Each group is an iterable of
            records. Two records are in the same group iff they
            represent the same entity. Here, a record is a two-tuple of
            dataset index and record index.
    """
    dset_indices_sseq, rec_indices_sseq, sims_seq = candidates
    
    # Sort pairs in decreasing order of similarity
    sorted_indices = np.argsort(sims_seq)[::-1]
    dset_indices = np.asarray(dset_indices_sseq)[:,sorted_indices]
    rec_indices = np.asarray(rec_indices_sseq)[:,sorted_indices]

    assert len(sorted_indices.shape) == 1
    assert len(dset_indices.shape) == 2
    assert len(rec_indices.shape) == 2
    assert dset_indices.shape == rec_indices.shape
    assert dset_indices.shape[1] == sorted_indices.shape[0]
    assert rec_indices.shape[1] == sorted_indices.shape[0]

    # Map (dataset index, record index) to its group.
    matches = {}  # type: Dict[Tuple[int, int], List[Tuple[int,int]]]

    # Each group is a set of records. We merge two groups when 
    # pair of their records is matchable. A pair is matchable if we have
    # seen it. Store the number of matchable pairs between two groups.
    # This is a sparse matrix: the default number of matchable pairs is
    # 0. Since the groups themselves are not hashable, we use their id
    # as the key.
    matchable_pairs = collections.defaultdict(
        collections.Counter)  # type: DefaultDict[int, Dict[int, int]]

    for dset_is, rec_is in zip(dset_indices.T, rec_indices.T): 
        i0, i1 = zip(dset_is, rec_is)

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
                # Optimisation: Make sure we always extend the bigger group.
                if len(i0_matches) < len(i1_matches):
                    i0, i1 = i1, i0
                    i0_mid, i1_mid = i1_mid, i0_mid
                    i0_matches, i1_matches = i1_matches, i0_matches
                # Merge groups.
                i0_matches.extend(i1_matches)
                matches.update(zip(i1_matches, repeat(i0_matches)))
                
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
                
    # Return all nontrivial groups
    return (group for group in matches.values() if len(group) > 1)
