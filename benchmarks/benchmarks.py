# Write the benchmarking functions here.
# See "Writing benchmarks" in the asv docs for more information.
import random

from anonlink import util, distributed_processing
from anonlink.entitymatch import calculate_mapping_greedy, calculate_filter_similarity
from anonlink.util import popcount_vector


class TimeSuite:

    def setup(self):
        some_filters = util.generate_clks(10000)
        n1, n2 = 10000, 5000
        self.filters1 = [some_filters[random.randrange(0, 8000)] for _ in range(n1)]
        self.filters2 = [some_filters[random.randrange(2000, 10000)] for _ in range(n2)]

    def time_greedy_solve(self):
        calculate_mapping_greedy(self.filters1, self.filters2)

    def time_default_compare_calc(self):
        calculate_filter_similarity(self.filters1, self.filters2)

    def time_parallel_compare_calc(self):
        distributed_processing.calculate_filter_similarity(self.filters1, self.filters2)

    def time_popcount(self):
        clks = [f[0] for f in self.filters1]
        popcount_vector(clks)


class MemSuite:

    def setup(self):
        some_filters = util.generate_clks(10000)
        n1, n2 = 10000, 5000
        self.filters1 = [some_filters[random.randrange(0, 8000)] for _ in range(n1)]
        self.filters2 = [some_filters[random.randrange(2000, 10000)] for _ in range(n2)]

    def peakmem_mapping(self):
        calculate_mapping_greedy(self.filters1, self.filters2)

