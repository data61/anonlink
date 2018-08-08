from array import array
from itertools import repeat
from numbers import Real
from typing import Optional, Sequence, Tuple

import numpy as np
from bitarray import bitarray

from anonlink.typechecking import FloatArrayType, IntArrayType

__all__ = ['dice_coefficient_python']


def dice_coefficient_python(
    datasets: Sequence[Sequence[bitarray]],
    threshold: Real,
    k: Optional[int] = None
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    """Find Dice coefficients of CLKs.

    This version is written in Python, so it does not rely on
    architecture-specific instructions. It may be slower than an
    accelerated version.

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
            coeffs = (2 * (f0 & f1).count() / (f0_count + f1_count)
                      for f1, f1_count in zip(filters1, f1_counts))
        else:  # Avoid division by zero.
            coeffs = repeat(0., len(filters1))
        
        cands = filter(lambda c: c[1] >= threshold, enumerate(coeffs))
        top_k = sorted(cands, key=lambda x: -x[1])[:k]

        result_sims.extend(sim for _, sim in top_k)
        result_indices0.extend(repeat(i, len(top_k)))
        result_indices1.extend(j for j, _ in top_k)

    np_sims = np.frombuffer(result_sims, dtype=result_sims.typecode)
    np_indices0 = np.frombuffer(result_indices0,
                                dtype=result_indices0.typecode)
    np_indices1 = np.frombuffer(result_indices1,
                                dtype=result_indices1.typecode)
    
    np.negative(np_sims, out=np_sims)  # Sort in reverse.
    # Mergesort is stable. We need that for correct tiebreaking.
    order = np.argsort(np_sims, kind='mergesort')
    np.negative(np_sims, out=np_sims)

    # This modifies the original arrays since they share a buffer.
    np_sims[:] = np_sims[order]
    np_indices0[:] = np_indices0[order]
    np_indices1[:] = np_indices1[order]
    
    return result_sims, (result_indices0, result_indices1)
