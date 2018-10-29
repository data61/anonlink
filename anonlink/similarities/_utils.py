from bitarray import bitarray
import numpy as np

from anonlink.typechecking import FloatArrayType, IntArrayType


def sort_similarities_inplace(
    sims: FloatArrayType,
    rec_is0: IntArrayType,
    rec_is1: IntArrayType
) -> None:
    np_sims = np.frombuffer(sims, dtype=sims.typecode)
    np_indices0 = np.frombuffer(rec_is0, dtype=rec_is0.typecode)
    np_indices1 = np.frombuffer(rec_is1, dtype=rec_is1.typecode)
    
    np.negative(np_sims, out=np_sims)  # Sort in reverse.
    # Mergesort is stable. We need that for correct tiebreaking.
    order = np.argsort(np_sims, kind='mergesort')
    np.negative(np_sims, out=np_sims)

    # This modifies the original arrays since they share a buffer.
    np_sims[:] = np_sims[order]
    np_indices0[:] = np_indices0[order]
    np_indices1[:] = np_indices1[order]


def to_bitarray(record) -> bitarray:
    if isinstance(record, bitarray):
        return record
    if not isinstance(record, bytes):
        try:  # Not bitarray, not bytes. But is it bytes-like?
            record = bytes(record)
        except TypeError:
            raise TypeError('unsupported record type') from None
    ba = bitarray()
    ba.frombytes(record)
    return ba


def to_bitarrays(records):
    if all(isinstance(record, bitarray) for record in records):
        return records
    else:
        return tuple(map(to_bitarray, records))

