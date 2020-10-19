from bitarray import bitarray
import array
from anonlink.similarities import _dice

byte_sizes = [8, 32, 64, 512, 1024, 100000]


def test_popcnt():
    for num_bytes in byte_sizes:
        data = bitarray("10101010" * num_bytes)
        assert _dice.popcnt(data.tobytes(), num_bytes) == data.count()


def test_popcnt_char_array():
    for num_bytes in byte_sizes:
        data = bitarray("10101010" * num_bytes)
        carr = array.array('b', data.tobytes())
        assert _dice.popcount_arrays(carr, num_bytes)[0] == data.count()



