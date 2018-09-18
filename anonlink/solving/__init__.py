"""Solvers.
Solvers accept candidate pairs and return a concrete matching. In other
words, they accept a similarity for every candidate pair and turn it
into a boolean for every candidate pair.
"""

from anonlink.solving._multiparty_solving import greedy_solve
