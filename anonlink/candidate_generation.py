from array import array
from itertools import combinations, repeat
from heapq import merge
from numbers import Real
from typing import Optional, Sequence

from .typechecking import (BlockingFunction, CandidatePairs,
                           Record, SimilarityFunction)


def _merge_similarities(similarities):
    # Merge similarities in sorted order.
    # This is almost certainly an inefficient way of doing this, but
    # it's hard to get anything more efficient in pure Python.
    # Future: redo this in Cython, which has the ability to directly
    # modify and resize array buffers.
    if not similarities:
        raise ValueError('empty similarities')
    similarities_iters = (zip(sims, repeat(dataset_is), zip(*record_is))
                          for dataset_is, (sims, record_is) in similarities)
    merged_similarities = merge(*similarities_iters,
                                key=lambda x: (-x[0],) + x[1:])
    
    # Assume all arrays are the same type.
    # Future: this may require changing.
    fst_datset_is, (fst_sims, fst_record_is) = similarities[0]
    result_sims = array(fst_sims.typecode)
    result_dataset_is = tuple(array('I') for _ in fst_datset_is)
    result_record_is = tuple(array(f.typecode) for f in fst_record_is)
    for sim, dataset_is, record_is in merged_similarities:
        result_sims.append(sim)
        for result_dataset_i, dataset_i in zip(result_dataset_is, dataset_is):
            result_dataset_i.append(dataset_i)
        for result_record_i, record_i in zip(result_record_is, record_is):
            result_record_i.append(record_i)
    return result_sims, result_dataset_is, result_record_is


def find_candidate_pairs(
    datasets: Sequence[Sequence[Record]],
    similarity_f: SimilarityFunction,
    threshold: Real,
    k: Optional[int] = None,
    blocking_f: BlockingFunction = None
) -> CandidatePairs:
    """ Find candidate pairs from multiple datasets. Optional blocking.

        :param datasets: A sequence of datasets. Each dataset is a
            sequence of hashes.
        :param similarity_f: A function that computes a similarity
            matrix between two sequences of hashes and finds candidates
            above the threshold.
        :param threshold: The similarity threshold. We accept pairs that
            have similarity above this value.
        :param 

        :return: A 3-tuple `(similarity, dataset_i, record_i)`. 
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

    # Computational shortcuts
    if len(datasets) < 2:
        # Empty result of correct type
        return array('d'), (array('I'), array('I')), (array('I'), array('I'))
    if len(datasets) == 2:
        sims, record_is = similarity_f(datasets, threshold, k=k)
        n = len(sims)
        assert all(len(r) == n for r in record_is)
        return (sims,
                (array('I', repeat(0, n)) , array('I', repeat(1, n))),
                record_is)

    similarities = []
    for (i0, dataset0), (i1, dataset1) in combinations(enumerate(datasets), 2):
        similarity = similarity_f((dataset0, dataset1), threshold, k=k)
        similarities.append(((i0, i1), similarity))

    return _merge_similarities(similarities)


