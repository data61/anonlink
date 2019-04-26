#!/usr/bin/env python3.4

import unittest

from anonlink import benchmark


class TestBenchmark(unittest.TestCase):
    def test_comparison_speed_benchmark(self):
        benchmark.compute_comparison_speed(100, 100, 0.7)

    def test_comparing_python_c_bench(self):
        benchmark.compare_python_c(500, 30, frac=0.8)

    def test_benchmark(self):
        benchmark.benchmark(1000, True)
