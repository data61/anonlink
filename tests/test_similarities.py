import itertools
import random

import pytest
from bitarray import bitarray

from anonlink.similarities.hamming import _hamming_sim
from anonlink.similarities import hamming_similarity


def test_hamming_sim_k():
    # This tests an internal function. It may need to change if the
    # implementation of `hamming_similarity` changes.
    assert _hamming_sim(bitarray('0'), bitarray('0')) == 1
    assert _hamming_sim(bitarray('0'), bitarray('1')) == 0
    assert _hamming_sim(bitarray('1'), bitarray('0')) == 0
    assert _hamming_sim(bitarray('1'), bitarray('1')) == 1

    assert _hamming_sim(bitarray('00'), bitarray('00')) == 1
    assert _hamming_sim(bitarray('00'), bitarray('01')) == .5
    assert _hamming_sim(bitarray('00'), bitarray('10')) == .5
    assert _hamming_sim(bitarray('00'), bitarray('11')) == 0
    assert _hamming_sim(bitarray('01'), bitarray('00')) == .5
    assert _hamming_sim(bitarray('01'), bitarray('01')) == 1
    assert _hamming_sim(bitarray('01'), bitarray('10')) == 0
    assert _hamming_sim(bitarray('01'), bitarray('11')) == .5
    assert _hamming_sim(bitarray('10'), bitarray('00')) == .5
    assert _hamming_sim(bitarray('10'), bitarray('01')) == 0
    assert _hamming_sim(bitarray('10'), bitarray('10')) == 1
    assert _hamming_sim(bitarray('10'), bitarray('11')) == .5
    assert _hamming_sim(bitarray('11'), bitarray('00')) == 0
    assert _hamming_sim(bitarray('11'), bitarray('01')) == .5
    assert _hamming_sim(bitarray('11'), bitarray('10')) == .5
    assert _hamming_sim(bitarray('11'), bitarray('11')) == 1


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
class TestHammingSimilarity:
    def test_no_k(self, datasets, threshold):
        sims, indices = hamming_similarity(datasets, threshold, k=None)
        candidates = dict(zip(zip(indices[0], indices[1]), sims))
        
        _sanity_check_candidates(sims, indices, candidates)

        for (i0, record0), (i1, record1) \
                in itertools.product(enumerate(datasets[0]),
                                     enumerate(datasets[1])):
            sim = _hamming_sim(record0, record1)

            if sim >= threshold:
                assert (i0, i1) in candidates
                assert candidates[i0, i1] == sim
            else:
                assert (i0, i1) not in candidates

    @pytest.mark.parametrize('k', [0, 20, 80])
    def test_k(self, datasets, threshold, k):
        sims, indices = hamming_similarity(datasets, threshold, k=k)
        candidates = dict(zip(zip(indices[0], indices[1]), sims))
        
        _sanity_check_candidates(sims, indices, candidates)

        # Make sure we return at most k
        for i, _ in enumerate(datasets[0]):
            assert sum(indices[0] == i for indices in candidates) <= k
        for i, _ in enumerate(datasets[1]):
            assert sum(indices[1] == i for indices in candidates) <= k

        for (i0, record0), (i1, record1) \
                in itertools.product(*map(enumerate, datasets)):
            sim = _hamming_sim(record0, record1)

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
