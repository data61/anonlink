from array import array

from typing import (Callable, Hashable, Iterable, Mapping,
                    Optional, Sequence, Set, Tuple, TYPE_CHECKING)


Record = Sequence[bool]

if TYPE_CHECKING:
    FloatArrayType = array[float]
    IntArrayType = array[int]
else:
    FloatArrayType = array
    IntArrayType = array

CandidatePairs = Tuple[FloatArrayType,
                       Tuple[IntArrayType, ...],
                       Tuple[IntArrayType, ...]]

BlockingFunction = Callable[[int, int, Record],
                            Iterable[Hashable]]

SimilarityFunction = Callable[
    [Sequence[Sequence[Record]], float, Optional[int]],
    Tuple[Sequence[Sequence[int]], Sequence[float]]]

RecordId = Tuple[int, int]

MatchedGroup = Set[RecordId]

SolvingFunction = Callable[[CandidatePairs, float],
    Mapping[RecordId, MatchedGroup]]
