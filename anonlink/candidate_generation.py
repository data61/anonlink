"""Finding candidate pairs from multiple datasets."""

import array as _array
import heapq as _heapq
import itertools as _itertools
import numbers as _numbers
import typing as _typing

import anonlink.typechecking as _typechecking

_OnePairSimilarities = _typing.Tuple[
    _typing.Tuple[int, int],
    _typing.Tuple[_typechecking.FloatArrayType,
                  _typing.Sequence[_typechecking.IntArrayType]]]


def _merge_similarities(
    similarities: _typing.Sequence[_OnePairSimilarities]
) -> _typechecking.CandidatePairs:
    # Merge similarities in sorted order.
    # This is almost certainly an inefficient way of doing this, but
    # it's hard to get anything more efficient in pure Python.
    # Future: redo this in Cython, which has the ability to directly
    # modify and resize array buffers.
    if not similarities:
        # Empty but correct type.
        return (_array.array('d'),
                (_array.array('I'), _array.array('I')),
                (_array.array('I'), _array.array('I')))

    similarities_iters = (
        zip(sims, _itertools.repeat(dataset_is), zip(*record_is))
        for dataset_is, (sims, record_is) in similarities)
    merged_similarities = _heapq.merge(*similarities_iters,
                                       key=lambda x: (-x[0], *x[1:]))

    # Assume all arrays are the same type.
    # Future: this may require changing.
    fst_datset_is, (fst_sims, fst_record_is) = similarities[0]
    result_sims: _typechecking.FloatArrayType = _array.array(fst_sims.typecode)
    result_dataset_is: _typing.Tuple[_typechecking.IntArrayType, ...] \
        = tuple(_array.array('I') for _ in fst_datset_is)
    result_record_is: _typing.Tuple[_typechecking.IntArrayType, ...] \
        = tuple(_array.array(f.typecode) for f in fst_record_is)
    for sim, dataset_is, record_is in merged_similarities:
        result_sims.append(sim)
        for result_dataset_i, dataset_i in zip(result_dataset_is, dataset_is):
            result_dataset_i.append(dataset_i)
        for result_record_i, record_i in zip(result_record_is, record_is):
            result_record_i.append(record_i)
    return result_sims, result_dataset_is, result_record_is


def find_candidate_pairs(
    datasets: _typing.Sequence[_typechecking.Dataset],
    similarity_f: _typechecking.SimilarityFunction,
    threshold: _numbers.Real,
    k: _typing.Optional[_numbers.Integral] = None,
    blocking_f: _typing.Optional[_typechecking.BlockingFunction] = None
) -> _typechecking.CandidatePairs:
    """Find candidate pairs from multiple datasets. Optional blocking.

    :param datasets: A sequence of datasets. Each dataset is a sequence
        of hashes.
    :param similarity_f: A function that computes a similarity matrix
        between two sequences of hashes and finds candidates above the
        threshold.
    :param threshold: The similarity threshold. We accept pairs that
        have similarity of at least this value.
    :param k: Only permit this many candidate pairs per dataset pair per
        record. Set to `None` to permit all pairs above with similarity
        at least `threshold`.
    :param blocking_f: Not yet implemented. Future: A function returning
        all block IDs for a record. Two records are compared iff they
        have at least one block ID in common.

    :return: A 3-tuple `(similarity, dataset_i, record_i)`. `dataset_i`
        and `record_i` are sequences of sequences. Every sequence in
        `dataset_i` has the same length as `similarity`; also, every
        sequence in `record_i` has the same length as `similarity`.
        Currently `dataset_i` and `record_i` have length 2, but this may
        be changed in the future.
            Every valid index `i` corresponds to one candidate match.
        `dataset[0][i]` is the index of the dataset of the first record
        in the pair; `record[0][i]` is this record's index in its
        dataset. `dataset_[1][i]` is the index of the dataset of the
        second record in the pair; `record_[1][i]` is this record's
        index in its dataset. `similarity[i]` is the pair's similarity;
        this value will be greater than `threshold`.
        """
    if blocking_f is not None:
        raise NotImplementedError('blocking is not yet implemented')

    similarities = []
    for (i0, dataset0), (i1, dataset1) \
            in _itertools.combinations(enumerate(datasets), 2):
        similarity = similarity_f((dataset0, dataset1), threshold, k=k)
        similarities.append(((i0, i1), similarity))

    return _merge_similarities(similarities)
