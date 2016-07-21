"""
Module to produce a dataset of names, genders and dates of birth and manipulate that list

Currently very simple and not realistic. Additional functions for manipulating the list of names
- producing reordered and subset lists with a specific overlap

ClassList class - generate a list of length n of [id, name, dob, gender] lists

TODO: Get age distribution right by using a mortality table
TODO: Get first name distributions right by using distributions
TODO: Generate realistic errors
TODO: Add RESTfull api to generate reasonable name data as requested
"""

import csv
import random
from datetime import datetime, timedelta
import math

import pkgutil


def load_csv_data(resource_name):
    """Loads a specified data file as csv and returns the first column as a Python list
    """
    data = pkgutil.get_data('anonlink', 'data/{}'.format(resource_name)).decode('utf8')
    reader = csv.reader(data.splitlines())
    next(reader, None)  # skip the headers
    return list({row[0] for row in reader})


def save_csv(data, schema, file):
    """
    Output generated data as csv with header.

    :param data: An iterable of tuples containing raw data.
    :param schema: Tuple of column names as defined in anonlink.identifier_types
    :param file: A writeable stream in which to write the csv
    """

    print(','.join(schema), file=file)
    writer = csv.writer(file)
    writer.writerows(data)


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
            sex = 'M' if random.random() > 0.5 else 'F'
            dob = random_date(self.earliest_birthday, self.latest_birthday).strftime("%Y/%m/%d")
            first_name = random.choice(self.all_male_first_names) if sex == 'M' else random.choice(self.all_female_first_names)
            last_name = random.choice(self.all_last_names)

            yield (
                i,
                first_name + ' ' + last_name,
                dob,
                sex
            )

    def load_names(self):
        """
        This function loads a name database into globals firstNames and lastNames

        initial version uses data files from
        http://www.quietaffiliate.com/free-first-name-and-last-name-databases-csv-and-sql/

        """

        self.all_male_first_names = load_csv_data('male-first-names.csv')
        self.all_female_first_names = load_csv_data('female-first-names.csv')
        self.all_last_names = load_csv_data('CSV_Database_of_Last_Names.csv')

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
        rsamp = random.sample(list(range(nrec)), sz + notoverlap)
        l1 = rsamp[:sz]
        l2 = rsamp[:overlap] + rsamp[sz:sz + notoverlap]
        random.shuffle(l1)
        random.shuffle(l2)
        return [self.names[i] for i in l1],  [self.names[i] for i in l2]
