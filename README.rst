
.. image:: https://github.com/data61/anonlink/actions/workflows/unittests.yml/badge.svg?branch=main
    :target: https://github.com/data61/anonlink/actions/workflows/unittests.yml

.. image:: https://codecov.io/gh/data61/anonlink/branch/main/graph/badge.svg?token=04DblXwUsT
    :target: https://codecov.io/gh/data61/anonlink

.. image:: https://pepy.tech/badge/anonlink
    :target: https://pepy.tech/project/anonlink


A Python (and optimised C++) implementation of **anonymous linkage** using
*cryptographic linkage keys* as described by Rainer Schnell, Tobias
Bachteler, and Jörg Reiher in `A Novel Error-Tolerant Anonymous Linking
Code <http://grlc.german-microsimulation.de/wp-content/uploads/2017/05/downloadwp-grlc-2011-02.pdf>`__.

``anonlink`` computes similarity scores, and/or best guess matches between sets
of *cryptographic linkage keys* (hashed entity records).

Use `clkhash <https://github.com/data61/clkhash>`__ to create cryptographic linkage keys
from personally identifiable data.

Installation
============

Install a precompiled wheel from PyPi::

    pip install anonlink

Or install from source using `uv <https://docs.astral.sh/uv/>`__::

    uv sync


Benchmark
---------

You can run the benchmark with ``python -m anonlink.benchmark`` (or ``uv run python -m anonlink.benchmark``).

The following results were obtained on an Apple M1 (ARM):

::

    $ python -m anonlink.benchmark
    Anonlink benchmark -- see README for explanation
    ------------------------------------------------
    using 'greedy_solve_native' as solver and 'dice_coefficient_accelerated' as similarity metric

    Threshold: 0.5, All results returned
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  (48.94%) |  0.201  (59.2% / 40.8%) |     8.426
      2000 |   2000 |    4e6  (49.95%) |  1.344  (37.1% / 62.9%) |     8.025
      3000 |   3000 |    9e6  (50.11%) |  3.204  (36.0% / 64.0%) |     7.799
      4000 |   4000 |   16e6  (49.86%) |  5.873  (35.3% / 64.7%) |     7.725

    Threshold: 0.5, Top 100 matches per record returned
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  ( 6.79%) |  0.064  (84.6% / 15.4%) |    18.503
      2000 |   2000 |    4e6  ( 3.23%) |  0.134  (85.9% / 14.1%) |    34.651
      3000 |   3000 |    9e6  ( 2.07%) |  0.220  (86.7% / 13.3%) |    47.213
      4000 |   4000 |   16e6  ( 1.53%) |  0.310  (86.2% / 13.8%) |    59.837
      5000 |   5000 |   25e6  ( 1.18%) |  0.414  (85.7% / 14.3%) |    70.435
      6000 |   6000 |   36e6  ( 0.98%) |  0.524  (86.7% / 13.3%) |    79.239
      7000 |   7000 |   49e6  ( 0.83%) |  0.636  (86.3% / 13.7%) |    89.303
      8000 |   8000 |   64e6  ( 0.71%) |  0.794  (82.8% / 17.2%) |    97.306
      9000 |   9000 |   81e6  ( 0.64%) |  0.894  (86.1% / 13.9%) |   105.184
     10000 |  10000 |  100e6  ( 0.56%) |  1.034  (86.8% / 13.2%) |   111.325
     20000 |  20000 |  400e6  ( 0.27%) |  2.679  (87.3% / 12.7%) |   170.965

    Threshold: 0.7, All results returned
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  ( 0.01%) |  0.003  (99.0% /  1.0%) |   312.191
      2000 |   2000 |    4e6  ( 0.01%) |  0.011  (98.1% /  1.9%) |   356.224
      3000 |   3000 |    9e6  ( 0.01%) |  0.026  (99.0% /  1.0%) |   347.011
      4000 |   4000 |   16e6  ( 0.01%) |  0.045  (99.0% /  1.0%) |   358.368
      5000 |   5000 |   25e6  ( 0.01%) |  0.071  (98.9% /  1.1%) |   356.423
      6000 |   6000 |   36e6  ( 0.01%) |  0.098  (98.9% /  1.1%) |   370.163
      7000 |   7000 |   49e6  ( 0.01%) |  0.133  (98.9% /  1.1%) |   373.096
      8000 |   8000 |   64e6  ( 0.01%) |  0.172  (98.9% /  1.1%) |   377.015
      9000 |   9000 |   81e6  ( 0.01%) |  0.218  (98.9% /  1.1%) |   374.817
     10000 |  10000 |  100e6  ( 0.01%) |  0.272  (99.0% /  1.0%) |   371.551
     20000 |  20000 |  400e6  ( 0.01%) |  1.053  (99.0% /  1.0%) |   383.731

    Threshold: 0.7, Top 100 matches per record returned
    Size 1 | Size 2 | Comparisons      | Total Time (s)          | Throughput
           |        |        (match %) | (comparisons / matching)|  (1e6 cmp/s)
    -------+--------+------------------+-------------------------+-------------
      1000 |   1000 |    1e6  ( 0.01%) |  0.003  (98.9% /  1.1%) |   314.762
      2000 |   2000 |    4e6  ( 0.01%) |  0.011  (98.7% /  1.3%) |   357.730
      3000 |   3000 |    9e6  ( 0.01%) |  0.024  (98.9% /  1.1%) |   372.850
      4000 |   4000 |   16e6  ( 0.01%) |  0.044  (98.9% /  1.1%) |   363.783
      5000 |   5000 |   25e6  ( 0.01%) |  0.066  (98.9% /  1.1%) |   382.863
      6000 |   6000 |   36e6  ( 0.01%) |  0.095  (98.9% /  1.1%) |   383.880
      7000 |   7000 |   49e6  ( 0.01%) |  0.128  (98.9% /  1.1%) |   385.778
      8000 |   8000 |   64e6  ( 0.01%) |  0.171  (98.9% /  1.1%) |   377.762
      9000 |   9000 |   81e6  ( 0.01%) |  0.210  (99.0% /  1.0%) |   389.182
     10000 |  10000 |  100e6  ( 0.01%) |  0.275  (99.0% /  1.0%) |   367.465
     20000 |  20000 |  400e6  ( 0.01%) |  1.040  (99.0% /  1.0%) |   388.491


