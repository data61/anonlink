import pytest
from bitarray import bitarray
import array
from anonlink.similarities import _dice

from hypothesis import given
from hypothesis.strategies import binary, data, integers
from hypothesis.strategies import composite


@composite
def aligned_bytes(draw, num_words=None):
    if num_words is None:
        num_words = draw(integers(min_value=1, max_value=2048))
    num_bytes = num_words
    return draw(binary(min_size=num_bytes, max_size=num_bytes))


@given(data())
@pytest.mark.parametrize('num_bytes', [8, 32, 64, 512, 1024, 2048])
def test_popcnt_array(num_bytes, data):
    input_as_bitarray = bitarray()
    input_as_bytes = data.draw(binary(min_size=num_bytes, max_size=num_bytes))
    input_as_bitarray.frombytes(input_as_bytes)
    carr = array.array('b', input_as_bytes)
    bitarray_count = input_as_bitarray.count()
    for array_size in [8, 16, 32, 64, 128, 256, 512, 1024]:
        if array_size <= num_bytes:
            output_counts = _dice.popcount_arrays(carr, array_size)
            assert output_counts[0] == input_as_bitarray[:array_size*8].count()
            assert sum(output_counts) == bitarray_count


@pytest.mark.parametrize('num_bytes', [2**i for i in range(10, 22)])
def test_popcnt_large(num_bytes):
    data = bitarray("10101010" * num_bytes)
    carr = array.array('b', data.tobytes())
    # Use an element size of 1024 bytes
    output_counts = _dice.popcount_arrays(carr, 1024)
    assert output_counts[0] == data[:1024*8].count()
    assert output_counts[-1] == data[-1024*8:].count()
    assert sum(output_counts) == data.count()

    for array_size in [8, 4096, 8192]:
        if array_size < num_bytes:
            assert sum(_dice.popcount_arrays(carr, array_size)) == data.count()


@given(aligned_bytes())
def test_popcnt_array_len_1(input_as_bytes):
    carr = array.array('b', input_as_bytes)
    resulting_popcount_array = _dice.popcount_arrays(carr, len(input_as_bytes))
    assert len(resulting_popcount_array) == 1
    assert sum(resulting_popcount_array) == resulting_popcount_array[0]
    input_as_bitarray = bitarray()
    input_as_bitarray.frombytes(input_as_bytes)
    assert sum(resulting_popcount_array) == input_as_bitarray.count()


def test_popcnt_empty_array():
    carr = array.array('b', b'')
    resulting_popcount_array = _dice.popcount_arrays(carr, 8)
    assert len(resulting_popcount_array) == 0
    # shouldn't make a difference having a array_size of zero
    resulting_popcount_array = _dice.popcount_arrays(carr, 0)
    assert len(resulting_popcount_array) == 0


@pytest.mark.parametrize('num_bytes', [15, 17, 23, 25, 255])
def test_data_not_multiple_of_element_size(num_bytes):
    data = bitarray("10101010" * num_bytes)
    carr = array.array('b', data.tobytes())
    # Use an element size of 8 bytes
    with pytest.raises(AssertionError):
        output_counts = _dice.popcount_arrays(carr, 8)
        assert output_counts[0] == data[:64].count()
        assert sum(output_counts) == data.count()


def test_data_length_not_multiple_of_64():
    # 32 bits of data, array_size of 8 bits (1 byte)
    data = bitarray("10101010" * 4)
    carr = array.array('b', data.tobytes())
    output_counts = _dice.popcount_arrays(carr, 1)
    assert len(output_counts) == 4
    assert sum(output_counts) == data.count()


@pytest.mark.parametrize('num_bytes', [2**i for i in range(6, 12)])
def test_popcnt_all_ones(num_bytes):
    data = bitarray("1" * 8 * num_bytes)
    carr = array.array('b', data.tobytes())
    output_counts = _dice.popcount_arrays(carr, 8)
    assert output_counts[0] == 64
    assert output_counts[-1] == 64
    assert sum(output_counts) == 8 * num_bytes


@pytest.mark.parametrize('num_bytes', [2**i for i in range(6, 12)])
def test_popcnt_all_zeros(num_bytes):
    data = bitarray("0" * 8 * num_bytes)
    carr = array.array('b', data.tobytes())
    output_counts = _dice.popcount_arrays(carr, 8)
    assert sum(output_counts) == 0

