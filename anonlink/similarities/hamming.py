import collections
import functools
import heapq
import itertools
import operator
from array import array
from typing import (cast, Counter, DefaultDict, Dict, Iterable,
                    List, Optional, Sequence, Tuple)

import numpy as np
from bitarray import bitarray

from anonlink.typechecking import Dataset, FloatArrayType, IntArrayType


_Similarity = Tuple[float, int, int]


def _hamming_sim(clk1: bitarray, clk2: bitarray) -> float:
    assert len(clk1) == len(clk2)
    assert len(clk1) != 0
    return 1 - (clk1 ^ clk2).count() / len(clk1)


def _hamming_sims_gt_threshold(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float
) -> Iterable[_Similarity]:
    dset0, dset1 = datasets
    for i0, clk0 in enumerate(dset0):
        for i1, clk1 in enumerate(dset1):
            sim = _hamming_sim(clk0, clk1)
            if sim >= threshold:
                yield sim, i0, i1


def _hamming_similarity_k(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float,
    k: int
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    # Dictionaries support sparsity, but these could also be list...
    candidates: Tuple[DefaultDict[int, List[_Similarity]], ...] = tuple(collections.defaultdict(list) for _ in datasets)

    for sim, i0, i1 in _hamming_sims_gt_threshold(datasets, threshold):
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


def _hamming_similarity_no_k(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    sims: FloatArrayType = array('d')
    indices0: IntArrayType = array('I')
    indices1: IntArrayType = array('I')
    
    for sim, i0, i1 in sorted(
            _hamming_sims_gt_threshold(datasets, threshold),
            key=lambda x: (-x[0], *x[1:])):
        sims.append(sim)
        indices0.append(i0)
        indices1.append(i1)

    return sims, (indices0, indices1)


def hamming_similarity(
    datasets: Sequence[Dataset[bitarray]],
    threshold: float,
    k: Optional[int]
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    if len(datasets) != 2:
        msg = 'only binary matching is currently supported'
        raise NotImplementedError(msg)
    
    if not datasets[0] or not datasets[1]:
        # Empty result of correct shape
        sims: FloatArrayType = array('d')
        indices0: IntArrayType = array('I')
        indices1: IntArrayType = array('I')
        return sims, (indices0, indices1)

    if k is None:
        sims, indices = _hamming_similarity_no_k(datasets, threshold)
    else:
        sims, indices = _hamming_similarity_k(datasets, threshold, k)

    # Quick sanity checks
    assert len(indices) == 2
    assert len(sims) == len(indices[0]) == len(indices[1])

    return sims, indices
