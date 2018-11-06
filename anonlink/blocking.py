"""Blocking functions.

These functions are a probabilistic optimisation of similarity
computation. They aim to avoid comparing all records to each other by
only comparing records that are more likely to be a match. Blocking
generally reduces recall, but does not reduce precision.

Records are split into discrete buckets. A record may belong to multiple
buckets. Generally, two records are compared by a similarity function if
they share at least one bucket.
"""

import itertools as _itertools
import random as _random
import typing as _typing

import bitarray as _bitarray

import anonlink.typechecking as _typechecking


_T = _typing.TypeVar('_T')
def _evalf(__funcs : _typing.Iterable[_typing.Callable[..., _T]],
           *args,
           **kwargs) -> _typing.Iterable[_T]:
    """Apply a number of functions to the same arguments.

    Think of this as reverse map. Instead of having one function and
    multiple data, you have multiple functions and one piece of data.
    """
    return (f(*args, **kwargs) for f in __funcs)


# https://mypy.readthedocs.io/en/stable/more_types.html#function-overloading
@_typing.overload
def block_and(
    __funcs: _typing.Iterable[
        _typechecking.BlockingFunction[_typechecking.Record]]
) -> _typechecking.BlockingFunction[_typechecking.Record]:
    ...
@_typing.overload
def block_and(
    __func1: _typechecking.BlockingFunction[_typechecking.Record],
    __func2: _typechecking.BlockingFunction[_typechecking.Record],
    *funcs: _typechecking.BlockingFunction[_typechecking.Record]
) -> _typechecking.BlockingFunction[_typechecking.Record]:
    ...
def block_and(*args) -> _typechecking.BlockingFunction[_typechecking.Record]:
    """Return conjunction of multiple blocking functions.

    Records share a block if they share a block in all of the functions.

    :param funcs: Functions whose conjunction we return.

    :return: The blocking function.
    """
    if len(args) == 0:
        raise TypeError('expected at least 1 argument, got 0')
    elif len(args) == 1:
        funcs = tuple(args[0])
    else:
        funcs = args

    def block_and_inner(
        dataset_index: int,
        record_index: int,
        hash_: _typechecking.Record
    ) -> _typing.Iterable[_typing.Hashable]:
        funcs_eval = _evalf(funcs, dataset_index, record_index, hash_)
        return _itertools.product(*funcs_eval)

    return block_and_inner


@_typing.overload
def block_or(
    __funcs: _typing.Iterable[
        _typechecking.BlockingFunction[_typechecking.Record]]
) -> _typechecking.BlockingFunction[_typechecking.Record]:
    ...
@_typing.overload
def block_or(
    __func1: _typechecking.BlockingFunction[_typechecking.Record],
    __func2: _typechecking.BlockingFunction[_typechecking.Record],
    *funcs: _typechecking.BlockingFunction[_typechecking.Record]
) -> _typechecking.BlockingFunction[_typechecking.Record]:
    ...
def block_or(*args) -> _typechecking.BlockingFunction[_typechecking.Record]:
    """Return disjunction of multiple blocking functions.

    Records share a block if they share a block in any of the functions.

    :param funcs: Functions whose disjunction we return.

    :return: The blocking function.
    """
    if len(args) == 0:
        raise TypeError('expected at least 1 argument, got 0')
    elif len(args) == 1:
        funcs = tuple(args[0])
    else:
        funcs = args

    def block_or_inner(
        dataset_index: int,
        record_index: int,
        hash_: _typechecking.Record
    ) -> _typing.Iterable[_typing.Hashable]:
        funcs_eval = _evalf(funcs, dataset_index, record_index, hash_)
        funcs_enum = (
            zip(_itertools.repeat(i), f) for i, f in enumerate(funcs_eval))
        return _itertools.chain.from_iterable(funcs_enum)

    return block_or_inner


def bit_blocking(
    g: int,
    r: int,
    *,
    seed: _typing.Any = None
) -> _typechecking.BlockingFunction[_bitarray.bitarray]:
    """Block on bits of the hash.

    This blocking type has the advantage that it doesn't require any
    auxilliary information. Despite this, it is still probabilistic and
    may decrease recall.

    :param int r: The number of bits to use per block.
    :param int g: The number of blocks per record.
    :param seed: Optional seed for pseudorandom number generation. Used
        to keep the results consistent.

    :return: The blocking function.
    """
    if g < 1:
        msg = f'g is expected to be positive but is {g}'
        raise ValueError(msg)
    if r < 1:
        msg = f'r is expected to be positive but is {r}'
        raise ValueError(msg)

    hash_len: _typing.Optional[int] = None
    hash_indices: _typing.Optional[_typing.Sequence[_typing.Sequence[int]]] \
        = None

    def bit_blocking_inner(
        dataset_index: int,
        record_index: int,
        hash_: _bitarray.bitarray
    ) -> _typing.Iterable[_typing.Hashable]:
        nonlocal hash_len, hash_indices

        this_hash_len = len(hash_)
        if hash_indices is None:
            # First call.
            hash_len = this_hash_len

            rng = _random.Random(seed)
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
    radius: float,
    source: _typing.Sequence[_typing.Sequence[float]]
) -> _typechecking.BlockingFunction[_typechecking.Record]:
    """Block on continuous variables.

    Split the real number line into overlapping blocks. A quantity is in
    exactly two blocks. Two quantities within `radius` of each other are
    guaranteed to have at least one block in common.

    :param float radius: Two quantities within this radius are
        guaranteed to have at least one block in common.
    :param source: The source as a sequence of sequences of reals.

    :return: The blocking function.
    """
    if radius <= 0:
        raise ValueError(f'radius should be positive, got {radius}')

    def continuous_blocking_inner(
        dataset_index: int,
        record_index: int,
        hash_: _typechecking.Record
    ) -> _typing.Iterable[_typing.Hashable]:
        x = source[dataset_index][record_index]
        r = radius

        bucket_1 = int(x // (2 * r))
        bucket_2 = int((x + r) // (2 * r))

        # Ensure bucket_1 is odd and bucket_2 is even to distinguish.
        return (bucket_1 * 2, bucket_2 * 2 + 1)

    return continuous_blocking_inner


def list_blocking(
    source: _typing.Sequence[_typing.Sequence[_typing.Hashable]]
) -> _typechecking.BlockingFunction[_typechecking.Record]:
    """Block on the contents of a sequence of sequences.

    This is a simple convenience function. Every inner sequence
    corresponds to a dataset. Every element of an inner sequence
    corresponds to a record.

    :param source: Sequence of sequence of blocks.

    :return: The blocking function.
    """
    def list_blocking_inner(
        dataset_index: int,
        record_index: int,
        hash_: _typechecking.Record
    ) -> _typing.Iterable[_typing.Hashable]:
        return (source[dataset_index][record_index],)

    return list_blocking_inner
