"""Serialisation of candidate pairs.

The file format is not fixed and is subject to change. Backwards
compatibility will be attempted, but not guaranteed.
"""

import array as _array
import heapq as _heapq
import io as _io
import struct as _struct
import typing as _typing

import anonlink.typechecking as _typechecking

# FILE FORMAT
#   This is subject to change.
#   The format is composed of a header and a sequence of entries. The
# header specifies the version of the format and the sizes of floating-
# -point and integer types used in the entries. Every entry is composed
# of a similarity score, two dataset indices, and two record indices.
#   The header is composed of a version (1 byte) and the format of the
# candidate pairs. This format consists of the number of bytes in a
# similarity (1 byte), the number of bytes in a dataset index (1 byte),
# and the number in a record index (1 byte). In total, the header is
# composed of 4 bytes.
#   An entry is composed of a similarity as a IEEE floating-point value,
# two dataset indices, and two record indices. Their sizes are
# determined by the header. For example, if the similarity is an IEEE
# double-precision floating-point value, the size noted by the header
# will be 8 [bytes].
#   All integers are unsigned. All values are *little-endian* since
# anonlink is realistically only ever run on little-endian machines.
# (This code will still run on big-endian machines, implicitly
# performing byteorder conversion.) The number of candidate matchings is
# not included on purpose: if needed, it can be computed from the length
# of the file.
#   Similarity scores are stored as a structure of arrays when in
# memory, but we serialise them as an array of structures. This makes it
# much easier to merge two serialised files.

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

_CandidatePair = _typing.Tuple[float, int, int, int, int]
_CandidatePairIter = _typing.Iterable[_CandidatePair]


def _entry_struct(
    sim_t_size: int,
    dset_i_t_size: int,
    rec_i_t_size: int
) -> _struct.Struct:
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
    # Every entry has: a similarity score, two datset indices, and two
    # record indices.
    return _struct.Struct(f"<{sim_t}2{dset_i_t}2{rec_i_t}")
    

def _dump_from_iterable(
    f: _typing.BinaryIO,
    sim_t_size: int,
    dset_i_t_size: int,
    rec_i_t_size: int,
    iterable: _CandidatePairIter
) -> None:
    # Fail without writing if the parameters are incorrect.
    entry_struct = _entry_struct(sim_t_size, dset_i_t_size, rec_i_t_size)
    
    # Write header.
    f.write(_HEADER_STRUCT.pack(1, sim_t_size, dset_i_t_size, rec_i_t_size))
    
    for entry in iterable:
        f.write(entry_struct.pack(*entry))


def _entries_iterable(
    f: _typing.BinaryIO,
    entry_struct: _struct.Struct
) -> _CandidatePairIter:
    buffer = f.read(entry_struct.size)
    while buffer:
        if len(buffer) != entry_struct.size:
            raise ValueError('ran out of input')
        yield _typing.cast(_CandidatePair, entry_struct.unpack(buffer))
        buffer = f.read(entry_struct.size)


def _make_buffered(
    f: _typing.BinaryIO
) -> _typing.BinaryIO:
    # Make sure that f.read(n) returns exactly n bytes.
    if not isinstance(f, _io.BufferedIOBase):
        f = _io.BufferedReader(f)  # type: ignore
        # Mypy complains that f is not guaranteed to be RawIOBase.
        # That's true but BufferedReader doesn't explicitly check this.
    return f


def _load_header_and_check_version(
    f: _typing.BinaryIO  # Must be buffered
) -> _typing.Tuple[int, int, int]:
    header_bytes = f.read(_HEADER_STRUCT.size)
    if len(header_bytes) != _HEADER_STRUCT.size:
        raise ValueError('ran out of input')
    version, sim_t_size, dset_i_t_size, rec_i_t_size = (
        _HEADER_STRUCT.unpack(header_bytes))
    if version != 1:
        raise ValueError('unsupported version of serialized file')
    return sim_t_size, dset_i_t_size, rec_i_t_size


