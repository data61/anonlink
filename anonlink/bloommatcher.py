from hashlib import sha1, md5
import hmac
from bitarray import bitarray

__author__ = 'shardy'


def hbloom(mlist, l=1024, k=30, keysha1="secret1", keymd5="secret2"):
    """
    Cryptographic bloom filter for list of strings

    :param mlist: list of strings to be hashed and encoded in filter
    :param l: length of filter
    :param k: number of hash functions to use per element
    :param keysha1: hmac secret key for sha1
    :param keymd5: hmac secret key for md5
    :return: bitarray with bloom filter
    """
    bf = bitarray(l)
    bf[:] = 0
    for m in mlist:
        sha1hm = int(hmac.new(keysha1.encode(), m.encode(), sha1).hexdigest(), 16) % l
        md5hm = int(hmac.new(keymd5.encode(), m.encode(), md5).hexdigest(), 16) % l
        for i in range(k):
            gi = (sha1hm + i * md5hm) % l
            bf[gi] = 1
    return bf


def bigramlist(word, toremove=None):
    """
    Make bigrams from word with pre- and ap-pended spaces

    s -> [' ' + s0, s0 + s1, s1 + s2, .. sN + ' ']

    :param word: string to make bigrams from
    :param toremove: List of strings to remove before construction
    :return: list of bigrams as strings
    """
    if toremove is not None:
        for substr in toremove:
            word = word.replace(substr, "")
    word = " " + word + " "
    return [word[i:i+2] for i in range(len(word)-1)]


def unigramlist(instr, toremove=None):
    """
    Make 1-grams (unigrams) from a word, possibly excluding particular substrings

    :param instr: input string
    :param toremove: Iterable of strings to remove
    :return: list of strings with unigrams
    """
    if toremove is not None:
        for substr in toremove:
            instr = instr.replace(substr, "")
    return list(instr)


def dicecoeff(e1, e2):
    """
    Dice coefficient measures the similarity of two bit patterns

    :return: real 0-1 similarity measure
    """
    return 2*(e1 & e2).count()/float(e1.count() + e2.count())


def dicecoeff_precount(e1, e2, count):
    """
    Dice coefficient measures the similarity of two bit patterns

    :param e1: bitarray1
    :param e2: bitarray2
    :param count: float bitcount1 + bitcount2
    :return: real 0-1 similarity measure
    """
    return 2*(e1 & e2).count()/count


def tanimoto(e1, e2):
    """
    Tanimoto coefficient measures the similarity of two bit patterns

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


