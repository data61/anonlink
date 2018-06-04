from array import array
from itertools import combinations, repeat
from typing import Optional, Sequence

from .typechecking import (BlockingFunction, CandidatePairs,
                           Record, SimilarityFunction)


def find_candidate_pairs(
    datasets: Sequence[Sequence[Record]],
    similarity_f: SimilarityFunction,
    threshold: float,
    blocking_f: Optional[BlockingFunction] = None,
    k: Optional[int] = None
) -> CandidatePairs:
    """ Find candidate pairs from multiple datasets. Optional blocking.

        :param datasets: A sequence of datasets. Each dataset is a
            sequence of hashes.
        :param similarity_f: A function that computes a similarity
            matrix between two sequences of hashes and finds candidates
            above the threshold.
        :param threshold: The similarity threshold. We accept pairs that
            have similarity above this value.
        :param blocking_f: A function returning all block IDs for a
            record. Two records are compared iff they have at least one
            block ID in common.
        :param k: Only consider the top `k` candidate partners from any
            one dataset for any particular record. Leave as `None` to
            keep all pairs with similarity above `threshold`.

        :return: A 3-tuple `(dataset_i, record_i, similarity)`. 
            `dataset_i` and `record_i` are sequences of sequences. 
            `similarity` as well as every sequence in `dataset_i` and in
            `record_i` as well as are of equal length. Currently
            `dataset_i` and `record_i` have length 2, but this may be
            changed in the future.

                Every valid index `i` corresponds to one candidate
            match. `dataset[0][i]` is the index of the dataset of the
            first record in the pair; `record[0][i]` is this record's
            index in its dataset. `dataset_[1][i]` is the index of the
            dataset of the secod record in the pair; `record_[1][i]` is
            this record's index in its dataset. `similarity[i]` is the
            pair's similarity; this value will be greater than
            `threshold`.
        """
    if blocking_f is not None:
        raise NotImplementedError('blocking is not yet implemented')

    if k is not None:
        raise NotImplementedError('k is not yet implemented')

    dataset_is0 = array('I')
    dataset_is1 = array('I')
    record_is0 = array('I')
    record_is1 = array('I')
    sims = array('d')  # type: array[float]

    for (i0, dataset0), (i1, dataset1) in combinations(enumerate(datasets), 2):
        (record_i0, record_i1), sim = similarity_f(
            (dataset0, dataset1), threshold, k)

        n = len(sim)
        assert len(record_i0) == n
        assert len(record_i1) == n

        dataset_is0.extend(repeat(i0, n))
        dataset_is1.extend(repeat(i1, n))
        record_is0.extend(record_i0)
        record_is1.extend(record_i1)
        sims.extend(sim)

    assert (len(dataset_is0) == len(dataset_is1)
            == len(record_is0) == len(record_is0)
            == len(sims))
    return (dataset_is0, dataset_is1), (record_is0, record_is1), sims
