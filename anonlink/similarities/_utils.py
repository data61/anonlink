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
