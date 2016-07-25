#!/usr/bin/env python3.4
import json
import os
import unittest
import random
from tempfile import NamedTemporaryFile, TemporaryFile
from click.testing import CliRunner

from anonlink.hashdata_cli import cli

import anonlink
from anonlink import randomnames

@unittest.skipUnless("INCLUDE_CLI" in os.environ,
                     "Set envvar INCLUDE_CLI to run. Disabled for jenkins")
class TestHasherDefaultSchema(unittest.TestCase):

    samples = 100

    def setUp(self):
        self.pii_file = NamedTemporaryFile('w', encoding='utf8')

        pii_data = randomnames.NameList(TestHasherDefaultSchema.samples)
        randomnames.save_csv(pii_data.names, pii_data.schema, self.pii_file)
        self.pii_file.flush()

    def test_cli_includes_help(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0

        assert 'Usage' in result.output
        assert 'Options' in result.output

    def test_version(self):
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])
        assert result.exit_code == 0
        self.assertIn(anonlink.__version__, result.output)

    def test_basic_hashing(self):
        runner = CliRunner()
        with NamedTemporaryFile() as output:
            cli_result = runner.invoke(cli, ['hash', self.pii_file.name, output.name])
            output.seek(0)
            json.loads(output.read().decode('utf-8'))


    def test_hashing_with_given_keys(self):
        runner = CliRunner()
        with NamedTemporaryFile() as output:
            cli_result = runner.invoke(cli,
                                       ['hash',
                                        '--keys', 'key1', 'key2',
                                        self.pii_file.name,
                                        output.name])
            output.seek(0)
            json.loads(output.read().decode('utf-8'))


@unittest.skipUnless("INCLUDE_CLI" in os.environ,
                     "Set envvar INCLUDE_CLI to run. Disabled for jenkins")
class TestHasherSimpleSchema(unittest.TestCase):

    samples = 100

    def setUp(self):
        self.pii_file = NamedTemporaryFile('w', encoding='utf8')
        self.schema_file = NamedTemporaryFile('w', encoding='utf8')

        pii_data = randomnames.NameList(TestHasherDefaultSchema.samples)
        data = [p[1] for p in pii_data.names]
        randomnames.save_csv(data, ('NAME freetext', ), self.pii_file)

        print('NAME freetext', file=self.schema_file)

        self.pii_file.flush()
        self.schema_file.flush()


    def test_hashing_given_schema(self):
        runner = CliRunner()

        with NamedTemporaryFile() as output:
            cli_result = runner.invoke(cli,
                                       ['hash',
                                        '-s', self.schema_file.name,
                                        self.pii_file.name,
                                        output.name])
            output.seek(0)
            json.loads(output.read().decode('utf-8'))

