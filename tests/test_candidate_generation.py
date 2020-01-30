from itertools import combinations
from array import array

import pytest
from bitarray import bitarray as ba

from anonlink.candidate_generation import find_candidate_pairs


@pytest.mark.parametrize('k_', [0, 1, 2, None])
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
        dset0, dset1 = map(list, datasets)
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

    if k_ == 0:
        assert list(sims) == []
        assert list(dset_is0) == []
        assert list(dset_is1) == []
        assert list(rec_is0) == []
        assert list(rec_is1) == []
    elif k_ == 1:
        assert list(sims) == [0.9962946784347061,
                              0.9432949307428928,
                              0.900267827898046,
                              0.88468228054972,
                              0.8568189930049877,
                              0.6956392099710476,
                              0.6343698774541688]
        assert list(dset_is0) == [0, 0, 0, 1, 0, 0, 0]
        assert list(dset_is1) == [2, 1, 2, 2, 1, 2, 1]
        assert list(rec_is0)  == [1, 1, 0, 3, 2, 2, 3]
        assert list(rec_is1)  == [2, 1, 1, 2, 0, 3, 3]
    else:
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


@pytest.mark.parametrize('k_', [0, 1, 2, None])
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
        dset0, dset1 = map(list, datasets)
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

    if k_ == 0:
        assert list(sims) == []
        assert list(dset_is0) == []
        assert list(dset_is1) == []
        assert list(rec_is0) == []
        assert list(rec_is1) == []
    elif k_ == 1:
        assert list(sims) == [0.9432949307428928,
                              0.8568189930049877,
                              0.6343698774541688]
        assert list(dset_is0) == [0, 0, 0]
        assert list(dset_is1) == [1, 1, 1]
        assert list(rec_is0) == [1, 2, 3]
        assert list(rec_is1) == [1, 0, 3]
    else:
        assert list(sims) == [0.9432949307428928,
                              0.8568189930049877,
                              0.8419286042520673,
                              0.6343698774541688,
                              0.6]
        assert list(dset_is0) == [0, 0, 0, 0, 0]
        assert list(dset_is1) == [1, 1, 1, 1, 1]
        assert list(rec_is0) == [1, 2, 0, 3, 0]
        assert list(rec_is1) == [1, 0, 0, 3, 2]


def test_blocking_three_datasets():
    THRESHOLD = .6
    SIMV = .7

    # These values don't actually matter...
    dataset0 = [ba('00'), ba('01'), ba('10'), ba('11')]
    dataset1 = [ba('00'), ba('01'), ba('11'), ba('10')]
    dataset2 = [ba('11'), ba('01'), ba('00'), ba('10')]
    datasets = [dataset0, dataset1, dataset2]

    def similarity_f(datasets, threshold, k=None):
        items = [(SIMV, i, j)
                 for i in range(len(datasets[0]))
                 for j in range(len(datasets[1]))]

        return (array('d', (i[0] for i in items)),
                (array('I', (i[1] for i in items)),
                 array('I', (i[2] for i in items))))

    def blocking_f(dataset_index, record_index, hash_):
        assert datasets[dataset_index][record_index] == hash_
        # Records share a block if either their first bits match or
        # their second bits match.
        return enumerate(hash_)
    
    blocks = [[(i, j)
               for i, dset in enumerate(datasets)
               for j, rec in enumerate(dset)
               if rec[k] == v]
              for k in range(2)
              for v in [False, True]]

    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = find_candidate_pairs(
        datasets, similarity_f, THRESHOLD, blocking_f=blocking_f)

    assert (len(sims) == len(dset_is0) == len(rec_is0)
                      == len(dset_is1) == len(rec_is1))
    assert all(s == SIMV for s in sims)

    for i0, i1 in zip(zip(dset_is0, rec_is0), zip(dset_is1, rec_is1)):
        assert any(i0 in block and i1 in block for block in blocks)
    for block in blocks:
        for i0, i1 in combinations(block, 2):
            if i0[0] != i1[0]:
                assert (i0, i1) in zip(zip(dset_is0, rec_is0),
                                       zip(dset_is1, rec_is1))


