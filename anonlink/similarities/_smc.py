import collections
import heapq
from array import array
from typing import (Counter, DefaultDict, Iterable,
                    List, Optional, Sequence, Tuple)

from bitarray import bitarray

from anonlink import _deprecation
from anonlink.typechecking import Dataset, FloatArrayType, IntArrayType

__all__ = ['hamming_similarity', 'simple_matching_coefficient']

_Similarity = Tuple[float, int, int]

_deprecated_decorator = _deprecation.make_decorator('similarities')


def _smc_sim(clk1: bitarray, clk2: bitarray) -> float:
    n = len(clk1)
    return (n - (clk1 ^ clk2).count()) / n


def _smc_sims_gt_threshold(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float
) -> Iterable[_Similarity]:
    dset0, dset1 = datasets
    for i0, clk0 in enumerate(dset0):
        for i1, clk1 in enumerate(dset1):
            sim = _smc_sim(clk0, clk1)
            if sim >= threshold:
                yield sim, i0, i1


def _smc_similarity_k(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float,
    k: int
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    # Dictionaries support sparsity, but these could also be list...
    candidates: Tuple[DefaultDict[int, List[_Similarity]], ...] \
        = tuple(collections.defaultdict(list) for _ in datasets)

    for sim, i0, i1 in _smc_sims_gt_threshold(datasets, threshold):
        c = sim, i0, i1
        candidates[0][i0].append(c)
        candidates[1][i1].append(c)
            
    # Take the best k candidates for each record and count them
    pair_counter: Counter[_Similarity] = collections.Counter()
    for dset_cands in candidates:
        for unfiltered_cands in dset_cands.values():
            best = heapq.nsmallest(k, unfiltered_cands,
                                   key=lambda x:(-x[0], *x[1:]))
            pair_counter.update(best)

    sims: FloatArrayType = array('d')
    indices0: IntArrayType = array('I')
    indices1: IntArrayType = array('I')
    for pair in pair_counter:
        if pair_counter[pair] == 2:
            sim, i0, i1 = pair
            sims.append(sim)
            indices0.append(i0)
            indices1.append(i1)

    return sims, (indices0, indices1)


def _smc_similarity_no_k(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    sims: FloatArrayType = array('d')
    indices0: IntArrayType = array('I')
    indices1: IntArrayType = array('I')
    
    for sim, i0, i1 in sorted(
            _smc_sims_gt_threshold(datasets, threshold),
            key=lambda x: (-x[0], *x[1:])):
        sims.append(sim)
        indices0.append(i0)
        indices1.append(i1)

    return sims, (indices0, indices1)


def simple_matching_coefficient(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float,
    k: Optional[int]
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    """Find Simple Matching Coefficients (SMCs) of CLKs.

    The SMC of two binary strings is defined as
    1 - (Hamming distance) / (string length).

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
    if len(datasets) != 2:
        msg = 'only binary matching is currently supported'
        raise NotImplementedError(msg)

    if k is None:
        sims, indices = _smc_similarity_no_k(datasets, threshold)
    else:
        sims, indices = _smc_similarity_k(datasets, threshold, k)

    # Quick sanity checks
    assert len(indices) == 2
    assert len(sims) == len(indices[0]) == len(indices[1])

    return sims, indices


@_deprecated_decorator(replacement='similarities.simple_matching_coefficient')
def hamming_similarity(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float,
    k: Optional[int]
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    return simple_matching_coefficient(datasets, threshold, k)
hamming_similarity.__doc__ = simple_matching_coefficient.__doc__
