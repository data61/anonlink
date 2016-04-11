"""
Module to produce a dataset of names, genders and dates of birth and manipulate that list

Currently very simple and not realistic. Additional functions for manipulating the list of names
- producing reordered and subset lists with a specific overlap

ClassList class - generate a list of length n of [id, name, dob, gender] lists

TODO: Get female / male names right by using a gendered database to first names
TODO: Get age distribution right by using a mortality table
TODO: Get first name distributions right by using distributions
TODO: Generate realistic errors
TODO: Add RESTfull api
"""


import os
import csv
import random
from datetime import datetime, timedelta
import math

__author__ = 'shardy'


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

    schema = ('INDEX', 'NAME freetext', 'DOB YYYY/MM/DD', 'GENDER M or F')

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
                random_date(self.earliest_birthday, self.latest_birthday).strftime("%Y/%m/%d"),
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

        self.all_first_names = loadCSV(os.path.join(dir_path, 'data', 'CSV_Database_of_First_Names.csv'))[1:]
        self.all_last_names = loadCSV(os.path.join(dir_path, 'data', 'CSV_Database_of_Last_Names.csv'))[1:]

    def generate_subsets(self, sz, overlap=0.8):
        """
        Generate a pair of subsets of the name list with a specified overlap

        :param sz: length of subsets to generate
        :param overlap: fraction of the subsets that should have the same names in them
        :return: 2-tuple of lists of subsets
        """
        nrec = len(self.names)
        overlap = int(math.floor(overlap * sz))
        notoverlap = sz - overlap
        rsamp = random.sample(range(nrec), sz + notoverlap)
        l1 = rsamp[:sz]
        l2 = rsamp[:overlap] + rsamp[sz:sz + notoverlap]
        random.shuffle(l1)
        random.shuffle(l2)
        return [self.names[i] for i in l1],  [self.names[i] for i in l2]