The tables are interpreted as follows. Each table measures the throughput
of the Dice coefficient comparison function. The four tables correspond to
two different choices of "matching threshold" and "result limiting".

These parameters have been chosen to characterise two different performance
scenarios. Since the data used for comparisons is randomly generated, the
first threshold value (`0.5`) will cause about 50% of the candidates to
"match", while the second threshold value (`0.7`) will cause ~0.01% of the
candidates to match (these values are reported in the "match %" column).
Where the table heading includes "All results returned", all matches above
the threshold are returned and passed to the solver.
With the threshold of `0.5`, the large number of matches means that much
of the time is spent keeping the candidates in order. Next we limit the
number of matches per record to the top 100 - which also must be above the
threshold.

In the final two tables we use the threshold value of `0.7`, this very
effectively filters the number of candidate matches down. Here the throughput
is determined primarily by the comparison code itself, adding the top 100
filter has no major impact.

Finally, the Total Time column includes indications as to the
proportion of time spent calculating the (sparse) similarity matrix
`comparisons` and the proportion of time spent `matching` in the
greedy solver. This latter is determined by the size of the similarity
matrix, which will be approximately `#comparisons * match% / 100`.

Tests
=====

Run unit tests with ``pytest``::

    $ uv run pytest -q
    9051 passed, 2 skipped in 12.87s

To enable slightly larger tests add the following environment variables:

-  INCLUDE_10K
-  INCLUDE_100K

Limitations
-----------

-  The linkage process has order n^2 time complexity - although algorithms exist to
   significantly speed this up. Several possible speedups are described
   in `Privacy Preserving Record Linkage with PPJoin <http://dbs.uni-leipzig.de/file/P4Join-BTW2015.pdf>`__.


Discussion
----------

If you run into bugs, you can file them in our `issue tracker <https://github.com/data61/anonlink/issues>`__
on GitHub.

There is also an `anonlink mailing list <https://groups.google.com/forum/#!forum/anonlink>`__
for development discussion and release announcements.

Wherever we interact, we strive to follow the `Python Community Code of Conduct <https://www.python.org/psf/codeofconduct/>`__.

Citing
======

Anonlink is designed, developed and supported by `CSIRO's Data61 <https://www.data61.csiro.au/>`__. If you use any part
of this library in your research, please cite it using the following BibTex entry::

    @misc{Anonlink,
      author = {CSIRO's Data61},
      title = {Anonlink Private Record Linkage System},
      year = {2017},
      publisher = {GitHub},
      journal = {GitHub Repository},
      howpublished = {\url{https://github.com/data61/anonlink}},
    }


License
-------

Copyright 2017 CSIRO (Data61)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
