import array
import collections
import contextlib
import io
import itertools
import os
import random
import struct
import uuid

import pytest

from anonlink import serialization

FLOAT_SIZES = (4, 8)
UINT_SIZES = (1, 2, 4, 8)
CANDIDATE_PAIR_LENGTHS = (0, 1, 1000) + (
    (1000000,) if os.getenv('TEST_SERIALIZATION_BIG') is not None else ())

ARRAY_FLOAT_SIZE_TO_FMT = {array.array(t).itemsize: t
                           for t in 'df'}
ARRAY_UINT_SIZE_TO_FMT = {array.array(t).itemsize: t
                          for t in 'BIHLQ'}
FLOAT_SIZE_TO_STRUCT = {2: struct.Struct('<e'),
                        4: struct.Struct('<f'),
                        8: struct.Struct('<d')}

RANDOM_SEED = 3214
BITS_IN_BYTE = 8
FORMAT_VERSION = 1
FORMAT_BYTEORDER = 'little'
UNSUPPORTED_SIZE = 3  # This may unfortunately be platform-dependent.
DEFAULT_SIZE = 4  # This may unfortunately be platform-dependent.
DEFAULT_FILES_NUM = 3
DEFAULT_LENGTH = 5


def random_pairs_list(sim_size, dset_i_size, rec_i_size,
                      length, seed=RANDOM_SEED):
    dset_i_range_stop = 2 ** (BITS_IN_BYTE * dset_i_size)
    rec_i_range_stop = 2 ** (BITS_IN_BYTE * rec_i_size)
    float_array = array.array(ARRAY_FLOAT_SIZE_TO_FMT[sim_size], [0])

    rng = random.Random(seed)
    random_pairs = []
    for _ in range(length):
        # Coerce precision
        float_array[0] = rng.uniform(0, 1)
        sim = float_array[0]

        dset_i0 = rng.randrange(dset_i_range_stop)
        dset_i1 = rng.randrange(dset_i_range_stop)
        rec_i0 = rng.randrange(rec_i_range_stop)
        rec_i1 = rng.randrange(rec_i_range_stop)

        random_pairs.append((sim, dset_i0, dset_i1, rec_i0, rec_i1))

    random_pairs.sort(key=lambda x: (-x[0],) + x[1:])
    return random_pairs


def pairs_list_to_candidate_pairs(pairs_list,
                                  sim_size, dset_i_size, rec_i_size):
    sims = array.array(ARRAY_FLOAT_SIZE_TO_FMT[sim_size])
    dset_is0 = array.array(ARRAY_UINT_SIZE_TO_FMT[dset_i_size])
    dset_is1 = array.array(ARRAY_UINT_SIZE_TO_FMT[dset_i_size])
    rec_is0 = array.array(ARRAY_UINT_SIZE_TO_FMT[rec_i_size])
    rec_is1 = array.array(ARRAY_UINT_SIZE_TO_FMT[rec_i_size])
    for sim, dset_i0, dset_i1, rec_i0, rec_i1 in pairs_list:
        sims.append(sim)
        dset_is0.append(dset_i0)
        dset_is1.append(dset_i1)
        rec_is0.append(rec_i0)
        rec_is1.append(rec_i1)
    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)


def pairs_list_to_bytes(pairs_list, sim_size, dset_i_size, rec_i_size):
    bytes_ = bytearray((1, sim_size, dset_i_size, rec_i_size))
    for sim, dset_i0, dset_i1, rec_i0, rec_i1 in pairs_list:
        bytes_.extend(FLOAT_SIZE_TO_STRUCT[sim_size].pack(sim))
        bytes_.extend(dset_i0.to_bytes(dset_i_size, FORMAT_BYTEORDER))
        bytes_.extend(dset_i1.to_bytes(dset_i_size, FORMAT_BYTEORDER))
        bytes_.extend(rec_i0.to_bytes(rec_i_size, FORMAT_BYTEORDER))
        bytes_.extend(rec_i1.to_bytes(rec_i_size, FORMAT_BYTEORDER))
    return bytes_


