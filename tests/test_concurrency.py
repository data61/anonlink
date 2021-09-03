import array
import itertools
import random

import pytest

import anonlink.blocking
from anonlink import concurrency

DATASET_SIZES = (0, 1, 100)
DATASET_NUMS = (0, 1, 2, 3)
DATASETS = tuple(itertools.chain.from_iterable(
    itertools.product(DATASET_SIZES, repeat=n) for n in DATASET_NUMS))
CHUNK_SIZE_AIMS = (1, 10, 100)
SEED = 51


@pytest.mark.parametrize('datasets', DATASETS)
@pytest.mark.parametrize('chunk_size_aim', CHUNK_SIZE_AIMS)
def test_chunk_size(datasets, chunk_size_aim):
    # Guarantee: chunk_size_aim / 4 < chunk_size < chunk_size_aim * 4.
    # It may be possible to prove a better bound.
    chunks = concurrency.split_to_chunks(chunk_size_aim,
                                         dataset_sizes=datasets)
    for chunk in chunks:
        size = 1
        for source in chunk:
            a, b = source['range']
            assert a <= b
            size *= b - a
        i0 = chunk[0]['datasetIndex']
        i1 = chunk[1]['datasetIndex']
        assert (chunk_size_aim / 4 < size
                or 4 * chunk_size_aim > datasets[i0] * datasets[i1])
        assert size < chunk_size_aim * 4
                

@pytest.mark.parametrize('datasets', DATASETS)
@pytest.mark.parametrize('chunk_size_aim', CHUNK_SIZE_AIMS)
def test_comparison_coverage(datasets, chunk_size_aim):
    all_comparisons = set()
    for (i0, s0), (i1, s1) in itertools.combinations(enumerate(datasets), 2):
        for j0, j1 in itertools.product(range(s0), range(s1)):
            all_comparisons.add((i0, i1, j0, j1))
    chunks = concurrency.split_to_chunks(chunk_size_aim,
                                         dataset_sizes=datasets)
    for chunk in chunks:
        i0 = chunk[0]['datasetIndex']
        i1 = chunk[1]['datasetIndex']
        r0 = chunk[0]['range']
        r1 = chunk[1]['range']
        for j0, j1 in itertools.product(range(*r0), range(*r1)):
            # This will raise KeyError if we have duplicates
            all_comparisons.remove((i0, i1, j0, j1))
    # Make sure we've touched everything (so our set is empty)
    assert not all_comparisons


@pytest.mark.parametrize('dataset_size0', (1, 100))
@pytest.mark.parametrize('dataset_size1', (1, 100))
@pytest.mark.parametrize('k_', (None, 5))
@pytest.mark.parametrize('threshold_', (0.5, 0.9))
def test_process_chunk(dataset_size0, dataset_size1, k_, threshold_):
    rng = random.Random(SEED)
    offset0 = rng.randrange(1000)
    offset1 = rng.randrange(1000)

    results_num = dataset_size0 * dataset_size1 // 10
    if k_ is not None:
        results_num = min(k_, results_num)
    dset_i0 = 5
    dset_i1 = 9

    chunk = [{'datasetIndex': dset_i0,
              'range': [offset0, offset0 + dataset_size0]},
             {'datasetIndex': dset_i1,
              'range': [offset1, offset1 + dataset_size1]}]

    dataset0 = [rng.randrange(100) for _ in range(dataset_size0)]
    dataset1 = [rng.randrange(100) for _ in range(dataset_size1)]
    datasets_ = [dataset0, dataset1]

    sims = array.array('d', (rng.uniform(threshold_, 1)
                                 for _ in range(results_num)))
    rec_is0 = array.array('I')
    rec_is1 = array.array('I')
    for i0, i1 in rng.choices(list(itertools.product(range(dataset_size0),
                                                     range(dataset_size1))),
                              k=results_num):
        rec_is0.append(i0)
        rec_is1.append(i1)

    def similarity_f(datasets, threshold, k=None):
        assert k == k_
        assert threshold == threshold_
        
        # Copy so we can modify in-place and compare
        return sims, (array.array('I', rec_is0), array.array('I', rec_is1))

    sims_, (dset_is0_, dset_is1_), (rec_is0_, rec_is1_) \
        = concurrency.process_chunk(
            chunk,
            datasets_,
            similarity_f,
            threshold_,
            k=k_)

    assert sims == sims_
    assert len(rec_is0) == len(rec_is0_)
    assert all(rec_i0 + offset0 == rec_i0_
               for rec_i0, rec_i0_ in zip(rec_is0, rec_is0_))
    assert len(rec_is1) == len(rec_is1_)
    assert all(rec_i1 + offset1 == rec_i1_
               for rec_i1, rec_i1_ in zip(rec_is1, rec_is1_))
    assert list(dset_is0_) == [dset_i0] * results_num
    assert list(dset_is1_) == [dset_i1] * results_num


