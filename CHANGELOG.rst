new version
===========

0.14.1
======

- fixed broken source distribution #388

0.14.0
======

- test and release for Python 3.9 too #384
- fix cibuildwheel #382
Thanks Brian for the following two PRs. That's awesome!
- Feature arbitrary (byte)-size encodings #366
- Creates a cython wrapper for the similarity comparison C++ code and removes the cffi compiler. #363

0.13.1
======

- Relaxed requirements for clkhash dependency to allow newer versions. (#318)
- Improved test coverage. (#320)

0.13.0
======

- Adds support for Windows including accelerated extensions. Note performance on Windows is
  roughly half that of Linux.
- Switch to using a fork of `bitarray` that distributes binary wheels.

0.12.5
======

- Feature azure pipeline (#223)
- Delete Jenkinsfile. (#226)
- Fix flaky test (#225)
- Fix tar.gz release file
- Updates hypothesis (#231)
- Build and test wheel for each Python version in manylinux1 container (#232)
- Build wheels for multiple platforms (#234)
- Get azure to install and import the previously built wheel (#233)
- Azure Pipelines: Publish wheel for OSX (#235)

0.12.4
======

- Update broken GRLC link in docs
- Add cython dependency to setup.py

0.12.3
======

- Tweak twine upload to exclude non anonlink packages
- Update clkhash and cython requirement

0.12.2
======

- Automatic release from travis-ci now includes sdist and manylinux wheel.
- Update requirements.

0.12.0
======

- Removes deprecated API.
- Minor housekeeping moving to a new home at github.com/data61/anonlink
- PyPi release should be automatically made by travis-ci

0.11.2
======

- Fixes an issue that caused the loading functions in `anonlink.serialization` to raise when loading from Minio objects.

0.11.1
======

- Fixes an issue that prevented anonlink being installed from a .tar.gz archive. This caused installations from PyPI to fail.

0.11.0
======

Major changes:
--------------
- The greedy solver has been ported to C++, bringing performance improvements. The pure Python version remains in the package as `anonlink.solving.greedy_solve_python`.
- Candidate pair generation now supports blocking. Some blocking functions are defined in `anonlink.blocking` but custom ones may be defined.
- New utilities assist in analysis of similarity scores. They can help an analyst find a good threshold or determine the quality of the linkage, and can be found in `anonlink.stats`. Examples are located in `docs/examples/similarity-plots`.
- Adds a _probabilistic_ multiparty greedy solver. It generally yields more accurate results than the previous multiparty greedy solver. It is able to infer that some pairs match even they are below the similarity threshold.

Minor changes:
--------------
- The `hamming_similarity` in the `similarities` module is renamed to `simple_matching_coefficient`, which is the canonical name for this similarity measure. `hamming_similarity` is now a deprecated alias.
- `anonlink.similarities` is now imported whenever `anonlink` is imported. This means that `anonlink.similarities` no longer has to be imported separately.
- The new helper function `anonlink.solving.pairs_from_groups` turns the output of the greedy solver (a set of groups) into an iterable of pairs for bipartite problems.
- Dice similarity functions now support `bytes` as input. Previously the inputs had to be `bitarray`s.
- Mypy typing is enforced in the automated tests.
- Adds a heuristic for estimating the quality of the linkage, `anonlink.stats.nonmatch_index_score`.

0.10.0
======

Major changes:
-------------
- Adds ability to serialise similarities into an iterable of bytes, instead of into a stream.
  - Similarly, files with serialised similarities can now be serialised into an iterable of bytes.

Minor changes:
-------------
- Some flaky tests were adjusted to allow occasional mismatches.
- Minor changes to type annotations.
- The greedy solver is now tested with Hypothesis.
- Use of the old API generates ``DeprecationWarning``.
- Similarity serialisation functions that write to file return the number of bytes written.

0.9.0
=====

This release contains a major overhaul of Anonlink’s API and introduces support for multi-party linkage.

The changes are all additive, so the previous API continues to work. That API has now been deprecated and will be removed in a future release. The deprecation timeline is:
- v0.9.0: old API deprecated
- v0.10.0: use of old API raises a warning
- v0.11.0: remove old API

Major changes
-------------
- Introduce abstract similarity functions. The Sørensen–Dice coefficient is now just one possible similarity function.
  - Implement Hamming similarity as a similarity function.
  - Permit linkage of records other than CLKs (BYO similarity function).
  - Similarity functions now return multiple contiguous arrays instead of a list of tuples.
  - Candidate pairs from similarity functions are now always sorted.
- Introduce a standard type for storing candidate pairs. This is now used consistently throughout the API.
- Provide a function for multiparty candidate generation. It takes multiple datasets and compares them against each other using a similarity function.
- Extend the greedy solver to multiparty problems.
  - The greedy solver also takes the new candidate pairs type.
- Implement serialisation and deserialisation of candidate pairs.
  - Multiple files with serialised candidate pairs can be merged without loading everything into memory at once.
- Introduce type annotations in the new API.

Minor changes
-------------
- Automatically test on Python 3.7.
- Remove support for Python 3.5 and below.
- Update Clkhash dependency to 0.11.
- Minor documentation and style in ``anonlink.concurrency``.
- Provide a convenience function for generating valid candidate pairs from a chunk.
- Change the format of a chunk and move the type definition to ``anonlink.typechecking``.

New modules
-----------
- ``anonlink.blocking``: Implementation of functions that assign blocks to every record. These are generally used to optimise matching.
- ``anonlink.candidate_generation``: Finding candidate pairs from multiple datasets using a similarity function.
- ``anonlink.serialization``: Tools for serialisation and deserialisation of candidate pairs. Also permits efficient merging multiple files of serialised candidate pairs.
- ``anonlink.similarities``: Exposes different similarity functions that can be used to compare records. Currently implemented are ``hamming_similarity`` and ``dice_coefficient``.
- ``anonlink.solving``: Exposes solvers that can be used to turn candidate pairs into a concrete matching. Currently, only the ``greedy_solve`` function is exposed.
- ``anonlink.typechecking``: Types for Mypy and other typecheckers.

Deprecated modules
------------------
- ``anonlink.bloommatcher`` is replaced by ``anonlink.similarities``. The Tanimoto coefficient functions currently have no replacement.
- ``anonlink.distributed_processing`` is deprecated with no replacement.
- ``anonlink.network_flow`` is deprecated with no replacement.
- ``anonlink.util`` is deprecated with no replacement.

New usage examples
------------------
Before
~~~~~~
.. code-block:: python

   >>> dataset0[0]
   (bitarray('0111101001001100101001001010101000100100010010011011010110110000'),
    0,
    28)
   >>> dataset1[0]
   (bitarray('1100101101001110100001110000110000110101110010101001010001110100'),
    3,
    30)
   >>> candidate_pairs = anonlink.entitymatch.calculate_filter_similarity(
           dataset0, dataset1, k=len(dataset1), threshold=0.7)
   >>> candidate_pairs[0:3]
   [(1, 0.75, 6), (1, 0.75, 96), (1, 0.7457627118644068, 13)]
   >>> mapping = anonlink.entitymatch.greedy_solver(candidate_pairs)
   >>> mapping
   {1: 6,
    2: 44,
    3: 86,
    4: 4,
    5: 61,
    6: 10,
    ...

After
~~~~~~
- The function generating candidate pairs needs only the bloom filters. It does not need the record indices or the popcounts.
- The same function returns a tuple of arrays, instead of a list of tuples.
- The solvers return groups of 2-tuples (dataset index, record index) instead of a mapping.

.. code-block:: python

   >>> dataset0[0]
   bitarray('0111101001001100101001001010101000100100010010011011010110110000')
   >>> dataset1[0]
   bitarray('0101001110110000101110101101110000110001010000000011010010100011')
   >>> datasets = [dataset0, dataset1]
   >>> candidate_pairs = anonlink.candidate_generation.find_candidate_pairs(
           datasets,
           anonlink.similarities.dice_coefficient,
           0.7)
   >>> candidate_pairs[0][:3]
   array('d', [1.0, 0.9850746268656716, 0.9841269841269841])
   >>> candidate_pairs[1][0][:3]
   array('I', [0, 0, 0])
   >>> candidate_pairs[1][1][:3]
   array('I', [1, 1, 1])
   >>> candidate_pairs[2][0][:3]
   array('I', [85, 66, 83])
   >>> candidate_pairs[2][1][:3]
   array('I', [82, 62, 79])
   >>> groups = anonlink.solving.greedy_solve(candidate_pairs)
   >>> groups
   ([(0, 85), (1, 82)],
    [(0, 66), (1, 62)],
    [(0, 83), (1, 79)],
    [(0, 49), (1, 44)],
    [(0, 20), (1, 22)],
    ...

0.8.2
=====

Fix discrepancies between Python and C++ versions #102
Utility added to ``anonlink/concurrency.py`` help with chunking.
Better Github status messages posted by jenkins.

0.8.1
=====

Minor updates and fixes. Code cleanup.
- Remove checking of chunk size to prevent crashes on small chunks.

0.8.0
=====

Fix to greedy solver, so that mappings are set by the first match, not repeatedly overwritten. #89

Other improvements
------------------

- Order of k and threshold parameters now consistent across library
- Limit size of `k` to prevent OOM DoS
- Fix misaligned pointer handling #77

0.7.1
=====
Removed the default values for the threshold and "top k results" parameters
throughout as these parameters should always be determined by the requirements
at the call site. This modifies the API of the functions
`entitymatch.{*filter_similarity*,calculate_mapping_greedy}`,
`distributed_processing.calculate_filter_similarity` and
`network_flow.map_entities` by requiring the values of `k` and `threshold` to
be specified in every case.

0.7.0
=====

Introduces support for comparing "arbitrary" length cryptographic linkage keys.
Benchmark is much more comprehensive and more comparable between releases - see the
readme for an example report.

Other improvements
------------------

- Internal C/C++ cleanup/refactoring and optimization.
- Expose the native popcount implementation to Python.
- Bug fix to avoid configuring a logger.
- Testing is now with `py.test` and runs on [travis-ci](https://travis-ci.org/data61/anonlink/)

0.6.3
=====

Small fix to logging setup.

0.6.2 - Changelog init
======================

``anonlink`` computes similarity scores, and/or best guess matches between two sets
of *cryptographic linkage keys* (hashed entity records).
