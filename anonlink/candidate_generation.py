"""Finding candidate pairs from multiple datasets."""

import array as _array
import collections as _collections
import heapq as _heapq
import itertools as _itertools
import typing as _typing

import anonlink.typechecking as _typechecking

_Block = _typing.Tuple[_typing.List[int], ...]
_CandidatePair = _typing.Tuple[float, int, int, int, int]
_CandidatePairIterable = _typing.Iterable[_CandidatePair]


def _to_candidate_pairs(
    sims: _typing.Iterable[float],
    rec_is0: _typing.Iterable[int],
    rec_is1: _typing.Iterable[int],
    i0: int,
    i1: int,
    block: _typing.Sequence[_typing.Sequence[int]]
) -> _CandidatePairIterable:
    return ((sim, i0, i1, block[i0][rec_i0], block[i1][rec_i1])
            for sim, rec_i0, rec_i1 in zip(sims, rec_is0, rec_is1))


def _block_similarities(
    block: _Block,
    datasets: _typing.Sequence[_typechecking.Dataset],
    similarity_f: _typechecking.SimilarityFunction,
    threshold: float,
    k: _typing.Optional[int]
) -> _typing.Iterable[_CandidatePairIterable]:
    for i0, i1 in _itertools.combinations(range(len(block)), 2):
        recs_dset0 = tuple(map(datasets[i0].__getitem__, block[i0]))
        recs_dset1 = tuple(map(datasets[i1].__getitem__, block[i1]))
        sims, (rec_is0, rec_is1) = similarity_f(
            (recs_dset0, recs_dset1), threshold, k=k)

        yield _to_candidate_pairs(sims, rec_is0, rec_is1, i0, i1, block)


def _enforce_k(
    similarities: _CandidatePairIterable,
    k: int
) -> _CandidatePairIterable:
    candidates_counter: _typing.Counter[_typing.Tuple[int, int, int]] \
        = _collections.Counter()
    for similarity in similarities:
        _, dset_i0, dset_i1, rec_i0, rec_i1 = similarity
        # At most k candidate pairs per record per dataset pair.
        i0 = dset_i0, dset_i1, rec_i1
        i1 = dset_i1, dset_i0, rec_i0
        candidates_counter[i0] += 1
        candidates_counter[i1] += 1
        if candidates_counter[i0] <= k and candidates_counter[i1] <= k:
            yield similarity


def _merge_similarities(
    similarities: _typing.Iterable[_CandidatePairIterable],
    k: _typing.Optional[int]
) -> _typechecking.CandidatePairs:
    # Merge multiple sorted sequences
    sorted_similarities = _heapq.merge(*similarities,
                                       key=lambda x: (-x[0], *x[1:]))
    
    # One record can be in multiple blocks. Remove duplicates.
    deduplicated_similarities = (
        k for k, _ in _itertools.groupby(sorted_similarities))
    
    if k is None:
        k_enforced_similarities: _CandidatePairIterable \
            = deduplicated_similarities
    else:
        k_enforced_similarities = _enforce_k(deduplicated_similarities, k)

    # Assume all arrays are the same type.
    # Future: this may require changing.
    sims: _typechecking.FloatArrayType = _array.array('d')
    dset_is0: _typechecking.IntArrayType = _array.array('I')
    dset_is1: _typechecking.IntArrayType = _array.array('I')
    rec_is0: _typechecking.IntArrayType = _array.array('I')
    rec_is1: _typechecking.IntArrayType = _array.array('I')
    for sim, dset_i0, dset_i1, rec_i0, rec_i1 in k_enforced_similarities:
        sims.append(sim)
        dset_is0.append(dset_i0)
        dset_is1.append(dset_i1)
        rec_is0.append(rec_i0)
        rec_is1.append(rec_i1)
    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)


def find_candidate_pairs(
    datasets: _typing.Sequence[_typechecking.Dataset],
    similarity_f: _typechecking.SimilarityFunction,
    threshold: float,
    k: _typing.Optional[int] = None,
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
    :param blocking_f: A function returning all block IDs for a record.
        Two records are compared iff they have at least one block ID in
        common. Support for this is experimental and subject to change.

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
    if blocking_f is None:
        # Dummy blocking function.
        def blocking_f(dataset_index, record_index, hash_):
            return None,
    assert blocking_f is not None  # This is for Mypy.

    blocks: _typing.DefaultDict[_typing.Hashable, _Block] \
        = _collections.defaultdict(lambda: tuple([] for _ in datasets))
    for i, dataset in enumerate(datasets):
        for j, record in enumerate(dataset):
            for block_id in blocking_f(i, j, record):
                blocks[block_id][i].append(j)

    similarities = tuple(_itertools.chain.from_iterable(
        map(_block_similarities,
            blocks.values(),
            _itertools.repeat(datasets),
            _itertools.repeat(similarity_f),
            _itertools.repeat(threshold),
            _itertools.repeat(k))))

    return _merge_similarities(similarities, k)
