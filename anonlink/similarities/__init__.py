"""Similarity functions.

These functions take datasets of records and compute the records'
similarities. A threshold must be passed: only record pairs with
similarity of at least this threshold are returned. We call these the
candidate pairs.

Currently, the Dice Coefficient and the Simple Matching Coefficient are
implemented. These work on binary strings. However, other similarity
functions are possible as well.
"""

from anonlink.similarities._dice_python import dice_coefficient_python
from anonlink.similarities._smc import (hamming_similarity,
                                        simple_matching_coefficient)

try:
    from anonlink.similarities._dice_x86 import dice_coefficient_accelerated
except ImportError:
    # Alias that works even if the import fails, but always points to
    # the fastest implementation.
    dice_coefficient = dice_coefficient_python
else:
    dice_coefficient = dice_coefficient_accelerated
