import array

import hypothesis
import pytest

import anonlink
from tests import UINT_MAX


def zip_candidates(candidates):
    candidates = tuple(candidates)
    sims = array.array('d')
    dset_is0 = array.array('I')
    dset_is1 = array.array('I')
    rec_is0 = array.array('I')
    rec_is1 = array.array('I')
    for sim, ((dset_i0, rec_i0), (dset_i1, rec_i1)) in candidates:
        sims.append(sim)
        dset_is0.append(dset_i0)
        dset_is1.append(dset_i1)
        rec_is0.append(rec_i0)
        rec_is1.append(rec_i1)
    return sims, (dset_is0, dset_is1), (rec_is0, rec_is1)


def apply_threshold(candidate_pairs, threshold):
    sims, (dset_is0, dset_is1), (rec_is0, rec_is1) = candidate_pairs
    try:
        i = next(i for i, s in enumerate(sims) if s < threshold)
    except StopIteration:
        return candidate_pairs
    return sims[:i], (dset_is0[:i], dset_is1[:i]), (rec_is0[:i], rec_is1[:i])


def dict_to_candidate_pairs(candidate_dict):
    candidates = map(tuple, map(reversed, candidate_dict.items()))
    return sorted(candidates, key=lambda x: (-x[0],) + x[1:])


indices0_2p = hypothesis.strategies.tuples(
    hypothesis.strategies.just(0),
    hypothesis.strategies.integers(min_value=0, max_value=UINT_MAX))
indices1_2p = hypothesis.strategies.tuples(
    hypothesis.strategies.just(1),
    hypothesis.strategies.integers(min_value=0, max_value=UINT_MAX))
index_pair_2p = hypothesis.strategies.tuples(indices0_2p, indices1_2p)
candidate_pairs_2p = hypothesis.strategies.dictionaries(
        index_pair_2p,
        hypothesis.strategies.floats(min_value=0, max_value=1)
    ).map(dict_to_candidate_pairs
    ).map(zip_candidates)


@hypothesis.given(candidate_pairs_2p,
                  hypothesis.strategies.integers(
                      min_value=1,
                      max_value=100,  # Linear in this
                      ))
def test_similarities_hist(candidate_pairs, bins):
    sims, _, _ = candidate_pairs
    counts, bin_edges = anonlink.stats.similarities_hist(
        candidate_pairs, bins=bins)

    assert sorted(bin_edges) == list(bin_edges)
    assert len(counts) == bins

    for count, bin_edge_left, bin_edge_right in zip(
            counts[:-1], bin_edges[:-2], bin_edges[1:-1]):
        assert count == sum(bin_edge_left <= s < bin_edge_right for s in sims)
    # The last one is special. The interval is closed.
    assert counts[-1] == sum(bin_edges[-2] <= s <= bin_edges[-1] for s in sims)


@hypothesis.given(candidate_pairs_2p,
                  hypothesis.strategies.integers(
                      min_value=1,
                      max_value=100,  # Linear in this
                      ))
def test_cumul_number_matches_vs_threshold(candidate_pairs, steps):
    counts, thresholds = anonlink.stats.cumul_number_matches_vs_threshold(
        candidate_pairs, steps=steps)
    
    assert len(counts) == len(thresholds) == steps + 1
    # if we have less pairs than steps, then the threshold bins are not necessarily unique. E.g: two pairs with
    # similarities 0.5000000000000003, 0.5000000000000001, and steps=3, we end up with the thresholds
    # [0.5000000000000001, 0.5000000000000002, 0.5000000000000001, 0.5000000000000003]
    if len(candidate_pairs[0]) >= steps:
        assert len(set(thresholds)) == len(thresholds)
    assert sorted(thresholds) == list(thresholds)

    for count, threshold in zip(counts, thresholds):
        candidate_pairs_thresh = apply_threshold(candidate_pairs, threshold)
        solution = anonlink.solving.greedy_solve(candidate_pairs_thresh)
        assert count == len(solution)


