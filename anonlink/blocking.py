from abc import ABCMeta, abstractmethod
from itertools import chain, product, repeat
from numbers import Real
from random import Random
from typing import (Any, Callable, Hashable, Iterable, List,
                    Optional, overload, Sequence, Tuple, TypeVar, Union)

from .typechecking import BlockingFunction


_T = TypeVar('_T')
def _evalf(__funcs : 'Iterable[Callable[..., _T]]',  # https://github.com/python/typing/issues/259
           *args,
           **kwargs) -> Iterable[_T]:
    """ Apply a number of functions to the same arguments.

        Think of this as reverse map. Instead of having one function and
        multiple data, you have multiple functions and one piece of
        data.
    """
    return (f(*args, **kwargs) for f in __funcs)


class _AssociativeBinaryOp(metaclass=ABCMeta):
    __slots__ = '_funcs'

    # http://mypy.readthedocs.io/en/latest/function_overloading.html
    @overload
    def __init__(self,
                 __funcs: Iterable[BlockingFunction]
                 ) -> None:
        pass

    @overload
    def __init__(self,
                 __func1: BlockingFunction,
                 __func2: BlockingFunction,
                 *funcs: BlockingFunction
                 ) -> None:
        pass

    def __init__(self, *args):
        if len(args) == 0:
            raise ValueError('at least one argument required')
        elif len(args) == 1:
            self._funcs = tuple(args[0])
        else:
            self._funcs = args

    @abstractmethod
    def __call__(self,
                 dataset_index: int,
                 record_index: int,
                 hash_: Sequence[bool]
                 ) -> Iterable[Hashable]:
        pass


class block_and(_AssociativeBinaryOp):
    """ Conjunction of multiple blocking functions.

        Records share a block if they share a block in all of the
        functions.

        :param funcs: Functions whose conjunction we return.

        :return: The blocking function.
    """
    __slots__ = ()

    def __call__(self,
                 dataset_index: int,
                 record_index: int,
                 hash_: Sequence[bool]
                 ) -> Iterable[Hashable]:
        funcs_eval = _evalf(self._funcs, dataset_index, record_index, hash_)
        return product(*funcs_eval)


class block_or(_AssociativeBinaryOp):
    """ Disjunction of multiple blocking functions.

        Records share a block if they share a block in any of the
        functions.

        :param funcs: Functions whose disjunction we return.

        :return: The blocking function.
    """
    __slots__ = ()

    def __call__(self,
                 dataset_index: int,
                 record_index: int,
                 hash_: Sequence[bool]
                 ) -> Iterable[Hashable]:
        funcs_eval = _evalf(self._funcs, dataset_index, record_index, hash_)
        funcs_enum = (zip(repeat(i), f) for i, f in enumerate(funcs_eval))
        return chain.from_iterable(funcs_enum)


class bit_blocking:
    """ Blocking on bits of the hash.

        This blocking type has the advantage that it doesn't require any
        auxilliary information. Despite this, it is still probabilistic
        and may decrease recall.

        :param int r: The number of bits to use per block.
        :param int g: The number of blocks per record.
        :param seed: Optional seed for pseudorandom number generation.
            Use to keep the results consistent.

        :return: The blocking function.
    """
    
    __slots__ = '_initial_params', '_hash_len', '_hash_indices'

    def __init__(self,
                 g: int,
                 r: int,
                 *,
                 seed: Any = None
                 ) -> None:
        if g < 1:
            msg = 'g is expected to be positive but is {}'.format(g)
            raise ValueError(msg)
        if r < 1:
            msg = 'r is expected to be positive but is {}'.format(r)
            raise ValueError(msg)
        
        self._initial_params = g, r, seed  # type: Optional[Tuple[int, int, Any]]
        self._hash_len = None  # type: Optional[int]
        self._hash_indices = None  # type: Optional[Sequence[Sequence[int]]]

    def _first_call(self,
                    hash_len: int
                    ) -> None:
        assert self._initial_params is not None
        g, r, seed = self._initial_params

        self._hash_len = hash_len

        rng = Random()
        rng.seed(seed)

        # Future: consider keeping track of already chosen indices and
        # avoiding them. This may improve performance by making tables
        # more independent.
        self._hash_indices = tuple(rng.sample(range(hash_len), r)
                                   for _ in range(g))

        self._initial_params = None  # No longer needed.

    def __call__(self,
                 dataset_index: int,
                 record_index: int,
                 hash_: Sequence[bool]
                 ) -> Iterable[Hashable]:
        hash_len = len(hash_)
        if self._hash_indices is None:
            self._first_call(hash_len)

        assert self._hash_len is not None
        if hash_len != self._hash_len:
            raise ValueError('inconsistent hash length')

        hash_indices = self._hash_indices
        assert hash_indices is not None
        for i, table_indices in enumerate(hash_indices):
            vals = map(hash_.__getitem__, table_indices)
            
            # We need to turn this iterable of boolsinto something
            # hashable. An int will do just fine.
            table_block = sum(b << j for j, b in enumerate(vals))

            # Distinguish between tables.
            yield table_block * len(hash_indices) + i


class continuous_blocking:
    """ Block on continuous variables.

        Split the real number line into overlapping blocks. A quantity
        is in exactly two blocks. Two quantities within `radius` of each
        other are guaranteed to have at least one block in common.

        :param float radius: Two quantities within this radius are
            guaranteed to have at least one block in common.
        :param source: The source as a sequence of sequences of reals.

        :return: The blocking function.
    """
    __slots__ = '_radius', '_source'

    def __init__(self,
                 radius: Real,
                 source: Sequence[Sequence[Real]]
                 ) -> None:
        self._radius = radius
        self._source = source

    def __call__(self,
                 dataset_index: int,
                 record_index: int,
                 hash_: Sequence[bool]) -> Iterable[Hashable]:
        x = self._source[dataset_index][record_index]
        r = self._radius

        bucket_1 = int(x // (2 * r))
        bucket_2 = int((x + r) // (2 * r))

        # Ensure bucket_1 is odd and bucket_2 is even to distinguish.
        return (bucket_1 * 2, bucket_2 * 2 + 1)


class list_blocking:
    """ Convenience function getting blocks from sequence of sequences.

        :param source: Sequence of sequence of blocks.

        :return: The blocking function.
    """
    __slots__ = '_source'

    def __init__(self,
                 source: Sequence[Sequence[Hashable]]
                 ) -> None:
        self._source = source

    def __call__(self,
                 dataset_index: int,
                 record_index: int,
                 hash_: Sequence[bool]) -> Iterable[Hashable]:
        return self._source[dataset_index][record_index],
