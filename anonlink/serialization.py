"""Serialisation of candidate pairs.

The file format is not fixed and is subject to change. Backwards
compatibility will be attempted, but not guaranteed.
"""

import array as _array
import heapq as _heapq
import io as _io
import itertools as _itertools
import operator as _operator
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
    

def _bytes_iter_from_iterable(
    sim_t_size: int,
    dset_i_t_size: int,
    rec_i_t_size: int,
    entry_struct: _struct.Struct,
    iterable: _CandidatePairIter
) -> _typing.Iterable[bytes]:
    return _itertools.chain(
        (_HEADER_STRUCT.pack(1, sim_t_size, dset_i_t_size, rec_i_t_size),),
        _itertools.starmap(entry_struct.pack, iterable))


def _write_bytes_iter(
    f: _typing.BinaryIO,
    bytes_iter: _typing.Iterable[bytes]
) -> int:
    # Relies on the side effects of `f.write`. `f.write` returns the
    # number of bytes written. `sum` exhausts the iterator.
    return sum(map(f.write, bytes_iter))


def _entries_iterable(
    f: _typing.BinaryIO,
    entry_struct: _struct.Struct
) -> _CandidatePairIter:
    buffers = map(f.read, _itertools.repeat(entry_struct.size))
    nonempty_buffers = _itertools.takewhile(bool, buffers)
    try:
        yield from _typing.cast(_CandidatePairIter, map(entry_struct.unpack, nonempty_buffers))
    except _struct.error:
        raise ValueError('ran out of input') from None


def _make_buffered(
    f: _typing.BinaryIO
) -> _typing.BinaryIO:
    # Make sure that f.read(n) returns exactly n bytes.
    if isinstance(f, _io.RawIOBase):
        f = _io.BufferedReader(f)
    # If f is neither BufferedReader nor RawIOBase then we shrug and see
    # what happens...
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


def _load_to_iter_with_sizes(
    f: _typing.BinaryIO
) -> _typing.Tuple[_CandidatePairIter, int, int, int, int]:
    f = _make_buffered(f)
    sim_t_size, dset_i_t_size, rec_i_t_size = _load_header_and_check_version(f)

    # This may throw ValueError if the specified format isn't supported
    # on this platform.
    entry_struct = _entry_struct(sim_t_size, dset_i_t_size, rec_i_t_size)

    return (_entries_iterable(f, entry_struct),
            sim_t_size, dset_i_t_size, rec_i_t_size,
            entry_struct.size)


def load_to_iterable(
    f: _typing.BinaryIO
) -> _CandidatePairIter:
    """Load candidate pairs from file as an iterable.

    This function does not load all the candidate pairs into memory at
    once.

    :param f: Binary stream to read from.

    :return: An iterable of 5-tuples. Each 5-tuple represents one
        candidate pair and is composed of the similarity, the index of
        the first record's dataset, the index of the second record's
        dataset, the index of the first record within its dataset, and
        the index of the second record within its dataset.
    """
    iterable, _, _, _, _ = _load_to_iter_with_sizes(f)
    return iterable


def _file_size(entry_struct, entries):
    return _HEADER_STRUCT.size + entry_struct.size * entries


def dump_candidate_pairs_iter(
    candidate_pairs: _typechecking.CandidatePairs
) -> _typing.Tuple[_typing.Iterable[bytes], int]:
    """Dump candidate pairs as an iterable of bytes objects.

    No guarantees are made about the size of those bytes objects.

    :param candidate_pairs: Candidate pairs, as returned by a similarity
        function or `load_candidate_pairs`.

    :return: 2-tuple containing an iterable of bytes objects and the
        length of the dump as an integer.
    """
    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = candidate_pairs
    entries = len(sims)
    assert (entries
            == len(dset_is0) == len(dset_is1)
            == len(rec_is0) == len(rec_is1))

    sim_t_size = sims.itemsize
    dset_i_t_size = max(dset_is0.itemsize, dset_is1.itemsize)
    rec_i_t_size = max(rec_is0.itemsize, rec_is1.itemsize)
    entry_struct = _entry_struct(sim_t_size, dset_i_t_size, rec_i_t_size)

    iterable = zip(sims, dset_is0, dset_is1, rec_is0, rec_is1)
    bytes_iter = _bytes_iter_from_iterable(
        sim_t_size, dset_i_t_size, rec_i_t_size,
        entry_struct,
        iterable)

    file_size = _file_size(entry_struct, entries)

    return bytes_iter, file_size


