__author__ = 'shardy'


from hashlib import sha1
import hmac
from bitarray import bitarray

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
    for i in range(0, l):
        bf[i] = 0
    for m in mlist:
        sha1hm = int(hmac.new(keysha1, m, sha1).hexdigest(), 16) % l
        md5hm = int(hmac.new(keymd5, m).hexdigest(), 16) % l
        for i in range(0, k):
            gi = (sha1hm + i * md5hm) % l
            bf[gi] = 1
    return bf


def bigramlist(word):
    """
    Make bigrams from word with pre- and ap-pended spaces

    :param word: string to make bigrams from
    :return: list of bigrams as strings
    """
    word = " " + word + " "
    return [word[i:i+2] for i in range(0, len(word)-1)]

def unigramlist(instr, toremove='/'):
    """
    Make unigrams from a word, excluding string

    :param instr: input string
    :param toremove: string to remove before unigram construction
    :return: list of strings with unigrams
    """
    instr = instr.replace(toremove, "")
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


