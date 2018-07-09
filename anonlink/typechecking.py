import array as _array
import numbers as _numbers
import typing as _typing

import mypy_extensions as _mypy_extensions

_Record = _typing.TypeVar('_Record')
Dataset = _typing.Sequence[_Record]

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
    [int, int, _Record],
    _typing.Iterable[_typing.Hashable]]

SimilarityFunction = _typing.Callable[
    [_typing.Sequence[Dataset],
     _numbers.Real,
     _mypy_extensions.DefaultNamedArg(_typing.Optional[_numbers.Integral],
                                      'k')],
    _typing.Tuple[FloatArrayType, _typing.Sequence[IntArrayType]]]
