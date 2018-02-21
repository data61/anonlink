from bitarray import bitarray
from itertools import combinations_with_replacement

def bitarrays_of_length(L):
    """
    Return a bit array of length L*64 whose contents are combinations of
    the words 0, 2^64-1, 1 or 2^63 (ie. all zeros, all ones, or a one in
    the least or most significant position).
    """
    special_words = [64*bitarray('0'),
                     63*bitarray('0') + bitarray('1'),
                     bitarray('1') + 63*bitarray('0'),
                     64*bitarray('1')]
    # '+' on bitarrays is concatenation
    return [sum(word, bitarray())
            for word in combinations_with_replacement(special_words, L)]

# Interesting key lengths (usually around 2^something +/-1).
key_lengths = [1, 2, 3, 4, 8, 9, 10, 15, 16, 17,
               23, 24, 25, 30, 31, 32, 33, 63, 64, 65]
