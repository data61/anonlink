from itertools import product, repeat
from typing import Dict, List, Mapping, Sequence, Tuple

import numpy as np

from .typechecking import CandidatePairs 


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
    matchable_pairs = set()

    # Optimise. This is not nice but it makes things 8% faster on large
    # problems...
    matchable_pairs_contains = matchable_pairs.__contains__
    matchable_pairs_add = matchable_pairs.add
    product_ = product
    repeat_ = repeat
    zip_ = zip
    map_ = map
    all_ = all
    

    for dset_is, rec_is in zip_(dset_indices.T, rec_indices.T): 
        i0, i1 = zip_(dset_is, rec_is)

        if i0 in matches and i1 in matches:
            # Both records are assigned to a group.
            # Check if mergeable.
            matchable_pairs_add((i0, i1))
            if all_(map_(matchable_pairs_contains, product_(matches[i0], matches[i1]))):
                # Minor cleanup.
                matchable_pairs.difference_update(product_(matches[i0], matches[i1]))
                # Merge groups.
                matches[i0].extend(matches[i1])
                matches.update(zip_(matches[i1], repeat_(matches[i0])))
        
        elif i0 not in matches and i1 in matches:
            # i0 is not in a group, but i1 is.
            # See if we may assign i0 to that group.
            matchable_pairs_add((i0, i1))
            if all_(map_(matchable_pairs_contains, zip_(repeat_(i0), matches[i1]))):
                # Minor cleanup.
                matchable_pairs.difference_update(zip_(repeat_(i0), matches[i1]))
                # Yes. We let's do that.
                matches[i1].append(i0)
                matches[i0] = matches[i1]

        elif i0 in matches and i1 not in matches:
            # i0 is in a group, but i1 isn't.
            # See if we may assign i1 to that group.
            matchable_pairs_add((i0, i1))
            if all_(map_(matchable_pairs_contains, zip_(matches[i0], repeat_(i1)))):
                # Minor cleanup.
                matchable_pairs.difference_update(zip_(matches[i0], repeat_(i1)))
                # Yes. We let's do that.
                matches[i0].append(i1)
                matches[i1] = matches[i0]

        elif i0 not in matches and i1 not in matches:
            # Neither is in a group, so let's make a new one.
            matches[i0] = matches[i1] = [i0, i1]

        else:
            raise RuntimeError('nonexhaustive cases')

    return matches
