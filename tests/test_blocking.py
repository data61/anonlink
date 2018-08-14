import itertools
import operator
import random
import unittest

import bitarray
import pytest

from anonlink import blocking


class TestBlockAnd:
    def test_block_and_two(self):
        datasets = 3
        samples = 20

        rng = random.Random()
        rng.seed(452)

        vals1 = [[{rng.randrange(5), rng.randrange(5)} for _ in range(samples)]
                 for _ in range(datasets)]
        vals2 = [[{rng.randrange(2)} for _ in range(samples)]
                 for _ in range(datasets)]

        blocking_f1 = lambda i, j, _: vals1[i][j]
        blocking_f2 = lambda i, j, _: vals2[i][j]
        blocking_f = blocking.block_and(blocking_f1, blocking_f2)

        blocks = [[set(blocking_f(i, j, ())) for j in range(samples)]
                  for i in range(datasets)]

        for i1, j1, i2, j2 in itertools.product(
                range(datasets), range(samples), repeat=2):
            b_intersect = bool(blocks[i1][j1] & blocks[i2][j2])
            v1_intersect = bool(vals1[i1][j1] & vals1[i2][j2])
            v2_intersect = bool(vals2[i1][j1] & vals2[i2][j2])

            assert b_intersect == (v1_intersect and v2_intersect)

    def test_block_and_three(self):
        datasets = 3
        samples = 20

        rng = random.Random()
        rng.seed(452)

        vals1 = [[{rng.randrange(2)} for _ in range(samples)]
                 for _ in range(datasets)]
        vals2 = [[{rng.randrange(2)} for _ in range(samples)]
                 for _ in range(datasets)]
        vals3 = [[{rng.randrange(2)} for _ in range(samples)]
                 for _ in range(datasets)]

        blocking_f1 = lambda i, j, _: vals1[i][j]
        blocking_f2 = lambda i, j, _: vals2[i][j]
        blocking_f3 = lambda i, j, _: vals3[i][j]
        blocking_f = blocking.block_and([blocking_f1, blocking_f2, blocking_f3])

        blocks = [[set(blocking_f(i, j, ())) for j in range(samples)]
                  for i in range(datasets)]

        for i1, j1, i2, j2 in itertools.product(
                range(datasets), range(samples), repeat=2):
            b_intersect = bool(blocks[i1][j1] & blocks[i2][j2])
            v1_intersect = bool(vals1[i1][j1] & vals1[i2][j2])
            v2_intersect = bool(vals2[i1][j1] & vals2[i2][j2])
            v3_intersect = bool(vals3[i1][j1] & vals3[i2][j2])

            assert (b_intersect
                    == (v1_intersect and v2_intersect and v3_intersect))

    def test_empty(self):
        with pytest.raises(TypeError):
            blocking.block_and()


class TestBlockOr:
    def test_block_or_two(self):
        datasets = 3
        samples = 20

        rng = random.Random()
        rng.seed(452)

        vals1 = [[{rng.randrange(5), rng.randrange(5)} for _ in range(samples)]
                 for _ in range(datasets)]
        vals2 = [[{rng.randrange(2)} for _ in range(samples)]
                 for _ in range(datasets)]

        blocking_f1 = lambda i, j, _: vals1[i][j]
        blocking_f2 = lambda i, j, _: vals2[i][j]
        blocking_f = blocking.block_or(blocking_f1, blocking_f2)

        blocks = [[set(blocking_f(i, j, ())) for j in range(samples)]
                  for i in range(datasets)]

        for i1, j1, i2, j2 in itertools.product(
                range(datasets), range(samples), repeat=2):
            b_intersect = bool(blocks[i1][j1] & blocks[i2][j2])
            v1_intersect = bool(vals1[i1][j1] & vals1[i2][j2])
            v2_intersect = bool(vals2[i1][j1] & vals2[i2][j2])

            assert b_intersect == (v1_intersect or v2_intersect)

    def test_block_or_three(self):
        datasets = 3
        samples = 20

        rng = random.Random()
        rng.seed(452)

        vals1 = [[{rng.randrange(2)} for _ in range(samples)]
                 for _ in range(datasets)]
        vals2 = [[{rng.randrange(2)} for _ in range(samples)]
                 for _ in range(datasets)]
        vals3 = [[{rng.randrange(2)} for _ in range(samples)]
                 for _ in range(datasets)]

        blocking_f1 = lambda i, j, _: vals1[i][j]
        blocking_f2 = lambda i, j, _: vals2[i][j]
        blocking_f3 = lambda i, j, _: vals3[i][j]
        blocking_f = blocking.block_or([blocking_f1, blocking_f2, blocking_f3])

        blocks = [[set(blocking_f(i, j, ())) for j in range(samples)]
                  for i in range(datasets)]

        for i1, j1, i2, j2 in itertools.product(
                range(datasets), range(samples), repeat=2):
            b_intersect = bool(blocks[i1][j1] & blocks[i2][j2])
            v1_intersect = bool(vals1[i1][j1] & vals1[i2][j2])
            v2_intersect = bool(vals2[i1][j1] & vals2[i2][j2])
            v3_intersect = bool(vals3[i1][j1] & vals3[i2][j2])

            assert (b_intersect
                    == (v1_intersect or v2_intersect or v3_intersect))

    def test_empty(self):
        with pytest.raises(TypeError):
            blocking.block_or()