def _load_to_iterable(
    f: _typing.BinaryIO
) -> _typing.Tuple[_CandidatePairIter, int, int, int]:
    f = _make_buffered(f)
    sim_t_size, dset_i_t_size, rec_i_t_size = _load_header_and_check_version(f)

    # This may throw ValueError if the specified format isn't supported
    # on this platform.
    entry_struct = _entry_struct(sim_t_size, dset_i_t_size, rec_i_t_size)

    return (_entries_iterable(f, entry_struct),
            sim_t_size, dset_i_t_size, rec_i_t_size)


def dump_candidate_pairs(
    candidate_pairs: _typechecking.CandidatePairs,
    f: _typing.BinaryIO
) -> None:
    """Dump candidate pairs to file.

    :param f: Binary buffer to write to.
    :param candidate_pairs: Candidate pairs, as returned by a similarity
        function or `load_candidate_pairs`.
    """
    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = candidate_pairs
    assert (len(sims)
            == len(dset_is0) == len(dset_is1)
            == len(rec_is0) == len(rec_is1))
    assert sims.itemsize in _ARRAY_FLOAT_LEN_TO_FMT
    assert all(a.itemsize in _ARRAY_UINT_LEN_TO_FMT
               for a in (dset_is0, dset_is1, rec_is0, rec_is1))

    iterable = zip(sims, dset_is0, dset_is1, rec_is0, rec_is1)
    sim_t_size = sims.itemsize
    dset_i_t_size = max(dset_is0.itemsize, dset_is1.itemsize)
    rec_i_t_size = max(rec_is0.itemsize, rec_is1.itemsize)

    _dump_from_iterable(
        f, sim_t_size, dset_i_t_size, rec_i_t_size, iterable)


def load_candidate_pairs(f: _typing.BinaryIO) -> _typechecking.CandidatePairs:
    """Load candidate pairs from file.

    :param f: Binary buffer to read from.
    :return: Candidate pairs, compatible with the type returned from a
        similarity function.
    """
    iterable, sim_t_size, dset_i_t_size, rec_i_t_size = _load_to_iterable(f)

    try:
        sim_t = _ARRAY_FLOAT_LEN_TO_FMT[sim_t_size]
    except KeyError:
        msg = f'floats of {sim_t_size} bytes are not supported'
        raise ValueError(msg) from None
    try:
        dset_i_t = _ARRAY_UINT_LEN_TO_FMT[dset_i_t_size]
    except KeyError:
        msg = f'indices of {dset_i_t_size} bytes are not supported'
        raise ValueError(msg) from None
    try:
        rec_i_t = _ARRAY_UINT_LEN_TO_FMT[rec_i_t_size]
    except KeyError:
        msg = f'indices of {rec_i_t_size} bytes are not supported'
        raise ValueError(msg) from None

    # Future: preallocate memory according to length of file. This is
    # not possible in pure Python, but can be done in Cython.
    sims: _typechecking.FloatArrayType = _array.array(sim_t)
    dset_is0: _typechecking.IntArrayType = _array.array(dset_i_t)
    dset_is1: _typechecking.IntArrayType = _array.array(dset_i_t)
    rec_is0: _typechecking.IntArrayType = _array.array(rec_i_t)
    rec_is1: _typechecking.IntArrayType = _array.array(rec_i_t)
    for sim, dset_i0, dset_i1, rec_i0, rec_i1 in iterable:
        sims.append(sim)
        dset_is0.append(dset_i0)
        dset_is1.append(dset_i1)
        rec_is0.append(rec_i0)
        rec_is1.append(rec_i1)
    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)


