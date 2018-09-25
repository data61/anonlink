import itertools
from array import array
from collections import Counter

import pytest
from hypothesis import given, strategies

from anonlink.solving import greedy_solve

def _zip_candidates(candidates):
    candidates = tuple(candidates)
    sims = array('d')
    dset_is0 = array('I')
    dset_is1 = array('I')
    rec_is0 = array('I')
    rec_is1 = array('I')
    for sim, ((dset_i0, rec_i0), (dset_i1, rec_i1)) in candidates:
        sims.append(sim)
        dset_is0.append(dset_i0)
        dset_is1.append(dset_i1)
        rec_is0.append(rec_i0)
        rec_is1.append(rec_i1)
    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)


def _compare_matching(result, truth):
    result_set = set(map(frozenset, result))
    assert len(result) == len(result_set)
    truth_set = set(map(frozenset, truth))
    assert len(truth) == len(truth_set)
    assert result_set == truth_set


def test_greedy_twoparty():
    candidates = [(.8, ((0, 0), (1, 0)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)}])

    candidates = [(.8, ((0, 0), (1, 0))),
                  (.7, ((0, 1), (1, 0)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)}])
    
    candidates = []
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [])
    
    candidates = [(.8, ((0, 0), (1, 0))),
                  (.7, ((0, 0), (1, 1))),
                  (.7, ((0, 1), (1, 0))),
                  (.6, ((0, 1), (1, 1)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)},
                               {(0,1), (1,1)}])


def test_greedy_threeparty():
    candidates = [(.9, ((1, 0), (2, 0))),
                  (.8, ((0, 0), (1, 1))),
                  (.8, ((0, 0), (2, 1))),
                  (.8, ((1, 1), (2, 1))),
                  (.7, ((0, 0), (1, 0))),
                  (.7, ((0, 0), (2, 0)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,1), (2,1)},
                               {(1,0), (2,0)}])
    
    candidates = [(.8, ((0, 0), (1, 0))),
                  (.8, ((0, 1), (2, 1))),
                  (.8, ((1, 1), (2, 1))),
                  (.7, ((0, 0), (2, 0))),
                  (.7, ((0, 1), (1, 1)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)},
                               {(0,1), (1,1), (2,1)}])
    
    candidates = [(1., ((0, 0), (1, 0))),
                  (1., ((0, 0), (2, 0))),
                  (1., ((2, 0), (2, 1)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0)}, {(2,0), (2,1)}])
    
    candidates = [(1., ((0, 0), (1, 0))),
                  (1., ((2, 0), (3, 0))),
                  (1., ((2, 0), (4, 0))),
                  (1., ((3, 0), (4, 0))),
                  (1., ((0, 0), (2, 0))),
                  (1., ((0, 0), (3, 0))),
                  (1., ((0, 0), (4, 0))),
                  (1., ((1, 0), (2, 0))),
                  (1., ((1, 0), (3, 0))),
                  (1., ((1, 0), (4, 0)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0), (2,0), (3,0), (4,0)}])


def test_greedy_fourparty():
    candidates = [(.9, ((0, 0), (1, 0))),
                  (.9, ((2, 0), (3, 0))),
                  (.7, ((0, 0), (2, 0))),
                  (.7, ((1, 0), (3, 0))),
                  (.7, ((0, 0), (3, 0))),
                  (.7, ((1, 0), (2, 0)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0), (2,0), (3,0)}])