class TestBitBlocking:
    @pytest.mark.parametrize('seed', [345, None])
    def test_bit_blocking(self, seed):
        datasets = 3
        samples = 25
        hash_lens = 5
        r = 2
        g = 2

        rng = random.Random()
        rng.seed(seed)
        hashes = [[[rng.choice((False, True)) for _ in range(hash_lens)]
                   for _ in range(samples)]
                  for _ in range(datasets)]

        blocking_f = blocking.bit_blocking(r, g, seed=seed)
        blocks = [[set(blocking_f(i, j, hashes[i][j])) for j in range(samples)]
                  for i in range(datasets)]

        for i1, j1, i2, j2 in itertools.product(
                range(datasets), range(samples), repeat=2):
            hash_diffs = sum(map(operator.ne, hashes[i1][j1], hashes[i2][j2]))
            same_block = bool(blocks[i1][j1] & blocks[i2][j2])

            if hash_diffs == 0:
                assert same_block
            elif hash_diffs > r * g:
                assert not same_block

    @pytest.mark.parametrize('g', [-5, -1, 0, 1, 5])
    @pytest.mark.parametrize('r', [-5, -1, 0, 1, 5])
    def test_invalid_r_g(self, g, r):
        if g <= 0 or r <= 0:
            with pytest.raises(ValueError):
                blocking.bit_blocking(g, r)
        else:
            # Make sure doesn't raise
            blocking.bit_blocking(g, r)

    def test_inconsistent_hash_length(self):
        g = 2
        r = 2
        bitarray5 = bitarray.bitarray('01010')
        bitarray6 = bitarray.bitarray('010101')
        
        fun = blocking.bit_blocking(g, r)
        tuple(fun(0, 0, bitarray5))
        with pytest.raises(ValueError):
            tuple(fun(0, 1, bitarray6))


class TestContinuousBlocking:
    def test_int(self):
        datasets = 3
        samples = 20
        radius = 3

        values = [range(samples) for _ in range(datasets)]

        blocking_f = blocking.continuous_blocking(radius, values)
        blocks = {(values[i][j], frozenset(blocking_f(i, j, ())))
                  for j in range(samples)
                  for i in range(datasets)}

        for (v1, b1), (v2, b2) in itertools.product(blocks, repeat=2):
            dist = abs(v1 - v2)
            intersect = bool(b1 & b2)
            assert dist > radius or intersect, \
                'Records separated by <= radius should share a block.'
            assert dist <= 2 * radius or not intersect, \
                'Records separated by > 2 * radius should not share a block.'

    def test_float(self):
        datasets = 3
        samples = 20
        radius = 3
        seed = 453
        
        rng = random.Random()
        rng.seed(seed)
        values = [[rng.uniform(0, samples) for _ in range(samples)]
                  for _ in range(datasets)]

        blocking_f = blocking.continuous_blocking(radius, values)
        blocks = {(values[i][j], frozenset(blocking_f(i, j, ())))
                  for j in range(samples)
                  for i in range(datasets)}

        for (v1, b1), (v2, b2) in itertools.product(blocks, repeat=2):
            dist = abs(v1 - v2)
            intersect = bool(b1 & b2)
            assert dist > radius or intersect, \
                'Records separated by <= radius should share a block.'
            assert dist <= 2 * radius or not intersect, \
                'Records separated by > 2 * radius should not share a block.'

    @pytest.mark.parametrize('radius', [-5, -1, -.5, 0, .5, 1, 5])
    def test_nonpositive_radius(self, radius):
        datasets = [[.2, .4], [.6, .8]]
        if radius > 0:
            # Shouldn't throw.
            blocking.continuous_blocking(radius, datasets)
        else:
            with pytest.raises(ValueError):
                blocking.continuous_blocking(radius, datasets)


class TestListBlocking:
    def test_list_blocking(self):
        datasets = 3
        samples = 20

        values = [[(i, j) for j in range(samples)] for i in range(datasets)]

        blocking_f = blocking.list_blocking(values)
        blocks = [[(values[i][j], blocking_f(i, j, ())) for j in range(samples)]
                  for i in range(datasets)]

        for v, b in itertools.chain.from_iterable(blocks):
            assert (v,) == b
