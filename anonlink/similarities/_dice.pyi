import anonlink.typechecking as _typechecking


def popcount_arrays(input_data: _typechecking.CharArrayType, array_bytes: int) -> _typechecking.IntArrayType: ...


def dice_many_to_many(
        carr0: _typechecking.CharArrayType,
        carr1: _typechecking.CharArrayType,
        length_f0: int,
        length_f1: int,
        c_popcounts: _typechecking.IntArrayType,
        filter_bytes: int,
        k: int,
        threshold: float,
        result_sims: _typechecking.FloatArrayType,
        result_indices0: _typechecking.IntArrayType,
        result_indices1: _typechecking.IntArrayType
): ...
