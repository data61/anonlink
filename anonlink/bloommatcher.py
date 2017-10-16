from hashlib import sha1, md5
import hmac
from bitarray import bitarray
from anonlink._entitymatcher import ffi, lib

__author__ = 'Stephen Hardy, Brian Thorne'


def dicecoeff_pure_python(e1, e2):
    """
    Dice coefficient measures the similarity of two bit patterns.

    :param e1,e2: bitset arrays of same length
    :return: real 0-1 similarity measure
    """
    count1 = e1.count()
    count2 = e2.count()
    combined_count = count1 + count2
    overlap_count = (e1 & e2).count()
    if combined_count == 0:
        return 0.0
    else:
        return 2.0 * overlap_count / combined_count


def dicecoeff(e1, e2):
    """
    Dice coefficient measures the similarity of two bit patterns

    :return: real 0-1 similarity measure
    """
    e1array = ffi.new("char[]", e1.tobytes())
    e2array = ffi.new("char[]", e2.tobytes())

    if len(e1) == 1024 and len(e2) == 1024:
        return lib.dice_coeff_1024(e1array, e2array)
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
    if count == 0:
        return 0
    return 2*(e1 & e2).count()/count


def tanimoto(e1, e2):
    """
    Tanimoto coefficient measures the similarity of two bit patterns.

    Also referred to as the Jaccard similarity

    :return: real 0-1 similarity measure
    """
    return (e1 & e2).count() / float((e1 | e2).count())


def tanimoto_precount(e1, e2, count):
    """
    Tanimoto coefficient measures the similarity of two bit patterns

    :param e1: bitarray1
    :param e2: bitarray2
    :param count: float bitcount1 + bitcount2
    :return: real 0-1 similarity measure
    """
    a = (e1 & e2).count()
    return a / float(count - a)


