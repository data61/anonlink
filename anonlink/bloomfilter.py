#!/usr/bin/env python3
import base64

from anonlink.identifier_types import basic_types

from anonlink import bloommatcher as bm
import logging
logging.basicConfig(level=logging.WARNING)


def cryptoBloomFilter(record, tokenizers, key1="test1", key2="test2"):
    """
    Make a bloom filter from a record with given tokenizers

    Using the method from
    http://www.record-linkage.de/-download=wp-grlc-2011-02.pdf

    :param record: record tuple. E.g. (index, name, dob, gender)
    :param tokenizers: A list of IdentifierType tokenizers (one for each record element)
    :param key1: key for first hash function
    :param key2: key for second hash function

    :return: 3-tuple - bitarray with bloom filter for record, index of record, bitcount
    """

    mlist = []
    for (entry, tokenizer) in zip(record, tokenizers):
        for token in tokenizer(entry):
            mlist.append(token)

    bf = bm.hbloom(mlist, keysha1=key1, keymd5=key2)

    return bf, record[0], bf.count()


def calculate_bloom_filters(dataset, schema, keys):
    """
    :param dataset: A list of indexable records.
    :param schema: An iterable of identifier type names.
    :param keys: A tuple of two secret keys used in the HMAC.
    :return: List of bloom filters as 3-tuples, each containing
             bloom filter (bitarray), index (int), bitcount (int)
    """
    return list(stream_bloom_filters(dataset, schema, keys))


def stream_bloom_filters(dataset, schema, keys):
    """
    Yield bloom filters

    :param dataset: An iterable of indexable records.
    :param schema: An iterable of identifier type names.
    :param keys: A tuple of two secret keys used in the HMAC.
    :return: Yields bloom filters as 3-tuples
    """
    schema_types = [basic_types[column] for column in schema]
    for s in dataset:
        yield cryptoBloomFilter(s, schema_types, key1=keys[0], key2=keys[1])


def serialize_bitarray(ba):
    """Serialize a bitarray (bloomfilter)

    """
    return base64.encodebytes(ba.tobytes()).decode('utf8')
