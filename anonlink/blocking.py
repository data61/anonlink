from abc import ABCMeta, abstractmethod
from itertools import chain, product, repeat
from numbers import Real
from random import Random
from typing import (Any, Callable, Generic, Hashable, Iterable, List,
                    Optional, overload, Sequence, Tuple, TypeVar, Union)

from bitarray import bitarray

from .typechecking import BlockingFunction, Record


_T = TypeVar('_T')
def _evalf(__funcs : Iterable[Callable[..., _T]],
           *args,
           **kwargs) -> Iterable[_T]:
    """ Apply a number of functions to the same arguments.

        Think of this as reverse map. Instead of having one function and
        multiple data, you have multiple functions and one piece of
        data.
    """
    return (f(*args, **kwargs) for f in __funcs)


# http://mypy.readthedocs.io/en/latest/function_overloading.html
@overload
def block_and(
    __funcs: Iterable[BlockingFunction[Record]]
) -> BlockingFunction[Record]:
    ...
@overload
def block_and(
    __func1: BlockingFunction[Record],
    __func2: BlockingFunction[Record],
    *funcs: BlockingFunction[Record]
) -> BlockingFunction[Record]:
    ...
def block_and(*args) -> BlockingFunction[Record]:
    """ Conjunction of multiple blocking functions.

        Records share a block if they share a block in all of the
        functions.

        :param funcs: Functions whose conjunction we return.

        :return: The blocking function.
    """
    if len(args) == 0:
        raise ValueError('at least one argument required')
    elif len(args) == 1:
        funcs = tuple(args[0])
    else:
        funcs = args

    def block_and_inner(
        dataset_index: int,
        record_index: int,
        hash_: Record
    ) -> Iterable[Hashable]:
        funcs_eval = _evalf(funcs, dataset_index, record_index, hash_)
        return product(*funcs_eval)

    return block_and_inner


@overload
def block_or(
    __funcs: Iterable[BlockingFunction[Record]]
) -> BlockingFunction[Record]:
    ...
@overload
def block_or(
    __func1: BlockingFunction[Record],
    __func2: BlockingFunction[Record],
    *funcs: BlockingFunction[Record]
) -> BlockingFunction[Record]:
    ...
def block_or(*args) -> BlockingFunction[Record]:
    """ Disjunction of multiple blocking functions.

        Records share a block if they share a block in any of the
        functions.

        :param funcs: Functions whose disjunction we return.

        :return: The blocking function.
    """
    if len(args) == 0:
        raise ValueError('at least one argument required')
    elif len(args) == 1:
        funcs = tuple(args[0])
    else:
        funcs = args

    def block_or_inner(
        dataset_index: int,
        record_index: int,
        hash_: Record
    ) -> Iterable[Hashable]:
        funcs_eval = _evalf(funcs, dataset_index, record_index, hash_)
        funcs_enum = (zip(repeat(i), f) for i, f in enumerate(funcs_eval))
        return chain.from_iterable(funcs_enum)

    return block_or_inner


def bit_blocking(
    g: int,
    r: int,
    *,
    seed: Any = None
) -> BlockingFunction[bitarray]:
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
    if g < 1:
        msg = 'g is expected to be positive but is {}'.format(g)
        raise ValueError(msg)
    if r < 1:
        msg = 'r is expected to be positive but is {}'.format(r)
        raise ValueError(msg)
    
    hash_len: Optional[int] = None
    hash_indices: Optional[Sequence[Sequence[int]]] = None

    def bit_blocking_inner(
        dataset_index: int,
        record_index: int,
        hash_: bitarray
    ) -> Iterable[Hashable]:
        nonlocal hash_len, hash_indices

        this_hash_len = len(hash_)
        if hash_indices is None:
            # First call.
            hash_len = this_hash_len

            rng = Random(seed)
            # Future: consider keeping track of already chosen indices
            # and avoiding them. This may improve performance by making
            # tables more independent.
            hash_indices = tuple(rng.sample(range(hash_len), r)
                                 for _ in range(g))

        assert hash_len is not None
        if this_hash_len != hash_len:
            raise ValueError('inconsistent hash length')

        assert hash_indices is not None
        for i, table_indices in enumerate(hash_indices):
            vals = map(hash_.__getitem__, table_indices)
            
            # We need to turn this iterable of bools into something
            # hashable. An int will do just fine.
            table_block = sum(b << j for j, b in enumerate(vals))

            # Distinguish between tables.
            yield table_block * len(hash_indices) + i

    return bit_blocking_inner


def continuous_blocking(
    radius: Real,
    source: Sequence[Sequence[Real]]
) -> BlockingFunction[Record]:
    """ Block on continuous variables.

        Split the real number line into overlapping blocks. A quantity
        is in exactly two blocks. Two quantities within `radius` of each
        other are guaranteed to have at least one block in common.

        :param float radius: Two quantities within this radius are
            guaranteed to have at least one block in common.
        :param source: The source as a sequence of sequences of reals.

        :return: The blocking function.
    """
    def continuous_blocking_inner(
        dataset_index: int,
        record_index: int,
        hash_: Record
    ) -> Iterable[Hashable]:
        x = source[dataset_index][record_index]
        r = radius

        bucket_1 = int(x // (2 * r))
        bucket_2 = int((x + r) // (2 * r))

        # Ensure bucket_1 is odd and bucket_2 is even to distinguish.
        return (bucket_1 * 2, bucket_2 * 2 + 1)

    return continuous_blocking_inner


def list_blocking(
    source: Sequence[Sequence[Hashable]]
) -> BlockingFunction[Record]:
    """ Convenience function getting blocks from sequence of sequences.

        :param source: Sequence of sequence of blocks.

        :return: The blocking function.
    """
    def list_blocking_inner(
        dataset_index: int,
        record_index: int,
        hash_: Record
    ) -> Iterable[Hashable]:
        return (source[dataset_index][record_index],)
    
    return list_blocking_inner