def merge_streams(
    files_in: _typing.Sequence[_typing.BinaryIO],
    f_out: _typing.BinaryIO
) -> None:
    """Merge multiple files with serialised candidate pairs.

    This function preserves the candidate pairs' sorted order. It avoids
    loading everything into memory.

    The field sizes in the resulting file will be chosen so no
    information is lost.
     
    Note that you cannot simply concatenate two files to obtain a valid
    candidate pairs dump.

    :param files_in: Iterable of files to read from.
    :param f_out: Binary buffer write the merged candidate pairs to.
    """
    if not files_in:
        raise ValueError('no files provided')

    file_iterables, *sizes = zip(*map(_load_to_iterable, files_in))
    file_sim_t_size, file_dset_i_t_size, file_rec_i_t_size = sizes

    sim_t_size = max(file_sim_t_size)
    dset_i_t_size = max(file_dset_i_t_size)
    rec_i_t_size = max(file_rec_i_t_size)
    
    # Sort in decreasing order of similarities. Tiebreak with dataset
    # indices and then with record indices, in increasing order.
    sorted_iterable = _heapq.merge(*file_iterables,
                                   key=lambda x: (-x[0],) + x[1:])
    _dump_from_iterable(f_out,
                        sim_t_size, dset_i_t_size, rec_i_t_size,
                        sorted_iterable)


def _records_in_file(
    f: _typing.BinaryIO,
    sim_t_size: int,
    dset_i_size: int,
    rec_i_t_size: int
) -> int:
    f.seek(0, 2)
    length = f.tell()

    # This assumes we've checked that the header is there.
    length -= _HEADER_STRUCT.size
    entry_struct = _entry_struct(sim_t_size, dset_i_size, rec_i_t_size)

    entries, remainder = divmod(length, entry_struct.size)
    if remainder:
        raise ValueError('invalid file: number of entries is non-integer')
    return entries


def compute_merged_length(
    files_in: _typing.Iterable[_typing.BinaryIO]
) -> int:
    """Compute the number of bytes wrtten by ``merge_streams``.

    No data is actually written.

    Note: If you're passing the same file objects to ``merge_streams``,
    make sure to .seek(0).

    :param files_in: Iterable of files to read from.
    """
    if not files_in:
        raise ValueError('no files provided')

    files_in = tuple(map(_make_buffered, files_in))

    # This also checks the version and raises if incompatible.
    sizes = map(_load_header_and_check_version, files_in)
    sim_t_sizes, dset_i_t_sizes, rec_i_t_sizes = zip(*sizes)

    # Find size of each entry. We always choose the biggest type.
    sim_t_size = max(sim_t_sizes)
    dset_i_t_size = max(dset_i_t_sizes)
    rec_i_t_size = max(rec_i_t_sizes)
    entry_struct = _entry_struct(sim_t_size, dset_i_t_size, rec_i_t_size)
    entry_struct_size = entry_struct.size

    entries = sum(map(_records_in_file,
                      files_in, sim_t_sizes, dset_i_t_sizes, rec_i_t_sizes))

    return _HEADER_STRUCT.size + entry_struct_size * entries


def compute_dump_length(
    candidate_pairs: _typechecking.CandidatePairs,
) -> int:
    """Compute the number of bytes wrtten by ``dump_candidate_pairs``.

    :param files_in: Candidate pairs, as returned by a similarity
        function or `load_candidate_pairs`.
    """
    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = candidate_pairs
    entries = len(sims)
    assert entries == len(dset_is0)
    assert entries == len(dset_is1)
    assert entries == len(rec_is0)
    assert entries == len(rec_is1)

    sim_t_size = sims.itemsize
    dset_i_t_size = max(dset_is0.itemsize, dset_is1.itemsize)
    rec_i_t_size = max(rec_is0.itemsize, rec_is1.itemsize)
    
    assert sim_t_size in _ARRAY_FLOAT_LEN_TO_FMT
    assert dset_i_t_size in _ARRAY_UINT_LEN_TO_FMT
    assert rec_i_t_size in _ARRAY_UINT_LEN_TO_FMT

    entry_struct_size = _entry_struct(
        sim_t_size, dset_i_t_size, rec_i_t_size).size
    return _HEADER_STRUCT.size + entry_struct_size * entries
