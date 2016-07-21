#!/usr/bin/env python3.4

import click
import json
import csv

import anonlink
from anonlink import bloomfilter
from anonlink import randomnames


def log(m, color='red'):
    click.echo(click.style(m, fg=color), err=True)


@click.group("clkutil")
@click.version_option(anonlink.__version__)
@click.option('--verbose', '-v', is_flag=True,
              help='Enables verbose mode.')
def cli(verbose=False):
    """
    This command line application allows a user to hash their data into CLKs.

    Example:

        clkutil hash --keys secretkey1 secretkey2 private_data.csv output-clks.json


    All rights reserved Confidential Computing 2016.
    """



@cli.command()
@click.argument('input', type=click.File('r'))
@click.option('--keys', '-k', nargs=2, type=click.Tuple([str, str]), default=('test1', 'test2'))
@click.option('--schema', '-s', type=click.File('r'), default=None)
@click.argument('output', type=click.File('w'))
def hash(input, output, schema, keys):
    """Process data to create CLKs

    Given a file containing csv data as INPUT, and optionally a json document defining
    the expected schema, verify the schema, then hash the data to create CLKs writing
    to OUTPUT.

    Use "-" to output to stdout.
    """
    clk_data = []

    schema = load_schema(schema)

    log("Hashing data")
    reader = csv.reader(input)

    #log("Hashing with keys: {}".format(keys))

    for clk in bloomfilter.stream_bloom_filters(reader, schema, keys):
        clk_data.append(bloomfilter.serialize_bitarray(clk[0]).strip())
    json.dump(clk_data, output)
    log("CLK data written to {}".format(output.name))


@cli.command()
@click.argument('size', type=int, default=100)
@click.argument('output', type=click.File('w'))
@click.option('--schema', '-s', type=click.File('r'), default=None)
def generate(size, output, schema):
    """Generate fake PII data for testing"""
    pii_data = randomnames.NameList(size)

    if schema is not None:
        raise NotImplementedError

    randomnames.save_csv(pii_data.names, pii_data.schema, output)


def load_schema(schema_file):
    if schema_file is None:
        log("Assuming default schema")
        schema = ('INDEX', 'NAME freetext', 'DOB YYYY/MM/DD', 'GENDER M or F')
    else:
        log("Loading schema from file")
        schema = schema_file.read().strip().split(",")

        log("{}".format(schema))
    return schema


if __name__ == "__main__":
    cli()
