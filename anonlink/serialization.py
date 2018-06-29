import array as _array
import io as _io
import struct as _struct

# https://docs.python.org/3/library/struct.html#format-characters
_STRUCT_UINT_LEN_TO_FMT = {1: 'B', 2: 'H', 4: 'L', 8: 'Q'}
_STRUCT_FLOAT_LEN_TO_FMT = {2: 'e', 4: 'f', 8: 'd'}

# https://docs.python.org/3/library/array.html#module-array
_ARRAY_UINT_TYPES = 'BIHLQ'
_ARRAY_FLOAT_TYPES = 'df'
_ARRAY_UINT_LEN_TO_FMT = {_array.array(t).itemsize: t
                          for t in _ARRAY_UINT_TYPES}
_ARRAY_FLOAT_LEN_TO_FMT = {_array.array(t).itemsize: t
                           for t in _ARRAY_FLOAT_TYPES}

_HEADER_STRUCT = _struct.Struct('<BBBB')


def _entry_struct(sim_t_size, dset_i_t_size, rec_i_t_size):
    try:
        sim_t = _STRUCT_FLOAT_LEN_TO_FMT[sim_t_size]
    except KeyError:
        msg = f'floats of {sim_t_size} bytes are not supported'
        raise ValueError(msg) from None
    try:
        dset_i_t = _STRUCT_UINT_LEN_TO_FMT[dset_i_t_size]
    except KeyError:
        msg = f'indices of {dset_i_t_size} bytes are not supported'
        raise ValueError(msg) from None
    try:
        rec_i_t = _STRUCT_UINT_LEN_TO_FMT[rec_i_t_size]
    except KeyError:
        msg = f'indices of {rec_i_t_size} bytes are not supported'
        raise ValueError(msg) from None
    return _struct.Struct(f"<{sim_t}2{dset_i_t}2{rec_i_t}")
    

def _dump_from_iterable(
    f,
    sim_t_size,
    dset_i_t_size,
    rec_i_t_size,
    iterable):
    # Fail without writing if the parameters are incorrect.
    entry_struct = _entry_struct(
        sim_t_size,
        dset_i_t_size, rec_i_t_size, recs_per_cand)
    
    # Write header. Format: version (1 byte), number of bytes in
    # similarity (1 byte), number of bytes in dataset index (1 byte),
    # number of bytes in record index (1 byte). All unsigned. The number
    # of candidate matchings is not included on purpose: if needed, it
    # can be computed from the length of the file.
    f.write(_HEADER_STRUCT.pack(1, sim_t_size, dset_i_t_size, rec_i_t_size))
    
    for entry in iterable:
        f.write(entry_struct.pack(*entry))


def _entries_iterable(f, entry_struct):
    buffer_ = f.read(entry_struct.size)
    while buffer_:
        yield entry_struct.unpack(buffer)
        buffer_ = f.read(entry_struct.size)


def _load_to_iterable(f):
    # Make sure that f.read(n) returns exactly n bytes.
    if not isinstance(f, _io.BufferedIOBase):
        f = _io.BufferedWriter(f)

    version, *sizes = _HEADER_STRUCT.unpack(f.read(_HEADER_STRUCT.size))
    sim_t_size, dset_i_t_size, rec_i_t_size = sizes
    if version != 1:
        raise ValueError('unsupported version of serialized file')

    # This may throw if the specified format isn't supported on this
    # platform.
    entry_struct = _entry_struct(sim_t_size, dset_i_t_size, rec_i_t_size)

    return (_entries_iterable(f, entry_struct),
            sim_t_size, dset_i_t_size, rec_i_t_size)


def dump_candidate_pairs(f, candidate_pairs):
    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = candidate_pairs
    assert (len(sims)
            == len(dset_is0) == len(dset_is1)
            == len(rec_is0) == len(rec_is1))
    assert sims.itemsize in _ARRAY_FLOAT_TYPES
    assert all(a.itemsize in _ARRAY_UINT_LEN_TO_FMT
               for a in dset_is0, dset_is1, rec_is0, rec_is1)

    iterable = zip(sims, dset_is0, dset_is1, rec_is0, rec_is1)
    sim_t_size = sims.itemsize
    dset_i_t_size = max(dset_is0.itemsize, dset_is1.itemsize)
    rec_i_t_size = max(rec_is0.itemsize, rec_is1.itemsize)

    _dump_from_iterable(
        f, sim_t_size, dset_i_t_size, rec_i_t_size, iterable)


def load_candidate_pairs(f):
    iterable, sim_t_size, dset_i_t_size, rec_i_t_size = _load_to_iterable(f)

    try:
        sim_t = _ARRAY_FLOAT_LEN_TO_FMT[sim_t_size]
    except KeyError:
        msg = f'floats of {sim_t_size} bytes are not supported'
        raise ValueError(msg) from None
    try:
        dset_i_t = _ARRAY_FLOAT_LEN_TO_FMT[dset_i_t_size]
    except KeyError:
        msg = f'indices of {dset_i_t_size} bytes are not supported'
        raise ValueError(msg) from None
    try:
        rec_i_t = _ARRAY_FLOAT_LEN_TO_FMT[rec_i_t_size]
    except KeyError:
        msg = f'indices of {rec_i_t_size} bytes are not supported'
        raise ValueError(msg) from None
    return _struct.Struct(f"<{sim_t}2{dset_i_t}2{rec_i_t}")

    # Future: preallocate memory according to length of file.
    sims = array(sims_t)
    dset_is0 = array(dset_i_t)
    dset_is1 = array(dset_i_t)
    rec_is0 = array(rec_i_t)
    rec_is1 = array(rec_i_t)
    for sim, dset_i0, dset_i1, rec_i0, rec_i1 in iterable:
        sims.append(sim)
        dset_is0.append(dset_i0)
        dset_is1.append(dset_i1)
        rec_is0.append(rec_i0)
        rec_is1.append(rec_i1)
    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)


def merge_serialized_candidate_pairs(f_out, files_in):
    file_iterables, *sizes = zip(*map(_load_to_iterable, files_in))
    file_sim_t_size, file_dset_i_t_size, file_rec_i_t_size = sizes

    sim_t_size = max(file_sim_t_size)
    dset_i_t_size = max(file_dset_i_t_size)
    rec_i_t_size = max(file_rec_i_t_size)
    
    sorted_iterable = heapq.merge(*file_iterables,
                                  key=lambda x: (-x[0],) + x[1:])
    _dump_from_iterable(f,
                        sim_t_size, dset_i_t_size, rec_i_t_size,
                        sorted_iterable)