@hypothesis.given(candidate_pairs_2p,
                  hypothesis.strategies.integers(
                      min_value=1,
                      max_value=100,  # Linear in this
                      ))
#@hypothesis.example(((0.5325659332756726, ((0, 97), (1, 628))), (0.08830395403829218, ((0, 5052346094), (1, 340))), (0.023114404426094696, ((0, 34975), (1, 725)))), 3
#)
def test_matches_nonmatches_hist(candidate_pairs, bins):
    hist = anonlink.stats.matches_nonmatches_hist(
        candidate_pairs, bins=bins)
    matches_nums, nonmatches_nums, bin_boundaries = hist
    
    assert len(matches_nums) == len(nonmatches_nums) == bins
    assert len(bin_boundaries) == bins + 1
    assert len(set(bin_boundaries)) == len(bin_boundaries)
    assert sorted(bin_boundaries) == list(bin_boundaries)

    for matches_num, nonmatches_num, bin_boundary_left, bin_boundary_right \
            in zip(matches_nums[:-1], nonmatches_nums[:-1],
                   bin_boundaries[:-2], bin_boundaries[1:-1]):
        candidate_pairs_left = apply_threshold(candidate_pairs,
                                               bin_boundary_left)
        candidate_pairs_right = apply_threshold(candidate_pairs,
                                                bin_boundary_right)
        all_num_true = (len(candidate_pairs_left[0])
                        - len(candidate_pairs_right[0]))
        matches_num_true = (
            len(anonlink.solving.greedy_solve(candidate_pairs_left))
            - len(anonlink.solving.greedy_solve(candidate_pairs_right)))
        nonmatches_num_true = all_num_true - matches_num_true
        assert matches_num == matches_num_true
        assert nonmatches_num == nonmatches_num_true

    # The last one is special. The interval is closed.
    matches_num = matches_nums[-1]
    nonmatches_num = nonmatches_nums[-1]
    bin_boundary_left = bin_boundaries[-2]
    candidate_pairs_left = apply_threshold(candidate_pairs,
                                           bin_boundary_left)
    all_num_true = len(candidate_pairs_left[0])
    matches_left = len(anonlink.solving.greedy_solve(candidate_pairs_left))
    matches_num_true = matches_left
    nonmatches_num_true = all_num_true - matches_num_true
    assert matches_num == matches_num_true
    assert nonmatches_num == nonmatches_num_true


@hypothesis.given(candidate_pairs_2p,
                  hypothesis.strategies.integers(min_value=1))
def test_nonmatch_index_score(candidate_pairs, n):
    matches = set(anonlink.solving.pairs_from_groups(
        anonlink.solving.greedy_solve(candidate_pairs)))

    m = 0
    _, _, rec_is = candidate_pairs
    for i, pair in enumerate(zip(*rec_is)):
        m += pair not in matches
        if n == m:
            assert i == anonlink.stats.nonmatch_index_score(candidate_pairs, n)
            break
    else:
        with pytest.raises(ValueError):
            anonlink.stats.nonmatch_index_score(candidate_pairs, n)


def test_nonmatch_index_score_exhaustive():
    candidate_pairs = (array.array('f', [0.9, 0.8, 0.7, 0.6, 0.5]),
                       (array.array('I', [0, 0, 0, 0, 0]), array.array('I', [1, 1, 1, 1, 1])),
                       (array.array('I', [0, 0, 1, 1, 2]),
                       array.array('I', [1, 0, 1, 2, 2])))
    for num_nonmatch, pos in zip((1, 2, 3), (1, 2, 4)):
        assert pos == anonlink.stats.nonmatch_index_score(candidate_pairs, num_nonmatch)
    with pytest.raises(ValueError):
        anonlink.stats.nonmatch_index_score(candidate_pairs, 4)
    candidate_pairs = (array.array('f', [0.8]),
                      (array.array('I', [0]), array.array('I', [1]), array.array('I', [2])),
                      (array.array('I', [0]), array.array('I', [0]), array.array('I', [0])))
    with pytest.raises(ValueError):
        anonlink.stats.nonmatch_index_score(candidate_pairs, 1)
