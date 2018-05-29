from typing import Dict, Mapping, Sequence, Set, Tuple

import numpy as np

from .typechecking import CandidatePairs


def greedy_solve(
    candidates: CandidatePairs,
    threshold: float
) -> Mapping[Tuple[int, int], Set[Tuple[int, int]]]:
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

    matches = {}  # type: Dict[Tuple[int, int], Set[Tuple[int,int]]]
    matchable_pairs = set()
    for dset_is, rec_is in zip(dset_indices.T, rec_indices.T): 
        i0, i1 = zip(dset_is, rec_is)

        if i0 in matches and i1 in matches:
            # Both records are assigned to a group.
            # Check if mergeable.
            matchable_pairs.add(frozenset((i0, i1)))
            if all(frozenset((j0, j1)) in matchable_pairs
                   for j0 in matches[i0]
                   for j1 in matches[i1]):
                # Yes, mergeable.
                # Minor cleanup.
                matchable_pairs.difference(frozenset((j0, j1))
                                             for j0 in matches[i0]
                                             for j1 in matches[i1])
                # Merge groups.
                merged_group = matches[i0]
                merged_group.update(matches[i1])
                matches.update((j, merged_group) for j in matches[i1])
            continue

        if i0 not in matches and i1 in matches:
            i0, i1 = i1, i0
            # Symmetry. Fall through.
        if i0 in matches and i1 not in matches:
            # i0 is in a group, but i1 isn't.
            # See if we may assign i1 to that group.
            matchable_pairs.add(frozenset((i0, i1)))
            if all(frozenset((j, i1)) in matchable_pairs
                   for j in matches[i0]):
                # Yes. We let's do that.
                # Minor cleanup.
                matchable_pairs.difference(frozenset((j, i1))
                                             for j in matches[i0])
                # Add i1 to i0's group.
                matches[i0].add(i1)
                matches[i1] = matches[i0]
            continue

        if i0 not in matches and i1 not in matches:
            # Neither is in a group, so let's make a new one.
            group = {i0, i1}
            matches[i0] = group
            matches[i1] = group

    return matches