def dump_candidate_pairs(
    candidate_pairs: _typechecking.CandidatePairs,
    f: _typing.BinaryIO
) -> int:
    """Dump candidate pairs to file.

    :param f: Binary stream to write to.
    :param candidate_pairs: Candidate pairs, as returned by a similarity
        function or `load_candidate_pairs`.

    :return: Number of bytes written.
    """
    bytes_iter, _ = dump_candidate_pairs_iter(candidate_pairs)
    return _write_bytes_iter(f, bytes_iter)


def load_candidate_pairs(f: _typing.BinaryIO) -> _typechecking.CandidatePairs:
    """Load candidate pairs from file.

    :param f: Binary stream to read from.

    :return: Candidate pairs, compatible with the type returned from a
        similarity function.
    """
    iterable_with_sizes = _load_to_iter_with_sizes(f)
    iterable, sim_t_size, dset_i_t_size, rec_i_t_size, _ = iterable_with_sizes

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
    arrays = sims, dset_is0, dset_is1, rec_is0, rec_is1

    # Rely on side side-effecting function passed to append.
    # any exhausts the iterator since array.append returns None.
    any(map(_array.array.append,  # type: ignore  # Just give up, Mypy.
            _itertools.cycle(arrays),
            _itertools.chain.from_iterable(iterable)))

    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)


def _number_entries(file_size, entry_size):
    entries, remainder = divmod(file_size - _HEADER_STRUCT.size, entry_size)
    if remainder:
        raise ValueError('invalid file: number of entries is non-integer')
    return entries 


def merge_streams_iter(
    files_in: _typing.Iterable[_typing.BinaryIO],
    *,
    sizes: _typing.Optional[_typing.Iterable[int]] = None
) -> _typing.Tuple[_typing.Iterable[bytes], int]:
    """Merge multiple files with candidate pairs to iterable of bytes.

    This function preserves the candidate pairs' sorted order. It avoids
    loading everything into memory.

    The field sizes in the resulting file will be chosen so no
    information is lost.
     
    Note that you cannot simply concatenate two files to obtain a valid
    candidate pairs dump.

    :param files_in: Sequence of files to read from.
    :param sizes: Optional iterable of file sizes. Permits us to compute
        the number of bytes in the returned iterator.

    :return: 2-tuple containing an iterable of bytes objects and 
        (optionally if the `sizes` parameter was provided) the length of
        the merged file as an integer.
    """
    if not files_in:
        raise ValueError('no files provided')

    iterables_with_sizes = map(_load_to_iter_with_sizes, files_in)
    file_iterables, *field_sizes = zip(*iterables_with_sizes)
    file_sim_t_size, file_dset_i_t_size, file_rec_i_t_size, file_entry_size \
        = field_sizes

    sim_t_size = max(file_sim_t_size)
    dset_i_t_size = max(file_dset_i_t_size)
    rec_i_t_size = max(file_rec_i_t_size)
    
    entry_struct = _entry_struct(sim_t_size, dset_i_t_size, rec_i_t_size)

    # Sort in decreasing order of similarities. Tiebreak with dataset
    # indices and then with record indices, in increasing order.
    sorted_iterable = _heapq.merge(*file_iterables,
                                   key=lambda x: (-x[0],) + x[1:])
    bytes_iter = _bytes_iter_from_iterable(
        sim_t_size, dset_i_t_size, rec_i_t_size,
        entry_struct,
        sorted_iterable)

    if sizes is not None:
        entries_num = sum(map(_number_entries, sizes, file_entry_size))
        file_size = _file_size(entry_struct, entries_num)
    else:
        file_size = None

    return bytes_iter, file_size


def merge_streams(
    files_in: _typing.Iterable[_typing.BinaryIO],
    f_out: _typing.BinaryIO
) -> int:
    """Merge multiple files with serialised candidate pairs.

    This function preserves the candidate pairs' sorted order. It avoids
    loading everything into memory.

    The field sizes in the resulting file will be chosen so no
    information is lost.
     
    Note that you cannot simply concatenate two files to obtain a valid
    candidate pairs dump.

    :param files_in: Sequence of files to read from.
    :param f_out: Binary stream write the merged candidate pairs to.

    :return: Number of bytes written.
    """
    bytes_iter, _ = merge_streams_iter(files_in)
    return _write_bytes_iter(f_out, bytes_iter)
