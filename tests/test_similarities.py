import itertools

import numpy as np
import pytest

from anonlink.similarities.hamming import _hamming_sim
from anonlink.similarities import hamming_similarity


def test_hamming_sim_k():
    # This tests an internal function. It may need to change if the
    # implementation of `hamming_similarity` changes.
    assert _hamming_sim([False], [False]) == 1
    assert _hamming_sim([False], [True]) == 0
    assert _hamming_sim([True], [False]) == 0
    assert _hamming_sim([True], [True]) == 1

    assert _hamming_sim([False, False], [False, False]) == 1
    assert _hamming_sim([False, False], [False, True]) == .5
    assert _hamming_sim([False, False], [True, False]) == .5
    assert _hamming_sim([False, False], [True, True]) == 0
    assert _hamming_sim([False, True], [False, False]) == .5
    assert _hamming_sim([False, True], [False, True]) == 1
    assert _hamming_sim([False, True], [True, False]) == 0
    assert _hamming_sim([False, True], [True, True]) == .5
    assert _hamming_sim([True, False], [False, False]) == .5
    assert _hamming_sim([True, False], [False, True]) == 0
    assert _hamming_sim([True, False], [True, False]) == 1
    assert _hamming_sim([True, False], [True, True]) == .5
    assert _hamming_sim([True, True], [False, False]) == 0
    assert _hamming_sim([True, True], [False, True]) == .5
    assert _hamming_sim([True, True], [True, False]) == .5
    assert _hamming_sim([True, True], [True, True]) == 1

    if __debug__:
        with pytest.raises(AssertionError):
            _hamming_sim([True], [True, True])
        with pytest.raises(AssertionError):
            _hamming_sim([True, False, False], [True, True])
        with pytest.raises(AssertionError):
            _hamming_sim([], [])


def _sanity_check_candidates(indices, sims, candidates):
    assert len(indices) == 2
    assert all(len(i) == len(sims) for i in indices)
    assert len(candidates) == len(sims)
    assert not candidates or len(next(iter(candidates))) == 2


@pytest.fixture(scope='module',
                params=itertools.product([0, 80], [64]))
def datasets(request):
    recs_per_dataset, length = request.param

    result = np.random.choice((True, False),
                                size=(2, recs_per_dataset, length))
    assert len(result) == 2
    assert all(len(dataset) == recs_per_dataset for dataset in result)
    assert all(len(record) == length for dataset in result
                                     for record in dataset)

    return result


@pytest.mark.parametrize('threshold', [1.0, 0.6, 0.0], scope='class')
class TestHammingSimilarity:
    def test_no_k(self, datasets, threshold):
        indices, sims = hamming_similarity(datasets, threshold, k=None)
        candidates = dict(zip(zip(indices[0], indices[1]), sims))
        
        _sanity_check_candidates(indices, sims, candidates)

        for (i0, record0), (i1, record1) \
                in itertools.product(*map(enumerate, datasets)):
            sim = _hamming_sim(record0, record1)

            if sim >= threshold:
                assert (i0, i1) in candidates
                assert candidates[i0, i1] == sim
            else:
                assert (i0, i1) not in candidates

    @pytest.mark.parametrize('k', [0, 20, 80])
    def test_k(self, datasets, threshold, k):
        indices, sims = hamming_similarity(datasets, threshold, k=k)
        candidates = dict(zip(zip(indices[0], indices[1]), sims))
        
        _sanity_check_candidates(indices, sims, candidates)

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