@pytest.fixture(scope='session',
                params=itertools.product(
                    FLOAT_SIZES, UINT_SIZES, UINT_SIZES,
                    CANDIDATE_PAIR_LENGTHS))
def cands_bytes_pair(request):
    sim_size, dset_i_size, rec_i_size, length = request.param
    pairs_list = random_pairs_list(sim_size, dset_i_size, rec_i_size, length)
    candidate_pairs = pairs_list_to_candidate_pairs(
        pairs_list, sim_size, dset_i_size, rec_i_size)
    bytes_ = pairs_list_to_bytes(pairs_list, sim_size, dset_i_size, rec_i_size)
    return candidate_pairs, bytes_, pairs_list, request.param


@pytest.fixture(scope='session')
def tmpdir_path(tmpdir_factory):
    return tmpdir_factory.mktemp('tmpdata')


@pytest.fixture(scope='session',
                params=('file', 'bytesio'))
def new_file_function(request, tmpdir_path):
    if request.param == 'bytesio':
        return io.BytesIO
    if request.param == 'file':
        return lambda: open(tmpdir_path.join(str(uuid.uuid4())), 'w+b')
    raise ValueError('invalid param')


def consume(iterator):
    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    "Consume iterator entirely."
    # Use functions that consume iterators at C speed.
    # Feed the entire iterator into a zero-length deque.
    collections.deque(iterator, maxlen=0)


def get_file_size(f):
    opos = f.tell()
    f.seek(0, 2)
    length = f.tell() - opos
    f.seek(opos)
    return length


def dump_to_file_stream(candidate_pairs, f):
    bytes_written = serialization.dump_candidate_pairs(candidate_pairs, f)
    assert f.tell() == bytes_written
def dump_iter_to_file(candidate_pairs, f):
    bytes_iter, file_size = serialization.dump_candidate_pairs_iter(
        candidate_pairs)
    consume(map(f.write, bytes_iter))
    assert f.tell() == file_size
def merge_to_file_stream(files_in, f_out):
    bytes_written = serialization.merge_streams(files_in, f_out)
    assert f_out.tell() == bytes_written
def merge_iter_to_file_size_provided(files_in, f_out):
    bytes_iter, file_size = serialization.merge_streams_iter(
        files_in,
        sizes=tuple(map(get_file_size, files_in)))
    consume(map(f_out.write, bytes_iter))
    assert f_out.tell() == file_size
def merge_iter_to_file_size_not_provided(files_in, f_out):
    bytes_iter, file_size = serialization.merge_streams_iter(files_in)
    assert file_size is None
    consume(map(f_out.write, bytes_iter))


@pytest.mark.parametrize('dump_function', [dump_to_file_stream,
                                           dump_iter_to_file])
class TestDumpCandidatePairs:
    def test_general(self, cands_bytes_pair, new_file_function, dump_function):
        candidate_pairs, bytes_, *_ = cands_bytes_pair
        with new_file_function() as f:
            dump_function(candidate_pairs, f)
            f.seek(0)
            assert f.read() == bytes_


class TestLoadCandidatePairs:
    def test_general(self, cands_bytes_pair, new_file_function):
        candidate_pairs, bytes_, *_ = cands_bytes_pair
        with new_file_function() as f:
            length = f.write(bytes_)
            f.seek(0)
            assert candidate_pairs == serialization.load_candidate_pairs(f)


class TestLoadCandidatePairsToIterable:
    def test_general(self, cands_bytes_pair, new_file_function):
        candidate_pairs, bytes_, *_ = cands_bytes_pair
        sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = candidate_pairs
        candidate_pairs_iter = zip(sims, dset_is0, dset_is1, rec_is0, rec_is1)
        with new_file_function() as f:
            length = f.write(bytes_)
            f.seek(0)
            for p0, p1 in itertools.zip_longest(
                    candidate_pairs_iter, serialization.load_to_iterable(f)):
                assert p0 == p1


