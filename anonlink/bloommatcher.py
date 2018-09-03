import inspect
import warnings

from anonlink._entitymatcher import ffi, lib

__author__ = 'Stephen Hardy, Brian Thorne'


def _fname():
    return inspect.currentframe().f_back.f_back.f_code.co_name
def _deprecation(use_instead=None):
    msg = (f'anonlink.bloommatcher.{_fname()} has been deprecated ')
    if use_instead is not None:
        msg += f'(use anonlink.{use_instead} instead)'
    else:
        msg += 'without replacement'
    warnings.warn(msg, DeprecationWarning, stacklevel=2)


def dicecoeff_pure_python(e1, e2):
    """
    Dice coefficient measures the similarity of two bit patterns.

    Implemented exclusively in Python.

    :param e1: bitarray of same length as e2
    :param e2: bitarray of same length as e1
    :return: real 0-1 similarity measure
    """
    _deprecation('similarities.dice_coefficient_python')
    count1 = e1.count()
    count2 = e2.count()
    combined_count = count1 + count2
    overlap_count = (e1 & e2).count()
    if combined_count == 0:
        return 0.0
    else:
        return 2.0 * overlap_count / combined_count


def dicecoeff_native(e1, e2):
    """
    Dice coefficient measures the similarity of two bit patterns.

    Implemented via an external library.

    :param e1: bitarray of same length as e2
    :param e2: bitarray of same length as e1
    :return: real 0-1 similarity measure
    """
    _deprecation('similarities.dice_coefficient_accelerated')
    e1array = ffi.new("char[]", e1.tobytes())
    e2array = ffi.new("char[]", e2.tobytes())
    return lib.dice_coeff(e1array, e2array, len(e1array))


def dicecoeff(e1, e2):
    """
    Dice coefficient measures the similarity of two bit patterns

    :return: real 0-1 similarity measure
    """
    _deprecation('similarities.dice_coefficient')
    if e1.length() == e2.length() and (e1.length()/8) % 8 == 0:
        return dicecoeff_native(e1, e2)
    else:
        return dicecoeff_pure_python(e1, e2)


def dicecoeff_precount(e1, e2, count):
    """
    Dice coefficient measures the similarity of two bit patterns

    :param e1: bitarray1
    :param e2: bitarray2
    :param count: float bitcount1 + bitcount2
    :return: real 0-1 similarity measure
    """
    _deprecation()
    if count == 0:
        return 0
    return 2*(e1 & e2).count()/count


def tanimoto(e1, e2):
    """
    Tanimoto coefficient measures the similarity of two bit patterns.

    Also referred to as the Jaccard similarity

    :return: real 0-1 similarity measure
    """
    _deprecation()
    return (e1 & e2).count() / float((e1 | e2).count())


def tanimoto_precount(e1, e2, count):
    """
    Tanimoto coefficient measures the similarity of two bit patterns

    :param e1: bitarray1
    :param e2: bitarray2
    :param count: float bitcount1 + bitcount2
    :return: real 0-1 similarity measure
    """
    _deprecation()
    a = (e1 & e2).count()
    return a / float(count - a)
