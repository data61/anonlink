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
    num_bytes = num_words * 8
    return draw(binary(min_size=num_bytes, max_size=num_bytes))


@given(data())
@pytest.mark.parametrize('num_bytes', [8, 32, 64, 512, 1024])
def test_popcnt_array(num_bytes, data):
    input_as_bitarray = bitarray()
    input_as_bytes = data.draw(binary(min_size=num_bytes, max_size=num_bytes))
    input_as_bitarray.frombytes(input_as_bytes)
    carr = array.array('b', input_as_bytes)
    for array_size in [8, 16, 32, 64, 128, 256, 512]:
        if array_size < num_bytes:
            assert sum(_dice.popcount_arrays(carr, array_size)) == input_as_bitarray.count()
    assert sum(_dice.popcount_arrays(carr, num_bytes)) == input_as_bitarray.count()


@pytest.mark.parametrize('num_bytes', [2**i for i in range(12, 26)])
def test_popcnt_large(num_bytes):
    data = bitarray("10101010" * num_bytes)
    carr = array.array('b', data.tobytes())
    # Use an element size of 1024
    output_counts = _dice.popcount_arrays(carr, 1024)
    assert output_counts[0] == data[:1024*8].count()
    assert output_counts[-1] == data[-1024*8:].count()
    assert sum(output_counts) == data.count()

    for array_size in [2048, 4096, 8192]:
        if array_size < num_bytes:
            assert sum(_dice.popcount_arrays(carr, array_size)) == data.count()


@given(aligned_bytes())
def test_popcnt_array_len_1(input_as_bytes):
    """
    The array_bytes is set to the length of the input
    """

    carr = array.array('b', input_as_bytes)
    resulting_popcount_array = _dice.popcount_arrays(carr, len(input_as_bytes))
    assert len(resulting_popcount_array) == 1
    assert sum(resulting_popcount_array) == resulting_popcount_array[0]
    input_as_bitarray = bitarray()
    input_as_bitarray.frombytes(input_as_bytes)
    assert sum(resulting_popcount_array) == input_as_bitarray.count()


def test_popcnt_empty_array():
    carr = array.array('b', b'')
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


@pytest.mark.parametrize('num_bytes', [2**i for i in range(6, 20)])
def test_popcnt_all_ones(num_bytes):
    data = bitarray("1" * 8 * num_bytes)
    carr = array.array('b', data.tobytes())
    output_counts = _dice.popcount_arrays(carr, 8)
    assert output_counts[0] == 64
    assert output_counts[-1] == 64
    assert sum(output_counts) == 8 * num_bytes


# @pytest.mark.parametrize('sim_fun', SIM_FUNS)
#     @pytest.mark.parametrize('k', [None, 0, 1])
#     @pytest.mark.parametrize('threshold', [0., .5])
#     def test_all_low(self, sim_fun, k, threshold):