@pytest.mark.parametrize(
    'load_function',
    [serialization.load_candidate_pairs,
     serialization.load_to_iterable])
class TestLoadCandidatePairsErrorCases:
    @pytest.mark.parametrize('sim_size', FLOAT_SIZES)
    @pytest.mark.parametrize('dset_i_size', UINT_SIZES)
    @pytest.mark.parametrize('rec_i_size', UINT_SIZES)
    @pytest.mark.parametrize('length', (0, 5))
    @pytest.mark.parametrize('version', (0, 2, 172))
    def test_incorrect_version(
            self,
            new_file_function, load_function,
            sim_size, dset_i_size, rec_i_size, length,
            version):
        pairs_list = random_pairs_list(
            sim_size, dset_i_size, rec_i_size, length)
        bytes_ = pairs_list_to_bytes(
            pairs_list, sim_size, dset_i_size, rec_i_size)
        bytes_[0] = version
        with new_file_function() as f:
            f.write(bytes_)
            f.seek(0)
            with pytest.raises(ValueError):
                load_function(f)

    @pytest.mark.parametrize('sim_size', FLOAT_SIZES)
    @pytest.mark.parametrize('dset_i_size', UINT_SIZES)
    @pytest.mark.parametrize('rec_i_size', UINT_SIZES)
    @pytest.mark.parametrize('length', (0, 5))
    def test_unsupported_sizes(
            self,
            new_file_function, load_function,
            sim_size, dset_i_size, rec_i_size, length):
        pairs_list = random_pairs_list(
            sim_size, dset_i_size, rec_i_size, length)
        
        bytes_ = pairs_list_to_bytes(
            pairs_list, sim_size, dset_i_size, rec_i_size)
        bytes_[1] = 3
        with new_file_function() as f:
            f.write(bytes_)
            f.seek(0)
            with pytest.raises(ValueError):
                load_function(f)
        
        bytes_ = pairs_list_to_bytes(
            pairs_list, sim_size, dset_i_size, rec_i_size)
        bytes_[2] = 3
        with new_file_function() as f:
            f.write(bytes_)
            f.seek(0)
            with pytest.raises(ValueError):
                load_function(f)
        
        bytes_ = pairs_list_to_bytes(
            pairs_list, sim_size, dset_i_size, rec_i_size)
        bytes_[3] = 3
        with new_file_function() as f:
            f.write(bytes_)
            f.seek(0)
            with pytest.raises(ValueError):
                load_function(f)

    def test_empty_file(self, new_file_function, load_function):
        with new_file_function() as f:
            with pytest.raises(ValueError):
                load_function(f)

    def test_incomplete_header(self, new_file_function, load_function):
        with new_file_function() as f:
            f.write(FORMAT_VERSION.to_bytes(1, 'little'))
            f.seek(0)
            with pytest.raises(ValueError):
                load_function(f)

            f.seek(0, 2)
            f.write(DEFAULT_SIZE.to_bytes(1, 'little'))
            f.seek(0)
            with pytest.raises(ValueError):
                load_function(f)

            f.seek(0, 2)
            f.write(DEFAULT_SIZE.to_bytes(1, 'little'))
            f.seek(0)
            with pytest.raises(ValueError):
                load_function(f)

    @pytest.mark.parametrize('sim_size', FLOAT_SIZES)
    @pytest.mark.parametrize('dset_i_size', UINT_SIZES)
    @pytest.mark.parametrize('rec_i_size', UINT_SIZES)
    @pytest.mark.parametrize('preceeding', (0, 5))
    def test_incomplete_entry(
            self,
            new_file_function, load_function,
            sim_size, dset_i_size, rec_i_size,
            preceeding):
        pairs_list = random_pairs_list(
            sim_size, dset_i_size, rec_i_size, preceeding + 1)
        bytes_ = pairs_list_to_bytes(
            pairs_list, sim_size, dset_i_size, rec_i_size)
        with new_file_function() as f:
            f.write(bytes_)
            for _ in range(1, sim_size + 2 * dset_i_size + 2 * rec_i_size):
                f.seek(-1, 2)
                f.truncate()
                f.seek(0)
                if load_function is serialization.load_to_iterable:
                    with pytest.raises(ValueError):
                        consume(load_function(f))
                else:
                    with pytest.raises(ValueError):
                        load_function(f)


