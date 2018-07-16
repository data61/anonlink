import itertools as _itertools
import math as _math
import numbers as _numbers
import typing as _typing

import mypy_extensions as _mypy_extensions


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
