"""Solvers.

Solvers accept candidate pairs and return a concrete matching. In other
words, they accept a similarity for every candidate pair and turn it
into a boolean for every candidate pair.
"""

import typing as _typing

import anonlink.typechecking as _typechecking

from anonlink.solving._multiparty_solving_python import (
    greedy_solve_python, probabilistic_greedy_solve_python)
try:
    from anonlink.solving._multiparty_solving import (
        greedy_solve_native, probabilistic_greedy_solve_native)
except ImportError:
    greedy_solve = greedy_solve_python
    probabilistic_greedy_solve = probabilistic_greedy_solve_python
else:
    greedy_solve = greedy_solve_native
    probabilistic_greedy_solve = probabilistic_greedy_solve_native


def pairs_from_groups(
    groups: _typechecking.MatchGroups
) -> _typing.Iterable[_typing.Tuple[int, int]]:
    """Make an iterable of pairs (i, j) from an iterable of groups.

    The set of pairs representation is often more convenient for
    bipartite matching problems.

    To make a mapping, use ``dict(pairs_from_groups(groups))``.

    :param groups: An iterable of groups.
    :return: An iterable of pairs (i, j), where i is the record index in
        the first dataset, and j is the record index in the second
        dataset.
    """
    group: _typing.List[_typing.Tuple[int, int]]
    for group in map(sorted, groups):  # type: ignore
        if len(group) == 2:
            (dset_i0, rec_i0), (dset_i1, rec_i1) = group
            if dset_i0 == 0 and dset_i1 == 1:
                yield rec_i0, rec_i1
                continue
        raise ValueError('non-bipartite problems are unsupported')