@pytest.mark.parametrize('merge_function',
                         [merge_to_file_stream,
                          merge_iter_to_file_size_provided,
                          merge_iter_to_file_size_not_provided])
class TestMergeStreams:
    @pytest.mark.parametrize('split', (1, 2, 5))
    def test_general(self,
                     cands_bytes_pair, new_file_function,
                     split,
                     merge_function):
        (_, _, all_pairs_list,
         (sim_size, dset_i_size, rec_i_size, _)) = cands_bytes_pair
        pairs_lists = tuple([] for _ in range(split))

        rng = random.Random(RANDOM_SEED)
        for pair in all_pairs_list:
            rng.choice(pairs_lists).append(pair)

        with contextlib.ExitStack() as stack:
            files = tuple(stack.enter_context(new_file_function())
                          for _ in pairs_lists)

            for f, pairs_list in zip(files, pairs_lists):
                f.write(pairs_list_to_bytes(pairs_list,
                                            sim_size, dset_i_size, rec_i_size))
                f.seek(0)

            f_out = stack.enter_context(new_file_function())
            merge_function(files, f_out)
            f_out.seek(0)
            assert f_out.read() == pairs_list_to_bytes(
                all_pairs_list, sim_size, dset_i_size, rec_i_size)

    def test_no_files(self, new_file_function, merge_function):
        with new_file_function() as f:
            with pytest.raises(ValueError):
                merge_function([], f)

    @pytest.mark.parametrize('length', (0, 5))
    @pytest.mark.parametrize('split', (1, 2, 5))
    def test_sizes(self, new_file_function, length, split, merge_function):
        rng = random.Random(RANDOM_SEED)
        sim_sizes = tuple(rng.choice(FLOAT_SIZES) for _ in range(split))
        dset_i_sizes = tuple(rng.choice(UINT_SIZES) for _ in range(split))
        rec_i_sizes = tuple(rng.choice(UINT_SIZES) for _ in range(split))

        with contextlib.ExitStack() as stack:
            files = tuple(stack.enter_context(new_file_function())
                          for _ in range(split))

            for i, f, sim_size, dset_i_size, rec_i_size in zip(
                    itertools.count(),
                    files,
                    sim_sizes, dset_i_sizes, rec_i_sizes):
                pairs_list = random_pairs_list(
                    sim_size, dset_i_size, rec_i_size, length,
                    seed=RANDOM_SEED + i)
                f.write(pairs_list_to_bytes(
                    pairs_list, sim_size, dset_i_size, rec_i_size))
                f.seek(0)

            f_out = stack.enter_context(new_file_function())
            merge_function(files, f_out)
            f_out.seek(1)
            assert int.from_bytes(f_out.read(1), 'little') == max(sim_sizes)
            assert int.from_bytes(f_out.read(1), 'little') == max(dset_i_sizes)
            assert int.from_bytes(f_out.read(1), 'little') == max(rec_i_sizes)

    @pytest.mark.parametrize('sim_size', FLOAT_SIZES)
    @pytest.mark.parametrize('dset_i_size', UINT_SIZES)
    @pytest.mark.parametrize('rec_i_size', UINT_SIZES)
    def test_tiebreaking(self,
                         new_file_function,
                         sim_size, dset_i_size, rec_i_size,
                         merge_function):
        # This order is relied on in the test. Make sure that after
        # flattening these are still sorted.
        pairs_zip = (((0.91, 0, 2, 6, 2),
                      (0.9, 0, 2, 6, 2)),
                     ((0.8, 1, 4, 2, 8),
                      (0.8, 2, 4, 2, 8)),
                     ((0.7, 3, 4, 1, 7),
                      (0.7, 3, 6, 1, 7)),
                     ((0.6, 6, 2, 6, 109),
                      (0.6, 6, 2, 32, 109)),
                     ((0.5, 43, 45, 13, 62),
                      (0.5, 43, 45, 13, 232)))
        for swap in itertools.product((False, True), repeat=len(pairs_zip)):
            swapped_pair_zip = tuple(
                pair[::-1] if swap_pair else pair
                for swap_pair, pair in zip(swap, pairs_zip))
            swapped_pair0, swapped_pair1 = zip(*swapped_pair_zip)
            with new_file_function() as f0, new_file_function() as f1:
                f0.write(pairs_list_to_bytes(
                    swapped_pair0,
                    sim_size, dset_i_size, rec_i_size))
                f0.seek(0)
                f1.write(pairs_list_to_bytes(
                    swapped_pair1,
                    sim_size, dset_i_size, rec_i_size))
                f1.seek(0)

                with new_file_function() as f_out:
                    merge_function([f0, f1], f_out)
                    f_out.seek(0)
                    bytes_out = f_out.read()

            bytes_sorted = pairs_list_to_bytes(
                    itertools.chain.from_iterable(pairs_zip),
                    sim_size, dset_i_size, rec_i_size)

            assert bytes_out == bytes_sorted

    @pytest.mark.parametrize('length', (0, 5))
    @pytest.mark.parametrize('version', (0, 2, 172))
    def test_incorrect_version(
            self,
            new_file_function,
            length, version,
            merge_function):
        for invalid_file_i in range(DEFAULT_FILES_NUM):
            with contextlib.ExitStack() as stack:
                files = tuple(stack.enter_context(new_file_function())
                              for _ in range(DEFAULT_FILES_NUM))
                for i, f in enumerate(files):
                    pairs_list = random_pairs_list(
                        DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE, length)
                    bytes_ = pairs_list_to_bytes(
                        pairs_list, DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE)        
                    bytes_[0] = version if i == invalid_file_i else bytes_[0]
                    f.write(bytes_)
                    f.seek(0)
                with new_file_function() as f_out:
                    with pytest.raises(ValueError):
                        merge_function(files, f_out)

    @pytest.mark.parametrize('length', (0, 5))
    def test_unsupported_sizes(
            self,
            new_file_function,
            length,
            merge_function):
        for invalid_file_i, size_pos in itertools.product(
                range(DEFAULT_FILES_NUM), range(1, 4)):
            with contextlib.ExitStack() as stack:
                files = tuple(stack.enter_context(new_file_function())
                              for _ in range(DEFAULT_FILES_NUM))
                for i, f in enumerate(files):
                    pairs_list = random_pairs_list(
                        DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE, length)
                    bytes_ = pairs_list_to_bytes(
                        pairs_list, DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE)
                    f.write(bytes_)
                    if i == invalid_file_i:
                        f.seek(size_pos)
                        f.write(UNSUPPORTED_SIZE.to_bytes(1, 'little'))
                    f.seek(0)
                with new_file_function() as f_out:
                    with pytest.raises(ValueError):
                        merge_function(files, f_out)

    def test_empty_file(self, new_file_function, merge_function):
        for invalid_file_i in range(DEFAULT_FILES_NUM):
            with contextlib.ExitStack() as stack:
                files = tuple(stack.enter_context(new_file_function())
                              for _ in range(DEFAULT_FILES_NUM))
                for i, f in enumerate(files):
                    if i != invalid_file_i:
                        pairs_list = random_pairs_list(
                            DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE,
                            DEFAULT_LENGTH)
                        bytes_ = pairs_list_to_bytes(
                            pairs_list,
                            DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE)
                        f.write(bytes_)
                        f.seek(0)
                with new_file_function() as f_out:
                    with pytest.raises(ValueError):
                        merge_function(files, f_out)

    def test_incomplete_header(self, new_file_function, merge_function):
        for invalid_file_i, header_len in itertools.product(
                range(DEFAULT_FILES_NUM), range(1, 4)):
            with contextlib.ExitStack() as stack:
                files = tuple(stack.enter_context(new_file_function())
                              for _ in range(DEFAULT_FILES_NUM))
                for i, f in enumerate(files):
                    pairs_list = random_pairs_list(
                        DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE,
                        DEFAULT_LENGTH)
                    bytes_ = pairs_list_to_bytes(
                        pairs_list, DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE)
                    f.write(bytes_)
                    if i == invalid_file_i:
                        f.seek(header_len)
                        f.truncate()
                    f.seek(0)
                with new_file_function() as f_out:
                    with pytest.raises(ValueError):
                        merge_function(files, f_out)

    @pytest.mark.parametrize('length', (0, 5))
    def test_pairs_incomplete_entry(
            self,
            new_file_function,
            length,
            merge_function):
        for invalid_file_i in range(DEFAULT_FILES_NUM):
            with contextlib.ExitStack() as stack:
                files = tuple(stack.enter_context(new_file_function())
                              for _ in range(DEFAULT_FILES_NUM))
                f_out = stack.enter_context(new_file_function())
                for i, f in enumerate(files):
                    pairs_list = random_pairs_list(
                        DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE, length + 1)
                    bytes_ = pairs_list_to_bytes(
                        pairs_list,
                        DEFAULT_SIZE, DEFAULT_SIZE, DEFAULT_SIZE)
                    f.write(bytes_)
                    f.seek(0)

                for _ in range(1, 5 * DEFAULT_SIZE):
                    files[invalid_file_i].seek(-1, 2)
                    files[invalid_file_i].truncate()
                    files[invalid_file_i].seek(0)
                    with pytest.raises(ValueError):
                        merge_function(files, f_out)


