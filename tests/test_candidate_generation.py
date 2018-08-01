from array import array

import pytest
from bitarray import bitarray as ba

from anonlink.candidate_generation import find_candidate_pairs


@pytest.mark.parametrize('k_', [2, None])
def test_no_blocking_three_datasets(k_):
    THRESHOLD = .6

    # These values don't actually matter...
    dataset0 = [ba('00'), ba('01'), ba('10'), ba('11')]
    dataset1 = [ba('00'), ba('01'), ba('11'), ba('')]
    dataset2 = [ba('11'), ba('01'), ba('00'), ba('10')]
    datasets = [dataset0, dataset1, dataset2]

    def similarity_f(datasets, threshold, k=None):
        assert threshold == THRESHOLD
        # All we need to check for k is that it's been passed correctly
        assert k == k_
        dset0, dset1 = datasets
        if dset0 == dataset0 and dset1 == dataset1:
            sims = [0.9432949307428928,
                    0.8568189930049877,
                    0.8419286042520673,
                    0.6343698774541688,
                    0.6]
            rec_is0 = [1, 2, 0, 3, 0]
            rec_is1 = [1, 0, 0, 3, 2]
        elif dset0 == dataset0 and dset1 == dataset2:
            sims = [0.9962946784347061,
                    0.900267827898046,
                    0.88468228054972,
                    0.6956392099710476]
            rec_is0 = [1, 0, 3, 2]
            rec_is1 = [2, 1, 2, 3]
        elif dset0 == dataset1 and dset1 == dataset2:
            sims = [0.88468228054972,
                    0.699430643486643,
                    0.6121560533778709,
                    0.6076471833512952]
            rec_is0 = [3, 3, 2, 0]
            rec_is1 = [2, 3, 2, 3]
        else:
            assert False, 'datasets not passed through as expected'
        return array('d', sims), (array('I', rec_is0), array('I', rec_is1))

    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = find_candidate_pairs(
        datasets, similarity_f, THRESHOLD, k=k_)

    assert list(sims) == [0.9962946784347061,
                          0.9432949307428928,
                          0.900267827898046,
                          0.88468228054972,
                          0.88468228054972,
                          0.8568189930049877,
                          0.8419286042520673,
                          0.699430643486643,
                          0.6956392099710476,
                          0.6343698774541688,
                          0.6121560533778709,
                          0.6076471833512952,
                          0.6]
    assert list(dset_is0) == [0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1, 1, 0]
    assert list(dset_is1) == [2, 1, 2, 2, 2, 1, 1, 2, 2, 1, 2, 2, 1]
    assert list(rec_is0) == [1, 1, 0, 3, 3, 2, 0, 3, 2, 3, 2, 0, 0]
    assert list(rec_is1) == [2, 1, 1, 2, 2, 0, 0, 3, 3, 3, 2, 3, 2]

@pytest.mark.parametrize('k_', [2, None])
def test_no_blocking_two_datasets(k_):
    THRESHOLD = .6

    # These values don't actually matter...
    dataset0 = [ba('00'), ba('01'), ba('10'), ba('11')]
    dataset1 = [ba('00'), ba('01'), ba('11'), ba('')]
    datasets = [dataset0, dataset1]

    def similarity_f(datasets, threshold, k=None):
        assert threshold == THRESHOLD
        # All we need to check for k is that it's been passed correctly
        assert k == k_
        dset0, dset1 = datasets
        if dset0 == dataset0 and dset1 == dataset1:
            sims = [0.9432949307428928,
                    0.8568189930049877,
                    0.8419286042520673,
                    0.6343698774541688,
                    0.6]
            rec_is0 = [1, 2, 0, 3, 0]
            rec_is1 = [1, 0, 0, 3, 2]
        else:
            assert False, 'datasets not passed through as expected'
        return array('d', sims), (array('I', rec_is0), array('I', rec_is1))

    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = find_candidate_pairs(
        datasets, similarity_f, THRESHOLD, k=k_)

    assert list(sims) == [0.9432949307428928,
                          0.8568189930049877,
                          0.8419286042520673,
                          0.6343698774541688,
                          0.6]
    assert list(dset_is0) == [0, 0, 0, 0, 0]
    assert list(dset_is1) == [1, 1, 1, 1, 1]
    assert list(rec_is0) == [1, 2, 0, 3, 0]
    assert list(rec_is1) == [1, 0, 0, 3, 2]


@pytest.mark.parametrize('datasets_n', [0, 1])
@pytest.mark.parametrize('k_', [2, None])
def test_no_blocking_too_few_datasets(datasets_n, k_):
    THRESHOLD = .6

    # These values don't actually matter...
    dataset0 = [ba('00'), ba('01'), ba('10'), ba('11')]
    datasets = [dataset0] if datasets_n else []

    def similarity_f(datasets, threshold, k=None):
        assert False, 'should not be called at all'

    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = find_candidate_pairs(
        datasets, similarity_f, THRESHOLD, k=k_)

    assert list(sims) == []
    assert list(dset_is0) == []
    assert list(dset_is1) == []
    assert list(rec_is0) == []
    assert list(rec_is1) == []


@pytest.mark.parametrize('datasets_n', [0, 1, 2, 3, 5])
@pytest.mark.parametrize('k_', [2, None])
def test_blocking(datasets_n, k_):
    THRESHOLD = .6

    # These values don't actually matter...
    datasets = [[ba('00'), ba('01'), ba('10'), ba('11')]
                for _ in range(datasets_n)]

    def similarity_f(datasets, threshold, k=None):
        assert False, 'should not be called at all'

    def blocking_f(dset_i, rec_i, hash_):
        return None

    with pytest.raises(NotImplementedError):
        find_candidate_pairs(
            datasets, similarity_f, THRESHOLD, k=k_, blocking_f=blocking_f)
