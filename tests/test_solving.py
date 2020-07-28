import itertools
from array import array
from collections import Counter

import pytest
from hypothesis import given, strategies

from anonlink.solving import (
    greedy_solve, greedy_solve_python, greedy_solve_native, pairs_from_groups,
    probabilistic_greedy_solve, probabilistic_greedy_solve_native,
    probabilistic_greedy_solve_python)
from tests import UINT_MAX


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


@pytest.mark.parametrize("greedy_solve", [greedy_solve_native, greedy_solve_python])
def test_greedy_twoparty(greedy_solve):
    candidates = [(.8, ((0, 0), (1, 0)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0, 0), (1, 0)}])

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
    _compare_matching(result, [{(0, 0), (1, 0)},
                               {(0, 1), (1, 1)}])


@pytest.mark.parametrize("greedy_solve", [greedy_solve_native, greedy_solve_python])
def test_greedy_threeparty(greedy_solve):
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


@pytest.mark.parametrize("greedy_solve", [greedy_solve_native, greedy_solve_python])
def test_greedy_fourparty(greedy_solve):
    candidates = [(.9, ((0, 0), (1, 0))),
                  (.9, ((2, 0), (3, 0))),
                  (.7, ((0, 0), (2, 0))),
                  (.7, ((1, 0), (3, 0))),
                  (.7, ((0, 0), (3, 0))),
                  (.7, ((1, 0), (2, 0)))]
    result = greedy_solve(_zip_candidates(candidates))
    _compare_matching(result, [{(0,0), (1,0), (2,0), (3,0)}])


@pytest.mark.parametrize("greedy_solve", [greedy_solve_native, greedy_solve_python])
def test_inconsistent_dataset_number(greedy_solve):
    candidates = (
        array('d', [.5]),
        (array('I', [3]), array('I', [4])),
        (array('I', [2]), array('I', [6]), array('I', [7])))
    with pytest.raises(ValueError):
        greedy_solve(candidates)


@pytest.mark.parametrize("prob_greedy_solve", [probabilistic_greedy_solve_native, probabilistic_greedy_solve_python])
def test_wrong_merge_threshold(prob_greedy_solve):
    candidates = [(.8, ((0, 0), (1, 0)))]
    with pytest.raises(ValueError):
        prob_greedy_solve(_zip_candidates(candidates), merge_threshold=-0.1)
    with pytest.raises(ValueError):
        prob_greedy_solve(_zip_candidates(candidates), merge_threshold=1.01)


@pytest.mark.parametrize('datasets_n', [0, 1, 3, 5])
def test_unsupported_shape(datasets_n):
    candidates = (
        array('d', [.5]),
        tuple(array('I', [3]) for _ in range(datasets_n)),
        tuple(array('I', [2]) for _ in range(datasets_n)))
    with pytest.raises(NotImplementedError):
        greedy_solve(candidates)


@pytest.mark.parametrize("greedy_solve", [greedy_solve_native, greedy_solve_python])
def test_inconsistent_entry_number(greedy_solve):
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
    strategies.integers(min_value=0, max_value=UINT_MAX),
    strategies.integers(min_value=0, max_value=UINT_MAX))
index_pair_np = strategies.tuples(
        indices_np, indices_np
    ).filter(
        lambda x: x[0] != x[1]
    ).map(lambda x: tuple(sorted(x)))
candidate_pairs_np = strategies.dictionaries(
        index_pair_np,
        strategies.floats(min_value=0, max_value=1)
    ).map(dict_to_candidate_pairs)

index_pair_np_ndedup = strategies.tuples(
        indices_np, indices_np
    ).map(lambda x: tuple(sorted(x)))
candidate_pairs_np_ndedup = strategies.dictionaries(
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
                          strategies.integers(min_value=0, max_value=UINT_MAX))
indices1_2p = strategies.tuples(strategies.just(1),
                          strategies.integers(min_value=0, max_value=UINT_MAX))
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


@given(candidate_pairs_2p)
def test_python_native_match_2p(candidate_pairs):
    candidates = _zip_candidates(candidate_pairs)
    solution_python = greedy_solve_python(candidates)
    solution_native = greedy_solve_native(candidates)

    # We don't care about the order
    solution_python = frozenset(map(frozenset, solution_python))
    solution_native = frozenset(map(frozenset, solution_native))

    assert solution_python == solution_native


@given(candidate_pairs_np)
def test_python_native_match_np(candidate_pairs):
    candidates = _zip_candidates(candidate_pairs)
    solution_python = greedy_solve_python(candidates)
    solution_native = greedy_solve_native(candidates)

    # We don't care about the order
    solution_python = frozenset(map(frozenset, solution_python))
    solution_native = frozenset(map(frozenset, solution_native))

    assert solution_python == solution_native


def _all_indices_unique(groups):
    seen0 = set()
    seen1 = set()
    for group in groups:
        (dset_i0, rec_i0), (dset_i1, rec_i1) = group
        assert dset_i0 == 0
        assert dset_i1 == 1
        if rec_i0 in seen0 or rec_i1 in seen1:
            return False
        seen0.add(rec_i0)
        seen1.add(rec_i1)
    return True


groups_space_2p = strategies.lists(index_pair_2p).filter(_all_indices_unique)


def _groups_from_pairs(pairs):
    return [((0, i), (1, j)) for i, j in pairs]


@given(groups_space_2p)
def test_pairs_from_groups(groups):
    assert groups == _groups_from_pairs(pairs_from_groups(groups))


