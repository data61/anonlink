"""Types for typechecking. Aimed at Mypy."""

import array as _array
import numbers as _numbers
import typing as _typing

import mypy_extensions as _mypy_extensions

# This is for parametrisation only. You shouldn't need to import it.
Record = _typing.TypeVar('Record')

Dataset = _typing.Sequence[Record]

if _typing.TYPE_CHECKING:
    FloatArrayType = _array.array[float]
    IntArrayType = _array.array[int]
else:
    FloatArrayType = _array.array
    IntArrayType = _array.array

CandidatePairs = _typing.Tuple[FloatArrayType,
                       _typing.Tuple[IntArrayType, ...],
                       _typing.Tuple[IntArrayType, ...]]

BlockingFunction = _typing.Callable[
    [int, int, Record],
    _typing.Iterable[_typing.Hashable]]

SimilarityFunction = _typing.Callable[
    [_typing.Sequence[Dataset],
     _numbers.Real,
     _mypy_extensions.DefaultNamedArg(_typing.Optional[_numbers.Integral],
                                      'k')],
    _typing.Tuple[FloatArrayType, _typing.Sequence[IntArrayType]]]

DatasetChunkInfo = _mypy_extensions.TypedDict(
    'DatasetChunkInfo',
    {'datasetIndex': int,
     'range': _typing.List[int]})
ChunkInfo = _typing.List[DatasetChunkInfo]
