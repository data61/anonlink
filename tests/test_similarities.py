import itertools

import numpy as np
import pytest

from anonlink.similarities import _hamming_sim_f, hamming_similarity


def test_hamming_sim_k():
    # This tests an internal function. It may need to change if the
    # implementation of `hamming_similarity` changes.
    assert _hamming_sim_f([False], [False]) == 1
    assert _hamming_sim_f([False], [True]) == 0
    assert _hamming_sim_f([True], [False]) == 0
    assert _hamming_sim_f([True], [True]) == 1

    assert _hamming_sim_f([False, False], [False, False]) == 1
    assert _hamming_sim_f([False, False], [False, True]) == .5
    assert _hamming_sim_f([False, False], [True, False]) == .5
    assert _hamming_sim_f([False, False], [True, True]) == 0
    assert _hamming_sim_f([False, True], [False, False]) == .5
    assert _hamming_sim_f([False, True], [False, True]) == 1
    assert _hamming_sim_f([False, True], [True, False]) == 0
    assert _hamming_sim_f([False, True], [True, True]) == .5
    assert _hamming_sim_f([True, False], [False, False]) == .5
    assert _hamming_sim_f([True, False], [False, True]) == 0
    assert _hamming_sim_f([True, False], [True, False]) == 1
    assert _hamming_sim_f([True, False], [True, True]) == .5
    assert _hamming_sim_f([True, True], [False, False]) == 0
    assert _hamming_sim_f([True, True], [False, True]) == .5
    assert _hamming_sim_f([True, True], [True, False]) == .5
    assert _hamming_sim_f([True, True], [True, True]) == 1

    if __debug__:
        with pytest.raises(AssertionError):
            _hamming_sim_f([True], [True, True])
        with pytest.raises(AssertionError):
            _hamming_sim_f([True, False, False], [True, True])
        with pytest.raises(AssertionError):
            _hamming_sim_f([], [])


@pytest.mark.parametrize('recs_per_dataset', [0, 80])
@pytest.mark.parametrize('length', [64])
@pytest.mark.parametrize('threshold', [1.0, 0.6, 0.0])
def test_hamming_similarity_no_k(recs_per_dataset, length, threshold):
    datasets = np.random.choice((True, False),
                                size=(2, recs_per_dataset, length))
    indices, sims = hamming_similarity(datasets, threshold, k=None)
    candidates = dict(zip(zip(indices[0], indices[1]), sims))

    assert len(datasets) == 2
    assert len(datasets[0]) == len(datasets[1]) == recs_per_dataset
    assert all(len(datasets[0][i]) == length for i in range(recs_per_dataset))

    assert len(indices) == 2
    assert all(len(i) == len(sims) for i in indices)
    assert len(candidates) == len(sims)
    assert not candidates or len(next(iter(candidates))) == 2

    for i, j in itertools.product(range(recs_per_dataset), repeat=2):
        sim = _hamming_sim_f(datasets[0][i], datasets[1][j])

        if sim >= threshold:
            assert (i, j) in candidates
            assert candidates[i, j] == sim
        else:
            assert (i, j) not in candidates


@pytest.mark.parametrize('recs_per_dataset', [0, 80])
@pytest.mark.parametrize('length', [64])
@pytest.mark.parametrize('threshold', [1.0, 0.6, 0.0])
@pytest.mark.parametrize('k', [0, 20, 80])
def test_hamming_similarity_k(recs_per_dataset, length, threshold, k):
    datasets = np.random.choice((True, False),
                                size=(2, recs_per_dataset, length))
    indices, sims = hamming_similarity(datasets, threshold, k=k)
    candidates = dict(zip(zip(indices[0], indices[1]), sims))

    assert len(datasets) == 2
    assert len(datasets[0]) == len(datasets[1]) == recs_per_dataset
    assert all(len(datasets[0][i]) == length for i in range(recs_per_dataset))

    assert len(indices) == 2
    assert all(len(i) == len(sims) for i in indices)
    assert len(candidates) == len(sims)
    assert not candidates or len(next(iter(candidates))) == 2

    # Make sure we return at most k
    for i in range(recs_per_dataset):
        assert sum(indices[0] == i for indices in candidates) <= k
        assert sum(indices[1] == i for indices in candidates) <= k

    for i, j in itertools.product(range(recs_per_dataset), repeat=2):
        sim = _hamming_sim_f(datasets[0,i], datasets[1,j])

        if sim >= threshold:
            if (i, j) not in candidates:
                assert (not k
                        or sim <= min(val for index, val in candidates.items()
                                     if index[0] == i)
                        or sim <= min(val for index, val in candidates.items()
                                     if index[1] == j))
            else:
                assert candidates[i, j] == sim
        else:
            assert (i, j) not in candidates
