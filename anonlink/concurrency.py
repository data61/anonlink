"""Helpers for concurrency."""

import array as _array
import itertools as _itertools
import math as _math
import typing as _typing

import numpy as _np

import anonlink.typechecking as _typechecking

# Future: There may be better ways of chunking. Hamish suggests putting
# a better guarantee on the maximum size of a chunk. This may help with
# optimisation (e.g., set chunk size to be the size of a page,
# eliminating page faults).
# As the function currently makes no guarantees, any such changes would
# be backwards compatible.


def _split_points(size: int, chunks: int) -> _typing.Iterator[int]:
    chunk_size = size / chunks
    for i in range(chunks):
        yield round(i * chunk_size)
    yield size


def _chunks_1d(
    size: int,
    chunks: int
) -> _typing.Iterable[_typing.List[int]]:
    split_points = _split_points(size, chunks)
    a = next(split_points)
    for b in split_points:
        yield [a, b]
        a = b


def split_to_chunks(
    chunk_size_aim: float,
    *,
    # Keyword-only for forwards compatibility: this argument may not be
    # needed once we do blocking
    dataset_sizes: _typing.Sequence[int]
) -> _typing.Iterable[_typechecking.ChunkInfo]:
    """Split datasets into chunks for parallel processing.

    Resulting chunks are length 2 list of dictionaries. Each dictionary
    represents one data source for the chunk: it has a 'datasetIndex'
    key which maps to the index of the dataset as an integer, and it has
    a 'range' key mapping to the range of records within this dataset. A
    range is a length 2 list [a, b] representing range(a, b).

    Example: [{"datasetIndex": 2, "range": [3, 21]},
              {"datasetIndex": 4, "range": [18, 20]}]
    means that this chunk compares (0-indexed) datasets 2 and 4. We are
    looking at elements 3-20 (inclusive) of dataset 2 and elements 18
    and 19 of dataset 4.

    The chunks are always JSON serialisable.

    :param chunk_size_aim: Number of comparisons per chunk to aim for.
        This is a hint only. No promises.
    :param datset_sizes: The sizes of the datsets to compare, as a
        sequence.

    :return: An iterable of chunks.
    """

    # int-like and float-like types such as np.int64 are welcome but are
    # not JSON-serialisable.
    chunk_size_aim_float = float(chunk_size_aim)
    dataset_sizes_int = map(int, dataset_sizes)
    for (i0, size0), (i1, size1) in _itertools.combinations(
            enumerate(dataset_sizes_int), 2):
        if not size0 or not size1:
            continue
        chunks0 = round(size0 / _math.sqrt(chunk_size_aim_float)) or 1
        chunk_size0 = size0 / chunks0
        # chunk_size0 is unlikely to be exactly sqrt(chunk_size_aim).
        # Adjust goal chunk size for the second dataset.
        chunks1 = round(size1 * chunk_size0 / chunk_size_aim_float) or 1
        for c0, c1 in _itertools.product(
                _chunks_1d(size0, chunks0), _chunks_1d(size1, chunks1)):
            yield [{'datasetIndex': i0, 'range': c0},
                   {'datasetIndex': i1, 'range': c1}]


def _get_dataset_indices(
    dataset_chunk: _typechecking.DatasetChunkInfo,
    size: int
) -> _typechecking.IntArrayType:
    index = dataset_chunk['datasetIndex']
    return _array.array('I', (index,)) * size


def _offset_record_indices_inplace(
    dataset_chunk: _typechecking.DatasetChunkInfo,
    rec_is: _typechecking.IntArrayType
) -> None:
    a, _ = dataset_chunk['range']
    np_rec_is = _np.frombuffer(rec_is, dtype=rec_is.typecode)
    np_rec_is += a


def process_chunk(
    chunk: _typechecking.ChunkInfo,
    datasets: _typing.Sequence[_typechecking.Dataset],
    similarity_f: _typechecking.SimilarityFunction,
    threshold: float,
    k: _typing.Optional[int] = None
) -> _typechecking.CandidatePairs:
    """Find candidate pairs for the chunk.

    Calls the similarity function, offsets record indices by the
    required amount, and adds dataset index information.

    :param chunk: Chunk to process, as returned by `split_to_chunks`.
    :param datasets: A sequence of two datasets. Each dataset should
        contain as many records as required by `chunk`. It is up to you
        to extract the correct range from the larger dataset.
    :param similarity_f: A function that computes a similarity matrix
        between two sequences of hashes and finds candidates above the
        threshold.
    :param threshold: The similarity threshold. We accept pairs that
        have similarity of at least this value.
    :param k: Only permit this many candidate pairs per dataset pair per
        record. Set to `None` to permit all pairs above with similarity
        at least `threshold`.

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


    if len(chunk) != len(datasets):
        raise ValueError(
            f'number of datasets does not match chunk (expected {len(chunk)}, '
            f'got {len(datasets)})')
    for i, dataset_chunk in enumerate(chunk):
        if 'datasetIndex' not in dataset_chunk:
            raise ValueError(f"invalid chunk: expected value for "
                             f"'datasetIndex' at index {i}")
        if 'range' not in dataset_chunk:
            raise ValueError(f"invalid chunk: expected value for "
                             f"'range' at index {i}")
    for i, dataset_chunk, dataset_records in zip(
                _itertools.count(), chunk, datasets):
        a, b = dataset_chunk['range']
        if len(dataset_records) != b - a:
            raise ValueError(
                f'size of dataset at index {i} does not match chunk (expected '
                f'{b - a}, got {len(dataset_records)})')
    if len(chunk) != 2:
        raise NotImplementedError(
            f'only binary matching is currently supported '
            f'(chunk has {len(chunk)} datasets)')


    sims, (rec_is0, rec_is1) = similarity_f(datasets, threshold, k=k)
    assert len(sims) == len(rec_is0) == len(rec_is1)

    dset_is0 = _get_dataset_indices(chunk[0], len(sims))
    _offset_record_indices_inplace(chunk[0], rec_is0)

    dset_is1 = _get_dataset_indices(chunk[1], len(sims))
    _offset_record_indices_inplace(chunk[1], rec_is1)

    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)