@given(candidate_pairs_2p,
       strategies.floats(min_value=0, max_value=1),
       strategies.booleans())
def test_probabilistic_python_native_match_2p(
    candidate_pairs,
    merge_threshold,
    deduplicated
):
    candidates = _zip_candidates(candidate_pairs)
    solution_python = probabilistic_greedy_solve_python(
        candidates, merge_threshold=merge_threshold, deduplicated=deduplicated)
    solution_native = probabilistic_greedy_solve_native(
        candidates, merge_threshold=merge_threshold, deduplicated=deduplicated)

    # We don't care about the order
    solution_python = frozenset(map(frozenset, solution_python))
    solution_native = frozenset(map(frozenset, solution_native))

    assert solution_python == solution_native


@given(candidate_pairs_np,
       strategies.floats(min_value=0, max_value=1),
       strategies.booleans())
def test_probabilistic_python_native_match_np(
    candidate_pairs,
    merge_threshold,
    deduplicated
):
    candidates = _zip_candidates(candidate_pairs)
    solution_python = probabilistic_greedy_solve_python(
        candidates, merge_threshold=merge_threshold, deduplicated=deduplicated)
    solution_native = probabilistic_greedy_solve_native(
        candidates, merge_threshold=merge_threshold, deduplicated=deduplicated)

    # We don't care about the order
    solution_python = frozenset(map(frozenset, solution_python))
    solution_native = frozenset(map(frozenset, solution_native))

    assert solution_python == solution_native


@given(candidate_pairs_np_ndedup,
       strategies.floats(min_value=0, max_value=1),
       strategies.booleans())
def test_probabilistic_python_native_match_np_ndedup(
    candidate_pairs,
    merge_threshold,
    deduplicated
):
    candidates = _zip_candidates(candidate_pairs)
    solution_python = probabilistic_greedy_solve_python(
        candidates, merge_threshold=merge_threshold, deduplicated=deduplicated)
    solution_native = probabilistic_greedy_solve_native(
        candidates, merge_threshold=merge_threshold, deduplicated=deduplicated)

    # We don't care about the order
    solution_python = frozenset(map(frozenset, solution_python))
    solution_native = frozenset(map(frozenset, solution_native))

    assert solution_python == solution_native


@given(candidate_pairs_np)
def test_probabilistic_nonprobabilistic_match(candidate_pairs):
    candidates = _zip_candidates(candidate_pairs)
    solution_probabilistic = probabilistic_greedy_solve(
        candidates, merge_threshold=1, deduplicated=False)
    solution_nonprobabilistic = greedy_solve(candidates)

    # We don't care about the order
    solution_probabilistic = frozenset(map(frozenset, solution_probabilistic))
    solution_nonprobabilistic = frozenset(map(frozenset,
                                              solution_nonprobabilistic))

    assert solution_probabilistic == solution_nonprobabilistic


@given(candidate_pairs_np_ndedup)
def test_probabilistic_nonprobabilistic_match_ndedup(candidate_pairs):
    candidates = _zip_candidates(candidate_pairs)
    solution_probabilistic = probabilistic_greedy_solve(
        candidates, merge_threshold=1, deduplicated=False)
    solution_nonprobabilistic = greedy_solve(candidates)

    # We don't care about the order
    solution_probabilistic = frozenset(map(frozenset, solution_probabilistic))
    solution_nonprobabilistic = frozenset(map(frozenset,
                                              solution_nonprobabilistic))

    assert solution_probabilistic == solution_nonprobabilistic


def test_probabilistic_greedy():
    candidates = [(.9, ((0, 0), (0, 1))),
                  (.8, ((1, 0), (1, 1))),
                  (.7, ((0, 0), (1, 0))),
                  (.6, ((0, 0), (1, 1))),
                  (.5, ((0, 1), (1, 0)))]
    
    result = probabilistic_greedy_solve(
        _zip_candidates(candidates), merge_threshold=0., deduplicated=True)
    _compare_matching(result, [{(0,0), (1,0)}])
    
    result = probabilistic_greedy_solve(
        _zip_candidates(candidates), merge_threshold=.75, deduplicated=True)
    _compare_matching(result, [{(0,0), (1,0)}])
    
    result = probabilistic_greedy_solve(
        _zip_candidates(candidates), merge_threshold=.76, deduplicated=True)
    _compare_matching(result, [{(0,0), (1,0)}])
    
    result = probabilistic_greedy_solve(
        _zip_candidates(candidates), merge_threshold=1., deduplicated=True)
    _compare_matching(result, [{(0,0), (1,0)}])
    
    result = probabilistic_greedy_solve(
        _zip_candidates(candidates), merge_threshold=0.0, deduplicated=False)
    _compare_matching(result, [{(0,0), (1,0), (0,1), (1,1)}])
    
    result = probabilistic_greedy_solve(
        _zip_candidates(candidates), merge_threshold=0.75, deduplicated=False)
    _compare_matching(result, [{(0,0), (1,0), (0,1), (1,1)}])
    
    result = probabilistic_greedy_solve(
        _zip_candidates(candidates), merge_threshold=0.76, deduplicated=False)
    _compare_matching(result, [{(0,0), (0,1)}, {(1,0), (1,1)}])
    
    result = probabilistic_greedy_solve(
        _zip_candidates(candidates), merge_threshold=1, deduplicated=False)
    _compare_matching(result, [{(0,0), (0,1)}, {(1,0), (1,1)}])
