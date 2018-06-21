from collections import defaultdict, Counter
from itertools import product, repeat
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np

from .typechecking import CandidatePairs 


def _merge(i0, i1, i0_mid, i1_mid, i0_matches, i1_matches, matches, matchable_pairs):
    # Optimisation: Make sure we always extend the bigger group.
    if len(i0_matches) < len(i1_matches):
        i0, i1 = i1, i0
        i0_mid, i1_mid = i1_mid, i0_mid
        i0_matches, i1_matches = i1_matches, i0_matches

    i0_matches.extend(i1_matches)
    matches.update(zip(i1_matches, repeat(i0_matches)))
    # Update edges.
    del matchable_pairs[i0_mid][i1_mid]
    del matchable_pairs[i1_mid][i0_mid]
    for j_mid, j_count in matchable_pairs[i1_mid].items():
        matchable_pairs[i0_mid][j_mid] += j_count
        matchable_pairs[j_mid][i0_mid] += j_count
        del matchable_pairs[j_mid][i1_mid]
        if not matchable_pairs[j_mid]:
            del matchable_pairs[j_mid]
    del matchable_pairs[i1_mid]
    if not matchable_pairs[i0_mid]:
        del matchable_pairs[i0_mid]


def _2groups(i0, i1, matches, matchable_pairs, id_=id, len_=len, _merge_=_merge):
    i0_matches = matches[i0]
    i1_matches = matches[i1]

    i0_mid = id_(i0_matches)
    i1_mid = id_(i1_matches)

    # Both records are assigned to a group.
    # Check if mergeable.
    if (matchable_pairs[i0_mid][i1_mid] + 1
        == len_(i0_matches) * len_(i1_matches)):
        # Merge groups.
        _merge_(i0, i1, i0_mid, i1_mid, i0_matches, i1_matches, matches, matchable_pairs)

    else:
        # Don't merge. Mark they have another edge in common.
        matchable_pairs[i0_mid][i1_mid] += 1
        matchable_pairs[i1_mid][i0_mid] += 1


def _1group(i0, i1, matches, matchable_pairs):
    # i0 is not in a group, but i1 is.
    # See if we may assign i0 to that group.
    i0_matches = matches[i0]
    if len(i0_matches) == 1:
        i0_matches.append(i1)
        matches[i1] = i0_matches
    else:
        i1_matches = [i1]
        matches[i1] = i1_matches

        matchable_pairs[id(i1_matches)][id(i0_matches)] = 1
        matchable_pairs[id(i0_matches)][id(i1_matches)] = 1


def _0groups(i0, i1, matches):
    matches[i0] = matches[i1] = [i0, i1]


def greedy_solve(
    candidates: CandidatePairs,
    threshold: float
) -> Mapping[Tuple[int, int], List[Tuple[int, int]]]:
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
        :param bool overwrite_candidates: Discard data in `candidates`.
            Enabling may improve performance.

        :return: The mapping. A tuple of (dataset index, record index)
            maps to a set of its matches. Each match is a similar
            2-tuple.
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

    matches = {}  # type: Dict[Tuple[int, int], List[Tuple[int,int]]]
    matchable_pairs = defaultdict(Counter)  # Count edges.

    for dset_is, rec_is in zip(dset_indices.T, rec_indices.T): 
        i0, i1 = zip(dset_is, rec_is)

        if i0 in matches and i1 in matches:
            _2groups(i0, i1, matches, matchable_pairs)
            continue

        if i0 not in matches and i1 in matches:
            i0, i1 = i1, i0
            # Fall through
        if i0 in matches and i1 not in matches:
            _1group(i0, i1, matches, matchable_pairs)
            continue

        if i0 not in matches and i1 not in matches:
            _0groups(i0, i1, matches)
            continue

        raise RuntimeError('non-exhaustive cases')
                

    return matches