@pytest.mark.parametrize('threshold', (0.5, 0.9))
@pytest.mark.parametrize('k', (None, 5))
@pytest.mark.parametrize('number_datasets,dimension_chunk',
                         ((i, j)
                          for i in (0, 1, 2, 3, 5)
                          for j in (0, 1, 2, 3, 5)
                          if i != 2 or j != 2))
def test_process_chunk_nonmatching(
    threshold,
    k,
    number_datasets,
    dimension_chunk
):
    chunk = [{'datasetIndex': i, 'range': [5, 10]}
             for i in range(dimension_chunk)]
    datasets = [range(5) for _ in range(number_datasets)]

    def similarity_f(datasets, threshold, k=None):
        assert False, 'should not be called'

    expected_exception = (NotImplementedError
                          if number_datasets == dimension_chunk
                          else ValueError)
    with pytest.raises(expected_exception):
        concurrency.process_chunk(
            chunk, datasets, similarity_f, threshold, k=k)


@pytest.mark.parametrize('threshold', (0.5, 0.9))
@pytest.mark.parametrize('k', (None, 5))
@pytest.mark.parametrize('difference0,difference1',
                         ((i, j)
                          for i in (-5, -1, 0, 1, 5)
                          for j in (-5, -1, 0, 1, 5)
                          if i != 0 or j != 0))
def test_process_chunk_invalid_dataset_size(
    threshold,
    k,
    difference0,
    difference1
):
    chunk = [{'datasetIndex': 3, 'range': [20, 30]},
             {'datasetIndex': 5, 'range': [54, 64]}]
    dataset0 = range(10 + difference0)
    dataset1 = range(10 + difference1)
    datasets = [dataset0, dataset1]

    def similarity_f(datasets, threshold, k=None):
        assert False, 'should not be called'

    with pytest.raises(ValueError):
        concurrency.process_chunk(
            chunk, datasets, similarity_f, threshold, k=k)


def _powerset(iterable):
    # https://docs.python.org/3/library/itertools.html#itertools-recipes
    "_powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = tuple(iterable)
    return itertools.chain.from_iterable(
        itertools.combinations(s, r) for r in range(len(s)+1))


@pytest.mark.parametrize('threshold', (0.5, 0.9))
@pytest.mark.parametrize('k', (None, 5))
@pytest.mark.parametrize('missing',
                         ((i, j)
                          for i in _powerset(['range', 'datasetIndex'])
                          for j in _powerset(['range', 'datasetIndex'])
                          if i or j))
def test_process_chunk_invalid_chunk(
    threshold,
    k,
    missing
):
    chunk = [{'datasetIndex': 3, 'range': [20, 30]},
             {'datasetIndex': 5, 'range': [54, 64]}]
    for dataset_chunk, dataset_missing in zip(chunk, missing):
        for key in dataset_missing:
            del dataset_chunk[key]

    datasets = [range(10), range(10)]

    def similarity_f(datasets, threshold, k=None):
        assert False, 'should not be called'

    with pytest.raises(ValueError):
        concurrency.process_chunk(
            chunk, datasets, similarity_f, threshold, k=k)


@pytest.mark.parametrize('dataset_size0', (1, 100))
@pytest.mark.parametrize('dataset_size1', (1, 100))
@pytest.mark.parametrize('k_', (None, 5))
@pytest.mark.parametrize('threshold_', (0.5, 0.9))
def test_process_chunk_with_blocking(dataset_size0, dataset_size1, k_, threshold_):
    rng = random.Random(SEED)
    offset0 = rng.randrange(1000)
    offset1 = rng.randrange(1000)

    results_num = dataset_size0 * dataset_size1 // 10
    if k_ is not None:
        results_num = min(k_, results_num)
    dset_i0 = 5
    dset_i1 = 9

    chunk = [{'datasetIndex': dset_i0, 'range': [offset0, offset0 + dataset_size0]},
             {'datasetIndex': dset_i1, 'range': [offset1, offset1 + dataset_size1]}]

    dataset0 = [rng.randrange(500) for _ in range(dataset_size0)]
    dataset1 = [rng.randrange(500) for _ in range(dataset_size1)]
    datasets_ = [dataset0, dataset1]

    def similarity_f(datasets, threshold, k=None):
        results = []
        indicies_a = []
        indicies_b = []
        for i, record_a in enumerate(datasets[0]):
            for j, record_b in enumerate(datasets[1]):
                sim = abs(record_a - record_b)
                if sim > threshold:
                    results.append(sim)
                    indicies_a.append(i)
                    indicies_b.append(j)
        return (results, (indicies_a, indicies_b))

    blocking_f = anonlink.blocking.continuous_blocking(radius=10, source=[dataset0, dataset1])
    sims_with_blocking, _, _ = concurrency.process_chunk(
            chunk,
            datasets_,
            similarity_f,
            threshold_,
            k=k_,
            blocking_f=blocking_f
    )

    sims_without_blocking, _, _ = concurrency.process_chunk(
            chunk,
            datasets_,
            similarity_f,
            threshold_,
            k=k_,
            blocking_f=blocking_f
    )

    assert len(sims_with_blocking) <= len(sims_without_blocking)