def test_inconsistent_dataset_number():
    candidates = (
        array('d', [.5]),
        (array('I', [3]), array('I', [4])),
        (array('I', [2]), array('I', [6]), array('I', [7])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)


@pytest.mark.parametrize('datasets_n', [0, 1, 3, 5])
def test_unsupported_shape(datasets_n):
    candidates = (
        array('d', [.5]),
        tuple(array('I', [3]) for _ in range(datasets_n)),
        tuple(array('I', [2]) for _ in range(datasets_n)))
    with pytest.raises(NotImplementedError):
        greedy_solve(candidates)


def test_inconsistent_entry_number():
    candidates = (
        array('d', [.5, .3]),
        (array('I', [3]), array('I', [4])),
        (array('I', [2]), array('I', [6])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)
    
    candidates = (
        array('d', [.5]),
        (array('I', [3, 3]), array('I', [4])),
        (array('I', [2]), array('I', [6])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)
    
    candidates = (
        array('d', [.5]),
        (array('I', [3, 3]), array('I', [4, 6])),
        (array('I', [2]), array('I', [6])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)
    
    candidates = (
        array('d', [.5]),
        (array('I', [3]), array('I', [4, 6])),
        (array('I', [2]), array('I', [6])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)
    
    candidates = (
        array('d', [.5]),
        (array('I', [3]), array('I', [4])),
        (array('I', [2]), array('I', [6, 3])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)
    
    candidates = (
        array('d', [.5]),
        (array('I', [3]), array('I', [4])),
        (array('I', [2, 1]), array('I', [6, 3])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)
    
    candidates = (
        array('d', [.5]),
        (array('I', [3]), array('I', [4])),
        (array('I', [2, 1]), array('I', [6])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)


# === HYPOTHESIS TESTS ===

def dict_to_candidate_pairs(candidate_dict):
    candidates = map(tuple, map(reversed, candidate_dict.items()))
    return sorted(candidates, key=lambda x: (-x[0],) + x[1:])


indices_np = strategies.tuples(
    strategies.integers(min_value=0),
    strategies.integers(min_value=0))
index_pair_np = strategies.tuples(
        indices_np, indices_np
    ).filter(
        lambda x: x[0] != x[1]
    ).map(lambda x: tuple(sorted(x)))
candidate_pairs_np = strategies.dictionaries(
        index_pair_np,
        strategies.floats(min_value=0, max_value=1)
    ).map(dict_to_candidate_pairs)

@given(candidate_pairs_np)
def test_greedy_np(candidate_pairs):
    candidates = _zip_candidates(candidate_pairs)
    all_candidate_pairs = {x for _, x in candidate_pairs}
    all_records = set(itertools.chain.from_iterable(all_candidate_pairs))

    solution = list(greedy_solve(candidates))
    matched = Counter(itertools.chain.from_iterable(solution))
    # Every record is in at most one group
    assert all(matched[i] <= 1 and matched[j] <= 1
               for _, (i, j) in candidate_pairs)

    # Include singleton groups
    all_groups = list(solution)
    all_groups.extend([x] for x in all_records - matched.keys())
    # All groups that can be merged have been merged.
    for g1, g2 in itertools.combinations(all_groups, 2):
        assert any(tuple(sorted((r1, r2))) not in all_candidate_pairs
                   for r1 in g1 for r2 in g2)


indices0_2p = strategies.tuples(strategies.just(0),
                          strategies.integers(min_value=0))
indices1_2p = strategies.tuples(strategies.just(1),
                          strategies.integers(min_value=0))
index_pair_2p = strategies.tuples(indices0_2p, indices1_2p)
candidate_pairs_2p = strategies.dictionaries(
        index_pair_2p,
        strategies.floats(min_value=0, max_value=1)
    ).map(dict_to_candidate_pairs)

@given(candidate_pairs_2p)
def test_greedy_2p(candidate_pairs):
    candidates = _zip_candidates(candidate_pairs)
    solution = greedy_solve(candidates)
    assert all(len(group) <= 2 for group in solution)
    similarity_map = dict(map(reversed, candidate_pairs))
    matches = {records: similarity_map[records]
               for records in map(tuple, map(sorted, solution))}

    # Every record that could have a match does have a match
    matched = set(itertools.chain.from_iterable(solution))
    assert all(i in matched or j in matched for _, (i, j) in candidate_pairs)

    # Every pair is taken unless either of the candidates have a better match
    match_similarities = {i: sim for recs, sim in matches.items() for i in recs}
    for sim, (i, j) in candidate_pairs:
        assert ((i, j) in matches
                or match_similarities.get(i, float('-inf')) >= sim
                or match_similarities.get(j, float('-inf')) >= sim)
