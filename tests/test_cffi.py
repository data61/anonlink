from bitarray import bitarray
from anonlink._entitymatcher import ffi, lib


byte_sizes = [2, 32, 64, 512, 1024, 100000]


def test_popcnt():
    for num_bytes in byte_sizes:
        data = bitarray("10101010" * num_bytes)
        assert lib.popcnt(data.tobytes(), num_bytes) == data.count()


def test_popcnt_char_array():

    for num_bytes in byte_sizes:
        data = bitarray("10101010" * num_bytes)
        carr = ffi.new('char[]', data.tobytes())

        assert lib.popcnt(carr, num_bytes) == data.count()