@pytest.mark.parametrize('k_', [0, 1, 2, None])
def test_blocking_two_datasets(k_):
    THRESHOLD = .6

    # These values don't actually matter...
    dataset0 = [ba('00'), ba('01'), ba('10'), ba('11')]
    dataset1 = [ba('00'), ba('01'), ba('11'), ba('')]
    datasets = [dataset0, dataset1]

    def similarity_f(datasets, threshold, k=None):
        assert threshold == THRESHOLD
        # All we need to check for k is that it's been passed correctly
        assert k == k_
        dset0, dset1 = map(list, datasets)
        if (dset0 == list(map(dataset0.__getitem__, [0, 1])) 
                and dset1 == list(map(dataset1.__getitem__, [0, 1]))):
            # Block where first bits are 0
            sims = [0.9432949307428928, 0.8419286042520673]
            rec_is0 = [1, 0]
            rec_is1 = [1, 0]
        elif (dset0 == list(map(dataset0.__getitem__, [2, 3])) 
                and dset1 == list(map(dataset1.__getitem__, [2]))):
            # Block where first bits are 1
            sims = []
            rec_is0 = []
            rec_is1 = []
        elif (dset0 == list(map(dataset0.__getitem__, [0, 2])) 
                and dset1 == list(map(dataset1.__getitem__, [0]))):
            # Block where second bits are 0
            sims = [0.8568189930049877, 0.8419286042520673]
            rec_is0 = [1, 0]
            rec_is1 = [0, 0]
        elif (dset0 == list(map(dataset0.__getitem__, [1, 3])) 
                and dset1 == list(map(dataset1.__getitem__, [1, 2]))):
            # Block where second bits are 1
            sims = [0.9432949307428928]
            rec_is0 = [0]
            rec_is1 = [0]
        else:
            assert False, 'datasets not passed through as expected'
        return array('d', sims), (array('I', rec_is0), array('I', rec_is1))

    def blocking_f(dataset_index, record_index, hash_):
        assert datasets[dataset_index][record_index] == hash_
        if hash_:
            yield 0, hash_[0]
            yield 1, hash_[1]

    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = find_candidate_pairs(
        datasets, similarity_f, THRESHOLD, k=k_, blocking_f=blocking_f)

    if k_ == 0:
        assert list(sims) == []
        assert list(dset_is0) == []
        assert list(dset_is1) == []
        assert list(rec_is0) == []
        assert list(rec_is1) == []
    elif k_ == 1:
        assert list(sims) == [0.9432949307428928, 0.8568189930049877]
        assert list(dset_is0) == [0, 0]
        assert list(dset_is1) == [1, 1]
        assert list(rec_is0)  == [1, 2]
        assert list(rec_is1)  == [1, 0]
    else:
        assert list(sims) == [0.9432949307428928,
                              0.8568189930049877,
                              0.8419286042520673]
        assert list(dset_is0) == [0, 0, 0]
        assert list(dset_is1) == [1, 1, 1]
        assert list(rec_is0)  == [1, 2, 0]
        assert list(rec_is1)  == [1, 0, 0]


@pytest.mark.parametrize('datasets_n', [0, 1])
@pytest.mark.parametrize('k_', [2, None])
@pytest.mark.parametrize('blocking_f', [None, lambda i, j, h: None])
def test_no_blocking_too_few_datasets(datasets_n, k_, blocking_f):
    THRESHOLD = .6

    # These values don't actually matter...
    dataset0 = [ba('00'), ba('01'), ba('10'), ba('11')]
    datasets = [dataset0] if datasets_n else []

    def similarity_f(datasets, threshold, k=None, blocking_f=blocking_f):
        assert False, 'should not be called at all'

    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = find_candidate_pairs(
        datasets, similarity_f, THRESHOLD, k=k_)

    assert list(sims) == []
    assert list(dset_is0) == []
    assert list(dset_is1) == []
    assert list(rec_is0) == []
    assert list(rec_is1) == []
