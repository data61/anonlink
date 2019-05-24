import collections
import datetime
import operator

import numpy as np

PIVOT_SAMPLES = 3
MIN_BRANCH = 200
assert PIVOT_SAMPLES % 2
assert PIVOT_SAMPLES <= MIN_BRANCH


np.random.seed(666)


def accept_provable_matches(
        similarities, start, end, matches_a, matches_b, matches,
        *,
        __a_counter=collections.Counter(),
        __b_counter=collections.Counter()):

    __a_counter.update(map(operator.itemgetter(1),
                           map(similarities.__getitem__, range(start, end))))
    __b_counter.update(map(operator.itemgetter(2),
                           map(similarities.__getitem__, range(start, end))))

    i = start
    for j in range(start, end):
        _, a, b = similarities[j]
        if __a_counter[a] == 1 and __b_counter[b] == 1:
            matches_a.add(a)
            matches_b.add(b)
            matches.append((a, b))
        else:
            similarities[i] = similarities[j]
            i += 1
    
    __a_counter.clear()
    __b_counter.clear()

    return i == end, i
    

def run_naive(similarities, start, end, matches_a, matches_b, matches):
    sims = similarities[start:end]
    sims.sort()
    added_match = False
    for _, a, b in sims:
        if a not in matches_a and b not in matches_b:
            matches_a.add(a)
            matches_b.add(b)
            matches.append((a, b))
            added_match = True
    return added_match


def eliminate_provable_nonmatches(
        similarities, start, end, matches_a, matches_b, matches):
    i = start
    for j in range(start, end):
        _, a, b = similarities[j]
        if a not in matches_a and b not in matches_b:
            similarities[i] = similarities[j]
            i += 1
    return i


def find_pivot_i(similarities, start, end):
    sample_is = start + np.random.choice(
        end - start, size=PIVOT_SAMPLES, replace=False)
    samples = [(similarities[i], i) for i in sample_is]
    samples.sort()
    _, pivot_i = samples[PIVOT_SAMPLES // 2]
    return pivot_i


def partition(similarities, start, end):
    pivot_i = find_pivot_i(similarities, start, end)
    pivot = similarities[pivot_i]
    similarities[pivot_i], similarities[end - 1] \
        = similarities[end - 1], similarities[pivot_i]
    
    i = start
    for j in range(start, end - 1):
        if similarities[j] < pivot:
            similarities[i], similarities[j] = similarities[j], similarities[i]
            i += 1
    similarities[i], similarities[end - 1] = similarities[end - 1], similarities[i]

    return i


def fast_solve_inner(similarities, start, end, matches_a, matches_b, matches, eliminate):
    assert 0 <= start < len(similarities)
    assert 0 <= end <= len(similarities)
    if start >= end:
        return False

    if end - start < MIN_BRANCH:
        return run_naive(
            similarities, start, end, matches_a, matches_b, matches)

    if eliminate:
        end = eliminate_provable_nonmatches(
            similarities, start, end, matches_a, matches_b, matches)

    accepted_provable = False
    # Disabled because it doesn't improve speed.
    # accepted_provable, end = accept_provable_matches(
    #     similarities, start, end, matches_a, matches_b, matches)

    if end - start < MIN_BRANCH:
        return run_naive(
            similarities, start, end, matches_a, matches_b, matches)

    pivot_i = partition(similarities, start, end)
    
    second_recurse_should_accept = fast_solve_inner(
        similarities, start, pivot_i, matches_a, matches_b, matches, False)

    _, a, b = similarities[pivot_i]
    if a not in matches_a and b not in matches_b:
        matches_a.add(a)
        matches_b.add(b)
        matches.append((a, b))
        second_recurse_should_accept = True

    second_recurse_accepted = fast_solve_inner(
        similarities, pivot_i + 1, end,
        matches_a, matches_b, matches,
        second_recurse_should_accept)

    # Return True if we or our callees accepted any pairs.
    return (accepted_provable
            or second_recurse_should_accept
            or second_recurse_accepted)


def fast_solve(similarities):
    matches = []
    fast_solve_inner(
        similarities.copy(), 0, len(similarities), set(), set(), matches, False)
    return matches


def slow_solve(similarities):
    similarities = similarities.copy()
    similarities.sort()

    matches_a = set()
    matches_b = set()
    matches = []
    for _, a, b in similarities:
        if a not in matches_a and b not in matches_b:
            matches_a.add(a)
            matches_b.add(b)
            matches.append((a, b))

    return matches


def generate_problem(
        N, M, sparsity):
    if sparsity < .5:
        num = np.random.binomial(N * M, sparsity)
        pairs = set()
        while len(pairs) < num:
            l = num - len(pairs)
            pairs.update(zip(map(int, np.random.randint(N, size=l)),
                             map(int, np.random.randint(M, size=l))))
        assert len(pairs) == num
        return [(sim, i, j)
                for sim, (i, j) in zip(map(float, np.random.rand(num)), pairs)]
    else:
        similarities = []
        for i in range(N):
            for j in range(M):
                if np.random.rand() <= sparsity:
                    similarities.append((float(np.random.rand()), i, j))
        np.random.shuffle(similarities)
        return similarities


N_SIZE = 20000
SPARSITY = .02

rsims = generate_problem(N_SIZE, N_SIZE, SPARSITY)

print('problem generated')

start_slow = datetime.datetime.now()
slow_soln = set(slow_solve(rsims))
duration_slow = datetime.datetime.now() - start_slow
print(f'slow: {duration_slow}s')

start_fast = datetime.datetime.now()
fast_soln = set(fast_solve(rsims))
duration_fast = datetime.datetime.now() - start_fast
print(f'fast: {duration_fast}s')

if slow_soln == fast_soln:
    print('solutions match')
else:
    raise RuntimeError("solutions don't match!")
