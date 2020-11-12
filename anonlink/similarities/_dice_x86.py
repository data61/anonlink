from array import array
from itertools import chain, groupby, repeat
from typing import Optional, Sequence, Tuple

from bitarray import bitarray

from anonlink.similarities import _dice
from anonlink.similarities._utils import (sort_similarities_inplace,
                                          to_bitarrays)
from anonlink.typechecking import FloatArrayType, IntArrayType

__all__ = ['dice_coefficient_accelerated']


def _all_equal(iterable):
    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    """Return True if all the elements are equal to each other."""
    g = groupby(iterable)
    return next(g, True) and not next(g, False)


def dice_coefficient_accelerated(
    datasets: Sequence[Sequence[bitarray]],
    threshold: float,
    k: Optional[int] = None
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    """Find Dice coefficients of CLKs.

    This version uses a CPP implementation which will take advantage of
    native x86 popcount instructions.

    We assume all filters are the same length and that this length is a
    multiple of 8 bits.

    The returned pairs are sorted in decreasing order of similarity,
    then in increasing order of the record index in the first dataset,
    and then in increasing order of the record index in the second
    dataset.

    :param datasets: A length 2 sequence of datasets. A dataset is a
        sequence of bitarrays.
    :param threshold: The similarity threshold. We accept pairs that
        have similarity of at least this value.
    :param k: Only permit this many candidate pairs per dataset pair
        per record. Set to `None` to permit all pairs above with
        similarity at least `threshold`.

    :raises NotImplementedError: If an unsupported length filter is
        provided.

    :raises ValueError: If different filter lengths are provided.

    :return: A 2-tuple of similarity scores and indices. The similarity
        scores are an array of floating-point values. The indices are a
        2-tuple of arrays of integers.
    """
    n_datasets = len(datasets)
    if n_datasets < 2:
        raise ValueError(f'not enough datasets (expected 2, got {n_datasets})')
    elif n_datasets > 2:
        raise NotImplementedError(
            f'too many datasets (expected 2, got {n_datasets})')
    filters0, filters1 = datasets
    filters0 = to_bitarrays(filters0)
    filters1 = to_bitarrays(filters1)

    # Create empty output arrays
    result_sims: FloatArrayType = array('d')
    result_indices0: IntArrayType = array('I')
    result_indices1: IntArrayType = array('I')

    if not filters0 or not filters1:
        # Empty result of the correct type.
        return result_sims, (result_indices0, result_indices1)

    length_f0, length_f1 = map(len, datasets)

    # There's no sense in having k > length_f1. Also, k is used to
    # allocate memory below, so we need to protect against an
    # out-of-memory DoS if k is of untrustworthy origin.
    if k is None or k > length_f1:
        k = length_f1

    if not _all_equal(map(len, chain(filters0, filters1))):
        raise ValueError('inconsistent filter length')
    filter_bits = len(filters0[0])
    if filter_bits % 8:
        msg = (f'only filters whose length in bits is a multiple of 8 '
               f'are currently supported (got filter with length '
               f'{filter_bits})')
        raise NotImplementedError(msg)
    filter_bytes = filter_bits // 8
    # Python char arrays of all filters from filters0 and filter1
    carr0, carr1 = array('b'), array('b')

    carr0.frombytes(b''.join(memoryview(f) for f in filters0))
    carr1.frombytes(b''.join(memoryview(f) for f in filters1))

    # Only worth popcounting in C for a large number of filters.
    # Current threshold was found by trying out different values while benchmarking
    POPCOUNT_NATIVE_THRESHOLD = 10000
    if len(filters1) < POPCOUNT_NATIVE_THRESHOLD:
        c_popcounts = array('I', [f.count() for f in filters1])
    else:
        c_popcounts = _dice.popcount_arrays(carr1, filter_bytes)

    _dice.dice_many_to_many(
        carr0, carr1, length_f0, length_f1, c_popcounts, filter_bytes, k,
        threshold, result_sims, result_indices0, result_indices1)

    sort_similarities_inplace(result_sims, result_indices0, result_indices1)

    return result_sims, (result_indices0, result_indices1)

