from anonlink.solving import greedy_solve

def _zip_candidates(candidates):
    candidates = tuple(candidates)
    if not candidates:
        return ((), ()), ((), ()), ()
    records1, records2, sims = zip(*candidates)
    dataset_indices = []
    record_indices = []
    for (d1, r1), (d2, r2) in zip(records1, records2):
        dataset_indices.append((d1, d2))
        record_indices.append((r1, r2))
    return (tuple(zip(*dataset_indices)),
            tuple(zip(*record_indices)),
            sims)


def _compare_matching(result, truth):
    result = frozenset(map(frozenset, result.values()))
    truth = frozenset(map(frozenset, truth))
    assert result == truth


def test_greedy_twoparty():
    candidates = [((0, 0), (1, 0), .8)]
    result = greedy_solve(_zip_candidates(candidates), .5)
    _compare_matching(result, [{(0,0), (1,0)}])

    candidates = [((0, 0), (1, 0), .8),
                  ((0, 1), (1, 0), .7)]
    result = greedy_solve(_zip_candidates(candidates), .5)
    _compare_matching(result, [{(0,0), (1,0)}])
    result = greedy_solve(_zip_candidates(reversed(candidates)), .5)
    _compare_matching(result, [{(0,0), (1,0)}])
    
    candidates = []
    result = greedy_solve(_zip_candidates(candidates), .5)
    _compare_matching(result, [])
    
    candidates = [((0, 0), (1, 0), .8),
                  ((0, 0), (1, 1), .7),
                  ((0, 1), (1, 0), .7),
                  ((0, 1), (1, 1), .6)]
    result = greedy_solve(_zip_candidates(candidates), .5)
    _compare_matching(result, [{(0,0), (1,0)},
                               {(0,1), (1,1)}])
    result = greedy_solve(_zip_candidates(reversed(candidates)), .5)
    _compare_matching(result, [{(0,0), (1,0)},
                               {(0,1), (1,1)}])


def test_greedy_threeparty():
    candidates = [((0, 0), (1, 0), .7),
                  ((0, 0), (2, 0), .7),
                  ((1, 0), (2, 0), .9),
                  ((0, 0), (1, 1), .8),
                  ((0, 0), (2, 1), .8),
                  ((1, 1), (2, 1), .8)]
    result = greedy_solve(_zip_candidates(candidates), .5)
    _compare_matching(result, [{(0,0), (1,1), (2,1)},
                               {(1,0), (2,0)}])
    
    candidates = [((0, 0), (1, 0), .8),
                  ((0, 0), (2, 0), .7),
                  ((0, 1), (1, 1), .7),
                  ((0, 1), (2, 1), .8),
                  ((1, 1), (2, 1), .8)]
    result = greedy_solve(_zip_candidates(candidates), .5)
    _compare_matching(result, [{(0,0), (1,0)},
                               {(0,1), (1,1), (2,1)}])


def test_greedy_fourparty():
    candidates = [((0, 0), (1, 0), .9),
                  ((2, 0), (3, 0), .9),
                  ((0, 0), (2, 0), .7),
                  ((1, 0), (3, 0), .7),
                  ((0, 0), (3, 0), .7),
                  ((1, 0), (2, 0), .7)]
    result = greedy_solve(_zip_candidates(candidates), .5)
    _compare_matching(result, [{(0,0), (1,0), (2,0), (3,0)}])
