0.8.2
-----

Fix discrepancies between Python and C++ versions #102
Utility added to ``anonlink/concurrency.py`` help with chunking.
Better Github status messages posted by jenkins.

0.8.1
-----

Minor updates and fixes. Code cleanup.
- Remove checking of chunk size to prevent crashes on small chunks.

0.8.0
-----

Fix to greedy solver, so that mappings are set by the first match, not repeatedly overwritten. #89

Other improvements
~~~~~~~~~~~~~~~~~~

- Order of k and threshold parameters now consistent across library
- Limit size of `k` to prevent OOM DoS
- Fix misaligned pointer handling #77

0.7.1
-----
Removed the default values for the threshold and "top k results" parameters
throughout as these parameters should always be determined by the requirements
at the call site. This modifies the API of the functions
`entitymatch.{*filter_similarity*,calculate_mapping_greedy}`,
`distributed_processing.calculate_filter_similarity` and
`network_flow.map_entities` by requiring the values of `k` and `threshold` to
be specified in every case.

0.7.0
-----

Introduces support for comparing "arbitrary" length cryptographic linkage keys.
Benchmark is much more comprehensive and more comparable between releases - see the
readme for an example report.

Other improvements
~~~~~~~~~~~~~~~~~~

- Internal C/C++ cleanup/refactoring and optimization.
- Expose the native popcount implementation to Python.
- Bug fix to avoid configuring a logger.
- Testing is now with `py.test` and runs on [travis-ci](https://travis-ci.org/n1analytics/anonlink/)

0.6.3
-----

Small fix to logging setup.

0.6.2 - Changelog init
---------------------

``anonlink`` computes similarity scores, and/or best guess matches between two sets
of *cryptographic linkage keys* (hashed entity records).

