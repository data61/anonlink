import collections
import functools
import heapq
import itertools
import operator
from typing import Counter, DefaultDict, Dict, List, Optional, Sequence, Tuple

import numpy as np

from .typechecking import Record


def _hamming_sim_f(clk1: Record, clk2: Record) -> float:
    assert len(clk1) == len(clk2)
    assert len(clk1) != 0
    return sum(map(operator.eq, clk1, clk2)) / len(clk1)


def _hamming_similarity_k(
    datasets: Sequence[Sequence[Record]],
    threshold: float,
    k: int
) -> Tuple[Sequence[Sequence[int]], Sequence[float]]:
    # Dictionaries support sparsity, but these could also be list...
    candidates = tuple(collections.defaultdict(list) for _ in datasets)  # type: Tuple[DefaultDict[int, List], ...]

    for records in itertools.product(enumerate(datasets[0]),
                                     enumerate(datasets[1])):
        (i0, clk0), (i1, clk1) = records
        sim = _hamming_sim_f(clk0, clk1)

        if sim >= threshold:
            c = sim, (i0, i1)
            candidates[0][i0].append(c)
            candidates[1][i1].append(c)

    # Take the best k candidates for each record and count them
    pair_counter = collections.Counter()  # type: Counter[Tuple[float, Tuple[int, int]]]
    for dset_cands in candidates:
        for unfiltered_cands in dset_cands.values():
            pair_counter.update(heapq.nlargest(k, unfiltered_cands))

    result_pairs = tuple(filter(lambda pair: pair_counter[pair] == 2,
                                pair_counter))
    # Make into arrays
    if result_pairs:
        sims, indices = zip(*result_pairs)
        sims_arr = np.array(sims, dtype=float)
        indices_arr = np.array(indices, dtype=int, order='F').T
        assert len(sims_arr.shape) == 1
        assert len(indices_arr.shape) == 2
        assert indices_arr.shape[0] == 2
        assert indices_arr.shape[1] == sims_arr.shape[0]
    else:
        sims_arr = np.empty((0,), dtype=float)
        indices_arr = np.empty((2,0), dtype=int)

    return indices_arr, sims_arr


def _hamming_similarity_no_k(
    datasets: Sequence[Sequence[Record]],
    threshold: float
) -> Tuple[Sequence[Sequence[int]], Sequence[float]]:
    sims = []
    indices = [], []  # type: Tuple[List[int], List[int]]
    for records in itertools.product(enumerate(datasets[0]),
                                     enumerate(datasets[1])):
        (i0, clk0), (i1, clk1) = records
        sim = _hamming_sim_f(clk0, clk1)

        if sim >= threshold:
            sims.append(sim)
            indices[0].append(i0)
            indices[1].append(i1)

    if sims:
        assert all(indices)
        # Make into arrays
        sims_arr = np.array(sims, dtype=float)
        indices_arr = np.array(indices, dtype=int)
    else:
        assert not any(indices)
        sims_arr = np.empty((0,), dtype=float)
        indices_arr = np.empty((2,0), dtype=int)

    return indices_arr, sims_arr


def hamming_similarity(
    datasets: Sequence[Sequence[Record]],
    threshold: float,
    k: Optional[int]
) -> Tuple[Sequence[Sequence[int]], Sequence[float]]:
    if len(datasets) != 2:
        msg = 'only binary matching is currently supported'
        raise NotImplementedError(msg)
    
    # Explicitly test for len to support NumPy
    if not len(datasets) or not all(map(len,datasets)):
        return ((), ()), ()
    else:
        n = len(datasets[0][0])
        if any(len(record) != n for dataset in datasets for record in dataset):
            raise ValueError('inconsistent hash length')

    if k is None:
        indices, sims = _hamming_similarity_no_k(datasets, threshold)
    else:
        indices, sims = _hamming_similarity_k(datasets, threshold, k)

    # Quick sanity checks
    assert len(sims.shape) == 1
    assert len(indices.shape) == 2
    assert indices.shape[0] == 2
    assert indices.shape[1] == sims.shape[0]

    return indices, sims
