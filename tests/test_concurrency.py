import array
import itertools
import random

import pytest

from anonlink import concurrency

DATASET_SIZES = (0, 1, 100)
DATASET_NUMS = (0, 1, 2, 3)
DATASETS = tuple(itertools.chain.from_iterable(
    itertools.product(DATASET_SIZES, repeat=n) for n in DATASET_NUMS))
CHUNK_SIZE_AIMS = (1, 10, 100)
SEED = 52


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
    rng = random.Random(51)
    offset0 = rng.randrange(1000)
    offset1 = rng.randrange(1000)

    results_num = dataset_size0 * dataset_size1 // 10

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

    def similarity_f(datasets, threshold, k):
        assert datasets == datasets_
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