@pytest.mark.parametrize('dump_function', [dump_to_file_stream,
                                           dump_iter_to_file])
class TestIntegration:
    def test_dump_load(
            self,
            cands_bytes_pair,
            new_file_function,
            dump_function):
        candidate_pairs, *_ = cands_bytes_pair
        with new_file_function() as f:
            dump_function(candidate_pairs, f)
            f.seek(0)
            assert serialization.load_candidate_pairs(f) == candidate_pairs

    @pytest.mark.parametrize('split', (1, 2, 5))
    @pytest.mark.parametrize('merge_function',
                             [merge_to_file_stream,
                              merge_iter_to_file_size_provided,
                              merge_iter_to_file_size_not_provided])
    def test_merge(
            self,
            cands_bytes_pair,
            new_file_function,
            split,
            dump_function,
            merge_function):
        (sorted_pairs_list, _, all_pairs_list,
         (sim_size, dset_i_size, rec_i_size, _)) = cands_bytes_pair
        pairs_lists = tuple([] for _ in range(split))

        rng = random.Random(RANDOM_SEED)
        for pair in all_pairs_list:
            rng.choice(pairs_lists).append(pair)

        with contextlib.ExitStack() as stack:
            files = tuple(stack.enter_context(new_file_function())
                          for _ in pairs_lists)
            for f, pairs_list in zip(files, pairs_lists):
                candidate_pairs = pairs_list_to_candidate_pairs(
                        pairs_list, sim_size, dset_i_size, rec_i_size)
                dump_function(candidate_pairs, f)
                f.seek(0)
            with new_file_function() as f_out:
                merge_function(files, f_out)
                f_out.seek(0)
                assert (sorted_pairs_list
                        == serialization.load_candidate_pairs(f_out))
