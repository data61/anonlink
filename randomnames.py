"""
Module to produce a dataset of names, genders and dates of birth and manipulate that list

Currently very simple and not realistic. Additional functions for manipulating the list of names
- producing reordered and subset lists with a specific overlap

ClassList class - generate a list of length n of [id, name, dob, gender] lists

TODO: Get female / male names right by using a gendered database to first names
TODO: Get age distribution right by using a mortality table
TODO: Get first name distributions right by using distributions
TODO: Add RESTfull api
"""

__author__ = 'shardy'

import numpy as np

import bloommatcher as bm

import platform
import os
import csv
import random
from datetime import datetime, timedelta
from timeit import default_timer as timer
import sys as sys
from ctypes import cdll, c_double, byref


library_name = "dice_one_against_many"
libpath = os.path.abspath(os.path.join(os.path.dirname(__file__), library_name))

if platform.system() == "Darwin":
    c_dice = cdll.LoadLibrary(libpath + '.dll')
else:
    c_dice = cdll.LoadLibrary(libpath + '.so')

match_one_against_many_dice_c = c_dice.match_one_against_many_dice_c
match_one_against_many_dice_1024_c = c_dice.match_one_against_many_dice_1024_c


def loadCSV(fname):
    """
    Loads a specified csv file and returns as a list
    """
    res = []
    with open(fname, 'rU') as f:
        reader = csv.reader(f)
        for row in reader:
            res.append(row[0])
    return res


def random_date(start, end):
    """
    This function will return a random datetime between two datetime objects.

    :param start: datetime of start
    :param end: datetime of end
    :return: random datetime between start and end
    """
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    random_second = random.randrange(int_delta)
    return start + timedelta(seconds=random_second)


class NameList:
    """List of randomly generated names"""

    def __init__(self, n):
        self.load_names()

        self.earliest_birthday = datetime(year=1916, month=1, day=1)
        self.latest_birthday = datetime(year=2016, month=1, day=1)

        self.names = [person for person in self.generate_random_person(n)]

    def generate_random_person(self, n):
        """
        Generator that yields details on a person with plausible name, sex and age.

        :yields: Generated data for one person
            tuple - (id: int, name: str('First Last'), birthdate: str('DD/MM/YYYY'), sex: str('M' | 'F') )
        """
        for i in range(n):
            yield (
                i,
                random.choice(self.all_first_names) + ' ' + random.choice(self.all_last_names),
                random_date(self.earliest_birthday, self.latest_birthday).strftime("%d/%m/%Y"),
                'M' if random.random() > 0.5 else 'F'
            )

    def load_names(self):
        """
        This function loads a name database into globals firstNames and lastNames

        initial version uses data files from
        http://www.quietaffiliate.com/free-first-name-and-last-name-databases-csv-and-sql/

        """
        path = os.path.abspath(__file__)
        dir_path = os.path.dirname(path)

        self.all_first_names = loadCSV(os.path.join(dir_path, 'CSV_Database_of_First_Names.csv'))[1:]
        self.all_last_names = loadCSV(os.path.join(dir_path, 'CSV_Database_of_Last_Names.csv'))[1:]

    def generate_subsets(self, sz, overlap=0.8):
        """
        Generate a pair of subsets of the name list with a specified overlap

        :param sz: length of subsets to generate
        :param overlap: fraction of the subsets that should have the same names in them
        :return: 2-tuple of lists of subsets
        """
        nrec = len(self.names)
        overlap = int(np.floor(overlap * sz))
        notoverlap = sz - overlap
        rsamp = random.sample(range(nrec), sz + notoverlap)
        l1 = rsamp[:sz]
        l2 = rsamp[:overlap] + rsamp[sz:sz + notoverlap]
        random.shuffle(l1)
        random.shuffle(l2)
        return [self.names[i] for i in l1],  [self.names[i] for i in l2]


def cryptoBloomFilter(rec, key1="test1", key2="test2"):
    """
    Make a bloom filer from a record.

    Using the method from
    http://www.record-linkage.de/-download=wp-grlc-2011-02.pdf

    :param rec: record of index, name, dob, gender (M/F)
    :param key1: key for first hash function
    :param key2: key for second hash function
    :return: 2-tuple - bitarray with bloom filter for record, index of record
    """
    bf = bm.hbloom(
                    bm.bigramlist(rec[1]) +
                    bm.unigramlist(rec[2], toremove='/') +
                    bm.unigramlist(rec[3]), keysha1=key1, keymd5=key2
                )

    return bf, rec[0], bf.count()


def compare_python_c(ntotal=8000, nsubset=4000, frac=0.8):
    """Compare results and running time of python and C++ versions.

    :param ntotal: Total number of data points to generate
    :param nsubset: Number of points for each database
    :param frac: Fraction of overlap between subsets

    :raises: AssertionError if the results differ
    :return: dict with 'c' and 'python' keys with values of the total time taken
             for each implementation
    """

    nml = NameList(ntotal)
    sl1, sl2 = nml.generate_subsets(nsubset, frac)
    filters1 = [cryptoBloomFilter(s, key1="test1", key2="test2") for s in sl1]
    filters2 = [cryptoBloomFilter(s, key1="test1", key2="test2") for s in sl2]

    # Pure Python version
    start = timer()

    result = []
    for i, f1 in enumerate(filters1):
        coeffs = map(lambda x:  bm.dicecoeff_precount(f1[0], x[0], float(f1[2] + x[2])), filters2)
        best = np.argmax(coeffs)
        result.append((i, coeffs[best], f1[1], filters2[best][1], best))

    end = timer()

    python_time = end - start

    # C++ Version
    sys.stdout.flush()
    sys.stderr.flush()

    carr1 = ""
    carr1 = carr1.join([f[0].tobytes() for f in filters1])
    clist1 = [f[0].tobytes() for f in filters1]
    carr2 = ""
    carr2 = carr2.join([f[0].tobytes() for f in filters2])

    start = timer()

    result2 = []
    for i, f1 in enumerate(filters1):
        coeff = c_double()
        ind = match_one_against_many_dice_1024_c(clist1[i], carr2, nsubset, byref(coeff))
        result2.append((i, coeff.value, f1[1], filters2[ind][1], ind))

    end = timer()

    c_time = end - start

    assert result == result2, "Results are different"

    # Results are the same
    return {
        "c": c_time,
        "python": python_time
    }


if __name__ == '__main__':
    results = compare_python_c()
    print "{python:8.3f}\n{sep}\n{c:8.3f}".format(sep="="*8, **results)





