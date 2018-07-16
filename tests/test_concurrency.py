import itertools

import pytest

from anonlink import concurrency

DATASET_SIZES = (0, 1, 100)
DATASET_NUMS = (0, 1, 2, 3)
DATASETS = tuple(itertools.chain.from_iterable(
    itertools.product(DATASET_SIZES, repeat=n) for n in DATASET_NUMS))
CHUNK_SIZE_AIMS = (1, 10, 100)



@pytest.mark.parametrize('datasets', DATASETS)
@pytest.mark.parametrize('chunk_size_aim', CHUNK_SIZE_AIMS)
def test_chunk_size(datasets, chunk_size_aim):
    # Guarantee: chunk_size_aim / 4 < chunk_size < chunk_size_aim * 4.
    # It may be possible to prove a better bound.
    chunks = concurrency.split_to_chunks(chunk_size_aim,
                                         dataset_sizes=datasets)
    for chunk in chunks:
        size = 1
        i0, i1 = chunk['datasetIndices']
        for a, b in chunk['ranges']:
            assert a <= b
            size *= b - a
        try:
            assert (chunk_size_aim / 4 < size
                    or 4 * chunk_size_aim > datasets[i0] * datasets[i1])
        except AssertionError:
            print(datasets[i0], datasets[i1], size, chunk_size_aim)
            raise
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
        i0, i1 = chunk['datasetIndices']
        r0, r1 = chunk['ranges']
        for j0, j1 in itertools.product(range(*r0), range(*r1)):
            # This will raise KeyError if we have duplicates
            all_comparisons.remove((i0, i1, j0, j1))
    # Make sure we've touched everything (so our set is empty)
    assert not all_comparisons
