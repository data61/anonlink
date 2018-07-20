from array import array

from anonlink.solving import greedy_solve

def _zip_candidates(candidates):
    candidates = tuple(candidates)
    sims = array('d')
    dset_is0 = array('I')
    dset_is1 = array('I')
    rec_is0 = array('I')
    rec_is1 = array('I')
    for sim, (dset_i0, rec_i0), (dset_i1, rec_i1) in candidates:
        sims.append(sim)
        dset_is0.append(dset_i0)
        dset_is1.append(dset_i1)
        rec_is0.append(rec_i0)
        rec_is1.append(rec_i1)
    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)


def _compare_matching(result, truth):
    result = set(map(frozenset, result))
    truth = set(map(frozenset, truth))
    assert result == truth


def test_greedy_twoparty():
    candidates = [(.8, (0, 0), (1, 0))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)}])

    candidates = [(.8, (0, 0), (1, 0)),
                  (.7, (0, 1), (1, 0))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)}])
    
    candidates = []
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [])
    
    candidates = [(.8, (0, 0), (1, 0)),
                  (.7, (0, 0), (1, 1)),
                  (.7, (0, 1), (1, 0)),
                  (.6, (0, 1), (1, 1))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)},
                               {(0,1), (1,1)}])


def test_greedy_threeparty():
    candidates = [(.9, (1, 0), (2, 0)),
                  (.8, (0, 0), (1, 1)),
                  (.8, (0, 0), (2, 1)),
                  (.8, (1, 1), (2, 1)),
                  (.7, (0, 0), (1, 0)),
                  (.7, (0, 0), (2, 0))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,1), (2,1)},
                               {(1,0), (2,0)}])
    
    candidates = [(.8, (0, 0), (1, 0)),
                  (.8, (0, 1), (2, 1)),
                  (.8, (1, 1), (2, 1)),
                  (.7, (0, 0), (2, 0)),
                  (.7, (0, 1), (1, 1))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)},
                               {(0,1), (1,1), (2,1)}])


def test_greedy_fourparty():
    candidates = [(.9, (0, 0), (1, 0)),
                  (.9, (2, 0), (3, 0)),
                  (.7, (0, 0), (2, 0)),
                  (.7, (1, 0), (3, 0)),
                  (.7, (0, 0), (3, 0)),
                  (.7, (1, 0), (2, 0))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0), (2,0), (3,0)}])
