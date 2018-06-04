from anonlink.candidate_generation import find_candidate_pairs


def _similarity_f(datasets, _, __):
    dataset0, dataset1 = datasets
    matches = []
    for i0, d0 in enumerate(dataset0):
        for i1, d1 in enumerate(dataset1):
            if d0 == d1:
                matches.append((i0, i1, 1.))
    dataset_i0, dataset_i1, sims = zip(*matches)
    return (dataset_i0, dataset_i1), sims


def test_no_blocking_no_k():
    dataset0 = [(True,), (False,)]
    dataset1 = [(False,), (True,)]
    dataset2 = [(True,), (False,)]
    datasets = [dataset0, dataset1, dataset2]

    (dataset_is0, dataset_is1), (record_is0, record_is1), sims \
        = find_candidate_pairs(datasets, _similarity_f, .5)

    candidates = set(
        zip(dataset_is0, dataset_is1, record_is0, record_is1, sims))
    assert candidates == {
        (0, 1, 0, 1, 1),
        (0, 1, 1, 0, 1),
        (0, 2, 0, 0, 1),
        (0, 2, 1, 1, 1),
        (1, 2, 1, 0, 1),
        (1, 2, 0, 1, 1)
    }


