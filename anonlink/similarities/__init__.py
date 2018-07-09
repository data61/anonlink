from anonlink.similarities.hamming import hamming_similarity
from anonlink.similarities.dice_python import dice_coefficient_python

try:
    from anonlink.similarities.dice_x86 import dice_coefficient_accelerated
except ImportError:
    # Alias that works even if the import fails, but always points to
    # the fastest implementation.
    dice_coefficient = dice_coefficient_python
else:
    dice_coefficient = dice_coefficient_accelerated
