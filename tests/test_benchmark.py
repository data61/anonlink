#!/usr/bin/env python3.4

import unittest

from anonlink import benchmark


class TestBenchmark(unittest.TestCase):
    def test_comparison_speed_benchmark(self):
        benchmark.compute_comparison_speed(100, 100, 0.7)
        benchmark.compute_comparison_speed(100, 100, 0.7, 10)

    def test_benchmark(self):
        benchmark.benchmark(1000)
