import itertools
import typing as _typing

import numpy as _np

import anonlink.typechecking as _typechecking


def _similarities_as_nparray(candidate_pairs: _typechecking.CandidatePairs):
    sims, _, _ = candidate_pairs
    return _np.frombuffer(sims, dtype=sims.typecode)


def _check_bipartite(candidate_pairs: _typechecking.CandidatePairs) -> bool:
    _, (dset_is0, dset_is1), _ = candidate_pairs
    np_dset_is0 = _np.frombuffer(dset_is0, dtype=dset_is0.typecode)
    np_dset_is1 = _np.frombuffer(dset_is1, dtype=dset_is1.typecode)
    return (np_dset_is0 == 0).all() and (np_dset_is1 == 1).all()


def similarities_hist(candidate_pairs: _typechecking.CandidatePairs,
                      bins: int = 100):
    """Compute a histogram of the similarity scores in candidate pairs.

    This function is experimental and subject to change without warning.

    :param candidate_pairs: The candidate pairs.
    :param bins: An integer determining the number of bins to use.
        Default 100.

    :return: 2-tuple of (1) values of the histogram as an array length
        bins, and (2) the edges of the bins as an array length bins + 1.
    """
    return _np.histogram(_similarities_as_nparray(candidate_pairs),
                         bins=bins)


def _semiopen_hist_matches_nonmatches(
    candidate_pairs: _typechecking.CandidatePairs,
    steps: int = 100
):
    # Run the 2-party greedy solver.
    if not _check_bipartite(candidate_pairs):
        raise ValueError('only 2-party matching is supported')

    thresholds = _np.histogram_bin_edges(
        _similarities_as_nparray(candidate_pairs), bins=steps)
    thresholds_enumerate_iter = zip(
        range(thresholds.shape[0] - 1, -1, -1), thresholds[::-1])

    sims, _, (rec_is0, rec_is1) = candidate_pairs
    matched0: _typing.Set[int] = set()
    matched1: _typing.Set[int] = set()
    num_matches = _np.zeros_like(thresholds, dtype=int)
    num_nonmatches = _np.zeros_like(thresholds, dtype=int)
    try:
        i, threshold = next(thresholds_enumerate_iter)
    except StopIteration:
        return num_matches, num_nonmatches, thresholds
    for sim, rec_i0, rec_i1 in zip(sims, rec_is0, rec_is1):
        while sim < threshold:
            try:
                i, threshold = next(thresholds_enumerate_iter)
            except StopIteration:
                return num_matches, num_nonmatches, thresholds
        if rec_i0 not in matched0 and rec_i1 not in matched1:
            matched0.add(rec_i0)
            matched1.add(rec_i1)
            num_matches[i] += 1
        else:
            num_nonmatches[i] += 1
    return num_matches, num_nonmatches, thresholds


def matches_nonmatches_hist(
    candidate_pairs: _typechecking.CandidatePairs,
    bins: int = 100
):
    """Compute a histogram of possible matches and definite nonmatches.

    This function is experimental and subject to change without warning.

    We use the greedy solver to split the candidate pairs into possible
    matches and definite nonmatches. A possible match may or may not be
    accepted as a pair depending on the threshold chosen. A definite
    nonmatch will never be accepted, since one record in this pair has
    a more promising match with another record. We then make a histogram
    of possible matches and definite nonmatches.

    :param candidate_pairs: The candidate pairs.
    :param bins: An integer determining the number of bins to use.
        Default 100.

    :return: 3-tuple of (1) values of the histogram of the matches as an
        array of length bins, (2) values of the histogram of the
        nonmatches as an array of length bins, and (3) the edges of the
        bins as an array length bins + 1.
    """
    semiopen_hist = _semiopen_hist_matches_nonmatches(candidate_pairs, bins)
    num_matches, num_nonmatches, thresholds = semiopen_hist
    # Merge last and second last bins for consistency with np.histogram
    num_matches[-2] += num_matches[-1]
    num_matches = _np.array(num_matches[:-1])
    num_nonmatches[-2] += num_nonmatches[-1]
    num_nonmatches = _np.array(num_nonmatches[:-1])
    return num_matches, num_nonmatches, thresholds


def cumul_number_matches_vs_threshold(
    candidate_pairs: _typechecking.CandidatePairs,
    steps: int = 100
):
    """Compute the number of matches for each threshold.

    This function is experimental and subject to change without warning.

    We use the 2-party greedy solver to calculate the number of matches
    that would be returned if the candidate_pairs were found using a
    particular threshold. This function requires only a single pass of
    the data, so it is faster than simply running the greedy solver
    multiple times.

    :param candidate_pairs: The candidate pairs.
    :param steps: An integer determining the number of threshold steps
        to use. Default 100.

    :return: 2-tuple of (1) the number of matches for the threshold as
        an array length steps + 1, and (2) the thresholds as an array
        length steps + 1.
    """
    num_matches, _, thresholds = _semiopen_hist_matches_nonmatches(
        candidate_pairs, steps)
    num_matches_rev = num_matches[::-1]
    _np.cumsum(num_matches_rev, out=num_matches_rev)
    return num_matches, thresholds


def nonmatch_index_score(
    candidate_pairs: _typechecking.CandidatePairs,
    n: int = 1
) -> int:
    """Find the index of the ``n``th definite nonmatch.

    We use the 2-party greedy solver to split the candidate pairs into
    possible matches and definite nonmatches. The index (in decreasing
    order of similarity) of the ``n``th definite nonmatch is returned.

    Smaller values of ``n`` introduce more noise to the heuristic, but
    larger values of ``n`` provide less information.

    Raises ValueError if there are fewer than n definite nonmatches.

    :param candidate pairs: The candidate pairs. Must represent a
        bipartite problem.
    :param n: We return the index of the ``n``th definite nonmatch.
        Default 1.

    :return: The index of the ``n``th definite nonmatch if there are at
        least ``n`` definite nonmatches in the candidate pairs.
    """
    if not _check_bipartite(candidate_pairs):
        raise ValueError('only 2-party matching is supported')
    _, _, (rec_is0, rec_is1) = candidate_pairs

    matched0: _typing.Set[int] = set()
    matched1: _typing.Set[int] = set()
    nonmatches = 0
    for i, rec_i0, rec_i1 in zip(itertools.count(), rec_is0, rec_is1):
        if rec_i0 not in matched0 and rec_i1 not in matched1:
            matched0.add(rec_i0)
            matched1.add(rec_i1)
        else:
            nonmatches += 1
            if nonmatches == n:
                return i
    # Fewer than n definite nonmatches.
    raise ValueError('fewer than n definite nonmatches')
