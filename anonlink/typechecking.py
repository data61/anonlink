from typing import (Callable, Hashable, Iterable, Mapping,
                    Optional, Sequence, Set, Tuple)


Record = Sequence[bool]

CandidatePairs = Tuple[Sequence[Sequence[int]],
                       Sequence[Sequence[int]],
                       Sequence[float]]

BlockingFunction = Callable[[int, int, Record],
                            Iterable[Hashable]]

SimilarityFunction = Callable[
    [Sequence[Sequence[Record]], float, Optional[int]],
    Tuple[Sequence[Sequence[int]], Sequence[float]]]

RecordId = Tuple[int, int]

MatchedGroup = Set[RecordId]

SolvingFunction = Callable[[CandidatePairs, float],
    Mapping[RecordId, MatchedGroup]]
