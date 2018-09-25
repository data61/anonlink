import itertools
import random

import pytest
from bitarray import bitarray

from anonlink.similarities._smc import _smc_sim
from anonlink.similarities import (hamming_similarity,
                                   simple_matching_coefficient)

SIM_FUNS = [hamming_similarity, simple_matching_coefficient]


def test_smc_sim_k():
    # This tests an internal function. It may need to change if the
    # implementation of `simple_matching_coefficient` changes.
    assert _smc_sim(bitarray('0'), bitarray('0')) == 1
    assert _smc_sim(bitarray('0'), bitarray('1')) == 0
    assert _smc_sim(bitarray('1'), bitarray('0')) == 0
    assert _smc_sim(bitarray('1'), bitarray('1')) == 1

    assert _smc_sim(bitarray('00'), bitarray('00')) == 1
    assert _smc_sim(bitarray('00'), bitarray('01')) == .5
    assert _smc_sim(bitarray('00'), bitarray('10')) == .5
    assert _smc_sim(bitarray('00'), bitarray('11')) == 0
    assert _smc_sim(bitarray('01'), bitarray('00')) == .5
    assert _smc_sim(bitarray('01'), bitarray('01')) == 1
    assert _smc_sim(bitarray('01'), bitarray('10')) == 0
    assert _smc_sim(bitarray('01'), bitarray('11')) == .5
    assert _smc_sim(bitarray('10'), bitarray('00')) == .5
    assert _smc_sim(bitarray('10'), bitarray('01')) == 0
    assert _smc_sim(bitarray('10'), bitarray('10')) == 1
    assert _smc_sim(bitarray('10'), bitarray('11')) == .5
    assert _smc_sim(bitarray('11'), bitarray('00')) == 0
    assert _smc_sim(bitarray('11'), bitarray('01')) == .5
    assert _smc_sim(bitarray('11'), bitarray('10')) == .5
    assert _smc_sim(bitarray('11'), bitarray('11')) == 1


def _sanity_check_candidates(sims, indices, candidates):
    assert len(indices) == 2
    assert all(len(i) == len(sims) for i in indices)
    assert len(candidates) == len(sims)
    assert not candidates or len(next(iter(candidates))) == 2


@pytest.fixture(scope='module',
                params=itertools.product([0, 80], [64]))
def datasets(request):
    recs_per_dataset, length = request.param

    result = tuple([bitarray(random.choices((False, True), k=length))
                    for _ in range(recs_per_dataset)]
                   for _ in range(2))
    
    assert len(result) == 2
    assert all(len(dataset) == recs_per_dataset for dataset in result)
    assert all(len(record) == length for dataset in result
                                     for record in dataset)

    return result

@pytest.mark.parametrize('threshold', [1.0, 0.6, 0.0])
@pytest.mark.parametrize('f', SIM_FUNS)
class TestHammingSimilarity:
    def test_no_k(self, datasets, threshold, f):
        sims, indices = f(datasets, threshold, k=None)
        candidates = dict(zip(zip(indices[0], indices[1]), sims))
        
        _sanity_check_candidates(sims, indices, candidates)

        for (i0, record0), (i1, record1) \
                in itertools.product(enumerate(datasets[0]),
                                     enumerate(datasets[1])):
            sim = _smc_sim(record0, record1)

            if sim >= threshold:
                assert (i0, i1) in candidates
                assert candidates[i0, i1] == sim
            else:
                assert (i0, i1) not in candidates

    @pytest.mark.parametrize('k', [0, 20, 80])
    def test_k(self, datasets, threshold, k, f):
        sims, indices = f(datasets, threshold, k=k)
        candidates = dict(zip(zip(indices[0], indices[1]), sims))
        
        _sanity_check_candidates(sims, indices, candidates)

        # Make sure we return at most k
        for i, _ in enumerate(datasets[0]):
            assert sum(indices[0] == i for indices in candidates) <= k
        for i, _ in enumerate(datasets[1]):
            assert sum(indices[1] == i for indices in candidates) <= k

        for (i0, record0), (i1, record1) \
                in itertools.product(*map(enumerate, datasets)):
            sim = _smc_sim(record0, record1)

            if sim >= threshold:
                if (i0, i1) not in candidates:
                    assert (not k
                            or sim <= min(val
                                          for index, val in candidates.items()
                                          if index[0] == i0)
                            or sim <= min(val
                                          for index, val in candidates.items()
                                          if index[1] == i1))
                else:
                    assert candidates[i0, i1] == sim
            else:
                assert (i0, i1) not in candidates


@pytest.mark.parametrize('size', [0, 1, 3, 5])
@pytest.mark.parametrize('threshold', [0., .5, 1.])
@pytest.mark.parametrize('k', [None, 0, 10])
@pytest.mark.parametrize('f', SIM_FUNS)
def test_unsupported_size(size, threshold, k, f):
    datasets = [['01001101'] for _ in range(size)]
    with pytest.raises(NotImplementedError):
        f(datasets, threshold, k=k)
