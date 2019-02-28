from array import array
from itertools import chain, groupby, repeat
from typing import Optional, Sequence, Tuple

from bitarray import bitarray

from anonlink._entitymatcher import ffi, lib
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

    This version uses x86 popcount instructions.

    We assume all filters are the same length and that this length is a
    multiple of 64 bits.

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

    result_sims: FloatArrayType = array('d')
    result_indices0: IntArrayType = array('I')
    result_indices1: IntArrayType = array('I')

    if not filters0 or not filters1:
        # Empty result of the correct type.
        return result_sims, (result_indices0, result_indices1)

    length_f0, length_f1 = map(len, datasets)

    # There's no sense in having k > length_f1. Also, k is passed to
    # ffi.new(...) below, so we need to protect against an
    # out-of-memory DoS if k is of untrustworthy origin.
    if k is None or k > length_f1:
        k = length_f1

    if not _all_equal(map(len, chain(filters0, filters1))):
        raise ValueError('inconsistent filter length')
    filter_bits = len(filters0[0])
    if filter_bits % 64:
        msg = (f'only filters whose length in bits is a multiple of 64 '
               f'are currently supported (got filter with length '
               f'{filter_bits})')
        raise NotImplementedError(msg)
    filter_bytes = filter_bits // 8

    # Space for one filter. We will fill it with one filter from
    # filters0 at a time.
    carr0 = ffi.new('char[]', filter_bytes)

    # Array of all filters from filters1.
    carr1 = ffi.new(f"char[{filter_bytes * length_f1}]",
                    b''.join(f.tobytes() for f in filters1))

    c_popcounts = ffi.new(f"uint32_t[{length_f1}]",
                          tuple(f.count() for f in filters1))

    # easier to do all buffer allocations in Python and pass them to C,
    # even for output-only arguments
    c_scores = ffi.new("double[]", k)
    c_indices = ffi.new("int[]", k)

    for i, f0 in enumerate(filters0):
        carr0[0:filter_bytes] = f0.tobytes()
        matches = lib.match_one_against_many_dice_k_top(
            carr0,
            carr1,
            c_popcounts,
            length_f1,
            filter_bytes,
            k,
            threshold,
            c_indices,
            c_scores)

        if matches < 0:
            raise RuntimeError('bad key length')

        result_sims.extend(c_scores[0:matches])
        result_indices0.extend(repeat(i, matches))
        result_indices1.extend(c_indices[0:matches])

    sort_similarities_inplace(result_sims, result_indices0, result_indices1)

    return result_sims, (result_indices0, result_indices1)
