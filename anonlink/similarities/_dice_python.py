from array import array
from itertools import repeat
from typing import Iterable, Optional, Sequence, Tuple

import numpy as np
from bitarray import bitarray

from anonlink.similarities._utils import (sort_similarities_inplace,
                                          to_bitarrays)
from anonlink.typechecking import FloatArrayType, IntArrayType

__all__ = ['dice_coefficient_python']


def dice_coefficient_python(
    datasets: Sequence[Sequence[bitarray]],
    threshold: float,
    k: Optional[int] = None
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    """Find Dice coefficients of CLKs.

    This version is written in Python, so it does not rely on
    architecture-specific instructions. It may be slower than an
    accelerated version.

    The returned pairs are sorted in decreasing order of similarity,
    then in increasing order of the record index in the first dataset,
    and then in increasing order of the record index in the second
    dataset.

    :param datasets: A length 2 sequence of datasets. A dataset is a
        sequence of bitarrays.
    :param threshold: Pairs whose similarity is above this value may be
        a match.
    :param k: We only return the top k candidates for every record. Set
        to None to return all candidates.
    
    :return: A 2-tuple of similarity scores and indices. The similarity
        scores are an array of floating-point values. The indices are a
        2-tuple of arrays of integers.
    """
    n_datasets = len(datasets)
    if n_datasets < 2:
        raise ValueError(f'not enough datasets (expected 2, got {n_datasets})')
    elif n_datasets > 2:
        raise NotImplementedError(
            f'too many datasets (expected 2, got {n_datasets})')
    filters0, filters1 = datasets
    filters0 = to_bitarrays(filters0)
    filters1 = to_bitarrays(filters1)

    result_sims: FloatArrayType = array('d')
    result_indices0: IntArrayType = array('I')
    result_indices1: IntArrayType = array('I')

    if not filters0 or not filters1:
        # Empty result of the correct type.
        return result_sims, (result_indices0, result_indices1)

    f1_counts = tuple(f1.count() for f1 in filters1)

    for i, f0 in enumerate(filters0):
        f0_count = f0.count()
        if f0_count:
            coeffs: Iterable[float] = (
                2 * (f0 & f1).count() / (f0_count + f1_count)
                for f1, f1_count in zip(filters1, f1_counts))
        else:  # Avoid division by zero.
            coeffs = repeat(0., len(filters1))
        
        cands = filter(lambda c: c[1] >= threshold, enumerate(coeffs))
        top_k = sorted(cands, key=lambda x: -x[1])[:k]

        result_sims.extend(sim for _, sim in top_k)
        result_indices0.extend(repeat(i, len(top_k)))
        result_indices1.extend(j for j, _ in top_k)

    sort_similarities_inplace(result_sims, result_indices0, result_indices1)
    
    return result_sims, (result_indices0, result_indices1)



def dice_coefficient_pairs_python(
        datasets: Sequence[Tuple[bitarray, bitarray]]
):
    """Find Dice coefficients of bitarray pairs.

    This version is written in Python, so it does not rely on
    architecture-specific instructions. It may be slower than an
    accelerated version.

    A similarity is computed for every pair of bitarrays in the input
    datasets, the similarity for each pair is returned as a floating-point
    value.

    :param datasets: A sequence of candidate pairs. Each pair in a tuple
        of bitarrays.

    :return: Similarity scores for every input pair as an array of
        floating-point values.
    """
    candidate_pair_count = len(datasets)

    # Preallocate the result array.
    result_sims = np.zeros(candidate_pair_count, dtype=np.float64)

    for i, (f0, f1) in enumerate(datasets):
        f0_count = f0.count()
        f1_count = f1.count()
        combined_count = f0_count + f1_count

        if combined_count:
            score: float = (2.0 * (f0 & f1).count() / combined_count)
        else:  # Avoid division by zero.
            score = 0.0

        result_sims[i] = score

    return result_sims
