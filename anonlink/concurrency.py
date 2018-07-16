import itertools as _itertools
import math as _math
import numbers as _numbers
import typing as _typing

import mypy_extensions as _mypy_extensions


# Future: There may be better ways of chunking. Hamish suggests putting
# a better guarantee on the maximum size of a chunk. This may help with
# optimisation (e.g., set chunk size to be the size of a page,
# eliminating page faults).
# As the function currently makes no guarantees, any such changes would
# be backwards compatible.


ChunkInfo = _mypy_extensions.TypedDict(
    'ChunkInfo',
    {'datasetIndices': _typing.List[int],
     'ranges': _typing.List[_typing.List[int]]})


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
    chunk_size_aim: _numbers.Real,
    *,
    # Keyword-only for forwards compatibility: this argument may not be
    # needed once we do blocking
    dataset_sizes: _typing.Sequence[_numbers.Integral]
) -> _typing.Iterable[ChunkInfo]:
    """Split datasets into chunks for parallel processing.

    Resulting chunks are dictionaries with two keys: "datasetIndices"
    and "ranges". The value for "datasetIndices" is a length 2 list of
    the two datasets that we are comparing in this chunk. The value for
    "ranges" is a length 2 list of ranges within those datasets. A range
    is a length 2 list [a, b] representing range(a, b).

    For example, {"datasetIndices": [2, 4], "ranges": [[3, 21], [18, 20]]}
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
        if not size0 and not size1:
            continue
        chunks0 = round(size0 / _math.sqrt(chunk_size_aim_float)) or 1
        chunk_size0 = size0 / chunks0
        # chunk_size0 is unlikely to be exactly sqrt(chunk_size_aim).
        # Adjust goal chunk size for the second dataset.
        chunks1 = round(size1 * chunk_size0 / chunk_size_aim_float) or 1
        for c0, c1 in _itertools.product(
                _chunks_1d(size0, chunks0), _chunks_1d(size1, chunks1)):
            yield {'datasetIndices': [i0, i1], 'ranges': [c0, c1]}
