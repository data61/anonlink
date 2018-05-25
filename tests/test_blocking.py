import itertools
import operator
import random
import unittest

from anonlink import blocking


class TestBlockAnd(unittest.TestCase):
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

            self.assertEqual(b_intersect, v1_intersect and v2_intersect)

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

            self.assertEqual(b_intersect,
                             v1_intersect and v2_intersect and v3_intersect)


class TestBlockOr(unittest.TestCase):
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

            self.assertEqual(b_intersect, v1_intersect or v2_intersect)

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

            self.assertEqual(b_intersect,
                             v1_intersect or v2_intersect or v3_intersect)


class TestBitBlocking(unittest.TestCase):
    def test_bit_blocking(self):
        datasets = 3
        samples = 25
        seed = 345
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
                self.assertTrue(same_block)
            elif hash_diffs > r * g:
                self.assertFalse(same_block)




class TestContinuousBlocking(unittest.TestCase):
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
            self.assertTrue(
                dist > radius or intersect,
                'Records separated by <= radius should share a block.')
            self.assertTrue(
                dist <= 2 * radius or not intersect,
                'Records separated by > 2 * radius should not share a block.')

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
            self.assertTrue(
                dist > radius or intersect,
                'Records separated by <= radius should share a block.')
            self.assertTrue(
                dist <= 2 * radius or not intersect,
                'Records separated by > 2 * radius should not share a block.')


class TestListBlocking(unittest.TestCase):
    def test_list_blocking(self):
        datasets = 3
        samples = 20

        values = [[(i, j) for j in range(samples)] for i in range(datasets)]

        blocking_f = blocking.list_blocking(values)
        blocks = [[(values[i][j], blocking_f(i, j, ())) for j in range(samples)]
                  for i in range(datasets)]

        for v, b in itertools.chain.from_iterable(blocks):
            self.assertEqual((v,), b)
