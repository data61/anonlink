from array import array
from itertools import repeat
from numbers import Real
from typing import Optional, Sequence, Tuple

from bitarray import bitarray

from anonlink.typechecking import FloatArrayType, IntArrayType
from anonlink._entitymatcher import ffi, lib


def dice_coefficient_accelerated(
    datasets: Sequence[Sequence[bitarray]],
    threshold: Real,
    k: Optional[int] = None
) -> Tuple[FloatArrayType, Tuple[IntArrayType, ...]]:
    """Find Dice coefficients of CLKs.

    This version uses x86 popcount instructions.

    We assume all filters are the same length, being a multiple of 64
    bits.

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
        raise ValueError(f'too many datasets (expected 2, got {n_datasets})')
    filters0, filters1 = datasets

    result_sims = array('d')
    result_indices0 = array('I')
    result_indices1 = array('I')

    if not filters0 or not filters1:
        # Empty result of the correct type.
        return result_sims, (result_indices0, result_indices1)

    length_f0, length_f1 = map(len, datasets)

    # There's no sense in having k > length_f1. Also, k is passed to
    # ffi.new(...) below, so we need to protect against an
    # out-of-memory DoS if k is of untrustworthy origin.
    if k is None or k > length_f1:
        k = length_f1

    filter_bits = len(filters0[0])
    if (any(len(f) != filter_bits for f in filters0)
            or any(len(f) != filter_bits for f in filters1)):
        raise ValueError('inconsistent filter length')
    if filter_bits % 64:
        msg = (f'invalid filter length (expected multiple of 64, got '
               f'{filter_bits})')
        raise ValueError(msg)
    filter_bytes = filter_bits // 8

    # An array of the *one* filter
    clist0 = (ffi.new(f"char[{filter_bytes}]", f.tobytes()) for f in filters0)
    carr1 = ffi.new(f"char[{filter_bytes * length_f1}]",
                    b''.join(f.tobytes() for f in filters1))
    c_popcounts = ffi.new(f"uint32_t[{length_f1}]",
                          [f.count() for f in filters1])

    # easier to do all buffer allocations in Python and pass them to C,
    # even for output-only arguments
    c_scores = ffi.new("double[]", k)
    c_indices = ffi.new("int[]", k)

    for i, f0 in enumerate(clist0):
        assert len(f0) == filter_bytes
        matches = lib.match_one_against_many_dice_k_top(
            f0,
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
        elif matches > 0:  # TODO: Things may be faster without this check
            result_sims.extend(c_scores[0:matches])
            result_indices0.extend(repeat(i, matches))
            result_indices1.extend(c_indices[0:matches])

    return result_sims, (result_indices0, result_indices1)
